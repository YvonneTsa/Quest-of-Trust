# TrustHold roadmap status

This table marks what the current repository actually implements. “Prototype complete” means the stage runs in this synthetic project; it does not imply production validation.

| Stage | Deliverable | Status in this build |
|---|---|---|
| 0. Foundation | Charter, project structure, reproducible settings, learning protocol | Complete |
| 1. Customer simulation | IDs, segment, spend/rate profiles, region, independent KYC band | Complete |
| 2. Accounts and payment network | Accounts, merchants, terminals, ownership links | Complete |
| 3. Legitimate transaction engine | Time-stamped Poisson activity, amount, channel and authentication | Complete |
| 4. Fraud injection | Four typologies and separate hidden ground truth; two crisis phases | Complete |
| 5. Data storage | CSV artifacts plus local SQLite analytical database | Complete; SQLite selected instead of DuckDB/Parquet for a dependency-light first build |
| 6. SQL investigation | Volume, endpoint concentration, velocity, amount deviation, channel/auth queries | Complete |
| 7. Behavioral features | Point-in-time amount, velocity, terminal/customer familiarity, time, auth, region | Complete |
| 8. Rules engine | Transparent score, thresholds, alert reasons | Complete |
| 9. Model comparison | Temporal NumPy logistic baseline and rules/hybrid comparisons, PR-AUC | Baseline complete; tree/boosting models are deferred until they add value beyond this teaching baseline |
| 10. Decision engine | APPROVE, CHALLENGE, REVIEW, DECLINE actions | Complete |
| 11. Capacity planning | Per-day top-risk review queue and overflow routing | Complete |
| 12. Fraud economics | Loss, margin, challenge/review costs, attrition and sensitivity scenarios | Complete as documented assumptions |
| 13. Network intelligence | Customer-terminal connectivity and concentration summaries | Complete as a first bipartite graph layer; device/IP networks are future extensions |
| 14. Monitoring and governance | Daily observable metrics, lagged 14-day z-scores/3-sigma alerts, group diagnostics | Prototype complete; no production drift or fairness certification |
| 15. Executive simulator | Interactive browser dashboard for capacity/economic assumptions | Complete as a standalone HTML dashboard; Power BI packaging remains optional |
| 16. Case study | Context, method, holdout outcomes, sensitivity, limitations | Generated from the actual run |
| 17. Project presentation | GitHub README, reproducible run instructions, code/docs, dashboard and sample outputs | Complete for initial public repository publication |

## Known limits of this version

The simulated business economics and customer population are not calibrated to a real processor. Only a logistic model is included because the goal is a clear baseline; compare tree-based models later if they improve the decision outcome. The baseline has one account per customer and no device/IP/login events. The dashboard uses precomputed test outcomes rather than evaluating arbitrary live thresholds in the browser. The simulator is an educational project prototype, not a production fraud control.
