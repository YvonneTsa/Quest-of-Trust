# Simulation assumptions

All parameters below are fictional settings for an educational simulator, not public-industry estimates.

| Parameter | Default | Notes |
|---|---:|---|
| Seed | `20260915` through `20260944` | Thirty consecutive seeds are compared by default; each simulation layer uses deterministic seed offsets. |
| Horizon | 60 days | Start date in code: 2026-01-01. |
| Customers | 2,000 | CLI-overridable; the initial recovery sample of 20 remains in `customers.csv`. |
| Merchants / terminals | 800 / 1,200 | Each terminal maps to one merchant; dimensions are scaled with the payment book. |
| Segment mix | 70/20/10 | Standard/Premium/Business, fictional. |
| Segment median spend | $45/$100/$180 | Log-normal median parameterization; sigma 0.40 in log space. |
| Segment median transactions/day | 1.5/2.5/4.0 | Latent rate; daily count sampled with Poisson. Rate sigma 0.30 in log space. |
| Regions | Northeast 24%, South 36%, Midwest 22%, West 18% | Fictional customer mix. |
| KYC bands | Low 70%, Medium 25%, High 5% | Independent sample; not a fraud proxy or baseline feature. |
| Baseline channel mix | 52/33/15% | Card present/e-commerce/mobile wallet. |
| Home-region behavior | 95% habitual-region endpoints; 5% any endpoint | Fictional regular activity retains occasional out-of-region events. |
| Soft auth decline | 1.5% | Fictional. Incumbent challenges soft declines and approves the rest. |
| Crisis onset | Day 58% of horizon | Four scenario bursts are spaced later in the crisis period. |
| Fraud injections | 320/240/80/60 | Total planted events across 10 sampled campaigns per typology: terminal compromise/card testing/credential compromise/account takeover. Each later holdout contains 350 events. |
| Review capacity | 250 cases/day | Command-line configurable; scaled 10x with the payment book. Capacity sensitivity uses 10/50/150/250/500 cases/day. |
| Interchange margin | 1.1% | Used as a simplified legitimate-payment benefit. |
| Chargeback fee | $25 | Added to approved fraud loss. |
| Challenge | $0.40 and 80% fraud stop | Assumed step-up economics. |
| False-decline attrition | 5% × $500 lifetime value | Simplified customer-loss proxy. |
| Manual review | $4.50 and 90% recovery | Assumed investigator economics. |

## Distribution notes

Spend and latent transaction rate use log-normal distributions because they are positive and can be right-skewed. NumPy's `mean` argument is a log-space mean; passing the log of a configured median makes that value the population median. Daily transaction counts use Poisson draws with the customer rate. Beta is appropriate for bounded propensities, not unbounded dollars; exponential waiting times may be useful later for time gaps but do not describe the customer-level profile chosen here.

## Scale, fit/validation separation, and seed stability

Each full simulation creates about 246,000 events, including 700 simulated fraud events across 60 days. The later 30% of dates contains 350 fraud cases. Thresholds are selected on a campaign-stratified validation sample that is separate from model fitting; the later-date test stays untouched until final evaluation. A second, nested campaign-level check excludes half of campaign identities from both fitting and threshold selection and evaluates 175 later-phase fraud cases in the default seed. The primary later-date comparison uses 30 consecutive seeds. Attack count and daily review capacity are configured with the larger payment book.

The seed comparisons report observed min-to-max variation, medians, and paired win rates for both the later-date and unseen-campaign holdouts. Those ranges describe random variation under this synthetic design; they are **not** confidence intervals for real payment customers, a significance test, or evidence of external validity. The same four designed typologies and shared economics still govern every seed.

## Sensitivity

Every run exports review-capacity sensitivity and economic scenarios. The business break-even view varies challenge success, review recovery and cost, false-decline attrition, chargeback fee, legitimate-payment margin, and daily capacity. Cost assumptions are varied with decisions held fixed; capacity changes recalculate routing with fixed thresholds. Any crossover is conditional on the fictional assumptions and is not a forecast or confidence interval.
