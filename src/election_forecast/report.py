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


def benchmark_chart(artist, meta):
    ranking = pd.DataFrame(meta["benchmark"]["leaderboard"])
    fig, (ax,) = artist.canvas(
        "Which model had the lowest error?",
        "2018–2024 · equal weight per chamber and election",
        panel_height=5.1,
    )
    names = ranking.method.str.replace(" correction", "", regex=False).replace(
        {"Histogram-boosting": "Histogram boosting", "Huber-boosting": "Huber boosting"}
    )
    y = np.arange(len(ranking))
    colors = [artist.blue] + [artist.neutral] * (len(y) - 1)
    ax.hlines(y, 0, ranking.selection_mae_pp, color=colors, lw=1.4)
    ax.scatter(ranking.selection_mae_pp, y, c=colors, s=35, zorder=3)
    for yy, value in zip(y, ranking.selection_mae_pp):
        ax.text(value + 0.13, yy, f"{value:.2f}", va="center", fontsize=10)
    ax.set_yticks(y, names, fontsize=10 if artist.mobile else 11)
    ax.set(xlim=(0, 5.2), ylim=(len(y) - 0.4, -0.7), xlabel="Mean absolute error (pp)")
    artist.clean(ax)
    ax.set_xticks([0, 2, 4])
    fig.subplots_adjust(left=0.39 if artist.mobile else 0.25, right=0.98)
    artist.save(fig, "05-benchmark-comparison")


def render_figures(root, out, history, forecast, validation, scores, masked, meta):
    for dark, mobile in [(False, False), (True, False), (True, True)]:
        artist = Figures(out, root, dark, mobile)
        for chamber in ["house", "senate"]:
            national_map(artist, root, forecast, chamber)
            interval_chart(artist, forecast, chamber)
        artist.training(history)
        benchmark_chart(artist, meta)
        artist.validation(validation)
        artist.validation(validation, True)
        no_poll_chart(artist, scores, masked)
        artist.diagnostics(validation)


def article(root, out, history, forecast, validation, scores, masked, meta):
    from .audit import validation_benchmarks

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
    house, senate = counts.loc["house"], counts.loc["senate"]
    checks = validation_benchmarks(validation, meta["family"])
    fitted = checks[checks.method.eq(meta["family"])].set_index("chamber")
    fixed_count = int(forecast.fixed_party.notna().sum())
    benchmark = meta["benchmark"]
    ranking = pd.DataFrame(benchmark["leaderboard"])

    h("Model prediction", "model-prediction")
    p(
        f"The model gives Democrats {int(house.get('DEM', 0))} House seats and Republicans {int(house.get('REP', 0))}. Among the 35 Senate seats being contested, it puts {int(senate.get('DEM', 0))} on the Democratic side and {int(senate.get('REP', 0))} on the Republican side. The Senate total leaves out the 65 seats that are not up for election."
    )
    p(
        "I built this on November 8, after the election. These maps reconstruct estimates from inputs dated November 2; they are not live results or a forecast published before voting. The bars count the party leading in each race, without calculating the probability of controlling either chamber."
    )
    f(
        "2026-house-map",
        "House estimates covering all 435 districts across 50 states",
        "Colour shows which party leads in more districts within each state. Stripes mark a tie. The bar counts all 435 districts, including seats assigned from the candidate roster.",
    )
    f(
        "2026-senate-map",
        "Senate estimates for all 35 contests in 2026",
        "Grey states have no Senate election this year. Florida and Ohio are included because they have special elections. The bar covers the 35 contests, not the full Senate.",
    )

    h("Model description", "model-description")
    p(
        "The final model is a weighted average: 75% race polling and 25% of a simple partisan baseline. If a race has no matched poll, it uses the baseline alone. I arrived at that choice by comparing 13 model families across past elections. The more complicated models did not improve on it under the scoring rule below."
    )
    p(
        "For a Democratic versus Republican race, I predict the Democratic share of votes cast for those two parties. Third-party votes are left out of the denominator:"
    )
    eq(
        "Democratic share of the Democratic and Republican vote",
        r"y_i = 100\,\frac{D_i}{D_i + R_i}",
    )
    p(
        "The baseline adds the national Democratic generic-ballot share, q, to local presidential lean, ℓ. Lean measures how much more Democratic or Republican a district or state is than the country. House figures use the district boundaries relevant to the election. Values are kept between 0 and 100:"
    )
    eq(
        "National generic ballot plus local presidential lean",
        r"b_i = \operatorname{clip}(q + \ell_i,\,0,\,100)",
    )
    p(
        "Where a matched race poll exists, its Democratic two-party share, p, gets three times the weight of the baseline:"
    )
    eq(
        "Poll and baseline blend with a fallback for unpolled races",
        r"\widehat y_i = \begin{cases}0.75p_i + 0.25b_i & \text{with a poll} \\ b_i & \text{without a poll}\end{cases}",
    )
    p(
        "I compared polling weights of 25%, 50%, 75% and 100%. Earlier-year tests selected 75% for each of the four evaluated elections and for the final model. This weight is the model's tuned setting; there are no fitted regression coefficients in the final estimate."
    )
    p(
        "The 2026 polling averages cover the preceding 90 days. A poll's time weight halves every 14 days, while sample size contributes through its square root. Repeated surveys from one pollster are capped at that pollster's strongest survey weight. Questions must match the selected candidates in the roster."
    )
    p(
        f"The comparison uses {len(history):,} historical D/R races: {int(meta['training_by_chamber']['house']):,} House races from 2012 to 2024 and {int(meta['training_by_chamber']['senate']):,} Senate races from 2000 to 2024. The regression and tree models also had access to incumbency, the election cycle and presidential party. Those extra inputs are not part of the winning blend."
    )
    f(
        "01-training-years",
        "Historical races available for the model comparison, by year",
        "Polled and unpolled D/R races with the required fundamentals. Same-party contests, uncontested races and special elections are excluded. Florida's 2016 House races are omitted because the required presidential figures are missing.",
    )

    h("Comparing the models", "historical-validation")
    p(
        "I fixed the comparison rules before running this expanded benchmark: 13 model families, 47 settings in total, and mean absolute error as the selection measure. An error of three percentage points means, for example, predicting 53% when the actual share is 50%."
    )
    p(
        "The tests move forward through 2018, 2020, 2022 and 2024. For each election, a model can fit and choose its settings using earlier years only. Tests on 2014 and 2016 supply the initial tuning history. I average the errors equally across elections and chambers, so the much larger House sample does not overwhelm the Senate."
    )
    f(
        "05-benchmark-comparison",
        "Historical error for all 13 model families",
        "Mean absolute error in two-party vote-share percentage points. Each chamber and test election has equal weight. Lower is better; blue marks the selected model.",
    )
    comparison = (
        ranking[["method", "selection_mae_pp", "house_mae_pp", "senate_mae_pp"]].copy().round(2)
    )
    comparison.columns = ["Model", "Overall MAE (pp)", "House MAE (pp)", "Senate MAE (pp)"]
    table(comparison, "Full benchmark results (13 models)")
    p(
        f"The blend has an average error of {benchmark['winner_mae_pp']:.2f} points, compared with {benchmark['baseline_mae_pp']:.2f} for the baseline, a reduction of {100 * benchmark['relative_improvement']:.1f}%. Most of that improvement comes from Senate races: 2.50 points versus 3.49. The House difference is much smaller, 2.63 versus 2.72."
    )
    p(
        "It does not win every year. In 2020, the blend did worse than the baseline in both chambers. In 2024 House races they are identical because the saved inputs contain no race polls. Removing any one of the four test elections still leaves the blend first overall, but four elections are a small sample."
    )
    p(
        f"There is a second catch: I chose the winning family after seeing these historical scores. A separate check chooses both the family and its settings using earlier years only. That procedure scores {benchmark['sequential_selection_mae_pp']:.2f} points, rather than {benchmark['winner_mae_pp']:.2f}. It is a useful reminder that choosing a winner and measuring its performance on the same comparison makes the headline result look better. These tests have also informed earlier versions of this project, so neither number is an untouched final test."
    )
    p(
        f"On a common set of close races, defined by a baseline share between 45% and 55%, the blend puts the D/R candidates in the right order {100 * fitted.loc['house', 'close_d_r_order_accuracy']:.1f}% of the time across {int(fitted.loc['house', 'close_n'])} House races and {100 * fitted.loc['senate', 'close_d_r_order_accuracy']:.1f}% across {int(fitted.loc['senate', 'close_n'])} Senate races. The baseline gets 81.3% and 63.2%, respectively. This subset is the same for every model, and the Senate sample is small."
    )
    f(
        "02-historical-validation",
        "Predicted and actual Democratic two-party vote shares",
        "Each dot is a past race predicted from earlier years. Points on the diagonal are exact predictions; outlined points put the D/R candidates in the wrong order.",
    )
    f(
        "03-close-races",
        "Historical races where the simple baseline predicts 45 to 55 percent Democratic share",
        "The common close-race subset used in the benchmark. Neither the winning model nor the actual result determines which races enter this chart.",
    )
    unpolled = (
        forecast[forecast.poll_dem_share.isna() & forecast.fixed_party.isna()]
        .groupby("chamber")
        .size()
    )
    p(
        f"With all race polling hidden, the selected model reduces to the simple baseline. That is also how it handles the {int(unpolled.get('house', 0))} House races and {int(unpolled.get('senate', 0))} Senate races without a matched poll in the 2026 inputs. Polling helps in some years and hurts in others:"
    )
    f(
        "06-no-poll-validation",
        "Vote-share errors with available race polls and with polls withheld",
        "Same test races and selected settings. Only the race-poll inputs change. RMSE gives extra weight to large errors; it is reported here but did not select the winner.",
    )

    h("Race estimates and uncertainty", "race-estimates")
    p(
        "The ranges come from the blend's mistakes in earlier test elections. I group those errors by chamber and polling availability, giving each past election equal weight. A group with fewer than two earlier cycles falls back to the chamber's full error history. Errors from 2014 and 2016 make it possible to start checking the ranges in 2018."
    )
    coverage = scores[scores.coverage_95.notna()][
        ["cycle", "chamber", "brier", "coverage_95"]
    ].copy()
    coverage["chamber"] = coverage.chamber.str.title()
    coverage["coverage_95"] = coverage.coverage_95.map(lambda x: f"{100 * x:.1f}%")
    coverage.columns = ["Election", "Chamber", "Brier score", "95% range coverage"]
    table(coverage.round(3), "Historical probability and range checks")
    p(
        "The nominal 95% ranges contain more than 98% of House results in each test year. They are fairly wide, not precisely calibrated. The Brier scores measure the model's probability of a Democratic majority of the D/R vote; lower is better. Neither check establishes the probability of controlling Congress."
    )
    f(
        "2026-house-intervals",
        "Estimates for the 25 closest House races",
        "All other districts are in the House list below. For a non-D/R matchup, the share refers to the first candidate shown in that list against the selected opponent.",
    )
    f(
        "2026-senate-intervals",
        "Estimates for all 35 Senate contests",
        "The ranges for independent candidates and ranked-choice races borrow D/R errors. They show how far an estimate could move under those errors; they are not validated candidate-win intervals.",
    )

    for chamber in ["senate", "house"]:
        g = forecast[forecast.chamber.eq(chamber)].sort_values("label").copy()
        for side in ["left", "right"]:
            g[f"{side}_candidate"] = g.apply(
                lambda row: (
                    f"{row[f'{side}_candidate']} ({row[f'{side}_party']})"
                    if pd.notna(row[f"{side}_candidate"])
                    else "No listed candidate"
                ),
                axis=1,
            )
        g["prediction"] = g.prediction.map(lambda x: f"{x:.1f}%" if pd.notna(x) else "From roster")
        g["range"] = g.apply(
            lambda row: (
                f"{row.lower_95:.1f}–{row.upper_95:.1f}%"
                if pd.notna(row.lower_95)
                else "Not estimated"
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
            "First candidate(s)",
            "Opponent(s)",
            "First side's share",
            "Error range",
            "Projected party",
            "Inputs",
            "Treatment",
        ]
        table(frame, f"{chamber.title()} predictions ({len(g)} races)")

    h("Races that need extra assumptions", "ballot-rules")
    p(
        f"In {fixed_count} House contests, every candidate in the saved roster belongs to the same party. I assign those seats to that party without inventing a vote share or choosing between same-party candidates. This follows the roster, rather than modelling write-ins or later ballot changes."
    )
    p(
        "Some races have an independent or minor-party opponent in place of a major-party candidate. I borrow the missing party's baseline and use matched polls where available. That is a rough assumption, especially for an independent whose supporters cross party lines. It is not tested by the historical D/R results. Candidate-win probabilities are left blank for these races, and party labels stay separate: for example, Alan Aversa is No Labels (NOL), not independent (IND)."
    )
    p(
        "Alaska and Maine estimates describe first-preference support, without simulating ranked-choice transfers. Louisiana's 2026 House elections still use the open-primary system, so I add candidates' shares within each party. Those totals cannot identify a runoff winner. Louisiana's Senate race uses the separate party-primary system."
    )

    h("What this analysis cannot establish", "data-and-limitations")
    p(
        "By November 8, AP-based result reporting had called Democratic majorities in both chambers. That context is known while writing this article, but no 2026 outcomes enter the numerical benchmark, model selection or calibration. I have not scored these estimates against the 2026 results. The November 2 cutoff uses field dates and database dates from files retrieved later. I cannot verify that every input was available in the same form before voting."
    )
    p(
        "The historical data also need care. Candidate rosters come from election returns, and the older polling archive selected the eventual top candidates. Some district presidential percentages are rounded. These are useful research inputs, but they do not recreate the exact information a forecaster had at the time."
    )
    p(
        "Finally, the seat bars simply count which party leads each estimate. They do not give the chance of winning Congress. A national polling miss could move many races together, and this model does not simulate that shared error. The benchmark supports using this blend on these saved inputs. It does not establish that the model is the best choice for a new election or a different data source."
    )
    h("A closer look at the errors", "residual-diagnostics")
    f(
        "10-residual-diagnostics",
        "Historical errors and normal Q-Q plots",
        "Positive errors mean the model underestimated the Democratic share. The Q-Q plots compare the error distribution with a normal distribution; they do not test whether races move independently.",
    )

    sources = [
        (
            "2026 reported results, ABC / Associated Press",
            "https://www.abc.net.au/news/2026-11-04/us-midterm-election-results-2026/107235570",
        ),
        (
            "2026 candidate roster, House Clerk",
            "https://clerk.house.gov/member_info/electionInfo/2026/120-nominations.pdf",
        ),
        ("House election returns", "https://doi.org/10.7910/DVN/IG0UN2"),
        ("Senate election returns", "https://doi.org/10.7910/DVN/PEJ5QU"),
        ("Presidential election returns", "https://doi.org/10.7910/DVN/42MVDX"),
        (
            "District presidential calculations",
            "https://www.the-downballot.com/p/the-downballots-calculations-of-presidential",
        ),
        (
            "Historical polling and archive notes",
            "https://github.com/fivethirtyeight/data/tree/master/pollster-ratings",
        ),
        (
            "2024 Senate polling archive",
            "https://github.com/Jack-Whitcomb/All-US-Senate-polls-2006-2024",
        ),
        ("2026 House polling", "https://www.nytimes.com/newsgraphics/polls/house.csv"),
        ("2026 Senate polling", "https://www.nytimes.com/newsgraphics/polls/senate.csv"),
        ("Legislator service records", "https://github.com/unitedstates/congress-legislators"),
        ("State map boundaries", "https://github.com/topojson/us-atlas"),
        (
            "Louisiana's 2026 election rules",
            "https://www.sos.la.gov/elections-voting/how-candidates-are-elected",
        ),
    ]
    payload = {
        "title": "2026 US Midterm Election Model",
        "date": "2026-11-08",
        "dateLabel": "8 Nov 2026",
        "note": "Written after Election Day · reconstructed November 2 inputs",
        "blocks": blocks,
        "sources": [{"label": label, "url": url} for label, url in sources],
        "reproducibility": "The repository contains the saved inputs, model code, race estimates and historical checks, including all 13 models, the settings tried and the selection protocol.",
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
