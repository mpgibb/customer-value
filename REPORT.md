# Research report: Customer retention and lifetime value

## Executive summary

**A better churn score is not a case for more retention spending.**

Average value-forecast error fell from $184 to $149. Yet a policy targeting roughly one in five customers showed no clear net benefit at $35 per contact.

Decision implication: Keep the intervention in a controlled test until its incremental contribution clears its cost with adequate evidence.

Key caution: The learned policy ranged from a $7.06 loss to a $6.98 gain per eligible customer at the 95% interval. Selecting the highest-risk customers lost money in the stable simulation; a changed response pattern also harmed the learned policy.

All findings describe synthetic data. They are not client results. Independent technical review remains pending.

## Decision and design

Prioritize a fixed retention intervention for at most 20% of each eligible cohort. Evaluate twelve-month discounted contribution after the intervention cost, keeping predictive churn risk separate from the causal value of treatment.

A fully implemented study of 9,720 synthetic customers across 54 monthly cohorts. Models use 24 training cohorts, six matured validation cohorts and twelve untouched final cohorts after a maturity gap. Prediction is assessed on 1,051 final control customers; policy value uses all 2,160 final randomized customers.

## Method

Fit a regularized discrete-time cancellation model to untreated customers and combine survival probabilities with baseline margin and a 10% annual discount rate. Fit outcome regressions in three training folds to construct doubly robust treatment-effect scores using the known randomization probability. Learn a prespecified feature-based score, target positive expected net effects within a 20% cohort budget, and evaluate the frozen policy on later randomized cohorts.

- Compare segment means with a discrete-time survival model for six-month churn and twelve-month discounted contribution.
- Three-fold out-of-fold training creates a treatment-value score; freeze the policy before the twelve final cohorts.
- Compare no contact, contact everyone, highest churn risk, highest untreated value and learned incremental value; repeat under no effect and response shift.

## Evaluated results

Policy effects below are twelve-month incremental net contribution per eligible customer, not per treated customer. No-contact has zero incremental effect by definition. Targeted policies have the same at-most-20% budget; contact-everyone is an unconstrained comparator. Evaluation intervals use twelve cohort-cluster means with a t critical value (11 degrees of freedom).

### stable

| Policy | Contacted | Net effect | 95% interval | Oracle expected net | Regret vs budget oracle |
|---|---:|---:|---|---:|---:|
| none | 0.00% | $0.00 | $0.00 to $0.00 | $0.00 | $2.35 |
| all | 100.00% | $-27.37 | $-46.20 to $-8.53 | $-25.96 | Not comparable |
| high_risk | 20.00% | $-19.56 | $-28.05 to $-11.07 | $-14.51 | $16.86 |
| high_value | 20.00% | $-0.12 | $-8.34 to $8.09 | $1.20 | $1.15 |
| incremental_value | 19.86% | $-0.04 | $-7.06 to $6.98 | $1.04 | $1.31 |

Budget-constrained oracle expected net: $2.35. The oracle sees true potential expectations and is an unattainable evaluator benchmark.

| Untreated prediction | Churn Brier | Log loss | Value MAE | Value bias |
|---|---:|---:|---:|---:|
| segment_mean | 0.1836 | 0.5535 | $183.54 | $3.46 |
| survival | 0.1593 | 0.4887 | $149.24 | $-13.96 |

| Fixed selected policy | $15 contact cost | $35 contact cost | $55 contact cost |
|---|---:|---:|---:|
| none | $0.00 | $0.00 | $0.00 |
| all | $-7.37 | $-27.37 | $-47.37 |
| high_risk | $-15.56 | $-19.56 | $-23.56 |
| high_value | $3.88 | $-0.12 | $-4.12 |
| incremental_value | $3.93 | $-0.04 | $-4.01 |

### no_effect

| Policy | Contacted | Net effect | 95% interval | Oracle expected net | Regret vs budget oracle |
|---|---:|---:|---|---:|---:|
| none | 0.00% | $0.00 | $0.00 to $0.00 | $0.00 | $0.00 |
| all | 100.00% | $-37.73 | $-56.69 to $-18.77 | $-35.00 | Not comparable |
| high_risk | 20.00% | $-13.44 | $-21.62 to $-5.27 | $-7.00 | $7.00 |
| high_value | 20.00% | $-6.79 | $-15.44 to $1.87 | $-7.00 | $7.00 |
| incremental_value | 0.74% | $-0.69 | $-1.70 to $0.32 | $-0.26 | $0.26 |

Budget-constrained oracle expected net: $0.00. The oracle sees true potential expectations and is an unattainable evaluator benchmark.

| Untreated prediction | Churn Brier | Log loss | Value MAE | Value bias |
|---|---:|---:|---:|---:|
| segment_mean | 0.1836 | 0.5535 | $183.54 | $3.46 |
| survival | 0.1593 | 0.4887 | $149.24 | $-13.96 |

| Fixed selected policy | $15 contact cost | $35 contact cost | $55 contact cost |
|---|---:|---:|---:|
| none | $0.00 | $0.00 | $0.00 |
| all | $-17.73 | $-37.73 | $-57.73 |
| high_risk | $-9.44 | $-13.44 | $-17.44 |
| high_value | $-2.79 | $-6.79 | $-10.79 |
| incremental_value | $-0.54 | $-0.69 | $-0.84 |

### response_shift

| Policy | Contacted | Net effect | 95% interval | Oracle expected net | Regret vs budget oracle |
|---|---:|---:|---|---:|---:|
| none | 0.00% | $0.00 | $0.00 to $0.00 | $0.00 | $8.94 |
| all | 100.00% | $-82.16 | $-102.87 to $-61.45 | $-78.35 | Not comparable |
| high_risk | 20.00% | $3.63 | $-4.40 to $11.66 | $6.69 | $2.25 |
| high_value | 20.00% | $-40.11 | $-50.22 to $-30.00 | $-37.08 | $46.02 |
| incremental_value | 19.86% | $-38.27 | $-45.16 to $-31.37 | $-35.27 | $44.21 |

Budget-constrained oracle expected net: $8.94. The oracle sees true potential expectations and is an unattainable evaluator benchmark.

| Untreated prediction | Churn Brier | Log loss | Value MAE | Value bias |
|---|---:|---:|---:|---:|
| segment_mean | 0.1836 | 0.5535 | $183.54 | $3.46 |
| survival | 0.1593 | 0.4887 | $149.24 | $-13.96 |

| Fixed selected policy | $15 contact cost | $35 contact cost | $55 contact cost |
|---|---:|---:|---:|
| none | $0.00 | $0.00 | $0.00 |
| all | $-62.16 | $-82.16 | $-102.16 |
| high_risk | $7.63 | $3.63 | $-0.37 |
| high_value | $-36.11 | $-40.11 | $-44.11 |
| incremental_value | $-34.29 | $-38.27 | $-42.24 |

The stable learned policy has an interval spanning loss and gain. It does not justify claiming profitable retention. Prediction improves on the segment mean, but its value forecasts are still biased and the highest-risk calibration bins contain few observations. In the response-shift scenario, historical targeting is harmful; frozen historical learning cannot establish future responsiveness. No tuning used the final cohorts.

## Assumptions and limitations

- Training and validation outcomes mature before final scoring begins; no incomplete window is treated as a completed target.
- Randomized treatment, consistency and no interference identify incremental value; churn predictions alone do not.
- A $35 intervention has a fixed form and timing. Cost sensitivity changes accounting cost, not the treatment or its effectiveness.
- Confidence intervals use twelve cohort clusters and a t approximation. They remain uncertain with so few clusters and do not establish individual treatment effects.

The horizon is twelve months; the title does not imply value over an unlimited customer lifetime. Synthetic intervention response can fail to transfer over time: reversing that relationship makes the learned policy materially harmful. The survival model assumes baseline margin persists, and the upper-risk calibration bins are sparse. Known oracle expectations are unattainable evaluation benchmarks, never model inputs.

## Reproduction and checks

Run the README commands. Nine tests pass, including hand-calculated or exhaustive fixtures, temporal leakage attempts and seeded determinism. The protocol, configuration, lockfile, model code, detailed evaluation CSVs and content hashes are included. No favorable seeds were selected after seeing results. Numerical libraries are pinned; stored results round to six decimal places to make reproduction portable.

## Next practical step

Specify one real intervention and margin measure, then run a budget-limited randomized retention test. Require a positive, decision-relevant net-value result and stable response before broader use.

## Method references

- [Dudík, Langford & Li — doubly robust policy evaluation](https://arxiv.org/abs/1103.4601)
- [Athey & Wager — policy learning](https://arxiv.org/abs/1702.02896)

These references motivate the design; this implementation does not claim their complete estimators or theoretical guarantees.
