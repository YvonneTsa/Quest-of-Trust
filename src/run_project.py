"""Run TrustHold from synthetic data generation through strategy comparison."""

import argparse
from dataclasses import replace
from pathlib import Path

import numpy as np
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
from src.reporting import update_project_site, write_case_study, write_dashboard
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
        default=30,
        help="Number of deterministic simulation seeds used for robustness summaries.",
    )
    parser.add_argument(
        "--reuse-stability-cache",
        action="store_true",
        help="Reuse seed_stability_by_run.csv when its seed range matches this run.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def choose_thresholds(validation, score_column, capacity):
    """Choose a decision policy on independent validation rows, never fit rows."""
    results = []
    for thresholds in THRESHOLD_CANDIDATES:
        decisions = apply_policy(validation, score_column, thresholds, capacity)
        results.append((evaluate_policy(decisions, "candidate")["Net_Economic_Cost"], thresholds))
    return min(results, key=lambda item: item[0])[1]


def split_validation_rows(training_window, validation_campaign_ids, excluded_campaign_ids, seed):
    """Build disjoint fit and calibration rows using campaign-held fraud labels.

    Fraud transactions from validation campaigns are held out as groups. A
    reproducible 20% sample of legitimate transactions is also reserved for
    calibration, so the validation set contains both outcomes without reusing
    any row used to fit the model.
    """
    eligible = training_window.loc[
        ~training_window["Campaign_ID"].isin(excluded_campaign_ids)
    ].copy()
    validation_fraud = eligible.loc[
        (eligible["Fraud_Label"] == 1)
        & eligible["Campaign_ID"].isin(validation_campaign_ids)
    ]
    legitimate = eligible.loc[eligible["Fraud_Label"] == 0]
    validation_legitimate = legitimate.sample(frac=0.20, random_state=seed)
    validation = pd.concat([validation_fraud, validation_legitimate], ignore_index=False)
    fit = eligible.drop(index=validation.index).copy()
    if validation["Fraud_Label"].sum() == 0 or fit["Fraud_Label"].sum() == 0:
        raise SystemExit(
            "The campaign-stratified fit/validation split needs planted fraud in both samples. "
            "Increase --fraud-campaigns or review the campaign partition."
        )
    return fit, validation


def campaign_numbers_for_split(truth):
    """Create reproducible validation and campaign-holdout groups per typology."""
    numbers = sorted(int(value) for value in truth["Campaign_Number"].dropna().unique())
    campaign_holdout_numbers = set(numbers[1::2])
    campaign_pool_numbers = [value for value in numbers if value not in campaign_holdout_numbers]
    campaign_validation_numbers = set(campaign_pool_numbers[1::2])
    return campaign_holdout_numbers, campaign_validation_numbers


def campaign_ids_for_numbers(truth, numbers):
    """Return campaign IDs whose within-typology number is in ``numbers``."""
    return set(
        truth.loc[truth["Campaign_Number"].isin(numbers), "Campaign_ID"].astype(str)
    )


def prepare_seed(seed, args, progress=False, keep_data=False):
    """Run temporal and unseen-campaign evaluations for one reproducible seed."""
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
    campaign_lookup = truth.set_index("Transaction_ID")["Campaign_ID"]
    labeled["Campaign_ID"] = labeled["Transaction_ID"].map(campaign_lookup)
    campaign_number_lookup = truth.set_index("Transaction_ID")["Campaign_Number"]
    labeled["Campaign_Number"] = labeled["Transaction_ID"].map(campaign_number_lookup)
    dates = sorted(pd.to_datetime(labeled["Timestamp"]).dt.normalize().unique())
    split_index = max(1, min(len(dates) - 1, int(len(dates) * 0.70)))
    split_date = pd.Timestamp(dates[split_index])
    training_window = labeled.loc[pd.to_datetime(labeled["Timestamp"]) < split_date].copy()
    test = labeled.loc[pd.to_datetime(labeled["Timestamp"]) >= split_date].copy()
    if training_window["Fraud_Label"].sum() == 0 or test["Fraud_Label"].sum() == 0:
        raise SystemExit(
            "The temporal split needs fraud examples in both periods. Increase --days or change the documented crisis timing."
        )

    # Fit, validation, and campaign-holdout groups are disjoint. The primary
    # test is the later-date period; its campaign-only subset provides a second
    # view of fraud identities absent from both fitting and threshold tuning.
    campaign_holdout_numbers, campaign_validation_numbers = campaign_numbers_for_split(truth)
    campaign_holdout_ids = campaign_ids_for_numbers(truth, campaign_holdout_numbers)
    campaign_validation_ids = campaign_ids_for_numbers(truth, campaign_validation_numbers)
    model_fit, validation = split_validation_rows(
        training_window, campaign_validation_ids, campaign_holdout_ids, seed
    )

    if progress:
        print("[4/7] Fitting one model on its campaign-fit sample...")
    model = LogisticBaseline().fit(model_fit)
    scored["Model_Score"] = model.predict_proba(scored)
    scored["Hybrid_Score"] = scored[["Rule_Risk", "Model_Score"]].max(axis=1)
    labeled["Model_Score"] = model.predict_proba(labeled)
    labeled["Hybrid_Score"] = labeled[["Rule_Risk", "Model_Score"]].max(axis=1)
    validation = labeled.loc[validation.index].copy()
    model_fit = labeled.loc[model_fit.index].copy()
    test = labeled.loc[pd.to_datetime(labeled["Timestamp"]) >= split_date].copy()

    if progress:
        print("[5/7] Selecting thresholds on validation rows, then scoring the later-date holdout...")
    score_specs = [
        ("Rules", "Rule_Risk"),
        ("Logistic", "Model_Score"),
        ("Rules + logistic", "Hybrid_Score"),
    ]
    selected_thresholds = {
        name: choose_thresholds(validation, column, args.review_capacity)
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

    # Restrict the nested campaign-generalization result to later-period fraud
    # whose campaign identities were held out from fitting and validation.
    campaign_test = test.loc[
        (test["Fraud_Label"] == 0)
        | test["Campaign_ID"].isin(campaign_holdout_ids)
    ].copy()
    if campaign_test["Fraud_Label"].sum() == 0:
        raise SystemExit("The unseen-campaign holdout contains no planted fraud events.")
    campaign_strategies = [("Incumbent", campaign_test.assign(
        Decision=campaign_test["Incumbent_Decision"], Capacity_Overflow=0
    ))]
    for name, score_column in score_specs:
        decided = apply_policy(
            campaign_test, score_column, selected_thresholds[name], args.review_capacity
        )
        campaign_strategies.append((name, decided))
    campaign_metrics = pd.DataFrame(
        [evaluate_policy(decided, name) for name, decided in campaign_strategies]
    )
    campaign_score_by_strategy = dict(score_specs)
    campaign_metrics["PR_AUC"] = [
        (
            average_precision(
                campaign_test["Fraud_Label"],
                campaign_test[campaign_score_by_strategy[name]],
            )
            if name in campaign_score_by_strategy
            else None
        )
        for name in campaign_metrics["Strategy"]
    ]
    campaign_metrics["PR_AUC"] = campaign_metrics["PR_AUC"].round(4)
    campaign_metrics.insert(0, "Seed", seed)

    result = {"seed": seed, "metrics": metrics, "campaign_metrics": campaign_metrics}
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
                "train_count": len(model_fit),
                "temporal_fit_fraud_count": int(model_fit["Fraud_Label"].sum()),
                "validation_count": len(validation),
                "validation_fraud_count": int(validation["Fraud_Label"].sum()),
                "temporal_fit_campaign_count": int(
                    truth.loc[
                        ~truth["Campaign_ID"].isin(campaign_holdout_ids | campaign_validation_ids),
                        "Campaign_ID",
                    ].nunique()
                ),
                "temporal_validation_campaign_count": len(campaign_validation_ids),
                "test": test,
                "model": model,
                "campaign_metrics": campaign_metrics,
                "campaign_test": campaign_test,
                "campaign_strategies": campaign_strategies,
                "campaign_fit_count": len(model_fit),
                "campaign_fit_fraud_count": int(model_fit["Fraud_Label"].sum()),
                "campaign_validation_count": len(validation),
                "campaign_validation_fraud_count": int(validation["Fraud_Label"].sum()),
                "campaign_holdout_count": len(campaign_test),
                "campaign_holdout_fraud_count": int(campaign_test["Fraud_Label"].sum()),
                "campaign_fit_campaign_count": int(
                    truth.loc[
                        ~truth["Campaign_ID"].isin(campaign_holdout_ids | campaign_validation_ids),
                        "Campaign_ID",
                    ].nunique()
                ),
                "campaign_validation_campaign_count": len(campaign_validation_ids),
                "campaign_holdout_campaign_count": len(campaign_holdout_ids),
                "campaign_thresholds": selected_thresholds,
                "campaign_score_specs": score_specs,
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


def campaign_seed_metric_rows(seed_run):
    """Return paired Rules/Logistic results for the campaign holdout."""
    rows = seed_run["campaign_metrics"].loc[
        seed_run["campaign_metrics"]["Strategy"].isin(["Rules", "Logistic"])
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


def business_sensitivity(test, score_specs, selected_thresholds, strategies, capacity):
    """Vary fictional economics and review capacity to expose rank break-evens."""
    sweeps = {
        "Challenge success rate": (
            "challenge_fraud_stop_probability",
            np.linspace(0.0, 1.0, 21),
            "probability",
        ),
        "Review recovery rate": (
            "review_fraud_recovery_probability",
            np.linspace(0.0, 1.0, 21),
            "probability",
        ),
        "False-decline attrition probability": (
            "false_decline_probability_of_attrition",
            np.linspace(0.0, 0.25, 21),
            "probability",
        ),
        "Manual review cost": ("review_cost", np.linspace(0.0, 150.0, 31), "USD per case"),
        "Chargeback fee": ("chargeback_fee", np.linspace(0.0, 200.0, 21), "USD per event"),
        "Legitimate-payment margin": (
            "interchange_margin_rate",
            np.linspace(0.0, 0.02, 21),
            "rate",
        ),
    }
    rows = []
    strategy_frames = {name: frame for name, frame in strategies}
    for label, (field, values, unit) in sweeps.items():
        for value in values:
            economics = replace(ECONOMICS, **{field: float(value)})
            paired_costs = {}
            for name in ["Rules", "Logistic"]:
                paired_costs[name] = evaluate_policy(
                    strategy_frames[name], name, economics
                )["Net_Economic_Cost"]
            delta = paired_costs["Logistic"] - paired_costs["Rules"]
            for name, cost in paired_costs.items():
                rows.append(
                    {
                        "Parameter": label,
                        "Parameter_Field": field,
                        "Unit": unit,
                        "Value": round(float(value), 6),
                        "Strategy": name,
                        "Net_Economic_Cost": cost,
                        "Cost_Delta_Logistic_Minus_Rules": round(float(delta), 2),
                        "Preferred_Strategy": "Logistic" if delta < 0 else "Rules",
                        "Basis": "Fixed base-seed decisions; fictional economics varied",
                    }
                )

    capacity_levels = sorted(
        {max(1, int(capacity * factor)) for factor in [0.04, 0.20, 0.60, 1.0, 2.0]}
    )
    for review_capacity in capacity_levels:
        paired_costs = {}
        for name, column in score_specs:
            if name in {"Rules", "Logistic"}:
                decisions = apply_policy(
                    test, column, selected_thresholds[name], review_capacity
                )
                paired_costs[name] = evaluate_policy(decisions, name)["Net_Economic_Cost"]
        delta = paired_costs["Logistic"] - paired_costs["Rules"]
        for name, cost in paired_costs.items():
            rows.append(
                {
                    "Parameter": "Review capacity per day",
                    "Parameter_Field": "review_capacity_per_day",
                    "Unit": "cases per day",
                    "Value": review_capacity,
                    "Strategy": name,
                    "Net_Economic_Cost": cost,
                    "Cost_Delta_Logistic_Minus_Rules": round(float(delta), 2),
                    "Preferred_Strategy": "Logistic" if delta < 0 else "Rules",
                    "Basis": "Fixed thresholds; decisions recalculated at each capacity",
                }
            )
    sensitivity = pd.DataFrame(rows)

    summary_rows = []
    for label, group in sensitivity.groupby("Parameter", sort=False):
        pairs = group.drop_duplicates("Value").sort_values("Value")
        deltas = pairs["Cost_Delta_Logistic_Minus_Rules"].to_numpy(dtype=float)
        values = pairs["Value"].to_numpy(dtype=float)
        crossing = None
        for index in range(1, len(deltas)):
            if deltas[index - 1] == 0:
                crossing = values[index - 1]
                break
            if deltas[index - 1] * deltas[index] < 0:
                fraction = -deltas[index - 1] / (deltas[index] - deltas[index - 1])
                crossing = values[index - 1] + fraction * (values[index] - values[index - 1])
                break
        first, last = pairs.iloc[0], pairs.iloc[-1]
        base_values = {
            field: float(getattr(ECONOMICS, field))
            for field in [
                "challenge_fraud_stop_probability",
                "review_fraud_recovery_probability",
                "false_decline_probability_of_attrition",
                "review_cost",
                "chargeback_fee",
                "interchange_margin_rate",
            ]
        }
        base_value = (
            float(capacity)
            if label == "Review capacity per day"
            else base_values[str(first["Parameter_Field"])]
        )
        summary_rows.append(
            {
                "Parameter": label,
                "Unit": first["Unit"],
                "Tested_Min": float(values.min()),
                "Tested_Max": float(values.max()),
                "Base_Value": base_value,
                "Break_Even_Value": round(float(crossing), 4) if crossing is not None else None,
                "Ranking_Changes_In_Tested_Range": crossing is not None,
                "Preferred_At_Min": "Logistic" if float(first["Cost_Delta_Logistic_Minus_Rules"]) < 0 else "Rules",
                "Preferred_At_Max": "Logistic" if float(last["Cost_Delta_Logistic_Minus_Rules"]) < 0 else "Rules",
                "Cost_Delta_At_Min": float(first["Cost_Delta_Logistic_Minus_Rules"]),
                "Cost_Delta_At_Max": float(last["Cost_Delta_Logistic_Minus_Rules"]),
                "Interpretation": (
                    "Approximate modeled crossover under fixed base-seed decisions."
                    if crossing is not None
                    else "No strategy-rank crossover was observed in the tested fictional range."
                ),
            }
        )
    return sensitivity, pd.DataFrame(summary_rows)


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
    if args.fraud_campaigns < 5:
        raise SystemExit("At least five campaigns per typology are required for fit, validation, and campaign holdout partitions.")

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
    campaign_test = baseline["campaign_test"]
    campaign_strategies = baseline["campaign_strategies"]
    campaign_metrics = baseline["campaign_metrics"]
    incumbent = strategies[0][1]
    metrics = baseline["metrics"]

    print(f"[6/7] Calculating results across {args.stability_runs} synthetic seeds...")
    cached_stability_path = args.output_dir / "seed_stability_by_run.csv"
    if args.reuse_stability_cache:
        if not cached_stability_path.exists():
            raise SystemExit(f"Cannot reuse seed results: {cached_stability_path} was not found.")
        stability_by_seed = pd.read_csv(cached_stability_path)
        expected_seeds = list(range(args.seed, args.seed + args.stability_runs))
        actual_seeds = sorted(int(seed) for seed in stability_by_seed["Seed"].unique())
        if actual_seeds != expected_seeds:
            raise SystemExit(
                "Cannot reuse seed results: the cached seed range does not match "
                f"{expected_seeds[0]}–{expected_seeds[-1]}."
            )
        print("       Reused matching temporal-holdout seed results from the output directory.")
    else:
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
    # Keep the campaign-identity check focused on the full default-seed case.
    # The repeated-seed headline is the later-date holdout above.
    campaign_stability_by_seed = campaign_seed_metric_rows(baseline)
    campaign_stability_summary = summarize_seed_stability(campaign_stability_by_seed)
    campaign_stability_comparison = compare_seed_strategies(campaign_stability_by_seed)

    evaluation_design = pd.DataFrame(
        [
            {
                "Evaluation": "Later-date holdout",
                "Seed": args.seed,
                "Training_Rows": baseline["train_count"],
                "Validation_Rows": baseline["validation_count"],
                "Holdout_Rows": len(test),
                "Training_Fraud_Events": baseline["temporal_fit_fraud_count"],
                "Validation_Fraud_Events": baseline["validation_fraud_count"],
                "Holdout_Fraud_Events": int(test["Fraud_Label"].sum()),
                "Fit_Campaigns": baseline["temporal_fit_campaign_count"],
                "Validation_Campaigns": baseline["temporal_validation_campaign_count"],
                "Holdout_Campaigns": int(truth["Campaign_ID"].nunique()),
                "Holdout_Start": split_date.date().isoformat(),
            },
            {
                "Evaluation": "Unseen-campaign holdout",
                "Seed": args.seed,
                "Training_Rows": baseline["campaign_fit_count"],
                "Validation_Rows": baseline["campaign_validation_count"],
                "Holdout_Rows": baseline["campaign_holdout_count"],
                "Training_Fraud_Events": baseline["campaign_fit_fraud_count"],
                "Validation_Fraud_Events": baseline["campaign_validation_fraud_count"],
                "Holdout_Fraud_Events": baseline["campaign_holdout_fraud_count"],
                "Fit_Campaigns": baseline["campaign_fit_campaign_count"],
                "Validation_Campaigns": baseline["campaign_validation_campaign_count"],
                "Holdout_Campaigns": baseline["campaign_holdout_campaign_count"],
                "Holdout_Start": split_date.date().isoformat(),
            },
        ]
    )

    output_decisions = []
    for name, decided in strategies:
        safe = decided[["Transaction_ID", "Timestamp", "Customer_ID", "Terminal_ID", "Amount", "Decision", "Capacity_Overflow"]].copy()
        safe["Strategy"] = name
        output_decisions.append(safe)
    campaign_decision_frames = []
    for name, decided in campaign_strategies:
        safe = decided[[
            "Transaction_ID", "Timestamp", "Customer_ID", "Terminal_ID", "Amount",
            "Decision", "Capacity_Overflow",
        ]].copy()
        safe["Strategy"] = name
        campaign_decision_frames.append(safe)
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
    business_sensitivity_table, business_break_even_summary = business_sensitivity(
        test, score_specs, selected_thresholds, strategies, args.review_capacity
    )

    print("[7/7] Saving CSV, SQLite, monitoring, and reporting artifacts...")
    decisions = pd.concat(output_decisions, ignore_index=True)
    campaign_decisions = pd.concat(campaign_decision_frames, ignore_index=True)
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
        "campaign_holdout_metrics": campaign_metrics,
        "campaign_holdout_decisions": campaign_decisions,
        "campaign_stability_by_run": campaign_stability_by_seed,
        "campaign_stability_summary": campaign_stability_summary,
        "campaign_stability_comparison": campaign_stability_comparison,
        "evaluation_design": evaluation_design,
        "capacity_sensitivity": capacity_sensitivity,
        "economic_sensitivity": economic_sensitivity,
        "business_sensitivity": business_sensitivity_table,
        "business_break_even_summary": business_break_even_summary,
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
        campaign_metrics,
        campaign_stability_by_seed,
        campaign_stability_summary,
        campaign_stability_comparison,
        evaluation_design,
        business_sensitivity_table,
        business_break_even_summary,
    )
    write_case_study(
        PROJECT_ROOT / "docs" / "portfolio_case_study.md",
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
        campaign_metrics,
        campaign_stability_by_seed,
        campaign_stability_summary,
        campaign_stability_comparison,
        evaluation_design,
        business_sensitivity_table,
        business_break_even_summary,
    )
    write_dashboard(
        report_dir / "dashboard.html",
        metrics,
        monitoring,
        scenario_surface,
        stability_summary,
        stability_comparison,
        campaign_stability_summary,
        campaign_stability_comparison,
        business_sensitivity_table,
        business_break_even_summary,
    )
    write_dashboard(
        PROJECT_ROOT / "docs" / "dashboard.html",
        metrics,
        monitoring,
        scenario_surface,
        stability_summary,
        stability_comparison,
        campaign_stability_summary,
        campaign_stability_comparison,
        business_sensitivity_table,
        business_break_even_summary,
    )
    update_project_site(
        PROJECT_ROOT / "docs" / "index.html",
        len(transactions),
        metrics,
        stability_summary,
        stability_comparison,
    )
    print("[complete] Artifacts saved.")
    print(metrics[["Strategy", "Fraud_Value_Captured_Pct", "False_Declines", "Review_Overflow_Count", "PR_AUC", "Net_Economic_Cost"]].to_string(index=False))
    print(f"SQLite database: {database_path}")
    print(f"Held-out start: {split_date.date()} | Train: {train_count:,} | Test: {len(test):,}")
    print(f"Temporal holdout: Logistic lower modeled cost in {int(stability_comparison.iloc[0]['Logistic_Lower_Cost_Wins'])}/{args.stability_runs} seeds.")
    print(
        "Default-seed unseen-campaign check: Logistic lower modeled cost in "
        f"{int(campaign_stability_comparison.iloc[0]['Logistic_Lower_Cost_Wins'])}/"
        f"{int(campaign_stability_comparison.iloc[0]['Seeds'])} comparison."
    )
    print("Hidden labels were excluded from public transaction, feature, database, and decision tables.")


if __name__ == "__main__":
    main()

