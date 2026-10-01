# TrustHold — The Cost of Fraud: simulation case study

> All numbers below are outputs of this fictional synthetic simulation, not claims about a real company.

## Finding first
Across 10 deterministic simulation seeds, Logistic had lower modeled net cost than Rules in 10/10 runs. The median paired difference (Logistic minus Rules) was -$22,635.35, with observed seed-to-seed differences from -$25,345.00 to -$19,903.46. These are scenario-conditional simulation results, not real-world savings or formal confidence intervals.

## Context and decision problem
TrustHold models a digital-payments environment where each event can be approved, challenged, reviewed, or declined. The business objective is to balance fraud loss, customer friction, finite review capacity, and payment margin.

## Data and method
The generated world contains 246,314 timestamped transactions. A later time period beginning 2026-02-12 is held out for evaluation. Fraud truth is stored separately and is joined only for model training and offline evaluation.
The default book uses 2,000 customers, 800 merchants, 1,200 terminals, 60 days, and 10 separately sampled attacks per typology across four documented patterns. This yields 350 planted fraud events in each later-period holdout. Legitimate event volume, attack count, and review capacity are scaled together so the modeled fraud share and investigator-to-volume ratio stay near the earlier version.
Behavioral features use only information available before each transaction. A transparent rule score and a NumPy logistic-regression baseline are compared with the same four payment actions. Thresholds are selected on each seed's earlier dates; its later dates are reserved for evaluation.

## Results across seeds
Each of the 10 runs changes the random draws for customers, legitimate events, terminals, and attack campaigns. The paired comparison keeps the same fictional economics and 250-case daily review capacity. The ranges below are the observed minimum and maximum across those seeds; they summarize simulator variation and are not confidence intervals for real payment populations.
| Strategy | Holdout fraud events, mean (range) | Fraud value captured, mean (range) | False declines, median (range) | Legitimate challenges, median (range) | Legitimate reviews, median (range) | Modeled net cost, median (range) |
|---|---:|---:|---:|---:|---:|---:|
| Rules | 350 (350-350) | 73.15% (68.29-76.44%) | 32.5 (24-45) | 5,210 (4,552-5,764) | 138 (109-155) | -$53,583.32 (-$56,248.77 to -$48,112.39) |
| Logistic | 350 (350-350) | 90.43% (85.86-94.26%) | 19.5 (15-33) | 1,787.5 (1,568-1,838) | 328 (248-418) | -$75,243.60 (-$79,150.50 to -$68,811.92) |

Logistic captured a median +16.90 percentage points of fraud value relative to Rules (range +14.49 to +21.36). It sent a median 3,461.5 fewer legitimate events to challenge (range 2,852 to 4,059 fewer), while routing +213.5 more to investigators (range +93 to +273). Fewer challenges do not mean that every case disappears from the operating queue.

## Held-out strategy comparison
The table below is the single default seed (20260915), not the multi-seed summary. The fictional cost assumptions are documented in `docs/simulation_assumptions.md`. Lower net economic cost is better under those settings. The lowest cost in this base run is **Logistic**, at -$79,150.50.

```text
    Seed         Strategy  Transactions  Fraud_Transactions  Fraud_Value  Fraud_Value_Captured_Pct  Fraud_Loss_After_Intervention  Precision_Among_Interventions  Fraud_Recall  Legitimate_Challenge_Count  Legitimate_Review_Count  False_Declines  Review_Overflow_Count  Net_Economic_Cost         PR_AUC
20260915        Incumbent         74237                 350     67233.18                      0.00                       75983.18                         0.0000        0.0000                        1110                        0               0                      0          -15477.19 Not applicable
20260915            Rules         74237                 350     67233.18                     73.09                       20745.89                         0.0457        0.7486                        5305                      140              30                      0          -56248.77         0.2655
20260915         Logistic         74237                 350     67233.18                     91.42                        7219.04                         0.1193        0.8829                        1838                      410              33                      0          -79150.50         0.5855
20260915 Rules + logistic         74237                 350     67233.18                     82.27                       13749.75                         0.0508        0.8629                        5447                      169              30                      0          -62823.34         0.4119
```
Complete per-seed rows are available in `data/synthetic/run/seed_stability_by_run.csv`; the summary and paired comparison are also stored in SQLite.

## Capacity sensitivity
The same score bands were evaluated with different daily review limits. Overflow cases are routed to challenge.
```text
        Strategy  Review_Capacity_Per_Day  Fraud_Value_Captured_Pct  Review_Overflow_Count  Net_Economic_Cost
           Rules                       10                     69.46                     95          -54198.31
        Logistic                       10                     89.69                    324          -79318.19
Rules + logistic                       10                     77.75                    145          -60381.32
           Rules                       50                     70.76                     51          -54893.62
        Logistic                       50                     90.44                     66          -78764.96
Rules + logistic                       50                     79.80                     93          -61545.72
           Rules                      150                     73.09                      0          -56248.77
        Logistic                      150                     91.42                      0          -79150.50
Rules + logistic                      150                     82.27                      0          -62823.34
           Rules                      250                     73.09                      0          -56248.77
        Logistic                      250                     91.42                      0          -79150.50
Rules + logistic                      250                     82.27                      0          -62823.34
           Rules                      500                     73.09                      0          -56248.77
        Logistic                      500                     91.42                      0          -79150.50
Rules + logistic                      500                     82.27                      0          -62823.34
```

## Economic assumption sensitivity
The action decisions are held fixed while challenge effectiveness, false-decline attrition, and review recovery assumptions change.
```text
        Strategy              Economic_Scenario  Fraud_Loss_After_Intervention  False_Declines  Net_Economic_Cost
       Incumbent               Base assumptions                       75983.18               0          -15477.19
           Rules               Base assumptions                       20745.89              30          -56248.77
        Logistic               Base assumptions                        7219.04              33          -79150.50
Rules + logistic               Base assumptions                       13749.75              30          -62823.34
       Incumbent  Lower challenge effectiveness                       75983.18               0          -15477.19
           Rules  Lower challenge effectiveness                       24903.67              30          -52090.99
        Logistic  Lower challenge effectiveness                        8843.02              33          -77526.52
Rules + logistic  Lower challenge effectiveness                       16911.78              30          -59661.32
       Incumbent Higher challenge effectiveness                       75983.18               0          -15477.19
           Rules Higher challenge effectiveness                       17627.56              30          -59367.11
        Logistic Higher challenge effectiveness                        6001.06              33          -80368.49
Rules + logistic Higher challenge effectiveness                       11378.24              30          -65194.86
       Incumbent  Lower false-decline attrition                       75983.18               0          -15477.19
           Rules  Lower false-decline attrition                       20745.89              30          -56848.77
        Logistic  Lower false-decline attrition                        7219.04              33          -79810.50
Rules + logistic  Lower false-decline attrition                       13749.75              30          -63423.34
       Incumbent Higher false-decline attrition                       75983.18               0          -15477.19
           Rules Higher false-decline attrition                       20745.89              30          -55498.77
        Logistic Higher false-decline attrition                        7219.04              33          -78325.50
Rules + logistic Higher false-decline attrition                       13749.75              30          -62073.34
       Incumbent          Lower review recovery                       75983.18               0          -15477.19
           Rules          Lower review recovery                       26313.32              30          -50681.35
        Logistic          Lower review recovery                       10069.18              33          -76300.36
Rules + logistic          Lower review recovery                       20413.82              30          -56159.28
```

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
        Logistic       Segment  Business         16142      0.0029          0.0221       0.0099        0.0012               6
        Logistic       Segment   Premium         18177      0.0050          0.0259       0.0062        0.0021              14
        Logistic       Segment  Standard         39918      0.0053          0.0273       0.0057        0.0030              13
        Logistic KYC risk band      High          3819      0.0079          0.0285       0.0113        0.0031               3
        Logistic KYC risk band       Low         51585      0.0046          0.0260       0.0065        0.0024              24
        Logistic KYC risk band    Medium         18833      0.0043          0.0248       0.0063        0.0022               6
        Logistic   Home region   Midwest         16592      0.0040          0.0217       0.0077        0.0019               7
        Logistic   Home region Northeast         18094      0.0056          0.0216       0.0065        0.0031              10
        Logistic   Home region     South         26878      0.0044          0.0345       0.0062        0.0016               9
        Logistic   Home region      West         12673      0.0051          0.0189       0.0068        0.0036               7
Rules + logistic       Segment  Business         16142      0.0029          0.1798       0.0063        0.0022              23
Rules + logistic       Segment   Premium         18177      0.0050          0.0774       0.0034        0.0005               3
Rules + logistic       Segment  Standard         39918      0.0053          0.0316       0.0034        0.0009               4
Rules + logistic KYC risk band      High          3819      0.0079          0.0882       0.0060        0.0029               3
Rules + logistic KYC risk band       Low         51585      0.0046          0.0744       0.0041        0.0008              20
Rules + logistic KYC risk band    Medium         18833      0.0043          0.0741       0.0034        0.0013               7
Rules + logistic   Home region   Midwest         16592      0.0040          0.0800       0.0033        0.0010               5
Rules + logistic   Home region Northeast         18094      0.0056          0.0751       0.0047        0.0014               8
Rules + logistic   Home region     South         26878      0.0044          0.0760       0.0037        0.0009              14
Rules + logistic   Home region      West         12673      0.0051          0.0664       0.0047        0.0011               3
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
        Logistic      account_takeover                  30     12544.75                     92.37
        Logistic          card_testing                 120       325.19                     65.66
        Logistic credential_compromise                  40     19417.36                     96.20
        Logistic   terminal_compromise                 160     34945.88                     88.65
Rules + logistic      account_takeover                  30     12544.75                     83.73
Rules + logistic          card_testing                 120       325.19                     70.15
Rules + logistic credential_compromise                  40     19417.36                     87.85
Rules + logistic   terminal_compromise                 160     34945.88                     78.76
```

## Limitations and interpretation
More planted events and repeatable seeds reduce run-to-run noise inside this simulator; they do not make synthetic data representative or establish a statistically reliable real-world ranking. Fraud patterns, labels, intervention effects, and unit economics are still designed assumptions. Results do not establish causal impact, expected savings, or production performance. Thresholds, capacity, and assumptions should be validated against real labeled payment data before operational use.

## Next questions
Test sensitivity to fraud prevalence and chargeback cost. Then inspect typology-level performance, validate the simulator assumptions with domain experts, and expand the portfolio presentation.
