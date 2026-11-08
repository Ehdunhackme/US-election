"""Article and figures for the complete-roster, single-model experiment."""

from __future__ import annotations

import json

import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, Rectangle
import numpy as np
import pandas as pd

from .charts import Figures
from .geometry import state_paths, label_center


def national_map(artist, root, forecast, chamber):
    rows = forecast[forecast.chamber.eq(chamber)]
    counts = rows.projected_party.value_counts()
    total = len(rows)
    fig = plt.figure(figsize=(5.2 if artist.mobile else 10.4, 5.1 if artist.mobile else 8.2))
    fig.text(
        0.025,
        0.98,
        f"{chamber.title()} seat projections",
        va="top",
        fontsize=15 if artist.mobile else 18,
    )
    subtitle = (
        "435 districts across all 50 states"
        if chamber == "house"
        else "All 35 contests on the 2026 ballot"
    )
    fig.text(
        0.025,
        0.91 if artist.mobile else 0.93,
        subtitle,
        va="top",
        fontsize=10 if artist.mobile else 11,
        color=artist.muted,
    )
    d, r, i = [int(counts.get(p, 0)) for p in ["DEM", "REP", "IND"]]
    bar = fig.add_axes([0.025, 0.74 if artist.mobile else 0.79, 0.95, 0.12])
    bar.set(xlim=(0, total), ylim=(0, 1))
    bar.axis("off")
    size = 11 if artist.mobile else 14
    bar.text(0, 0.96, f"Democrats  {d}", color=artist.blue, fontsize=size, va="top")
    bar.text(
        total, 0.96, f"{r}  Republicans", color=artist.red, fontsize=size, va="top", ha="right"
    )
    start = 0
    for count, color in [(d, artist.blue), (i, "#c5b271"), (r, artist.red)]:
        if count:
            bar.add_patch(Rectangle((start, 0.28), count, 0.24, facecolor=color))
        start += count
    if i:
        bar.text(d + i / 2, 0.15, f"{i} independent", ha="center", fontsize=9, color=artist.muted)
    if chamber == "house":
        bar.plot([218, 218], [0.23, 0.58], color=artist.ink, lw=1)
        bar.text(
            218, 0.08, "218 for a majority", ha="center", va="top", fontsize=9, color=artist.muted
        )
    ax = fig.add_axes([0.005, 0.105, 0.985, 0.61 if artist.mobile else 0.66])
    ax.set(xlim=(-5, 1065), ylim=(615, -5), aspect="equal")
    ax.axis("off")
    reference = pd.read_csv(root / "data/reference/state-codes.csv")
    fips = {
        str(int(row.state_fips)).zfill(2): row.state_po
        for row in reference.itertuples()
        if row.state_po != "DC"
    }
    neutral = "#353535" if artist.dark else "#e7e7e3"
    labels = []
    small = {
        "VT": (1000, 155),
        "NH": (1040, 180),
        "MA": (1040, 210),
        "RI": (1040, 240),
        "CT": (1040, 270),
        "NJ": (1040, 300),
        "DE": (1040, 330),
        "MD": (1040, 360),
    }
    states = rows.groupby("state").projected_party.value_counts().unstack(fill_value=0)
    for code, path, rings in state_paths(
        json.loads((root / "assets/maps/states-albers-10m.json").read_text())
    ):
        state = fips.get(code)
        if state is None:
            continue
        party = None
        if state in states.index:
            count = states.loc[state]
            maximum = count.max()
            leaders = count[count.eq(maximum)].index
            party = leaders[0] if len(leaders) == 1 else "TIE"
            color = {"DEM": artist.blue, "REP": artist.red, "IND": "#c5b271"}.get(party, neutral)
        else:
            color = neutral
        if party == "TIE":
            ax.add_patch(
                PathPatch(path, facecolor=artist.blue, edgecolor=artist.red, hatch="////", lw=0)
            )
            ax.add_patch(
                PathPatch(
                    path, facecolor="none", edgecolor=artist.bg, lw=0.65 if artist.mobile else 1
                )
            )
        else:
            ax.add_patch(
                PathPatch(
                    path, facecolor=color, edgecolor=artist.bg, lw=0.65 if artist.mobile else 1
                )
            )
        if chamber == "house" or state in states.index:
            center = label_center(rings)
            if state == "FL":
                center = center + np.array([22, 30])
            if state in small:
                x, y = small[state]
                ax.plot([center[0], x - 10], [center[1], y], color=artist.muted, lw=0.5)
                labels.append((x, y, state, artist.ink))
            else:
                color_text = (
                    artist.ink
                    if color == neutral and party != "TIE"
                    else "#1a1a1a"
                    if artist.dark
                    else "white"
                )
                labels.append((*center, state, color_text))
    for x, y, label, color in labels:
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=7.6 if artist.mobile else 10,
            color=color,
        )
    foot = (
        "Colour: party with more projected House seats\nStripes: equal seat counts"
        if chamber == "house"
        else "Grey: no Senate election in 2026"
    )
    fig.text(0.025, 0.05, foot, fontsize=9 if artist.mobile else 10, color=artist.muted)
    artist.save(fig, f"2026-{chamber}-map")


def interval_chart(artist, forecast, chamber):
    group = forecast[forecast.chamber.eq(chamber) & forecast.prediction.notna()].copy()
    if chamber == "house":
        group = group.iloc[np.argsort(abs(group.prediction - 50).to_numpy())[:25]]
    group = group.sort_values("prediction", ascending=False)
    title = "The 25 closest House projections" if chamber == "house" else "Every Senate contest"
    chunks = [
        group.iloc[x]
        for x in np.array_split(
            np.arange(len(group)), 2 if chamber == "senate" and not artist.mobile else 1
        )
    ]
    subtitle = "Left-side two-candidate share (%) · point estimates and 95% D/R error ranges"
    fig, axes = artist.canvas(title, subtitle, len(chunks), max(4, len(chunks[0]) * 0.26))
    for ax, g in zip(axes, chunks):
        y = np.arange(len(g))
        for yy, row in zip(y, g.itertuples()):
            color = {"DEM": artist.blue, "REP": artist.red, "IND": "#c5b271"}[row.projected_party]
            ax.hlines(yy, row.lower_95, row.upper_95, color=artist.neutral, lw=1.3)
            ax.scatter(row.prediction, yy, s=25, color=color, zorder=3)
            if pd.notna(row.poll_dem_share):
                ax.scatter(
                    row.poll_dem_share,
                    yy,
                    s=20,
                    facecolors=artist.bg,
                    edgecolors=artist.neutral,
                    lw=0.8,
                    zorder=2,
                )
            ax.text(94, yy, f"{row.prediction:.1f}", ha="right", va="center", fontsize=10)
        ax.set(ylim=(len(g) - 0.4, -1), xlim=(15, 96), xlabel="Two-candidate share (%)")
        labels = [row.label + ("*" if row.race_kind != "D/R" else "") for row in g.itertuples()]
        ax.set_yticks(y, labels)
        ax.axvline(50, lw=0.8, color=artist.muted, linestyle=(0, (3, 3)))
        artist.clean(ax)
        ax.set_xticks([20, 35, 50, 65, 80])
    fig.subplots_adjust(
        left=0.17 if artist.mobile else 0.08, wspace=0.3, bottom=0.65 / fig.get_figheight()
    )
    artist.save(fig, f"2026-{chamber}-intervals")


def no_poll_chart(artist, scores, masked):
    fig, axes = artist.canvas(
        "How the model performs without race polling",
        "Historical vote-share RMSE in percentage points",
        2,
        3.2,
    )
    for ax, chamber in zip(axes, ["house", "senate"]):
        normal = scores[scores.chamber.eq(chamber)]
        missing = masked[masked.chamber.eq(chamber)]
        ax.plot(
            normal.cycle,
            normal.rmse_pp,
            marker="o",
            ms=4,
            color=artist.blue,
            lw=1.5,
            label="Available polls",
        )
        ax.plot(
            missing.cycle,
            missing.rmse_pp,
            marker="o",
            ms=4,
            color=artist.neutral,
            lw=1.5,
            label="All race polls withheld",
        )
        ax.set_title(chamber.title(), loc="left", fontsize=12)
        ax.set_ylim(0, 9)
        artist.clean(ax, "y")
        ax.set_xticks(normal.cycle)
        ax.legend(frameon=False, fontsize=9, loc="upper left")
    artist.save(fig, "06-no-poll-validation")


def render_figures(root, out, history, forecast, validation, scores, masked):
    for dark, mobile in [(False, False), (True, False), (True, True)]:
        artist = Figures(out, root, dark, mobile)
        for chamber in ["house", "senate"]:
            national_map(artist, root, forecast, chamber)
            interval_chart(artist, forecast, chamber)
        artist.training(history)
        artist.validation(validation)
        artist.validation(validation, True)
        no_poll_chart(artist, scores, masked)
        artist.diagnostics(validation)


def article(root, out, history, forecast, validation, scores, masked, meta):
    blocks = []

    def h(text, id):
        blocks.append({"type": "heading", "text": text, "id": id})

    def p(text):
        blocks.append({"type": "paragraph", "text": text})

    def f(slug, alt, caption):
        blocks.append({"type": "figure", "slug": slug, "alt": alt, "caption": caption})

    def eq(text, latex):
        blocks.append({"type": "equation", "text": text, "latex": latex})

    def table(frame, summary=None):
        frame = frame.astype(object).where(pd.notna(frame), "Not estimated")
        blocks.append(
            {
                "type": "table",
                "columns": list(frame.columns),
                "rows": frame.values.tolist(),
                "summary": summary,
            }
        )

    counts = forecast.groupby("chamber").projected_party.value_counts().unstack(fill_value=0)

    def tally(c):
        return ", ".join(
            f"{int(counts.loc[c].get(party, 0))} {name}"
            for party, name in [
                ("DEM", "Democratic"),
                ("REP", "Republican"),
                ("IND", "independent"),
            ]
            if counts.loc[c].get(party, 0)
        )

    h("Model prediction", "model-prediction")
    p(
        f"The model projects {tally('house')} House seats. Across the 35 Senate seats up for election, it projects {tally('senate')} wins. The forecast covers every House district in all 50 states and every Senate contest, using a November 2 polling cutoff."
    )
    f(
        "2026-house-map",
        "House projection covering all 435 districts across 50 states",
        "Each state is coloured by the party projected to win the most House seats there. Stripes indicate equal seat counts. The bar counts individual districts, including single-party ballots. These are point projections, not certain outcomes.",
    )
    f(
        "2026-senate-map",
        "Senate projection covering all 35 contests on the 2026 ballot",
        "All 35 Senate contests, including the Florida and Ohio special elections. Grey states have no Senate election in 2026. The bar counts seats being contested, not the full 100-seat chamber.",
    )
    h("Model description", "model-description")
    p(
        f"We use one elastic-net regression for both chambers. It is fitted once to {len(history):,} historical races: {int(meta['training_by_chamber']['house']):,} House races from 2012 to 2024 and {int(meta['training_by_chamber']['senate']):,} Senate races from 2000 to 2024. Chamber indicators and interaction terms let the same model represent differences between House and Senate elections."
    )
    p(
        "For an ordinary Democratic versus Republican contest, the target is Democratic two-party vote share:"
    )
    eq("Democratic two-party vote share", r"y_i = 100\,\frac{D_i}{D_i + R_i}")
    p(
        "The predictors describe local partisanship, the national environment, incumbency and available race polling. House partisanship comes from the previous presidential vote on that election’s district boundaries. The 2026 inputs use the 2024 presidential vote on the 2026 maps."
    )
    table(
        pd.DataFrame(
            [
                [
                    "Partisanship",
                    "Previous presidential two-party share minus the national share; district level for House, state level for Senate",
                ],
                [
                    "National environment",
                    "Generic-ballot polling average, midterm indicator and president’s party",
                ],
                ["Incumbency", "Indicators for the Democratic and Republican incumbents"],
                [
                    "Chamber",
                    "Senate indicator and Senate interactions with partisanship and incumbency",
                ],
                [
                    "Race polling",
                    "Polling deviation from the local-plus-national baseline, and a poll-availability indicator",
                ],
            ],
            columns=["Predictor", "Definition"],
        )
    )
    eq(
        "Polling deviation from the local and national baseline",
        r"\delta_i = p_i - (50 + \ell_i + g_i)",
    )
    p(
        "Here p is the race polling share, ℓ is local partisan lean and g is the generic-ballot Democratic share minus 50. All are measured in percentage points."
    )
    p(
        "Without a race poll, the polling deviation and availability indicator are zero. The regression then uses the remaining predictors. During training, each polled race contributes one copy with polling and one copy without it, each with half weight. Every race has total weight one. This teaches the same fitted model to work in both information settings."
    )
    p(
        "Race polls use a 90-day window, a 14-day recency half-life and square-root sample-size weighting, with a cap on each pollster’s influence. Poll questions are matched to the current roster. Candidates listed on fusion ballot lines are assigned to their stated major party."
    )
    eq(
        "Weighted elastic-net objective",
        r"\begin{aligned}\mathcal{L} ={}& \frac{1}{2W}\sum_{i=1}^{n} w_i(y_i-\widehat y_i)^2 \\ &+ \alpha r\lVert\boldsymbol{\beta}\rVert_1 + \frac{\alpha(1-r)}{2}\lVert\boldsymbol{\beta}\rVert_2^2\end{aligned}",
    )
    p(
        "W is the sum of the training weights. The intercept is unpenalized; β contains the predictor coefficients."
    )
    p(
        f"Elastic net shrinks coefficients to reduce instability among correlated predictors. We test six penalty settings within this model family. Each validation year uses settings selected from earlier completed validation years; the first two use the declared starting setting. The final fit uses α = {meta['params']['alpha']:g} and r = {meta['params']['l1_ratio']:g}. Numeric imputation and scaling are fitted only on training rows."
    )
    f(
        "01-training-years",
        "Historical training coverage by election year",
        "Usable D/R contests with the required historical fundamentals. Same-party and uncontested races are not regression training labels. Florida 2016 is omitted where prior presidential shares on that map are missing.",
    )
    h("Historical validation", "historical-validation")
    p(
        "We predict 2018, 2020, 2022 and 2024 in chronological order. Each election is held out from its own training and parameter selection. These are model-development backtests, not an untouched evaluation of a model specified before those elections."
    )
    summary = (
        scores.groupby("chamber")[["rmse_pp", "mae_pp", "winner_accuracy"]].mean().reset_index()
    )
    summary.columns = [
        "Chamber",
        "Mean-cycle RMSE (pp)",
        "Mean-cycle MAE (pp)",
        "Correct D/R ordering",
    ]
    summary["Chamber"] = summary.Chamber.str.title()
    summary["Correct D/R ordering"] = summary["Correct D/R ordering"].map(
        lambda x: f"{100 * x:.1f}%"
    )
    table(summary.round(2))
    f(
        "02-historical-validation",
        "Historical predicted versus actual vote shares",
        "Each point is a held-out race. The dashed diagonal is perfect prediction. Panel RMSE pools races; the table weights election cycles equally.",
    )
    f(
        "03-close-races",
        "Validation for races predicted within five points of 50 percent",
        "All actual outcomes remain visible for races with predicted Democratic share between 45% and 55%, including large misses.",
    )
    p(
        "We also predict every validation race with its race polls withheld. This checks the behavior required for unpolled 2026 contests. Polls do not improve every chamber in every year, so their presence should not be treated as a guarantee of greater accuracy."
    )
    p(
        "The saved archive contains no 2024 House race polling, so those forecasts already use fundamentals. Historical Senate polling is available for that year."
    )
    f(
        "06-no-poll-validation",
        "Backtest errors with available polls and with all race polls withheld",
        "Both lines use the same fitted model and the same held-out races. Only the polling inputs change.",
    )
    h("Race estimates and uncertainty", "race-estimates")
    p(
        "For ordinary D/R contests, intervals come from earlier held-out errors, grouped by chamber and polling availability, with equal weight per historical election. When a subgroup has fewer than two prior cycles, calibration falls back to the chamber’s earlier errors. Probability and interval checks therefore begin in 2022."
    )
    coverage = scores[scores.coverage_95.notna()][
        ["cycle", "chamber", "brier", "coverage_95"]
    ].copy()
    coverage.columns = ["Election", "Chamber", "Brier score", "95% interval coverage"]
    coverage["95% interval coverage"] = coverage["95% interval coverage"].map(
        lambda x: f"{100 * x:.1f}%"
    )
    table(coverage.round(3))
    p(
        "Dots show point estimates, open circles show polling averages and lines show historical-error ranges. The House figure focuses on the 25 closest projections; the tables contain all 470 contests. An asterisk identifies a contest whose candidate or voting-rule treatment differs from an ordinary D/R race."
    )
    f(
        "2026-house-intervals",
        "Vote-share estimates for the 25 closest House projections",
        "The remaining House districts are included in the full table. For an independent transfer, the horizontal axis is the left-side candidate’s share against the selected opponent, as named in the table.",
    )
    f(
        "2026-senate-intervals",
        "Vote-share estimates for all 35 Senate contests",
        "The same scale is used across panels. Independent transfers and first-preference proxies use D/R historical-error ranges as a sensitivity reference, not calibrated candidate-win intervals.",
    )
    for chamber in ["senate", "house"]:
        g = forecast[forecast.chamber.eq(chamber)].sort_values("label").copy()
        g["prediction"] = g.prediction.map(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "Ballot composition"
        )
        g["range"] = g.apply(
            lambda r: (
                f"{r.lower_95:.1f}–{r.upper_95:.1f}%" if pd.notna(r.lower_95) else "Not applicable"
            ),
            axis=1,
        )
        frame = g[
            [
                "label",
                "left_candidate",
                "right_candidate",
                "prediction",
                "range",
                "projected_party",
                "input_basis",
                "race_kind",
            ]
        ]
        frame.columns = [
            "Race",
            "Left side",
            "Right side",
            "Left share",
            "Error range",
            "Projected party",
            "Inputs",
            "Treatment",
        ]
        table(frame, f"{chamber.title()} predictions ({len(g)} races)")
    h("Ballot rules and coverage", "ballot-rules")
    p(
        "A ballot containing candidates from only one major party fixes the party outcome without requiring a regression estimate. This includes same-party California runoffs and unopposed candidates. No artificial vote share or model-derived win probability is reported for these seats."
    )
    p(
        "In races led by an independent opposition candidate, we transfer the corresponding partisan baseline and add matched polling when available. Examples include Dan Osborn in Nebraska, Todd Achilles in Idaho, Bill Hill in Alaska and Kevin Kiley in California. Independents remain a separate party in the output. This transfer is an assumption; ordinary D/R backtests do not validate its candidate-win probabilities, so those probabilities are left unreported."
    )
    p(
        "Alaska and Maine estimates are first-preference proxies. Louisiana House estimates aggregate candidates by party before any possible runoff. These point projections do not model ballot transfers or the full runoff process. They remain in the coverage table rather than disappearing from the forecast."
    )
    table(
        forecast.groupby(["chamber", "input_basis"])
        .size()
        .rename("Races")
        .reset_index()
        .rename(columns={"chamber": "Chamber", "input_basis": "Inputs"})
    )
    h("Data and limitations", "data-and-limitations")
    p(
        "This analysis was constructed after Election Day. No 2026 results enter the model, its tuning or its validation. The November 2 cutoff is a retrospective date proxy: saved database and field dates do not establish an unchanged pre-election archive. The article is a modeling exercise, not a claim that these forecasts were issued before voting."
    )
    p(
        "Historical candidate rosters are reconstructed from election returns. Historical polling covers selected races and uses field-date proxies. District presidential tables are retrospective calculations, with some values rounded to whole percentages. National polling can miss a shared shift, candidate-specific effects are incomplete, and redistricting inputs can introduce error. Full geographic coverage does not remove these limitations."
    )
    p(
        "The seat bars count point-estimate leaders. They are not expected seat totals or probabilities of chamber control. Independent transfers, ranked-choice rules and common election errors require a richer joint simulation before those probabilities can be justified."
    )
    h("Residual diagnostics", "residual-diagnostics")
    f(
        "10-residual-diagnostics",
        "Historical forecast errors and normal Q-Q plots",
        "Errors are actual minus predicted vote share. Departures from the reference lines help describe the error distribution; they do not establish that the errors are independent or normally distributed.",
    )
    sources = [
        (
            "Official 2026 candidate roster",
            "https://clerk.house.gov/member_info/electionInfo/2026/120-nominations.pdf",
        ),
        ("House election returns", "https://doi.org/10.7910/DVN/IG0UN2"),
        ("Senate election returns", "https://doi.org/10.7910/DVN/PEJ5QU"),
        ("Presidential election returns", "https://doi.org/10.7910/DVN/42MVDX"),
        (
            "District presidential calculations and historical maps",
            "https://www.the-downballot.com/p/the-downballots-calculations-of-presidential",
        ),
        (
            "Historical polling",
            "https://github.com/fivethirtyeight/data/tree/master/pollster-ratings",
        ),
        ("2024 Senate polling", "https://github.com/Jack-Whitcomb/All-US-Senate-polls-2006-2024"),
        ("2026 House polling", "https://www.nytimes.com/newsgraphics/polls/house.csv"),
        ("2026 Senate polling", "https://www.nytimes.com/newsgraphics/polls/senate.csv"),
        ("Legislator service records", "https://github.com/unitedstates/congress-legislators"),
        ("State map boundaries", "https://github.com/topojson/us-atlas"),
        (
            "Louisiana election rules",
            "https://www.sos.la.gov/elections-voting/how-candidates-are-elected",
        ),
    ]
    payload = {
        "title": "2026 US Midterm Election Model",
        "date": "2026-11-08",
        "dateLabel": "8 Nov 2026",
        "note": "Retrospective analysis · November 2 polling cutoff (unverified)",
        "blocks": blocks,
        "sources": [{"label": label, "url": url} for label, url in sources],
        "reproducibility": "The companion files include all 470 projections, historical predictions, validation scores, model coefficients, source hashes and roster corrections. One fitted elastic-net model supplies every modeled race.",
    }
    assert "\u2014" not in json.dumps(payload, ensure_ascii=False)
    (out / "article.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    md = f"# {payload['title']}\n\n{payload['note']}\n\n"
    for block in blocks:
        kind = block["type"]
        if kind == "heading":
            md += f"## {block['text']}\n\n"
        elif kind == "paragraph":
            md += block["text"] + "\n\n"
        elif kind == "equation":
            md += "$$\n" + block["latex"] + "\n$$\n\n"
        elif kind == "figure":
            md += f"![{block['alt']}]({block['slug']}.png)\n\n{block['caption']}\n\n"
        elif kind == "table":
            md += (
                pd.DataFrame(block["rows"], columns=block["columns"]).to_html(index=False, border=0)
                + "\n\n"
            )
    md += "## Sources\n\n" + "\n".join(f"- [{label}]({url})" for label, url in sources) + "\n"
    (out / "midterms-model-blog.md").write_text(md, encoding="utf-8")
    return payload
