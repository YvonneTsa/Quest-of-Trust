# Quest of Trust payments fraud analysis

## Finding first

Across 10 repeatable synthetic runs, Logistic had lower modeled net cost than Rules in **10 of 10** runs. Its median paired cost difference (Logistic minus Rules) was **−$22,635** per holdout, with observed differences from **−$25,345 to −$19,903**. Logistic also captured more fraud value and challenged fewer legitimate events, while routing more legitimate events to investigator review.

These figures describe the behavior of the simulator under its documented assumptions. They are not statistical confidence intervals, real-world savings, or a forecast.

## Business question

How should a payments business route a transaction when it must balance fraud loss, good-customer friction, payment margin, and finite investigator capacity?

TrustHold maps a risk score to four actions:

- **APPROVE** preserves convenience and payment margin while accepting modeled fraud loss if the payment is fraudulent.
- **CHALLENGE** adds verification friction and a modeled per-event cost.
- **REVIEW** sends the event to a human queue with finite daily capacity.
- **DECLINE** stops the payment and can create customer loss when the event is legitimate.

## Synthetic population and evaluation

The published default simulation contains 2,000 customers, 800 merchants, and 1,200 terminals over 60 days. It generates about 246,000 payment events per base seed. Ten separately sampled attacks are injected for each of four typologies. Each later-date holdout has 350 planted fraud events and about 72,000–75,000 total events. The 10 compared seeds are consecutive values beginning at `20260915`.

Legitimate event generation, attack count, and daily review capacity (250 cases) are scaled together to keep the fraud share and the review-to-volume ratio close to the original learning run. All profiles, labels, events, and economic inputs remain fictional.

Features are constructed in timestamp order before fraud labels are joined. The first 70% of dates are used to fit the logistic baseline and select strategy thresholds. The later 30% are held out for evaluation. The threshold search is repeated within each seed using only that seed's earlier dates. The label table remains separate from public transaction, feature, decision, and SQLite tables.

## Results across 10 seeds

The table reports the mean fraud-value capture and the median counts and modeled cost across the 10 runs. Parentheses show the observed minimum-to-maximum range across seeds.

| Strategy | Fraud value captured, mean (range) | False declines, median (range) | Legitimate challenges, median (range) | Legitimate reviews, median (range) | Modeled net cost, median (range) |
|---|---:|---:|---:|---:|---:|
| Rules | 73.15% (68.29–76.44%) | 32.5 (24–45) | 5,210 (4,552–5,764) | 138 (109–155) | −$53,583 (−$56,249 to −$48,112) |
| Logistic | 90.43% (85.86–94.26%) | 19.5 (15–33) | 1,787.5 (1,568–1,838) | 328 (248–418) | −$75,244 (−$79,151 to −$68,812) |

The paired differences preserve the same-seed comparison:

- Logistic captured a median **16.90 percentage points** more fraud value than Rules (range **14.49–21.36 points**).
- It challenged a median **3,462 fewer legitimate events** (range **2,852–4,059 fewer**).
- It sent a median **214 more legitimate events to investigators** (range **93–273 more**).
- Its false-decline count was a median **14 lower**, although the paired range ran from 25 fewer to 3 more.
- Logistic's modeled net cost was lower in **10/10** seed pairs. The paired cost difference ranged from −$25,345 to −$19,903.

The operating interpretation is not simply “fewer challenges.” The Logistic strategy shifts some legitimate events from verification to human review, so the reduced challenge burden comes with greater investigator demand. A real decision would compare queue staffing and customer friction alongside fraud losses.

## One-seed strategy comparison

The detailed dashboard and generated report also retain all four strategies for the default seed `20260915`. That holdout includes 74,237 events, of which 350 are planted fraud.

| Strategy | Fraud value captured | False declines | Legitimate challenges | Legitimate reviews | Cases above daily review limit | Modeled net cost |
|---|---:|---:|---:|---:|---:|---:|
| Incumbent | 0.00% | 0 | 1,110 | 0 | 0 | −$15,477.19 |
| Rules | 73.09% | 30 | 5,305 | 140 | 0 | −$56,248.77 |
| Logistic | 91.42% | 33 | 1,838 | 410 | 0 | −$79,150.50 |
| Rules + logistic | 82.27% | 30 | 5,447 | 169 | 0 | −$62,823.34 |

Lower modeled cost is better under the fictional economics. A negative cost includes assumed margin from approved legitimate payments; it is not measured profit. The base-seed table is one scenario, while the seed table above communicates variation under repeated random draws.

## Why the comparison changes the business discussion

The Logistic baseline has a higher modeled fraud-value capture rate and fewer legitimate challenges than Rules in this simulation. It also requires review of more legitimate events. Under the stated review-cost, challenge-effectiveness, recovery, attrition, and payment-margin assumptions, the added modeled fraud capture outweighs the additional review and false-decline costs. Different inputs can change that ranking, which is why the dashboard includes capacity and economic sensitivities.

## Reproducibility and artifacts

Run the full analysis from the repository root:

```powershell
python -m src.run_project
python -m scripts.package_dataset
```

The run writes a CSV and SQLite table for each artifact under `data/synthetic/run/`. The robustness outputs are `seed_stability_by_run.csv`, `seed_stability_summary.csv`, and `seed_stability_comparison.csv`. `data/synthetic/published_run/manifest.json` lists part files, row counts, and checksums. The dashboard reuses precomputed scenario results and does not train a model or make live payment decisions.

## What this can and cannot claim

Ten seeds make run-to-run variation visible and show that the simulated cost ranking repeats under this configuration. They do **not** make the synthetic population representative, prove the ranking is statistically reliable for real payments, or estimate savings. Attack behavior and intervention probabilities are designed into the simulator; results can change when those assumptions change.

The data has one account per customer and no device, IP, login, or recovery-event network. Group comparisons are descriptive diagnostics rather than fairness certification. The logistic model and dashboard are portfolio prototypes, not production controls. Before operational use, the analysis would need representative labeled payment data, validated costs, calibration, leakage and drift checks, and review by fraud operations and model-risk stakeholders.
