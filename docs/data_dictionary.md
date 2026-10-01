# Data dictionary

The synthetic generator emits separate tables so the business entities and event grain remain clear. `Fraud_Flag` is deliberately absent from customer, transaction, feature, database, and decision tables. Offline evaluation joins the restricted `fraud_ground_truth.csv` only after feature construction.

| Table / field | Grain and meaning | Available at decision time? |
|---|---|---|
| `customers.Customer_ID` | One stable fictional customer identifier. | Yes |
| `customers.Segment` | Fictional Standard/Premium/Business profile group. | Yes |
| `customers.Typical_Spend` | Customer's simulated positive typical amount, in USD. | Yes |
| `customers.Typical_Transactions_Per_Day` | Latent mean transaction rate, not an observed count. | Yes |
| `customers.Home_Region` | Fictional customer home region. | Yes |
| `customers.KYC_Risk_Band` | Fictional onboarding risk band; not a fraud label or model feature. | Yes, but excluded from this baseline model |
| Customer-to-terminal baseline | Each customer is assigned a small set of habitual endpoints for legitimate activity. | Known profile in the simulation; not an event label |
| `accounts.Account_ID` | One active account linked to a customer in this first version. | Yes |
| `merchants.Merchant_ID` | Fictional merchant with category, region, and assumed risk profile. | Yes |
| `terminals.Terminal_ID` | Endpoint belonging to exactly one merchant. | Yes |
| `transactions.Transaction_ID` | Unique transaction/event identifier. | Yes |
| `transactions.Timestamp` | Event timestamp, in the simulator's single local time zone (UTC-naive). | Yes |
| `transactions.Customer_ID`, `Account_ID` | Customer/account responsible for the event. | Yes |
| `transactions.Merchant_ID`, `Terminal_ID` | Business and endpoint used; merchant matches terminal ownership. | Yes |
| `transactions.Customer_Region`, `Merchant_Region` | Fictional home location and endpoint location. | Yes |
| `transactions.Amount`, `Currency` | Simulated transaction amount and USD currency. | Yes |
| `transactions.Channel`, `Auth_Type`, `Auth_Result` | Channel and authentication context available to policy. | Yes |
| `transactions.Incumbent_Decision` | Simple existing behavior: approve approved auth, challenge soft decline. | Yes |
| `behavior_features.Amount_To_Typical_Spend` | Current amount divided by customer profile amount. | Yes |
| `behavior_features.Tx_Count_Prior_24h` | Earlier transactions for the customer in the rolling 24 hours. | Yes; current event excluded |
| `behavior_features.Terminal_Prior_Tx_Count` | Earlier events at the terminal. | Yes; current event excluded |
| `behavior_features.Terminal_Prior_Distinct_Customers` | Distinct customers seen at endpoint before this event. | Yes; current event excluded |
| `behavior_features.Customer_Terminal_Prior_Count` | Earlier customer/terminal pair count. | Yes; current event excluded |
| `behavior_features.Is_Night`, `Is_Weekend` | Timestamp-derived time context. | Yes |
| `behavior_features.Region_Mismatch` | Whether current endpoint region differs from the fictional home region. | Yes; descriptive context only |
| `behavior_features.Auth_Soft_Decline`, channel/auth flags | Current authentication/channel result. | Yes |
| `terminal_network_summary` | Full-run endpoint degree and customer connectivity summary for offline investigation. | Investigation output; do not feed back as a point-in-time feature |
| `impact_by_customer_group` | Held-out action/friction/fraud rates by segment and KYC band. | Offline descriptive monitoring only |
| `restricted/fraud_ground_truth.Transaction_ID` | Injected event key, stored separately for offline evaluation. | **No** |
| `restricted/fraud_ground_truth.Typology` | Planted scenario label. | **No** |
| `test_decisions.Decision` | Strategy output: APPROVE, CHALLENGE, REVIEW, DECLINE. | Produced by the simulation |
| `strategy_metrics` | One row per strategy for the default seed's later-date holdout, including capture, false declines, customer friction, review overflow, modeled cost, and PR-AUC where a continuous score exists. | Offline evaluation output |
| `seed_stability_by_run` | One row per seed and strategy (Rules or Logistic), with the same holdout outcome metrics. | Offline evaluation output |
| `seed_stability_summary` | Per-strategy means, medians, and observed minimum/maximum across the configured seeds. | Offline summary; ranges are not confidence intervals |
| `seed_stability_comparison` | Paired Logistic-minus-Rules differences on each shared seed, including lower-cost win count and observed ranges. | Offline paired comparison |
| `scenario_surface` | Precomputed outcomes for strategy, daily review-capacity, and fictional economics combinations for the default seed. | Scenario analysis; no live decisions |

## Leakage boundary

`fraud_ground_truth.csv` is not written into the public SQLite database. The risk features are built before the hidden transaction IDs are joined to create the temporary training/evaluation label. The saved model coefficients, monitoring table, strategy outputs, and public decision rows do not contain the label. KYC band is excluded from model inputs to prevent an onboarding descriptor from becoming a concealed fraud shortcut.

## Seed stability outputs

The default run compares ten seeds and plants 350 fraud events in the later-date holdout for every seed. The `seed_stability_*` tables show the output spread observed in this specific synthetic design. They do not encode sampling uncertainty for real customers, confidence intervals, or evidence that the fictional population represents an actual payments book. `seed_stability_by_run` is the row-level source for the summary and paired comparison.
