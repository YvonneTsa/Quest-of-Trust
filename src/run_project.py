"""Run TrustHold from synthetic data generation through strategy comparison."""

import argparse
from dataclasses import replace
from pathlib import Path

import pandas as pd

from src.config import (
    DEFAULT_OUTPUT_DIR,
    ECONOMICS,
    N_CUSTOMERS,
    N_MERCHANTS,
    N_TERMINALS,
    PROJECT_ROOT,
    SIMULATION_DAYS,
)
from src.decisions.policies import (
    THRESHOLD_CANDIDATES,
    apply_policy,
    evaluate_policy,
)
from src.evaluation.metrics import action_counts, average_precision
from src.features.build_features import build_features
from src.models.logistic_baseline import LogisticBaseline
from src.monitoring import daily_monitoring
from src.network_intelligence import terminal_network_summary
from src.reporting import write_case_study, write_dashboard
from src.rules.score_rules import score_rules
from src.simulation.generate_world import generate_entities, generate_legitimate_transactions
from src.simulation.inject_fraud import inject_fraud
from src.storage import save_run


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--customers", type=int, default=N_CUSTOMERS)
    parser.add_argument("--days", type=int, default=SIMULATION_DAYS)
    parser.add_argument("--merchants", type=int, default=N_MERCHANTS)
    parser.add_argument("--terminals", type=int, default=N_TERMINALS)
    parser.add_argument("--review-capacity", type=int, default=25)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def choose_thresholds(train, score_column, capacity):
    results = []
    for thresholds in THRESHOLD_CANDIDATES:
        decisions = apply_policy(train, score_column, thresholds, capacity)
        results.append((evaluate_policy(decisions, "candidate")["Net_Economic_Cost"], thresholds))
    return min(results, key=lambda item: item[0])[1]


def main():
    args = parse_args()
    if min(args.customers, args.days, args.merchants, args.terminals, args.review_capacity) < 1:
        raise SystemExit("All counts and capacities must be positive integers.")

    print("[1/7] Generating customers, accounts, merchants, terminals, and legitimate activity...")
    customers, accounts, merchants, terminals = generate_entities(
        args.customers, args.merchants, args.terminals
    )
    legitimate = generate_legitimate_transactions(
        customers, accounts, merchants, terminals, args.days
    )
    print(f"       Baseline events: {len(legitimate):,}")

    print("[2/7] Injecting documented fraud scenarios; truth stays in a separate file...")
    transactions, truth = inject_fraud(legitimate, customers, terminals, args.days)
    print(f"       Injected fraud events: {len(truth):,} across {truth['Typology'].nunique()} typologies")

    print("[3/7] Building point-in-time behavior features...")
    features = build_features(transactions, customers)
    scored = score_rules(features)
    scored["Rule_Risk"] = scored["Rule_Score"] / 100.0

    # Only the modeling/evaluation frame joins the hidden label, after feature construction.
    truth_ids = set(truth["Transaction_ID"])
    labeled = scored.copy()
    labeled["Fraud_Label"] = labeled["Transaction_ID"].isin(truth_ids).astype(int)
    dates = sorted(pd.to_datetime(labeled["Timestamp"]).dt.normalize().unique())
    split_index = max(1, min(len(dates) - 1, int(len(dates) * 0.70)))
    split_date = pd.Timestamp(dates[split_index])
    train = labeled.loc[pd.to_datetime(labeled["Timestamp"]) < split_date].copy()
    test = labeled.loc[pd.to_datetime(labeled["Timestamp"]) >= split_date].copy()
    if train["Fraud_Label"].sum() == 0 or test["Fraud_Label"].sum() == 0:
        raise SystemExit(
            "The temporal split needs fraud examples in both periods. Increase --days or change the documented crisis timing."
        )

    print("[4/7] Fitting the temporal logistic-regression baseline...")
    model = LogisticBaseline().fit(train)
    scored["Model_Score"] = model.predict_proba(scored)
    scored["Hybrid_Score"] = scored[["Rule_Risk", "Model_Score"]].max(axis=1)
    labeled["Model_Score"] = model.predict_proba(labeled)
    labeled["Hybrid_Score"] = labeled[["Rule_Risk", "Model_Score"]].max(axis=1)
    train = labeled.loc[pd.to_datetime(labeled["Timestamp"]) < split_date].copy()
    test = labeled.loc[pd.to_datetime(labeled["Timestamp"]) >= split_date].copy()

    print("[5/7] Selecting thresholds on training history and evaluating the future holdout...")
    score_specs = [("Rules", "Rule_Risk"), ("Logistic", "Model_Score"), ("Rules + logistic", "Hybrid_Score")]
    selected_thresholds = {
        name: choose_thresholds(train, column, args.review_capacity)
        for name, column in score_specs
    }
    strategies = []
    incumbent = test.copy()
    incumbent["Decision"] = incumbent["Incumbent_Decision"]
    incumbent["Capacity_Overflow"] = 0
    strategies.append(("Incumbent", incumbent))

    for name, score_column in score_specs:
        decided = apply_policy(test, score_column, selected_thresholds[name], args.review_capacity)
        strategies.append((name, decided))

    result_rows = []
    output_decisions = []
    for name, decided in strategies:
        result_rows.append(evaluate_policy(decided, name))
        safe = decided[["Transaction_ID", "Timestamp", "Customer_ID", "Terminal_ID", "Amount", "Decision", "Capacity_Overflow"]].copy()
        safe["Strategy"] = name
        output_decisions.append(safe)
    impact_rows = []
    for name, decided in strategies:
        enriched = decided.merge(
            customers[["Customer_ID", "Segment", "KYC_Risk_Band", "Home_Region"]],
            on="Customer_ID",
            how="left",
        )
        for group_field, group_type in [
            ("Segment", "Segment"),
            ("KYC_Risk_Band", "KYC risk band"),
            ("Home_Region", "Home region"),
        ]:
            for group_value, group in enriched.groupby(group_field):
                impact_rows.append(
                    {
                        "Strategy": name,
                        "Group_Type": group_type,
                        "Group": group_value,
                        "Transactions": len(group),
                        "Fraud_Rate": group["Fraud_Label"].mean(),
                        "Challenge_Rate": (group["Decision"] == "CHALLENGE").mean(),
                        "Review_Rate": (group["Decision"] == "REVIEW").mean(),
                        "Decline_Rate": (group["Decision"] == "DECLINE").mean(),
                        "False_Declines": int(((group["Decision"] == "DECLINE") & (group["Fraud_Label"] == 0)).sum()),
                    }
                )
    impact_by_group = pd.DataFrame(impact_rows).round(4)
    typology_rows = []
    capture_fraction = {"APPROVE": 0.0, "CHALLENGE": 0.80, "REVIEW": 0.90, "DECLINE": 1.0}
    for name, decided in strategies:
        fraud_only = decided.loc[decided["Fraud_Label"] == 1].merge(
            truth[["Transaction_ID", "Typology"]], on="Transaction_ID", how="left"
        )
        for typology, group in fraud_only.groupby("Typology"):
            fraud_value = float(group["Amount"].sum())
            captured = sum(
                float(group.loc[group["Decision"] == action, "Amount"].sum()) * fraction
                for action, fraction in capture_fraction.items()
            )
            typology_rows.append(
                {
                    "Strategy": name,
                    "Typology": typology,
                    "Fraud_Transactions": len(group),
                    "Fraud_Value": round(fraud_value, 2),
                    "Fraud_Value_Captured_Pct": round(100 * captured / fraud_value, 2) if fraud_value else 0.0,
                }
            )
    typology_metrics = pd.DataFrame(typology_rows)
    metrics = pd.DataFrame(result_rows)
    metrics["PR_AUC"] = [
        average_precision(test["Fraud_Label"], test["Rule_Risk"]),
        average_precision(test["Fraud_Label"], test["Rule_Risk"]),
        average_precision(test["Fraud_Label"], test["Model_Score"]),
        average_precision(test["Fraud_Label"], test["Hybrid_Score"]),
    ]
    metrics["PR_AUC"] = metrics["PR_AUC"].round(4)

    capacity_rows = []
    economic_rows = []
    stress_economics = {
        "Base assumptions": ECONOMICS,
        "Lower challenge effectiveness": replace(ECONOMICS, challenge_fraud_stop_probability=0.60),
        "Higher challenge effectiveness": replace(ECONOMICS, challenge_fraud_stop_probability=0.95),
        "Lower false-decline attrition": replace(ECONOMICS, false_decline_probability_of_attrition=0.01),
        "Higher false-decline attrition": replace(ECONOMICS, false_decline_probability_of_attrition=0.10),
        "Lower review recovery": replace(ECONOMICS, review_fraud_recovery_probability=0.70),
    }
    scenario_surface_rows = []
    for capacity in [1, 5, 15, 25, 50]:
        for name, column in score_specs:
            scenario = apply_policy(test, column, selected_thresholds[name], capacity)
            row = evaluate_policy(scenario, name)
            row["Review_Capacity_Per_Day"] = capacity
            capacity_rows.append(row)
    for scenario_name, assumptions in stress_economics.items():
        for name, frame in strategies:
            row = evaluate_policy(frame, name, assumptions)
            row["Economic_Scenario"] = scenario_name
            economic_rows.append(row)
    for capacity in [1, 5, 15, 25, 50]:
        for economic_name, assumptions in stress_economics.items():
            for name, score_column in score_specs:
                scenario = apply_policy(test, score_column, selected_thresholds[name], capacity)
                row = evaluate_policy(scenario, name, assumptions)
                row["Review_Capacity_Per_Day"] = capacity
                row["Economic_Scenario"] = economic_name
                scenario_surface_rows.append(row)
            row = evaluate_policy(incumbent, "Incumbent", assumptions)
            row["Review_Capacity_Per_Day"] = capacity
            row["Economic_Scenario"] = economic_name
            scenario_surface_rows.append(row)
    capacity_sensitivity = pd.DataFrame(capacity_rows)
    economic_sensitivity = pd.DataFrame(economic_rows)
    scenario_surface = pd.DataFrame(scenario_surface_rows)

    print("[6/7] Saving CSV, SQLite, monitoring, and reporting artifacts...")
    decisions = pd.concat(output_decisions, ignore_index=True)
    monitoring = daily_monitoring(features, scored)
    observable_features = scored.drop(columns=["Fraud_Label"], errors="ignore")
    public_tables = {
        "customers": customers,
        "accounts": accounts,
        "merchants": merchants,
        "terminals": terminals,
        "transactions": transactions,
        "behavior_features": observable_features,
        "test_decisions": decisions,
        "strategy_metrics": metrics,
        "capacity_sensitivity": capacity_sensitivity,
        "economic_sensitivity": economic_sensitivity,
        "scenario_surface": scenario_surface,
        "daily_monitoring": monitoring,
        "terminal_network_summary": terminal_network_summary(transactions),
        "impact_by_customer_group": impact_by_group,
        "typology_metrics": typology_metrics,
        "model_coefficients": model.coefficients(),
        "action_counts": pd.concat(
            [action_counts(frame).assign(Strategy=name) for name, frame in strategies], ignore_index=True
        ),
    }
    database_path = save_run(args.output_dir, public_tables)
    truth_path = args.output_dir / "restricted" / "fraud_ground_truth.csv"
    truth_path.parent.mkdir(parents=True, exist_ok=True)
    truth.to_csv(truth_path, index=False)

    report_dir = PROJECT_ROOT / "reports"
    write_case_study(
        report_dir / "case_study.md",
        metrics,
        split_date.date().isoformat(),
        len(transactions),
        capacity_sensitivity,
        economic_sensitivity,
        impact_by_group,
        typology_metrics,
    )
    write_dashboard(report_dir / "dashboard.html", metrics, monitoring, scenario_surface)
    print("[7/7] Complete.")
    print(metrics[["Strategy", "Fraud_Value_Captured_Pct", "False_Declines", "Review_Overflow_Count", "PR_AUC", "Net_Economic_Cost"]].to_string(index=False))
    print(f"SQLite database: {database_path}")
    print(f"Held-out start: {split_date.date()} | Train: {len(train):,} | Test: {len(test):,}")
    print("Hidden labels were excluded from public transaction, feature, database, and decision tables.")


if __name__ == "__main__":
    main()
