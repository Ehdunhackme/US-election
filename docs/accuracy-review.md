# Accuracy review, 8 November 2026

The code reproduces its saved estimates. That does not establish that the
2026 predictions are right. This review checks the frozen inputs, reported
historical scores and selected source claims; it does not verify every survey
or compare the projections with 2026 election outcomes.

## What the historical tests show

The paired comparison uses the same 1,603 House and 122 Senate test races
from 2018, 2020, 2022 and 2024. Each race has equal weight. The simple benchmark
is local presidential lean plus national Democratic generic-ballot share,
clipped to 0–100, with no fitted coefficients.

| Chamber | Method          | MAE, pp | RMSE, pp |
| ------- | --------------- | ------: | -------: |
| House   | Elastic net     |    3.70 |     4.88 |
| House   | Simple baseline |    2.72 |     3.81 |
| Senate  | Elastic net     |    4.04 |     5.52 |
| Senate  | Simple baseline |    3.50 |     5.72 |

The benchmark has lower MAE in both chambers and lower House RMSE. Elastic
net has slightly lower Senate RMSE. The analysis does not support calling
elastic net the best model for these inputs.

Overall D/R ordering accuracy is 94.6% for the House and 91.0% for the Senate.
Restricting to model estimates between 45% and 55% lowers it to 69.2% of 195
House races and 69.6% of 23 Senate races. These are party-ordering checks,
not guarantees about candidate winners or chamber control.

Probability and interval validation covers only 2022 and 2024. The nominal
95% Senate ranges cover 89.7% of the 2022 outcomes. There is too little
independent validation to claim dependable calibration.

The benchmark comparison was added during this review, after the model was
developed. The chronological backtests remain development diagnostics.

## Source and presentation corrections

- The [House Clerk's roster](https://clerk.house.gov/member_info/electionInfo/2026/120-nominations.pdf)
  lists Alan Aversa under No Labels, not as independent. His output party is now
  `NOL`. Nadia Donya Milleron's party description is no longer part of her name.
- The training chart now says that it includes polled and unpolled races. Of
  the 3,063 training rows, 2,208 have no race poll.
- The forecast contains 435 House contests across 50 states and 35 Senate
  contests. Fourteen House seats are assigned from a same-party roster, rather
  than given invented vote shares. This assumes no unlisted candidate or later
  ballot change alters that assignment.
- Louisiana's [official rules](https://www.sos.la.gov/elections-voting/how-candidates-are-elected)
  confirm that House elections still use an open primary in 2026, while Senate
  elections use the closed-party-primary system. House party totals are not
  runoff-winner probabilities.
- Independent and minor-party transfers and ranked-choice proxies have not
  been validated as candidate-win models. Their probability fields remain empty.

Rebuilding the 2026 snapshot changed labels only. Vote-share estimates and
seat totals are unchanged.

## Timing limits

The files were collected and the model was built after the November 3 election.
No 2026 outcomes enter training, parameter selection or validation. The November
2 cutoff uses field and database dates, which cannot prove that every input
was publicly available in the same form before voting. Older polling archives
also select eventual top candidates retrospectively.

The article now states these limits near the results and in its methods.
It does not claim that this was a published pre-election forecast.
