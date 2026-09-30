# Simulation assumptions

All parameters below are fictional settings for an educational simulator, not public-industry estimates.

| Parameter | Default | Notes |
|---|---:|---|
| Seed | `20260915` | Reproducible random generators use offset seeds by layer. |
| Horizon | 60 days | Start date in code: 2026-01-01. |
| Customers | 200 | CLI-overridable; initial recovery sample of 20 remains in `customers.csv`. |
| Merchants / terminals | 80 / 120 | Each terminal maps to one merchant. |
| Segment mix | 70/20/10 | Standard/Premium/Business, fictional. |
| Segment median spend | $45/$100/$180 | Log-normal median parameterization; sigma 0.40 in log space. |
| Segment median transactions/day | 1.5/2.5/4.0 | Latent rate; daily count sampled with Poisson. Rate sigma 0.30 in log space. |
| Regions | Northeast 24%, South 36%, Midwest 22%, West 18% | Fictional customer mix. |
| KYC bands | Low 70%, Medium 25%, High 5% | Independent sample; not a fraud proxy or baseline feature. |
| Baseline channel mix | 52/33/15% | Card present/e-commerce/mobile wallet. |
| Home-region behavior | 95% habitual-region endpoints; 5% any endpoint | Fictional regular activity retains occasional out-of-region events. |
| Soft auth decline | 1.5% | Fictional. Incumbent challenges soft declines and approves the rest. |
| Crisis onset | Day 58% of horizon | Four scenario bursts are spaced later in the crisis period. |
| Fraud injections | 32/24/8/6 | Terminal compromise/card testing/credential compromise/ATO. |
| Review capacity | 25 cases/day | Command-line configurable; capacity sensitivity uses 1/5/15/25/50. |
| Interchange margin | 1.1% | Used as a simplified legitimate-payment benefit. |
| Chargeback fee | $25 | Added to approved fraud loss. |
| Challenge | $0.40 and 80% fraud stop | Assumed step-up economics. |
| False-decline attrition | 5% × $500 lifetime value | Simplified customer-loss proxy. |
| Manual review | $4.50 and 90% recovery | Assumed investigator economics. |

## Distribution notes

Spend and latent transaction rate use log-normal distributions because they are positive and can be right-skewed. NumPy's `mean` argument is a log-space mean; passing the log of a configured median makes that value the population median. Daily transaction counts use Poisson draws with the customer rate. Beta is appropriate for bounded propensities, not unbounded dollars; exponential waiting times may be useful later for time gaps but do not describe the customer-level profile chosen here.

## Sensitivity

Every run exports review-capacity sensitivity and economic scenarios for lower/higher challenge effectiveness, lower/higher false-decline attrition, and lower review recovery. These outputs quantify how the preferred strategy can change when assumptions change; they are not statistical confidence intervals.
