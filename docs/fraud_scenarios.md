# Synthetic fraud scenarios

The crisis begins after approximately 58% of the simulation horizon. Each of the four event families has an early crisis burst and a later burst so the temporal training period and future holdout both include every typology. The scenario table is synthetic ground truth stored in `data/synthetic/run/restricted/fraud_ground_truth.csv`; do not use it when investigating the public transactions or creating features.

| Typology | Injected signature | Evaluation interpretation |
|---|---|---|
| Terminal compromise | 32 total transactions across multiple customers at one shared endpoint, split between two moderate/high-value bursts. Legitimate customers use only a small habitual endpoint set. | Look for unusual terminal concentration and cross-customer bursts. |
| Card testing | 24 total low-value transactions across several customers at one endpoint, split between two bursts seconds apart. | Look for low amounts combined with rapid prior-24-hour velocity. |
| Credential compromise | Eight total larger purchases for one customer through an unfamiliar terminal, split across two bursts. | Compare amount to customer profile and endpoint familiarity. |
| Account takeover | Six total shifted-channel/authentication purchases for one customer at a new endpoint, split across two bursts. | Combine time, channel, authentication, and pair-familiarity context. |

The event rates, count, timing, and signatures are design assumptions for an educational prototype. They do not model the full variation or adversarial adaptation of real payment fraud. The simulator records transaction IDs, event IDs, typology, affected customers, terminal, and crisis start in the restricted truth file.
