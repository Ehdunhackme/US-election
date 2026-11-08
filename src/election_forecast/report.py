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
    house = counts.loc["house"]
    senate = counts.loc["senate"]
    checks = validation_benchmarks(validation)
    fitted = checks[checks.method.eq("Elastic net")].set_index("chamber")
    fixed_count = int(forecast.fixed_party.notna().sum())

    h("Model prediction", "model-prediction")
    p(
        f"Adding up the district estimates gives Democrats {int(house.get('DEM', 0))} House seats and Republicans {int(house.get('REP', 0))}. For the 35 Senate seats being contested, the split is {int(senate.get('DEM', 0))} Democratic and {int(senate.get('REP', 0))} Republican. The maps cover all 50 states; the Senate total leaves out the 65 seats that are not up for election."
    )
    p(
        "The House margin is narrow. Given the errors in the historical tests below, I would not treat it as a reliable call for control of Congress. These are model estimates, not reported election results."
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
        f"I used elastic net, a linear regression that penalises large coefficients. It is fitted to {len(history):,} past races: {int(meta['training_by_chamber']['house']):,} House races from 2012 to 2024 and {int(meta['training_by_chamber']['senate']):,} Senate races from 2000 to 2024. One model handles both chambers, with extra terms that let Senate races respond differently to local partisanship and incumbency."
    )
    p(
        "For a Democratic versus Republican race, the target is the Democratic share of the votes cast for those two parties. Third-party votes are left out of this denominator:"
    )
    eq(
        "Democratic share of the Democratic and Republican vote",
        r"y_i = 100\,\frac{D_i}{D_i + R_i}",
    )
    p(
        "The starting information is fairly simple: how the district or state voted for president, the national generic ballot, whether either candidate is an incumbent, and any available race polls. The model also knows whether it is a midterm and which party holds the presidency. For the House, the presidential figures use the boundaries of the district being predicted."
    )
    p("Race polling enters as a departure from the local lean plus the national environment:")
    eq(
        "Race polling minus the local and national baseline",
        r"\delta_i = p_i - (50 + \ell_i + g_i)",
    )
    p(
        "Here p is the Democratic two-party polling share, ℓ is local presidential lean relative to the country, and g is the Democratic generic-ballot share minus 50. A separate indicator records whether a race poll exists."
    )
    p(
        "For an unpolled race, both polling terms are zero. To train for that situation, I include each polled historical race twice: once with its poll and once with the poll hidden. Each copy gets half weight in the regression loss. Unpolled races appear once with weight one."
    )
    p(
        "The 2026 poll averages use the preceding 90 days. A poll's time weight halves every 14 days, and sample size contributes through its square root. Repeated surveys from one pollster are capped at that pollster's strongest survey weight. Questions must match the selected candidates in the roster."
    )
    eq(
        "Weighted elastic-net loss",
        r"\begin{aligned}\mathcal{L} ={}& \frac{1}{2W}\sum_{i=1}^{n} w_i(y_i-\widehat y_i)^2 \\ &+ \alpha r\lVert\boldsymbol{\beta}\rVert_1 + \frac{\alpha(1-r)}{2}\lVert\boldsymbol{\beta}\rVert_2^2\end{aligned}",
    )
    p(
        f"W is the total training weight, and β contains the coefficients after the inputs are standardised. The intercept is not penalised. I tried six penalty settings; the final fit uses α = {meta['params']['alpha']:g} and r = {meta['params']['l1_ratio']:g}. Missing values and scaling are learned from the training rows. These settings are selected within elastic net; that does not make it the best forecasting method."
    )
    f(
        "01-training-years",
        "Number of historical training races by election year",
        "Training includes polled and unpolled D/R races with the required fundamentals. Same-party contests, uncontested races and special elections are excluded. Florida's 2016 House races are omitted because the required presidential figures are missing.",
    )

    h("How it did on past elections", "historical-validation")
    p(
        "I tested 2018, 2020, 2022 and 2024 in order, fitting each prediction on earlier elections. Penalty selection also uses earlier test years, with a fixed starting setting for the first two. These tests helped develop the model, so they are not an untouched final exam."
    )
    p(
        "A useful check is whether the regression beats a simpler estimate. The benchmark below just adds local presidential lean to the national Democratic generic-ballot share, then clips the result to 0–100. It has no fitted coefficients. Both methods are scored on exactly the same races, with each race weighted equally."
    )
    comparison = checks[["chamber", "method", "n", "mae_pp", "rmse_pp"]].copy()
    comparison["chamber"] = comparison.chamber.str.title()
    comparison.columns = ["Chamber", "Method", "Races", "Mean absolute error (pp)", "RMSE (pp)"]
    table(comparison.round(2))
    p(
        "The simple benchmark has lower average absolute error in both chambers. Elastic net has slightly lower Senate RMSE, which puts more weight on large misses, but it does not beat the benchmark on House RMSE. There is no basis here for calling the regression the better forecaster."
    )
    p(
        f"Across all the test races, the model puts the D/R candidates in the right order {100 * fitted.loc['house', 'winner_accuracy']:.1f}% of the time for the House and {100 * fitted.loc['senate', 'winner_accuracy']:.1f}% for the Senate. Most races are not close. Among races it places between 45% and 55% Democratic share, those figures fall to {100 * fitted.loc['house', 'close_d_r_order_accuracy']:.1f}% across {int(fitted.loc['house', 'close_n'])} House races and {100 * fitted.loc['senate', 'close_d_r_order_accuracy']:.1f}% across {int(fitted.loc['senate', 'close_n'])} Senate races. That is the harder test, and the Senate sample is small."
    )
    f(
        "02-historical-validation",
        "Predicted and actual Democratic two-party vote shares",
        "Each dot is a past race predicted from earlier years. Points on the diagonal are exact predictions; outlined points put the D/R candidates in the wrong order.",
    )
    f(
        "03-close-races",
        "Historical races the model placed between 45 and 55 percent Democratic share",
        "The same test, limited to races the model thought were close. Large misses stay in view.",
    )
    p(
        "I also reran the test predictions with every race poll hidden. Polling does not help in every year. There are no 2024 House race polls in the saved inputs, so the two House lines meet there. In 2026, 327 House races and eight Senate races rely on fundamentals alone."
    )
    f(
        "06-no-poll-validation",
        "Vote-share errors with available race polls and with polls withheld",
        "Same fitted model, same test races. Only the race-poll inputs change. Lower RMSE is better.",
    )

    h("Race estimates and uncertainty", "race-estimates")
    p(
        "The ranges below come from mistakes on earlier test elections. I group those errors by chamber and polling availability, giving each past election equal weight. If a group has fewer than two earlier cycles, I use the chamber's full error history. This leaves only 2022 and 2024 for checking the ranges."
    )
    coverage = scores[scores.coverage_95.notna()][
        ["cycle", "chamber", "brier", "coverage_95"]
    ].copy()
    coverage["chamber"] = coverage.chamber.str.title()
    coverage["coverage_95"] = coverage.coverage_95.map(lambda x: f"{100 * x:.1f}%")
    coverage.columns = ["Election", "Chamber", "Brier score", "Results inside 95% range"]
    table(coverage.round(3))
    p(
        "Brier score measures the error in the D/R ordering probabilities; lower is better. A well-calibrated 95% range should contain about 95% of outcomes over many comparable elections. The Senate range covered only 89.7% in 2022. Two test years are not enough to establish dependable coverage."
    )
    p(
        "Dots mark the model estimate; open circles mark polling averages. The horizontal lines show the historical-error ranges. The House chart shows the 25 closest estimates, and the lists below contain every race. An asterisk flags a different candidate or voting-rule treatment."
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
        "I built this on November 8, after Election Day. No 2026 results are used in training, tuning or testing, and I have not scored these estimates against the 2026 results. The November 2 cutoff uses field dates and database dates from files retrieved later. I cannot verify that every input was available in the same form before voting."
    )
    p(
        "The historical data also need care. Candidate rosters come from election returns, and the older polling archive selected the eventual top candidates. Some district presidential percentages are rounded. These are useful research inputs, but they do not recreate the exact information a forecaster had at the time."
    )
    p(
        "Finally, the seat bars simply count which party leads each estimate. They do not give the chance of winning Congress. A national polling miss could move many races together, and this model does not simulate that shared error. The benchmark comparison and the close-race results are reasons to improve the model before relying on it."
    )
    h("A closer look at the errors", "residual-diagnostics")
    f(
        "10-residual-diagnostics",
        "Historical errors and normal Q-Q plots",
        "Positive errors mean the model underestimated the Democratic share. The Q-Q plots compare the error distribution with a normal distribution; they do not test whether races move independently.",
    )

    sources = [
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
        "reproducibility": "The repository contains the saved inputs, model code, race estimates and historical checks, including the simple benchmark comparison.",
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
