# 2026 US election model

One elastic-net model for **all 435 House districts and all 35 Senate contests**.
The project includes historical backtests, national maps, race-level estimates
and a technical article.

**This is a retrospective analysis dated November 8, 2026.** Polling inputs use
an unverified November 2 date cutoff. No 2026 election outcomes are used to train,
tune or evaluate the model. These estimates were not published before Election Day.

## Reproduce the analysis

Requires Python 3.13+ and Node.js 20+ for the article. The checked-in feature
snapshots let you reproduce the forecast without fetching mutable polling feeds.

```bash
python -m venv .venv
# Activate .venv using your shell's activation command.
python -m pip install -r requirements.lock
python -m pip install -e ".[dev]"
python -m election_forecast build
python -m pytest
npm ci
npm run article
npm run check:article
```

Open `site/index.html` in a browser. Charts, fonts and rendered equations are
embedded in the page, so the article works without a preview server or CDN.
For a local web preview, run `npm run preview` and open `http://127.0.0.1:4173`.
Generated CSVs, SVGs, PNGs, validation scores and the fitted estimator are in
`reports/`. Generated folders are excluded from Git.

The GitHub checks rebuild the analysis and test the article in desktop and mobile
Chromium. To run those browser checks locally, use `npx playwright install chromium`
followed by `npm run test:browser`.

## The model

The final fit uses **3,063 historical D/R contests**: 2,656 House races from
2012–2024 and 407 Senate races from 2000–2024. One pooled estimator represents
chamber differences through interaction terms.

Inputs are local presidential lean, national generic-ballot polling, incumbency,
the midterm cycle, presidential party and available race polling. House lean
uses the district boundaries relevant to each election, including the 2026 maps.

Polled races are also represented with their polls withheld, with half weight
on each copy. Unpolled races therefore receive fundamentals-based predictions
from the same fitted model. Six elastic-net penalty settings are selected using
completed earlier validation cycles. The final settings are `alpha=0.1` and
`l1_ratio=0.8`.

Validation moves forward through 2018, 2020, 2022 and 2024. Each test election is
excluded from its own training, preprocessing and parameter selection. An
additional backtest withholds every race poll to check the unpolled setting.

## Results and interpretation

The saved point projections are **219 Democratic / 216 Republican House seats**
and **14 Democratic / 21 Republican seats among the 35 Senate contests**.
The Senate numbers do not include the 65 seats that are not up for election.

See [race estimates](results/2026-estimates.csv),
[historical scores](results/historical-cycle-scores.csv) and
[withheld-poll scores](results/masked-poll-scores.csv).

Seat bars count point-estimate leaders, not expected seats or probabilities of
chamber control. The House map colors states by projected seat plurality, with
stripes for ties. The Senate map marks states without an election in grey.

Single-party ballots determine the party outcome without an invented vote share.
Independent opposition uses a labeled partisan-baseline transfer. Alaska and Maine
use first-preference proxies; Louisiana House estimates aggregate parties before
any runoff. These treatments are not validated candidate-level win models, and
their candidate-win probabilities are not reported. Historical D/R error ranges
are sensitivity references for these cases.

## Repository

| Path                     | Contents                                                        |
| ------------------------ | --------------------------------------------------------------- |
| `src/election_forecast/` | Final model, data preparation, calibration and figures          |
| `data/frozen/`           | Exact historical and 2026 feature snapshots                     |
| `data/reference/`        | District presidential calculations, polling features and roster |
| `data/sources.json`      | Upstream URLs and source hashes                                 |
| `results/`               | Compact, reviewed forecast and validation outputs               |
| `scripts/`               | Article generation and optional raw-source retrieval            |
| `tests/`                 | Coverage, temporal integrity and input-treatment checks         |
| `website/`               | Integration files for the Next.js article                       |

The earlier model-comparison experiments, downloaded raw archives, environments,
temporary files and unrelated portfolio code are not included.

## Data and attribution

Sources include [MIT Election Data and Science Lab](https://electionlab.mit.edu/data),
[The Downballot's district calculations](https://www.the-downballot.com/p/the-downballots-calculations-of-presidential),
the [House Clerk's candidate roster](https://clerk.house.gov/member_info/electionInfo/2026/120-nominations.pdf),
FiveThirtyEight/NYT polling archives and
[Congress legislator records](https://github.com/unitedstates/congress-legislators).
State geometry is from [us-atlas](https://github.com/topojson/us-atlas).

See [data provenance](data/README.md) for snapshot handling and limitations.
Source data and bundled fonts retain their own terms; the project code uses the
[MIT license](LICENSE).
