"""One pooled elastic-net model with optional race polling."""

from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .statistics import residual_distribution, score_predictions

FEATURES = [
    "partisan_lean",
    "national_environment",
    "dem_incumbent",
    "rep_incumbent",
    "midterm",
    "president_party",
    "senate",
    "senate_lean",
    "senate_dem_incumbent",
    "senate_rep_incumbent",
    "poll_deviation",
    "has_poll",
]
OPTIONS = [{"alpha": a, "l1_ratio": r} for a in [0.01, 0.1, 1.0] for r in [0.2, 0.8]]


def design(frame, mask_polls=False):
    x = frame.copy()
    x["senate"] = x.chamber.eq("senate").astype(float)
    x["national_environment"] = x.generic_dem_share - 50
    for field in ["partisan_lean", "dem_incumbent", "rep_incumbent"]:
        target = "senate_lean" if field == "partisan_lean" else "senate_" + field
        x[target] = x.senate * x[field]
    x["has_poll"] = (x.poll_dem_share.notna() & ~np.full(len(x), mask_polls)).astype(float)
    # A missing poll contributes no polling adjustment. It is never replaced by
    # the national median race poll, which would make safe seats look competitive.
    x["poll_deviation"] = np.where(
        x.has_poll.eq(1), x.poll_dem_share - (50 + x.partisan_lean + x.national_environment), 0.0
    )
    return x[FEATURES]


def fit(train, params):
    polled = train[train.poll_dem_share.notna()]
    x = pd.concat([design(train), design(polled, mask_polls=True)], ignore_index=True)
    y = np.concatenate([train.dem_share.to_numpy(), polled.dem_share.to_numpy()])
    # Each race has total weight one. Polled races appear once with polling and
    # once without it, so this same model learns both information settings.
    weight = np.concatenate(
        [np.where(train.poll_dem_share.notna(), 0.5, 1.0), np.full(len(polled), 0.5)]
    )
    pipeline = make_pipeline(
        SimpleImputer(strategy="median", keep_empty_features=True),
        StandardScaler(),
        ElasticNet(**params, max_iter=50000, tol=1e-5),
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        pipeline.fit(x, y, elasticnet__sample_weight=weight)
    if any(issubclass(w.category, ConvergenceWarning) for w in caught):
        raise RuntimeError("Elastic net did not converge")
    return pipeline


def predict(model, frame, mask_polls=False):
    values = np.clip(model.predict(design(frame, mask_polls)), 0, 100)
    if not np.isfinite(values).all():
        raise ValueError("Nonfinite forecast")
    return values


def calibrate(frame, values, residuals):
    probabilities, lower, upper = (
        np.full(len(frame), np.nan),
        np.full(len(frame), np.nan),
        np.full(len(frame), np.nan),
    )
    for chamber in ["house", "senate"]:
        for polled in [False, True]:
            idx = np.flatnonzero(
                frame.chamber.eq(chamber) & frame.poll_dem_share.notna().eq(polled)
            )
            pool = [r for r in residuals if r["chamber"] == chamber and r["polled"] == polled]
            if len({r["cycle"] for r in pool}) < 2:
                pool = [r for r in residuals if r["chamber"] == chamber]
            if len(idx):
                probabilities[idx], lower[idx], upper[idx] = residual_distribution(
                    pool, values[idx]
                )
    return probabilities, lower, upper


def run(history, target):
    assert history.cycle.max() < target.cycle.min()
    assert "dem_share" not in target
    parameter_scores = [[] for _ in OPTIONS]
    validations, scores, tuning, residuals, masked_scores = [], [], [], [], []
    # Both chambers have at least three completed training cycles by 2018.
    for year in sorted(y for y in history.cycle.unique() if y >= 2018):
        train, test = history[history.cycle.lt(year)], history[history.cycle.eq(year)].copy()
        selected = (
            int(np.argmin([np.mean(s) for s in parameter_scores])) if len(validations) >= 2 else 0
        )
        models = [fit(train, p) for p in OPTIONS]
        candidates = [predict(m, test) for m in models]
        values = candidates[selected]
        probability, lower, upper = calibrate(test, values, residuals)
        test["prediction"], test["p_dem_two_party_majority"] = values, probability
        test["lower_95"], test["upper_95"] = lower, upper
        test["trained_through"], test["params"] = (
            int(train.cycle.max()),
            json.dumps(OPTIONS[selected]),
        )
        masked = predict(models[selected], test, mask_polls=True)
        validations.append(test)
        for chamber in ["house", "senate"]:
            g = test[test.chamber.eq(chamber)]
            args = (
                (g.p_dem_two_party_majority, g.lower_95, g.upper_95)
                if g.p_dem_two_party_majority.notna().all()
                else ()
            )
            scores.append(
                {
                    "cycle": int(year),
                    "chamber": chamber,
                    **score_predictions(g.dem_share, g.prediction, *args),
                }
            )
            mask = test.chamber.eq(chamber)
            masked_scores.append(
                {
                    "cycle": int(year),
                    "chamber": chamber,
                    **score_predictions(test.loc[mask, "dem_share"], masked[mask]),
                }
            )
        residuals.extend(
            {
                "cycle": int(year),
                "chamber": row.chamber,
                "polled": bool(pd.notna(row.poll_dem_share)),
                "error": float(row.dem_share - row.prediction),
            }
            for row in test.itertuples()
        )
        # Select future settings only after this year's forecast has been recorded.
        for i, candidate in enumerate(candidates):
            errors = [
                np.sqrt(
                    np.mean(
                        (test.loc[test.chamber.eq(c), "dem_share"] - candidate[test.chamber.eq(c)])
                        ** 2
                    )
                )
                for c in ["house", "senate"]
            ]
            error = float(np.mean(errors))
            parameter_scores[i].append(error)
            tuning.append({"cycle": int(year), **OPTIONS[i], "equal_chamber_rmse": error})
    selected = int(np.argmin([np.mean(s) for s in parameter_scores]))
    model = fit(history, OPTIONS[selected])
    forecast = target.copy()
    forecast["prediction"] = predict(model, target)
    p, lo, hi = calibrate(target, forecast.prediction.to_numpy(), residuals)
    forecast["p_dem_two_party_majority"], forecast["lower_95"], forecast["upper_95"] = p, lo, hi
    forecast["projected_party"] = np.where(
        forecast.prediction.gt(50), forecast.left_party, forecast.right_party
    )
    forecast["projected_candidate"] = np.where(
        forecast.prediction.gt(50), forecast.left_candidate, forecast.right_candidate
    )
    for party, share in [("DEM", 100.0), ("REP", 0.0)]:
        fixed = forecast.fixed_party.eq(party)
        forecast.loc[fixed, ["prediction", "lower_95", "upper_95", "p_dem_two_party_majority"]] = (
            np.nan
        )
        forecast.loc[fixed, "projected_party"] = party
        forecast.loc[fixed, "projected_candidate"] = forecast.loc[
            fixed, "left_candidate" if party == "DEM" else "right_candidate"
        ]
    # D/R residual calibration does not establish candidate probabilities in
    # independent, RCV, or runoff contests. Keep point estimates, label transfers.
    transfer = forecast.race_kind.ne("D/R")
    forecast.loc[transfer, "p_dem_two_party_majority"] = np.nan
    coefficients = dict(zip(FEATURES, map(float, model[-1].coef_)))
    meta = {
        "family": "Elastic net",
        "fit": "One pooled House and Senate estimator",
        "params": OPTIONS[selected],
        "features": FEATURES,
        "standardized_coefficients": coefficients,
        "intercept": float(model[-1].intercept_),
        "training_rows": len(history),
        "training_by_chamber": history.groupby("chamber").size().to_dict(),
        "training_years": {
            c: sorted(map(int, g.cycle.unique())) for c, g in history.groupby("chamber")
        },
        "tuning": tuning,
        "calibration": "Earlier-cycle errors by chamber and availability of race polling",
        "kind": "retrospective_exploratory",
        "cutoff": "2026-11-02",
    }
    return (
        forecast,
        pd.concat(validations),
        pd.DataFrame(scores),
        pd.DataFrame(masked_scores),
        residuals,
        meta,
        model,
    )
