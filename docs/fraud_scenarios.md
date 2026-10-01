# Synthetic fraud scenarios

The crisis begins after approximately 58% of the simulation horizon. The default configuration samples ten campaigns for each of four event families. Each campaign has an earlier and a later phase, producing 700 planted events per seed; the temporal split places 350 in training and 350 in the later holdout. The scenario table is synthetic ground truth stored in `data/synthetic/run/restricted/fraud_ground_truth.csv`; do not use it when investigating the public transactions or creating features.

| Typology | Injected signature | Evaluation interpretation |
|---|---|---|
| Terminal compromise | 320 total transactions from ten sampled campaigns. Each campaign creates two 16-event bursts across several customers at one shared endpoint, with moderate/high amounts. | Look for unusual terminal concentration and cross-customer bursts. |
| Card testing | 240 total low-value transactions from ten campaigns. Each campaign creates two 12-event rapid sequences across several customers at one endpoint. | Look for low amounts combined with rapid prior-24-hour velocity. |
| Credential compromise | 80 larger purchases from ten campaigns. Each campaign creates two four-event blocks for one customer through an unfamiliar terminal. | Compare amount to customer profile and endpoint familiarity. |
| Account takeover | 60 shifted-channel/authentication purchases from ten campaigns. Each campaign creates two three-event blocks for one customer at a new endpoint. | Combine time, channel, authentication, and pair-familiarity context. |
| **Total** | **700 events per seed; 350 in each side of the temporal split.** | Each later holdout contains hundreds of planted events but remains synthetic and designed. |

The event rates, campaign count, timing, and signatures are design assumptions for an educational prototype. They do not model the full variation or adversarial adaptation of real payment fraud. The simulator records transaction IDs, event IDs, typology, affected customers, terminal, and crisis start in the restricted truth file. Ten-seed performance ranges measure variation under this generator; they are not confidence intervals for real payment populations.
