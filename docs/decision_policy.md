# Decision policy and economics

## Four actions

- **APPROVE:** release the payment; incurs assumed fraud loss and chargeback fee if fraudulent, or earns an assumed interchange margin if legitimate.
- **CHALLENGE:** request step-up verification. The base simulation assumes $0.40 per challenge and an 80% stop probability for challenged fraud. Legitimate challenges also incur the friction cost.
- **REVIEW:** send to a human queue. The base simulation assumes $4.50 per review and 90% fraud recovery. Daily capacity is finite; lower-ranked review candidates spill into CHALLENGE.
- **DECLINE:** block the event. Fraud loss is prevented; a legitimate false decline carries assumed customer attrition cost and lost margin.

Scores are converted to actions using ordered thresholds. Threshold choices are selected against training history from a short, explicit grid of candidate bands. The held-out time period is then evaluated once. This is a teaching baseline for decision economics, not production threshold tuning.

## Cost model

Fraud approval cost is amount + $25 chargeback fee. Fraud challenge cost is residual amount after the assumed challenge-stop probability plus challenge cost. Fraud review cost is residual amount after recovery plus review cost. Fraud decline cost is zero in this simplified model. Legitimate approval earns a negative cost equal to the configured interchange margin; challenge and review incur their unit costs; false decline incurs the attrition probability × customer lifetime value plus lost margin.

The cost model omits dispute time, regulatory impact, customer-level dependence, challenge abandonment, recovery delays, funding costs, and many other consequences. All rates and values in `src/config.py` are fictional and should be stressed before using results as portfolio recommendations.
