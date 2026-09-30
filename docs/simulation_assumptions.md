# Simulation assumptions — customer profiles

These parameters create a fictional learning environment. They are not industry benchmarks or measurements from a real payments company. The initial sample is deliberately small; random samples do not have to reproduce the configured population percentages exactly.

| Parameter | Current setting | Meaning |
|---|---:|---|
| Random seed | `20260915` | Reproducible pseudo-random draws. |
| Customer count | `20` | Continues the recovered local script; the older roadmap snapshot said 10. |
| Segment probabilities | Standard 70%, Premium 20%, Business 10% | Fictional composition used to sample a segment per customer. |
| Segment median typical spend | $45, $100, $180 | Dollar medians for Standard, Premium, Business customers. |
| Spend log-space sigma | `0.40` | Spread of customer typical spend around the segment median. |
| Segment median transaction rate | 1.5, 2.5, 4.0 per day | Fictional median customer-level latent rates by segment. |
| Rate log-space sigma | `0.30` | Spread around each segment's transaction-rate median. |
| Region probabilities | Northeast 24%, South 36%, Midwest 22%, West 18% | Fictional home-region composition. |
| KYC band probabilities | Low 70%, Medium 25%, High 5% | Fictional KYC risk mix, sampled independently. |

## Statistical choices

Typical spend and typical daily transaction rate are positive, heterogeneous customer profiles. A log-normal distribution is a reasonable starting assumption for these quantities because it cannot generate negative values and allows a right tail. NumPy's `lognormal(mean=..., sigma=...)` takes the mean and standard deviation in log space. Supplying `log(configured_median)` makes the configured value the distribution median, not its arithmetic mean.

The customer transaction rate is a profile, not a count of transactions observed on a particular day. A later event-generation step can draw an integer daily count from a Poisson model using this rate, after its assumptions are introduced and explained.

KYC risk describes an onboarding/control assessment in this synthetic world. It is not fraud ground truth and is not used to assign fraud labels. Region and KYC mix values are provisional design assumptions and should be stress-tested before portfolio conclusions rely on them.

## Scope limits

This milestone creates customer profiles only. It does not create accounts, merchants, terminals, transactions, fraud events, model features, or decision outcomes. The generated file is synthetic and reproducible, but it does not establish real-world fraud patterns.
