# Evaluation design: fit, validation, and holdouts

## Purpose

The project compares fraud decision strategies by modeled loss, customer friction, payment margin, and review workload. The evaluation must keep three activities separate:

1. **Fit:** estimate the logistic-regression coefficients from earlier simulated events and fit campaigns.
2. **Validation:** choose action thresholds using rows that were not used to fit that model.
3. **Evaluation:** report results on a later-date holdout, then show a nested result for later fraud events from campaign identities kept out of both fit and validation.

All outcomes and economics are synthetic. Seed ranges measure variability inside the simulator, not uncertainty about a real payment portfolio.

## 1. Create campaign identities in restricted truth

`src/simulation/inject_fraud.py` assigns each planted attack campaign a `Campaign_ID` and `Campaign_Number`. Both fields are written to the restricted fraud-truth table. They are not placed in the observable transaction features or in public decision outputs. This allows the offline evaluation code to keep related fraud events together when creating validation and holdout groups without giving the model campaign labels as predictors.

Each typology has 10 campaigns by default. Every campaign produces an early and a later phase. With 10 campaigns per typology, the simulation plants 700 events per seed, approximately 350 before the primary date split and 350 after it.

## 2. Preserve the later-date holdout

Dates are sorted, and the boundary remains at 70% of the simulated dates. All events on dates before the boundary form the historical training window. All events on or after the boundary form the later-date test period. No test-period fraud labels are used to fit coefficients or select thresholds.

This primary evaluation answers: **How do the policies compare on later events when the simulator continues the same designed attack campaigns?** Each later-date test period contains 350 simulated fraud cases.

## 3. Fit the temporal model and validate thresholds separately

Within the earlier training window, campaign identities are assigned to fit, validation, and holdout groups. The default fit group contains campaign numbers 1, 5, and 9 per typology; the validation group contains 3 and 7; the campaign holdout contains 2, 4, 6, 8, and 10. Fraud rows from the validation and holdout groups are excluded from model fitting. The model fit also uses a reproducible sample of legitimate rows, while 20% of eligible legitimate training-window rows are reserved for validation.

The validation sample therefore contains fraud from complete campaign identities plus legitimate events. The fit and validation row indexes do not overlap. The model is trained only on the fit group. Candidate threshold sets are scored on validation rows using the modeled net-cost formula; the selected thresholds are then frozen before the later-date test is evaluated.

This is a campaign-stratified validation sample from the historical window, not a second later-date validation period. It prevents the same fraud campaign and the same transaction rows from being used both to fit and tune the policy. The later-date holdout measures time-forward performance under a model whose fit and validation fraud campaigns were kept separate.

## 4. Run a stricter unseen-campaign evaluation

For the default seed, a second model fit is not required: the same fitted model and validation-selected thresholds are used for both views. The campaign-generalization result is a nested slice of the later-date test containing legitimate later-period context plus fraud from campaigns unseen during both fitting and threshold validation. Campaign numbers are divided into three groups within each typology:

| Role | Default campaign numbers | Use |
|---|---|---|
| Fit | 1, 5, 9 | Fit the separate logistic model using earlier dates. |
| Validation | 3, 7 | Choose action thresholds; these fraud labels do not enter fitting. |
| Campaign holdout | 2, 4, 6, 8, 10 | Keep every phase out of fitting and threshold selection; evaluate their later phase. |

All legitimate observations remain available to the relevant fit or validation sample, with 20% of eligible legitimate rows reserved for validation. The campaign test includes legitimate later-period context and fraud only from the campaigns reserved for the holdout. At the default scale, five of ten campaigns per typology are held out, yielding 175 later-phase fraud events in the default-seed check.

This answers: **How do the strategies compare on the portion of the later-date population tied to campaign identities neither fitting nor threshold selection saw?** Because this slice is nested inside the later-date holdout, it is a focused generalization check rather than an independent second experiment. It does not test unseen typologies, new attack signatures, adversarial adaptation, or production data.

## 5. Select thresholds by modeled net cost

The rules, logistic, and hybrid scores use the same candidate action thresholds. For each candidate, the policy maps events to **approve, challenge, review, or decline** and enforces the daily review limit. The candidate with the lowest validation-set `Net_Economic_Cost` is selected for that score strategy.

The final temporal or campaign test set is not used during this selection. `src/decisions/policies.py` defines the action mapping and fictional unit economics; `src/run_project.py` handles the separate fit/validation/test populations.

## 6. Repeat the primary comparison on 30 deterministic seeds

The default command evaluates seeds `20260915` through `20260944` for the primary later-date comparison. Rules and Logistic are paired within each seed; the project reports win counts, means, medians, and observed minimum-to-maximum ranges. The nested campaign-identity check is reported for the default seed only. Keeping this second, smaller diagnostic separate avoids presenting its approximately 175 events as a 30-seed stability result.

The reported range is the range across these 30 simulator runs. It is not a confidence interval, a significance test, or evidence that the generated population represents real cardholders. Repeating seeds quantifies simulator randomness only.

## 7. Interpret the business break-even table

`business_sensitivity` varies one assumption at a time on the base seed's held-out decisions:

- challenge success rate;
- review recovery rate;
- probability a false decline causes customer attrition;
- manual review cost per case;
- chargeback fee;
- legitimate-payment margin; and
- daily review capacity.

For cost assumptions, the action decisions remain fixed while the cost inputs vary. For review capacity, policies are rerun with their selected thresholds so overflow routing changes. `Cost_Delta_Logistic_Minus_Rules` is Logistic's modeled net cost minus Rules' modeled net cost: a negative value favors Logistic; a positive value favors Rules. If the sign changes over the tested range, the report interpolates an approximate crossover between grid points.

These are conditional scenarios, not estimates of true break-even economics. They show which assumptions control the strategy ranking and where more business evidence would matter. The HTML dashboard lets a reader select a parameter and inspect the modeled cost difference across the tested range.

## 8. Reproduce the pipeline

From the repository root, install the packages listed in `requirements.txt`, then run:

```powershell
python -m src.run_project
```

The default run generates the synthetic data, both evaluation populations, 30-seed later-date tables, the one-seed nested campaign check, economic sensitivity outputs, the case-study report, and the interactive dashboard. Files are written under `data/synthetic/run/`, `reports/`, and `docs/dashboard.html`. Fraud truth stays under `data/synthetic/run/restricted/` and must not be published with the public dataset.

Important outputs include:

| Artifact/table | Meaning |
|---|---|
| `strategy_metrics` | Default-seed later-date test results. |
| `campaign_holdout_metrics` | Default-seed results for withheld campaign identities. |
| `seed_stability_by_run` | Paired later-date results by seed. |
| `campaign_stability_by_run` | The default-seed nested campaign check; not a multi-seed stability sample. |
| `evaluation_design` | Fit, validation, and holdout row/event counts. |
| `business_sensitivity` | Costs for each tested assumption value and strategy. |
| `business_break_even_summary` | Tested ranges and approximate ranking crossovers. |

## Business interpretation

The analysis is intended to compare operating choices, not to maximize a classification score in isolation. A lower modeled cost can coexist with a larger investigation queue or additional false declines. Read cost, captured fraud value, challenges, reviews, false declines, and capacity together.

The simulator's fraud patterns, intervention effectiveness, attrition rate, review recovery, fees, and payment margin are all design inputs. Before using the workflow for a real decision, the same split discipline and cost model would need to be recalibrated and evaluated with approved, representative, labeled payment data.
