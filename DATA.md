# Data dictionary and observation rules

The study generates 54 cohorts × 180 customers = 9,720 customers per scenario. Model fitting uses cohorts 0–23, validation uses 24–29, and final scoring uses 42–53. At first final scoring, every training and validation 12-month outcome is already observed. Final evaluation waits through cohort 65. No missingness or loss to follow-up is generated.

`data/*_customers.csv` fields:

| Field | Meaning |
|---|---|
| customer_id, cohort | Synthetic identifier and zero-based scoring month |
| tenure_months | Observed tenure at scoring |
| engagement | Scoring-date beta-distributed engagement, 0–1 |
| friction | Scoring-date standardized service friction |
| tier | Fixed account tier, 0 or 1 |
| monthly_margin | Baseline USD contribution per active month |
| assigned | Independent randomized intervention, 0 or 1; probability 0.5 |
| churn6 | Cancellation by month 6, observed after scoring |
| churn_month | First cancellation month 1–12; 13 denotes still active at twelve months |
| discounted_contribution | Observed USD over twelve months, before intervention cost |

`data/*_monthly.csv` contains at-risk monthly records: customer_id, outcome_cohort, month, cancellation indicator, and realized contribution. Cancellation happens before that month’s contribution; cancellation is absorbing. A $35 intervention cost is charged once at scoring to contacted customers; it is deducted in policy evaluation, not in the observed gross contribution target. Discount is 10% annually, converted monthly. Margin has a small trend and random fluctuation; the predictive value model deliberately assumes constant baseline margin.

`data/*_oracle.csv` contains customer_id and exact expected control/treatment contribution, calculated from potential survival hazards. Model-fitting functions never receive it. This file is reserved for evaluation and regret calculations. No observed customer outcome is presented as an observed individual treatment effect.

`results/*_scored_customers.csv` includes final observed outcomes, frozen predictions, doubly robust gross-effect scores, selected-policy indicators and oracle expected effects. Policy indicators are 0/1. The README/report explain which quantities are deployable predictions versus evaluator-only benchmarks. Source/data hashes are in `results/summary.json`.
