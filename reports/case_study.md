# TrustHold — The Cost of Fraud: simulation case study

> All numbers below are outputs of this fictional synthetic simulation, not claims about a real company.

## Context and decision problem
TrustHold models a digital-payments environment where each event can be approved, challenged, reviewed, or declined. The business objective is to balance fraud loss, customer friction, finite review capacity, and payment margin.

## Data and method
The generated world contains 22,903 timestamped transactions. A later time period beginning 2026-02-12 is held out for evaluation. Fraud truth is stored separately and is joined only for model training and offline evaluation.
The simulation plants four documented typologies. Behavioral features use only data available before each transaction. A transparent rule score and a NumPy logistic-regression baseline are compared with the incumbent challenge behavior.

## Held-out strategy comparison
The fictional cost assumptions are documented in `docs/simulation_assumptions.md`. Lower net economic cost is better under those settings. The best strategy under these assumptions is **Logistic**, with held-out net economic cost $-5,847.42.

```text
        Strategy  Transactions  Fraud_Transactions  Fraud_Value  Fraud_Value_Captured_Pct  Fraud_Loss_After_Intervention  Precision_Among_Interventions  Fraud_Recall  Legitimate_Challenge_Count  Legitimate_Review_Count  False_Declines  Review_Overflow_Count  Net_Economic_Cost  PR_AUC
       Incumbent          6923                  35      7194.17                      0.00                        8069.17                         0.0000        0.0000                          97                        0               0                      0             385.41  0.4930
           Rules          6923                  35      7194.17                     78.52                        1749.65                         0.0673        0.8286                         390                        9               3                      0           -4859.65  0.4930
        Logistic          6923                  35      7194.17                     81.62                        1496.89                         0.1508        0.8571                         143                       23               3                      0           -5847.42  0.4881
Rules + logistic          6923                  35      7194.17                     81.08                        1532.47                         0.0683        0.8571                         394                       12               3                      0           -5053.89  0.4815
```

## Capacity sensitivity
The same score bands were evaluated with different daily review limits. Overflow cases are routed to challenge.
```text
        Strategy  Review_Capacity_Per_Day  Fraud_Value_Captured_Pct  Review_Overflow_Count  Net_Economic_Cost
           Rules                        1                     75.62                     12           -4699.86
        Logistic                        1                     77.90                     21           -5665.86
Rules + logistic                        1                     78.29                     12           -4902.66
           Rules                        5                     77.39                      6           -4802.84
        Logistic                        5                     77.90                     11           -5624.96
Rules + logistic                        5                     80.53                      4           -5030.93
           Rules                       15                     78.52                      0           -4859.65
        Logistic                       15                     81.62                      1           -5851.52
Rules + logistic                       15                     81.08                      0           -5053.89
           Rules                       25                     78.52                      0           -4859.65
        Logistic                       25                     81.62                      0           -5847.42
Rules + logistic                       25                     81.08                      0           -5053.89
           Rules                       50                     78.52                      0           -4859.65
        Logistic                       50                     81.62                      0           -5847.42
Rules + logistic                       50                     81.08                      0           -5053.89
```

## Economic assumption sensitivity
The action decisions are held fixed while challenge effectiveness, false-decline attrition, and review recovery assumptions change.
```text
        Strategy              Economic_Scenario  Fraud_Loss_After_Intervention  False_Declines  Net_Economic_Cost
       Incumbent               Base assumptions                        8069.17               0             385.41
           Rules               Base assumptions                        1749.65               3           -4859.65
        Logistic               Base assumptions                        1496.89               3           -5847.42
Rules + logistic               Base assumptions                        1532.47               3           -5053.89
       Incumbent  Lower challenge effectiveness                        8069.17               0             385.41
           Rules  Lower challenge effectiveness                        2234.61               3           -4374.69
        Logistic  Lower challenge effectiveness                        1792.18               3           -5552.13
Rules + logistic  Lower challenge effectiveness                        2058.39               3           -4527.97
       Incumbent Higher challenge effectiveness                        8069.17               0             385.41
           Rules Higher challenge effectiveness                        1385.93               3           -5223.38
        Logistic Higher challenge effectiveness                        1275.42               3           -6068.89
Rules + logistic Higher challenge effectiveness                        1138.03               3           -5448.33
       Incumbent  Lower false-decline attrition                        8069.17               0             385.41
           Rules  Lower false-decline attrition                        1749.65               3           -4919.65
        Logistic  Lower false-decline attrition                        1496.89               3           -5907.42
Rules + logistic  Lower false-decline attrition                        1532.47               3           -5113.89
       Incumbent Higher false-decline attrition                        8069.17               0             385.41
           Rules Higher false-decline attrition                        1749.65               3           -4784.65
        Logistic Higher false-decline attrition                        1496.89               3           -5772.42
Rules + logistic Higher false-decline attrition                        1532.47               3           -4978.89
       Incumbent          Lower review recovery                        8069.17               0             385.41
           Rules          Lower review recovery                        2190.53               3           -4418.78
        Logistic          Lower review recovery                        2080.82               3           -5263.50
Rules + logistic          Lower review recovery                        1933.85               3           -4652.51
```

## Descriptive customer-group impact
The following rates are descriptive diagnostics over synthetic data, not a fairness certification. Small group counts and the intentionally fictional population limit interpretation.
```text
        Strategy    Group_Type     Group  Transactions  Fraud_Rate  Challenge_Rate  Review_Rate  Decline_Rate  False_Declines
       Incumbent       Segment  Business          1030      0.0010          0.0184       0.0000        0.0000               0
       Incumbent       Segment   Premium          1811      0.0017          0.0138       0.0000        0.0000               0
       Incumbent       Segment  Standard          4082      0.0076          0.0130       0.0000        0.0000               0
       Incumbent KYC risk band      High           379      0.0106          0.0079       0.0000        0.0000               0
       Incumbent KYC risk band       Low          4450      0.0034          0.0151       0.0000        0.0000               0
       Incumbent KYC risk band    Medium          2094      0.0076          0.0129       0.0000        0.0000               0
       Incumbent   Home region   Midwest          1393      0.0029          0.0122       0.0000        0.0000               0
       Incumbent   Home region Northeast          1305      0.0046          0.0130       0.0000        0.0000               0
       Incumbent   Home region     South          3074      0.0059          0.0120       0.0000        0.0000               0
       Incumbent   Home region      West          1151      0.0061          0.0226       0.0000        0.0000               0
           Rules       Segment  Business          1030      0.0010          0.1456       0.0029        0.0019               2
           Rules       Segment   Premium          1811      0.0017          0.0823       0.0017        0.0006               1
           Rules       Segment  Standard          4082      0.0076          0.0255       0.0034        0.0012               0
           Rules KYC risk band      High           379      0.0106          0.0237       0.0053        0.0053               0
           Rules KYC risk band       Low          4450      0.0034          0.0548       0.0027        0.0004               2
           Rules KYC risk band    Medium          2094      0.0076          0.0716       0.0029        0.0019               1
           Rules   Home region   Midwest          1393      0.0029          0.0725       0.0022        0.0000               0
           Rules   Home region Northeast          1305      0.0046          0.0245       0.0015        0.0000               0
           Rules   Home region     South          3074      0.0059          0.0716       0.0033        0.0020               3
           Rules   Home region      West          1151      0.0061          0.0434       0.0043        0.0017               0
        Logistic       Segment  Business          1030      0.0010          0.0165       0.0039        0.0019               2
        Logistic       Segment   Premium          1811      0.0017          0.0226       0.0028        0.0000               0
        Logistic       Segment  Standard          4082      0.0076          0.0235       0.0059        0.0024               1
        Logistic KYC risk band      High           379      0.0106          0.0211       0.0079        0.0026               0
        Logistic KYC risk band       Low          4450      0.0034          0.0193       0.0052        0.0009               2
        Logistic KYC risk band    Medium          2094      0.0076          0.0287       0.0033        0.0033               1
        Logistic   Home region   Midwest          1393      0.0029          0.0208       0.0014        0.0000               0
        Logistic   Home region Northeast          1305      0.0046          0.0207       0.0077        0.0000               0
        Logistic   Home region     South          3074      0.0059          0.0234       0.0042        0.0020               3
        Logistic   Home region      West          1151      0.0061          0.0226       0.0070        0.0052               0
Rules + logistic       Segment  Business          1030      0.0010          0.1456       0.0049        0.0019               2
Rules + logistic       Segment   Premium          1811      0.0017          0.0834       0.0017        0.0006               1
Rules + logistic       Segment  Standard          4082      0.0076          0.0262       0.0032        0.0017               0
Rules + logistic KYC risk band      High           379      0.0106          0.0237       0.0053        0.0053               0
Rules + logistic KYC risk band       Low          4450      0.0034          0.0555       0.0031        0.0004               2
Rules + logistic KYC risk band    Medium          2094      0.0076          0.0726       0.0024        0.0029               1
Rules + logistic   Home region   Midwest          1393      0.0029          0.0725       0.0022        0.0000               0
Rules + logistic   Home region Northeast          1305      0.0046          0.0268       0.0015        0.0000               0
Rules + logistic   Home region     South          3074      0.0059          0.0716       0.0042        0.0020               3
Rules + logistic   Home region      West          1151      0.0061          0.0452       0.0026        0.0035               0
```

## Typology-level fraud value capture
These are offline evaluation summaries using the restricted planted labels after decisions were made.
```text
        Strategy              Typology  Fraud_Transactions  Fraud_Value  Fraud_Value_Captured_Pct
       Incumbent      account_takeover                   3      1555.39                      0.00
       Incumbent          card_testing                  12        31.73                      0.00
       Incumbent credential_compromise                   4      2059.96                      0.00
       Incumbent   terminal_compromise                  16      3547.09                      0.00
           Rules      account_takeover                   3      1555.39                     80.00
           Rules          card_testing                  12        31.73                     79.32
           Rules credential_compromise                   4      2059.96                     95.30
           Rules   terminal_compromise                  16      3547.09                     68.13
        Logistic      account_takeover                   3      1555.39                     46.28
        Logistic          card_testing                  12        31.73                     67.74
        Logistic credential_compromise                   4      2059.96                     92.15
        Logistic   terminal_compromise                  16      3547.09                     91.12
Rules + logistic      account_takeover                   3      1555.39                     80.00
Rules + logistic          card_testing                  12        31.73                     79.32
Rules + logistic credential_compromise                   4      2059.96                     95.30
Rules + logistic   terminal_compromise                  16      3547.09                     73.31
```

## Limitations and interpretation
Synthetic event injection makes ground truth known but simplifies real fraud, customer behavior, intervention effectiveness, and selection effects. Economic inputs are assumptions, not empirical estimates. This comparison does not establish causal impact or production performance. Thresholds and review capacity should be stress-tested before drawing portfolio recommendations.

## Next questions
Test sensitivity to fraud prevalence and chargeback cost. Then inspect typology-level performance, validate the simulator assumptions with domain experts, and expand the portfolio presentation.
