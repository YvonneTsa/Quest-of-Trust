"""Run TrustHold from synthetic data generation through strategy comparison."""

import argparse
from dataclasses import replace
from pathlib import Path

import pandas as pd

from src.config import (
    DEFAULT_OUTPUT_DIR,
    ECONOMICS,
    FRAUD_CAMPAIGNS_PER_TYPOLOGY,
    N_CUSTOMERS,
    N_MERCHANTS,
    N_TERMINALS,
    PROJECT_ROOT,
    REVIEW_CAPACITY_PER_DAY,
    SEED,
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
    parser.add_argument("--review-capacity", type=int, default=REVIEW_CAPACITY_PER_DAY)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--fraud-campaigns", type=int, default=FRAUD_CAMPAIGNS_PER_TYPOLOGY)
    parser.add_argument(
        "--stability-runs",
        type=int,
        default=10,
        help="Number of consecutive deterministic seeds used for the robustness summary.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def choose_thresholds(train, score_column, capacity):
    results = []
    for thresholds in THRESHOLD_CANDIDATES:
        decisions = apply_policy(train, score_column, thresholds, capacity)
        results.append((evaluate_policy(decisions, "candidate")["Net_Economic_Cost"], thresholds))
    return min(results, key=lambda item: item[0])[1]


def prepare_seed(seed, args, progress=False, keep_data=False):
    """Run the shared train/holdout pipeline once for a reproducible seed."""
    if progress:
        print("[1/7] Generating customers, accounts, merchants, terminals, and legitimate activity...")
    customers, accounts, merchants, terminals = generate_entities(
        args.customers, args.merchants, args.terminals, seed=seed
    )
    legitimate = generate_legitimate_transactions(
        customers, accounts, merchants, terminals, args.days, seed=seed
    )
    if progress:
        print(f"       Baseline events: {len(legitimate):,}")

    if progress:
        print("[2/7] Injecting documented fraud scenarios; truth stays in a separate file...")
    transactions, truth = inject_fraud(
        legitimate,
        customers,
        terminals,
        args.days,
        seed=seed,
        campaigns_per_typology=args.fraud_campaigns,
    )
    if progress:
        print(
            f"       Injected fraud events: {len(truth):,} across "
            f"{truth['Typology'].nunique()} typologies"
        )

    if progress:
        print("[3/7] Building point-in-time behavior features...")
    features = build_features(transactions, customers)
    scored = score_rules(features)
    scored["Rule_Risk"] = scored["Rule_Score"] / 100.0

    # Labels join after point-in-time feature construction and remain outside
    # the public feature and monitoring artifacts.
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

    if progress:
        print("[4/7] Fitting the temporal logistic-regression baseline...")
    model = LogisticBaseline().fit(train)
    scored["Model_Score"] = model.predict_proba(scored)
    scored["Hybrid_Score"] = scored[["Rule_Risk", "Model_Score"]].max(axis=1)
    labeled["Model_Score"] = model.predict_proba(labeled)
    labeled["Hybrid_Score"] = labeled[["Rule_Risk", "Model_Score"]].max(axis=1)
    train = labeled.loc[pd.to_datetime(labeled["Timestamp"]) < split_date].copy()
    test = labeled.loc[pd.to_datetime(labeled["Timestamp"]) >= split_date].copy()

    if progress:
        print("[5/7] Selecting thresholds on training history and evaluating the future holdout...")
    score_specs = [
        ("Rules", "Rule_Risk"),
        ("Logistic", "Model_Score"),
        ("Rules + logistic", "Hybrid_Score"),
    ]
    selected_thresholds = {
        name: choose_thresholds(train, column, args.review_capacity)
        for name, column in score_specs
    }
    incumbent = test.copy()
    incumbent["Decision"] = incumbent["Incumbent_Decision"]
    incumbent["Capacity_Overflow"] = 0
    strategies = [("Incumbent", incumbent)]
    for name, score_column in score_specs:
        decided = apply_policy(test, score_column, selected_thresholds[name], args.review_capacity)
        strategies.append((name, decided))

    metrics = pd.DataFrame(
        [evaluate_policy(decided, name) for name, decided in strategies]
    )
    score_column_by_strategy = dict(score_specs)
    metrics["PR_AUC"] = [
        (
            average_precision(test["Fraud_Label"], test[score_column_by_strategy[name]])
            if name in score_column_by_strategy
            else None
        )
        for name in metrics["Strategy"]
    ]
    metrics["PR_AUC"] = metrics["PR_AUC"].round(4)
    metrics.insert(0, "Seed", seed)

    result = {"seed": seed, "metrics": metrics}
    if keep_data:
        result.update(
            {
                "customers": customers,
                "accounts": accounts,
                "merchants": merchants,
                "terminals": terminals,
                "transactions": transactions,
                "truth": truth,
                "features": features,
                "scored": scored,
                "labeled": labeled,
                "train_count": len(train),
                "test": test,
                "model": model,
                "split_date": split_date,
                "score_specs": score_specs,
                "selected_thresholds": selected_thresholds,
                "strategies": strategies,
            }
        )
    return result


def seed_metric_rows(seed_run):
    """Return the rule and logistic rows used in the multi-seed comparison."""
    rows = seed_run["metrics"].loc[
        seed_run["metrics"]["Strategy"].isin(["Rules", "Logistic"])
    ].copy()
    if "Seed" not in rows.columns:
        rows.insert(0, "Seed", seed_run["seed"])
    return rows


def summarize_seed_stability(per_seed):
    """Summarize observed run-to-run ranges; these are not confidence intervals."""
    rows = []
    summary_fields = {
        "Transactions": ("Holdout_Events", ["mean", "min", "max"]),
        "Fraud_Transactions": ("Holdout_Fraud_Events", ["mean", "min", "max"]),
        "Fraud_Value_Captured_Pct": ("Fraud_Value_Captured_Pct", ["mean", "median", "min", "max"]),
        "Net_Economic_Cost": ("Net_Economic_Cost", ["mean", "median", "min", "max"]),
        "False_Declines": ("False_Declines", ["mean", "median", "min", "max"]),
        "Legitimate_Challenge_Count": ("Legitimate_Challenges", ["mean", "median", "min", "max"]),
        "Legitimate_Review_Count": ("Legitimate_Reviews", ["mean", "median", "min", "max"]),
        "Review_Overflow_Count": ("Cases_Over_Daily_Review_Limit", ["mean", "median", "min", "max"]),
    }
    for strategy, group in per_seed.groupby("Strategy", sort=False):
        row = {"Strategy": strategy, "Seeds": int(group["Seed"].nunique())}
        for field, (prefix, methods) in summary_fields.items():
            values = group[field]
            for method in methods:
                row[f"{prefix}_{method.title()}"] = round(float(getattr(values, method)()), 2)
        rows.append(row)
    return pd.DataFrame(rows)


def compare_seed_strategies(per_seed):
    """Calculate paired Logistic-versus-Rules outcomes on the same seeds."""
    wide = per_seed.pivot(index="Seed", columns="Strategy")
    net_delta = wide["Net_Economic_Cost"]["Logistic"] - wide["Net_Economic_Cost"]["Rules"]
    capture_delta = (
        wide["Fraud_Value_Captured_Pct"]["Logistic"]
        - wide["Fraud_Value_Captured_Pct"]["Rules"]
    )
    challenge_delta = (
        wide["Legitimate_Challenge_Count"]["Logistic"]
        - wide["Legitimate_Challenge_Count"]["Rules"]
    )
    review_delta = (
        wide["Legitimate_Review_Count"]["Logistic"]
        - wide["Legitimate_Review_Count"]["Rules"]
    )
    false_decline_delta = (
        wide["False_Declines"]["Logistic"] - wide["False_Declines"]["Rules"]
    )
    return pd.DataFrame(
        [
            {
                "Seeds": int(len(wide)),
                "Logistic_Lower_Cost_Wins": int((net_delta < 0).sum()),
                "Logistic_Lower_Cost_Win_Rate_Pct": round(100 * float((net_delta < 0).mean()), 1),
                "Net_Cost_Delta_Logistic_Minus_Rules_Median": round(float(net_delta.median()), 2),
                "Net_Cost_Delta_Logistic_Minus_Rules_Min": round(float(net_delta.min()), 2),
                "Net_Cost_Delta_Logistic_Minus_Rules_Max": round(float(net_delta.max()), 2),
                "Fraud_Capture_Delta_Pct_Points_Median": round(float(capture_delta.median()), 2),
                "Fraud_Capture_Delta_Pct_Points_Min": round(float(capture_delta.min()), 2),
                "Fraud_Capture_Delta_Pct_Points_Max": round(float(capture_delta.max()), 2),
                "Legitimate_Challenge_Delta_Median": round(float(challenge_delta.median()), 2),
                "Legitimate_Challenge_Delta_Min": int(challenge_delta.min()),
                "Legitimate_Challenge_Delta_Max": int(challenge_delta.max()),
                "Legitimate_Review_Delta_Median": round(float(review_delta.median()), 2),
                "Legitimate_Review_Delta_Min": int(review_delta.min()),
                "Legitimate_Review_Delta_Max": int(review_delta.max()),
                "False_Decline_Delta_Median": round(float(false_decline_delta.median()), 2),
                "False_Decline_Delta_Min": int(false_decline_delta.min()),
                "False_Decline_Delta_Max": int(false_decline_delta.max()),
            }
        ]
    )


def main():
    args = parse_args()
    if min(
        args.customers,
        args.days,
        args.merchants,
        args.terminals,
        args.review_capacity,
        args.fraud_campaigns,
    ) < 1 or args.stability_runs < 1:
        raise SystemExit("Counts, capacities, campaigns, and stability runs must be positive integers.")

    baseline = prepare_seed(args.seed, args, progress=True, keep_data=True)
    customers = baseline["customers"]
    accounts = baseline["accounts"]
    merchants = baseline["merchants"]
    terminals = baseline["terminals"]
    transactions = baseline["transactions"]
    truth = baseline["truth"]
    features = baseline["features"]
    scored = baseline["scored"]
    train_count = baseline["train_count"]
    test = baseline["test"]
    model = baseline["model"]
    split_date = baseline["split_date"]
    score_specs = baseline["score_specs"]
    selected_thresholds = baseline["selected_thresholds"]
    strategies = baseline["strategies"]
    incumbent = strategies[0][1]
    metrics = baseline["metrics"]

    print(f"[6/7] Calculating results across {args.stability_runs} synthetic seeds...")
    stability_parts = [seed_metric_rows(baseline)]
    for offset in range(1, args.stability_runs):
        seed = args.seed + offset
        print(f"       Seed {offset + 1}/{args.stability_runs}: {seed}")
        seed_run = prepare_seed(seed, args)
        stability_parts.append(seed_metric_rows(seed_run))
        del seed_run
    stability_by_seed = pd.concat(stability_parts, ignore_index=True)
    stability_summary = summarize_seed_stability(stability_by_seed)
    stability_comparison = compare_seed_strategies(stability_by_seed)

    output_decisions = []
    for name, decided in strategies:
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
    capacity_levels = sorted({max(1, int(args.review_capacity * factor)) for factor in [0.04, 0.20, 0.60, 1.0, 2.0]})
    for capacity in capacity_levels:
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
    for capacity in capacity_levels:
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

    print("[7/7] Saving CSV, SQLite, monitoring, and reporting artifacts...")
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
        "seed_stability_by_run": stability_by_seed,
        "seed_stability_summary": stability_summary,
        "seed_stability_comparison": stability_comparison,
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
        stability_by_seed,
        stability_summary,
        stability_comparison,
    )
    write_dashboard(
        report_dir / "dashboard.html",
        metrics,
        monitoring,
        scenario_surface,
        stability_summary,
        stability_comparison,
    )
    write_dashboard(
        PROJECT_ROOT / "docs" / "dashboard.html",
        metrics,
        monitoring,
        scenario_surface,
        stability_summary,
        stability_comparison,
    )
    print("[complete] Artifacts saved.")
    print(metrics[["Strategy", "Fraud_Value_Captured_Pct", "False_Declines", "Review_Overflow_Count", "PR_AUC", "Net_Economic_Cost"]].to_string(index=False))
    print(f"SQLite database: {database_path}")
    print(f"Held-out start: {split_date.date()} | Train: {train_count:,} | Test: {len(test):,}")
    print(f"Robustness: Logistic lower modeled cost in {int(stability_comparison.iloc[0]['Logistic_Lower_Cost_Wins'])}/{args.stability_runs} seeds.")
    print("Hidden labels were excluded from public transaction, feature, database, and decision tables.")


if __name__ == "__main__":
    main()
