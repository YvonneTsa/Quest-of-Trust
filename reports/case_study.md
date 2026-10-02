# TrustHold — The Cost of Fraud: simulation case study

> All numbers below are outputs of this fictional synthetic simulation, not claims about a real company.

## Finding first
Across 30 deterministic simulation seeds, Logistic had lower modeled net cost than Rules in 30/30 runs. The median paired difference (Logistic minus Rules) was -$15,501.82, with observed seed-to-seed differences from -$22,482.27 to -$11,207.82. These are scenario-conditional simulation results, not real-world savings or formal confidence intervals.

## Context and decision problem
TrustHold models a digital-payments environment where each event can be approved, challenged, reviewed, or declined. The business objective is to balance fraud loss, customer friction, finite review capacity, and payment margin.

## Data and method
The generated world contains 246,314 timestamped transactions. A later time period beginning 2026-02-12 is held out for evaluation. Fraud truth is stored separately and is joined only for model training and offline evaluation.
The default book uses 2,000 customers, 800 merchants, 1,200 terminals, 60 days, and 10 separately sampled attacks per typology across four documented patterns. This yields 350 simulated fraud cases in each later-period holdout. Legitimate event volume, attack count, and review capacity are scaled together so the modeled fraud share and investigator-to-volume ratio stay near the earlier version.
Behavioral features use only information available before each transaction. A transparent rule score and a NumPy logistic-regression baseline are compared with the same four payment actions. A campaign-stratified validation sample is kept out of model fitting and is used to select action thresholds; the later-date holdout remains untouched until evaluation.

## Results across seeds
Each of the 30 runs changes the random draws for customers, legitimate events, terminals, and attack campaigns. The paired comparison keeps the same fictional economics and 250-case daily review capacity. The ranges below are the observed minimum and maximum across those seeds; they summarize simulator variation and are not confidence intervals for real payment populations.
| Strategy | Fraud cases in later test period, mean (range) | Fraud value captured, mean (range) | Good payments declined, median (range) | Good payments challenged, median (range) | Good payments reviewed, median (range) | Modeled net cost, mean / median (range) |
|---|---:|---:|---:|---:|---:|---:|
| Rules | 350 (350-350) | 73.73% (68.29-81.25%) | 31 (19-52) | 5,139 (4,552-5,764) | 126 (88-155) | -$52,628.64 mean; -$52,948.04 median (-$58,036.35 to -$47,036.37) |
| Logistic | 350 (350-350) | 77.51% (69.76-87.21%) | 0 (0-2) | 598.5 (181-930) | 19 (7-37) | -$67,852.71 mean; -$68,082.01 median (-$73,729.50 to -$60,292.87) |

Logistic captured a median +3.66 percentage points of fraud value relative to Rules (range -1.86 to +14.31). It sent a median 4,463.5 fewer legitimate events to challenge (range 3,988 to 5,342 fewer), while sending a median 108 fewer legitimate events to investigator review (range 65–138 fewer). Fewer challenges do not mean that every case disappears from the operating queue.
The false-decline trade-off is also retained: the paired Logistic-minus-Rules median was -31 legitimate declines, with an observed range of -51 to -19. A positive value means Logistic declined more legitimate payments in that seed.

## Separate campaign-generalization check
A nested campaign-identity check on the default seed isolates later-period fraud from half of the numbered synthetic campaigns; those campaign labels were excluded from model fitting and threshold selection. It contains 175 held-out fraud events. In this single check, Logistic's modeled cost was -$81,966.76, versus -$66,923.22 for Rules. This is a focused one-seed diagnostic, not multi-seed evidence. It tests withheld campaign identities within the same four designed typologies; it does not test unseen fraud mechanisms or real-world generalization.
Mean fraud-value capture in this check was 75.72% for Logistic and 72.63% for Rules. This result is a focused subset of the later-date test, not a statistically independent experiment.

## Evaluation split audit
Counts below make the fitting, threshold-validation, and final evaluation samples explicit for the default seed.
```text
             Evaluation     Seed  Training_Rows  Validation_Rows  Holdout_Rows  Training_Fraud_Events  Validation_Fraud_Events  Holdout_Fraud_Events  Fit_Campaigns  Validation_Campaigns  Holdout_Campaigns Holdout_Start
     Later-date holdout 20260915         137487            34415         74237                    105                       70                   350             12                     8                 40    2026-02-12
Unseen-campaign holdout 20260915         137487            34415         74062                    105                       70                   175             12                     8                 20    2026-02-12
```

## Held-out strategy comparison
The table below is the single default seed (20260915), not the multi-seed summary. The fictional cost assumptions are documented in `docs/simulation_assumptions.md`. Lower net economic cost is better under those settings. The lowest cost in this base run is **Logistic**, at -$73,729.50.

```text
    Seed         Strategy  Transactions  Fraud_Transactions  Fraud_Value  Fraud_Value_Captured_Pct  Fraud_Loss_After_Intervention  Precision_Among_Interventions  Fraud_Recall  Legitimate_Challenge_Count  Legitimate_Review_Count  False_Declines  Review_Overflow_Count  Net_Economic_Cost         PR_AUC
20260915        Incumbent         74237                 350     67233.18                      0.00                       75983.18                         0.0000        0.0000                        1110                        0               0                      0          -15477.19 Not applicable
20260915            Rules         74237                 350     67233.18                     73.09                       20745.89                         0.0457        0.7486                        5305                      140              30                      0          -56248.77         0.2655
20260915         Logistic         74237                 350     67233.18                     78.37                       17658.22                         0.2425        0.6971                         740                       21               1                      0          -73729.50         0.5826
20260915 Rules + logistic         74237                 350     67233.18                     76.26                       18176.77                         0.0489        0.8057                        5310                      140              30                      0          -58811.13         0.2981
```
Complete temporal-holdout per-seed rows are available in `data/synthetic/run/seed_stability_by_run.csv`; summary and paired-difference tables are also stored in SQLite.

## Capacity sensitivity
The same score bands were evaluated with different daily review limits. Overflow cases are routed to challenge.
```text
        Strategy  Review_Capacity_Per_Day  Fraud_Value_Captured_Pct  Review_Overflow_Count  Net_Economic_Cost
           Rules                       10                     69.46                     95          -54198.31
        Logistic                       10                     74.89                     85          -71733.94
Rules + logistic                       10                     72.18                    108          -56514.85
           Rules                       50                     70.76                     51          -54893.62
        Logistic                       50                     76.84                     45          -72885.61
Rules + logistic                       50                     73.66                     64          -57327.10
           Rules                      150                     73.09                      0          -56248.77
        Logistic                      150                     78.37                      0          -73729.50
Rules + logistic                      150                     76.26                      0          -58811.13
           Rules                      250                     73.09                      0          -56248.77
        Logistic                      250                     78.37                      0          -73729.50
Rules + logistic                      250                     76.26                      0          -58811.13
           Rules                      500                     73.09                      0          -56248.77
        Logistic                      500                     78.37                      0          -73729.50
Rules + logistic                      500                     76.26                      0          -58811.13
```

## Economic assumption sensitivity
The action decisions are held fixed while challenge effectiveness, false-decline attrition, and review recovery assumptions change.
```text
        Strategy              Economic_Scenario  Fraud_Loss_After_Intervention  False_Declines  Net_Economic_Cost
       Incumbent               Base assumptions                       75983.18               0          -15477.19
           Rules               Base assumptions                       20745.89              30          -56248.77
        Logistic               Base assumptions                       17658.22               1          -73729.50
Rules + logistic               Base assumptions                       18176.77              30          -58811.13
       Incumbent  Lower challenge effectiveness                       75983.18               0          -15477.19
           Rules  Lower challenge effectiveness                       24903.67              30          -52090.99
        Logistic  Lower challenge effectiveness                       20416.92               1          -70970.80
Rules + logistic  Lower challenge effectiveness                       22261.81              30          -54726.08
       Incumbent Higher challenge effectiveness                       75983.18               0          -15477.19
           Rules Higher challenge effectiveness                       17627.56              30          -59367.11
        Logistic Higher challenge effectiveness                       15589.19               1          -75798.52
Rules + logistic Higher challenge effectiveness                       15112.98              30          -61874.91
       Incumbent  Lower false-decline attrition                       75983.18               0          -15477.19
           Rules  Lower false-decline attrition                       20745.89              30          -56848.77
        Logistic  Lower false-decline attrition                       17658.22               1          -73749.50
Rules + logistic  Lower false-decline attrition                       18176.77              30          -59411.13
       Incumbent Higher false-decline attrition                       75983.18               0          -15477.19
           Rules Higher false-decline attrition                       20745.89              30          -55498.77
        Logistic Higher false-decline attrition                       17658.22               1          -73704.50
Rules + logistic Higher false-decline attrition                       18176.77              30          -58061.13
       Incumbent          Lower review recovery                       75983.18               0          -15477.19
           Rules          Lower review recovery                       26313.32              30          -50681.35
        Logistic          Lower review recovery                       23088.62               1          -68299.10
Rules + logistic          Lower review recovery                       24282.27              30          -52705.62
```

## Business break-even analysis
The next view varies one fictional cost assumption at a time while holding the base-seed decisions fixed. Capacity scenarios recalculate routing with the existing thresholds. A crossover is an approximate modeled point where Logistic and Rules exchange lower net cost; it is not a forecast or a confidence interval.
```text
                          Parameter          Unit  Tested_Min  Tested_Max  Base_Value Break_Even_Value  Ranking_Changes_In_Tested_Range Preferred_At_Min Preferred_At_Max  Cost_Delta_At_Min  Cost_Delta_At_Max                                                         Interpretation
             Challenge success rate   probability         0.0        1.00       0.800             None                            False         Logistic         Logistic          -23077.04          -16081.65 No strategy-rank crossover was observed in the tested fictional range.
               Review recovery rate   probability         0.0        1.00       0.900             None                            False         Logistic         Logistic          -18097.36          -17412.22 No strategy-rank crossover was observed in the tested fictional range.
False-decline attrition probability   probability         0.0        0.25       0.050             None                            False         Logistic         Logistic          -16755.73          -20380.73 No strategy-rank crossover was observed in the tested fictional range.
                 Manual review cost  USD per case         0.0      150.00       4.500             None                            False         Logistic         Logistic          -16976.73          -33776.73 No strategy-rank crossover was observed in the tested fictional range.
                     Chargeback fee USD per event         0.0      200.00      25.000             None                            False         Logistic         Logistic          -17930.73          -14330.73 No strategy-rank crossover was observed in the tested fictional range.
          Legitimate-payment margin          rate         0.0        0.02       0.011             None                            False         Logistic         Logistic           -6174.17          -26731.54 No strategy-rank crossover was observed in the tested fictional range.
            Review capacity per day cases per day        10.0      500.00     250.000             None                            False         Logistic         Logistic          -17535.63          -17480.73 No strategy-rank crossover was observed in the tested fictional range.
```
Detailed one-variable-at-a-time scenario rows are available in `business_sensitivity.csv` and SQLite.

## Descriptive customer-group impact
The following rates are descriptive diagnostics over synthetic data, not a fairness certification. Small group counts and the intentionally fictional population limit interpretation.
```text
        Strategy    Group_Type     Group  Transactions  Fraud_Rate  Challenge_Rate  Review_Rate  Decline_Rate  False_Declines
       Incumbent       Segment  Business         16142      0.0029          0.0145       0.0000        0.0000               0
       Incumbent       Segment   Premium         18177      0.0050          0.0165       0.0000        0.0000               0
       Incumbent       Segment  Standard         39918      0.0053          0.0144       0.0000        0.0000               0
       Incumbent KYC risk band      High          3819      0.0079          0.0134       0.0000        0.0000               0
       Incumbent KYC risk band       Low         51585      0.0046          0.0153       0.0000        0.0000               0
       Incumbent KYC risk band    Medium         18833      0.0043          0.0144       0.0000        0.0000               0
       Incumbent   Home region   Midwest         16592      0.0040          0.0160       0.0000        0.0000               0
       Incumbent   Home region Northeast         18094      0.0056          0.0148       0.0000        0.0000               0
       Incumbent   Home region     South         26878      0.0044          0.0144       0.0000        0.0000               0
       Incumbent   Home region      West         12673      0.0051          0.0152       0.0000        0.0000               0
           Rules       Segment  Business         16142      0.0029          0.1785       0.0056        0.0020              23
           Rules       Segment   Premium         18177      0.0050          0.0761       0.0021        0.0003               3
           Rules       Segment  Standard         39918      0.0053          0.0296       0.0025        0.0006               4
           Rules KYC risk band      High          3819      0.0079          0.0861       0.0055        0.0024               3
           Rules KYC risk band       Low         51585      0.0046          0.0728       0.0030        0.0006              20
           Rules KYC risk band    Medium         18833      0.0043          0.0725       0.0027        0.0011               7
           Rules   Home region   Midwest         16592      0.0040          0.0777       0.0025        0.0007               5
           Rules   Home region Northeast         18094      0.0056          0.0738       0.0038        0.0011               8
           Rules   Home region     South         26878      0.0044          0.0746       0.0029        0.0009              14
           Rules   Home region      West         12673      0.0051          0.0645       0.0032        0.0007               3
        Logistic       Segment  Business         16142      0.0029          0.0142       0.0006        0.0002               1
        Logistic       Segment   Premium         18177      0.0050          0.0117       0.0013        0.0005               0
        Logistic       Segment  Standard         39918      0.0053          0.0100       0.0021        0.0009               0
        Logistic KYC risk band      High          3819      0.0079          0.0162       0.0016        0.0016               0
        Logistic KYC risk band       Low         51585      0.0046          0.0113       0.0017        0.0006               1
        Logistic KYC risk band    Medium         18833      0.0043          0.0105       0.0012        0.0007               0
        Logistic   Home region   Midwest         16592      0.0040          0.0125       0.0011        0.0007               1
        Logistic   Home region Northeast         18094      0.0056          0.0111       0.0018        0.0009               0
        Logistic   Home region     South         26878      0.0044          0.0107       0.0013        0.0004               0
        Logistic   Home region      West         12673      0.0051          0.0114       0.0024        0.0009               0
Rules + logistic       Segment  Business         16142      0.0029          0.1785       0.0057        0.0020              23
Rules + logistic       Segment   Premium         18177      0.0050          0.0762       0.0023        0.0003               3
Rules + logistic       Segment  Standard         39918      0.0053          0.0299       0.0027        0.0006               4
Rules + logistic KYC risk band      High          3819      0.0079          0.0864       0.0055        0.0024               3
Rules + logistic KYC risk band       Low         51585      0.0046          0.0730       0.0032        0.0006              20
Rules + logistic KYC risk band    Medium         18833      0.0043          0.0725       0.0029        0.0011               7
Rules + logistic   Home region   Midwest         16592      0.0040          0.0779       0.0027        0.0007               5
Rules + logistic   Home region Northeast         18094      0.0056          0.0739       0.0040        0.0011               8
Rules + logistic   Home region     South         26878      0.0044          0.0748       0.0030        0.0009              14
Rules + logistic   Home region      West         12673      0.0051          0.0646       0.0035        0.0007               3
```

## Typology-level fraud value capture
These are offline evaluation summaries using the restricted planted labels after decisions were made.
```text
        Strategy              Typology  Fraud_Transactions  Fraud_Value  Fraud_Value_Captured_Pct
       Incumbent      account_takeover                  30     12544.75                      0.00
       Incumbent          card_testing                 120       325.19                      0.00
       Incumbent credential_compromise                  40     19417.36                      0.00
       Incumbent   terminal_compromise                 160     34945.88                      0.00
           Rules      account_takeover                  30     12544.75                     77.99
           Rules          card_testing                 120       325.19                     65.71
           Rules credential_compromise                  40     19417.36                     84.98
           Rules   terminal_compromise                 160     34945.88                     64.79
        Logistic      account_takeover                  30     12544.75                     82.89
        Logistic          card_testing                 120       325.19                     35.37
        Logistic credential_compromise                  40     19417.36                     85.39
        Logistic   terminal_compromise                 160     34945.88                     73.26
Rules + logistic      account_takeover                  30     12544.75                     78.29
Rules + logistic          card_testing                 120       325.19                     68.38
Rules + logistic credential_compromise                  40     19417.36                     86.11
Rules + logistic   terminal_compromise                 160     34945.88                     70.13
```

## Limitations and interpretation
More planted events and repeatable seeds reduce run-to-run noise inside this simulator; they do not make synthetic data representative or establish a statistically reliable real-world ranking. Fraud patterns, labels, intervention effects, and unit economics are still designed assumptions. Results do not establish causal impact, expected savings, or production performance. Thresholds, capacity, and assumptions should be validated against real labeled payment data before operational use.

## Next questions
Vary attack signatures and prevalence, validate the simulator assumptions with fraud operations, and test the workflow on representative labeled payment data before drawing operational conclusions.
