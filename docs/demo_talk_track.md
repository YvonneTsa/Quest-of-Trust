# Quest of Trust — 3-minute project walkthrough

## 0:00–0:30 — The business problem

“Quest of Trust is a synthetic payments-risk case study. I wanted to compare fraud strategies by their business consequences, not just by a model metric. Each payment event can be approved, challenged, sent to review, or declined. Every action trades off fraud loss, customer friction, margin, and limited investigator capacity.”

## 0:30–1:00 — The data and safeguards

"I generated a fictional 60-day payments world with 2,000 customers and four documented attack patterns. Each of 30 later-date test periods contains 350 simulated fraud cases. The answer key stays separate from event features. Behavioral history is computed in timestamp order before the current event is added."

## 1:00–1:45 — The comparison

"I compared transparent rules with a logistic baseline, then mapped their scores into approve, challenge, review, or decline actions under a daily review cap. Across 30 synthetic seeds, logistic captured 77.51% of fraud value on average versus 73.73% for rules. Its modeled cost was lower in all 30 paired runs. Fraud-capture lift varied: the median was 3.66 percentage points, but the range included runs where logistic captured less."

## 1:45–2:20 — The business interpretation

"The median paired cost difference was −$15,502 per test period, ranging from −$22,482 to −$11,208. Logistic challenged a median 4,464 fewer good payments and sent 108 fewer good payments to review. Those are synthetic scenario outputs, not observed savings. The comparison depends on fictional challenge effectiveness, review recovery, customer value, and unit costs."

## 2:20–2:45 — Show the interactive artifact

Open the live dashboard. Change daily review capacity and economic assumptions. Explain that these controls reveal precomputed holdout outcomes under different scenarios; they do not retrain the model or make live payment decisions.

## 2:45–3:00 — Close with limits and next step

"This is a reproducible project prototype, not a production fraud control. Thirty seeds show how this simulator behaves under repeated random draws; they do not prove a real-world ranking or quantify uncertainty for actual customers. A separate nested campaign check has 175 fraud events in one seed, so it is a focused diagnostic rather than repeated evidence. The next step would be validating the assumptions and thresholds against representative governed payment data."

## Likely reviewer questions

**Why use a time-based holdout?** Fraud patterns and operations change over time. Training on earlier events and evaluating on later events better represents the forward-looking use case than a random event split.

**Why include a rules baseline?** It is auditable and makes an interpretable comparison point before adding model complexity.

**Why is the modeled cost negative?** Approved legitimate payment margin is represented as a negative cost. The total is an assumption-driven net-cost calculation, not realized profit.

**What is the biggest limitation?** The data, fraud scenarios, intervention probabilities, and unit economics are synthetic. More simulated events and repeated seeds reduce run-to-run noise inside the simulator, but they do not make the scenarios representative of actual fraud.

**Why is SQLite used?** It keeps the local analytical project self-contained. The current workload does not justify operating a database server.
