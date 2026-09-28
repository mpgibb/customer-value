# Customer retention and lifetime value

Completed reproducible synthetic study · Python 3.11.16 · NumPy 2.2.6 · SciPy 1.17.1

Case study: https://michaelpgibb.com/projects/customer-value

## Executive summary

**A better churn score is not a case for more retention spending.**

Average value-forecast error fell from $184 to $149. Yet a policy targeting roughly one in five customers showed no clear net benefit at $35 per contact.

Decision implication: Keep the intervention in a controlled test until its incremental contribution clears its cost with adequate evidence.

Key caution: The learned policy ranged from a $7.06 loss to a $6.98 gain per eligible customer at the 95% interval. Selecting the highest-risk customers lost money in the stable simulation; a changed response pattern also harmed the learned policy.

All findings describe synthetic data. They are not client results. Independent technical review remains pending.

## Reproduce

```bash
git clone https://github.com/mpgibb/customer-value.git
cd customer-value
uv sync --frozen
uv run python -W error -m unittest discover -s tests -v
uv run python -W error study.py
git diff --exit-code -- data results
```

The frozen `uv.lock` resolves the pinned numerical libraries. The pipeline requires no credentials, paid data or network calls after environment setup. Nine correctness tests cover numerical fixtures, information timing and decision constraints. Running the study regenerates every CSV and `results/summary.json` from `config.json`. Monetary and probability outputs are rounded to six decimal places when serialized; forecast comparisons use the unrounded calculations.

## Research materials

- [PROTOCOL.md](PROTOCOL.md): question, models, baselines, timing and evaluation design recorded before evaluation.
- [DATA.md](DATA.md): units, schema, observation windows and permitted model inputs.
- [REPORT.md](REPORT.md): complete comparisons, robustness, practical implications and limits.
- `study.py` and `common.py`: generator, model, evaluator and numerical/provenance utilities.
- `tests/`: hand-calculated and adversarial correctness checks.
- `data/`: original generated observations; evaluator-only oracle files where applicable.
- `results/`: detailed predictions/decisions and machine-readable summaries, including source/data SHA-256 hashes.

## Scope and use

The horizon is twelve months; the title does not imply value over an unlimited customer lifetime. Synthetic intervention response can fail to transfer over time: reversing that relationship makes the learned policy materially harmful. The survival model assumes baseline margin persists, and the upper-risk calibration bins are sparse. Known oracle expectations are unattainable evaluation benchmarks, never model inputs.

Specify one real intervention and margin measure, then run a budget-limited randomized retention test. Require a positive, decision-relevant net-value result and stable response before broader use.

The synthetic data are original study materials and contain no customer or employer records. No original source/data reuse license has been selected; public availability permits inspection but does not itself grant reuse rights. Numerical libraries retain their own licenses and are installed from the lockfile, not vendored here.
