# Synthetic fraud scenarios

The crisis begins after approximately 58% of the simulation horizon. The default configuration samples ten campaigns for each of four event families. Every planted transaction receives a campaign identity in the restricted truth table. Each campaign has an earlier and a later phase, producing 700 planted events per seed; the temporal split places about 350 events before the date boundary and 350 in the later-date holdout. The scenario table is synthetic ground truth stored in `data/synthetic/run/restricted/fraud_ground_truth.csv`; do not use it when investigating the public transactions or creating features.

| Typology | Injected signature | Evaluation interpretation |
|---|---|---|
| Terminal compromise | 320 total transactions from ten sampled campaigns. Each campaign creates two 16-event bursts across several customers at one shared endpoint, with moderate/high amounts. | Look for unusual terminal concentration and cross-customer bursts. |
| Card testing | 240 total low-value transactions from ten campaigns. Each campaign creates two 12-event rapid sequences across several customers at one endpoint. | Look for low amounts combined with rapid prior-24-hour velocity. |
| Credential compromise | 80 larger purchases from ten campaigns. Each campaign creates two four-event blocks for one customer through an unfamiliar terminal. | Compare amount to customer profile and endpoint familiarity. |
| Account takeover | 60 shifted-channel/authentication purchases from ten campaigns. Each campaign creates two three-event blocks for one customer at a new endpoint. | Combine time, channel, authentication, and pair-familiarity context. |
| **Total** | **700 events per seed; 350 in each side of the temporal split.** | Each later holdout contains hundreds of planted events but remains synthetic and designed. |

The event rates, campaign count, timing, and signatures are design assumptions for an educational prototype. They do not model the full variation or adversarial adaptation of real payment fraud. The simulator records transaction IDs, event IDs, typology, campaign identity, affected customers, terminal, and crisis start in the restricted truth file. Thirty-seed performance ranges measure variation under this generator; they are not confidence intervals for real payment populations.

## How campaign identities are used in evaluation

Campaign IDs are restricted labels used only to construct disjoint groups. In the historical window, the model-fit group uses campaign numbers 1, 5, and 9 per typology; threshold validation uses campaigns 3 and 7; campaigns 2, 4, 6, 8, and 10 are excluded from both. The primary temporal comparison then evaluates later-period events from all campaign identities, including campaigns seen in fit or validation and campaigns held out from both.

The separate unseen-campaign comparison uses campaigns 1, 5, and 9 for fitting, campaigns 3 and 7 for threshold validation, and campaigns 2, 4, 6, 8, and 10 as the held-out set. It tests later phases of identities unseen during fit and threshold selection. It still evaluates the same four hand-designed fraud typologies and does not represent an unseen attack type.

