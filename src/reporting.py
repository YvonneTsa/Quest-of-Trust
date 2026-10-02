"""Write a factual case-study summary and a lightweight interactive dashboard."""

import json
import re
from pathlib import Path

import pandas as pd
from src.config import REVIEW_CAPACITY_PER_DAY


def write_case_study(
    path: Path,
    metrics: pd.DataFrame,
    split_date: str,
    row_count: int,
    capacity_sensitivity: pd.DataFrame,
    economic_sensitivity: pd.DataFrame,
    impact_by_group: pd.DataFrame,
    typology_metrics: pd.DataFrame,
    stability_by_seed: pd.DataFrame,
    stability_summary: pd.DataFrame,
    stability_comparison: pd.DataFrame,
    campaign_metrics: pd.DataFrame,
    campaign_stability_by_seed: pd.DataFrame,
    campaign_stability_summary: pd.DataFrame,
    campaign_stability_comparison: pd.DataFrame,
    evaluation_design: pd.DataFrame,
    business_sensitivity: pd.DataFrame,
    business_break_even_summary: pd.DataFrame,
):
    ranked = metrics.sort_values("Net_Economic_Cost")
    best = ranked.iloc[0]
    paired = stability_comparison.iloc[0]
    summary = stability_summary.set_index("Strategy")
    logistic = summary.loc["Logistic"]
    rules = summary.loc["Rules"]
    median_delta = paired["Net_Cost_Delta_Logistic_Minus_Rules_Median"]
    delta_min = paired["Net_Cost_Delta_Logistic_Minus_Rules_Min"]
    delta_max = paired["Net_Cost_Delta_Logistic_Minus_Rules_Max"]
    campaign_paired = campaign_stability_comparison.iloc[0]
    campaign_summary = campaign_stability_summary.set_index("Strategy")
    campaign_logistic = campaign_summary.loc["Logistic"]
    campaign_rules = campaign_summary.loc["Rules"]
    campaign_delta = campaign_paired["Net_Cost_Delta_Logistic_Minus_Rules_Median"]
    false_decline_median = paired["False_Decline_Delta_Median"]
    false_decline_min = paired["False_Decline_Delta_Min"]
    false_decline_max = paired["False_Decline_Delta_Max"]
    review_delta = paired["Legitimate_Review_Delta_Median"]
    review_min = paired["Legitimate_Review_Delta_Min"]
    review_max = paired["Legitimate_Review_Delta_Max"]
    fmt_count = lambda value: f"{value:,.1f}".rstrip("0").rstrip(".")
    review_direction = "more" if review_delta > 0 else "fewer"
    review_range = (
        f"{fmt_count(abs(review_min))}–{fmt_count(abs(review_max))}"
        if review_delta > 0
        else f"{fmt_count(abs(review_max))}–{fmt_count(abs(review_min))}"
    )
    fmt_money = lambda value: f"-${abs(value):,.2f}" if value < 0 else f"${value:,.2f}"
    fmt_signed_count = lambda value: f"{value:+,.1f}".rstrip("0").rstrip(".")
    display_metrics = metrics.copy()
    display_metrics["PR_AUC"] = display_metrics["PR_AUC"].map(
        lambda value: "Not applicable" if pd.isna(value) else f"{value:.4f}"
    )
    summary_lines = [
        "| Strategy | Fraud cases in later test period, mean (range) | Fraud value captured, mean (range) | Good payments declined, median (range) | Good payments challenged, median (range) | Good payments reviewed, median (range) | Modeled net cost, mean / median (range) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for strategy in ["Rules", "Logistic"]:
        row = summary.loc[strategy]
        summary_lines.append(
            "| {strategy} | {fraud} ({fmin}-{fmax}) | "
            "{capture:.2f}% ({cmin:.2f}-{cmax:.2f}%) | "
            "{false_declines} ({fd_min}-{fd_max}) | "
            "{challenges} ({ch_min}-{ch_max}) | "
            "{reviews} ({r_min}-{r_max}) | "
                "{cost_mean} mean; {cost} median ({cost_min} to {cost_max}) |".format(
                strategy=strategy,
                fraud=fmt_count(row["Holdout_Fraud_Events_Mean"]),
                fmin=fmt_count(row["Holdout_Fraud_Events_Min"]),
                fmax=fmt_count(row["Holdout_Fraud_Events_Max"]),
                capture=row["Fraud_Value_Captured_Pct_Mean"],
                cmin=row["Fraud_Value_Captured_Pct_Min"],
                cmax=row["Fraud_Value_Captured_Pct_Max"],
                false_declines=fmt_count(row["False_Declines_Median"]),
                fd_min=fmt_count(row["False_Declines_Min"]),
                fd_max=fmt_count(row["False_Declines_Max"]),
                challenges=fmt_count(row["Legitimate_Challenges_Median"]),
                ch_min=fmt_count(row["Legitimate_Challenges_Min"]),
                ch_max=fmt_count(row["Legitimate_Challenges_Max"]),
                reviews=fmt_count(row["Legitimate_Reviews_Median"]),
                r_min=fmt_count(row["Legitimate_Reviews_Min"]),
                r_max=fmt_count(row["Legitimate_Reviews_Max"]),
                cost_mean=fmt_money(row["Net_Economic_Cost_Mean"]),
                cost=fmt_money(row["Net_Economic_Cost_Median"]),
                cost_min=fmt_money(row["Net_Economic_Cost_Min"]),
                cost_max=fmt_money(row["Net_Economic_Cost_Max"]),
            )
        )
    lines = [
        "# TrustHold — The Cost of Fraud: simulation case study",
        "",
        "> All numbers below are outputs of this fictional synthetic simulation, not claims about a real company.",
        "",
        "## Finding first",
        f"Across {int(paired['Seeds'])} deterministic simulation seeds, Logistic had lower modeled net cost than Rules in {int(paired['Logistic_Lower_Cost_Wins'])}/{int(paired['Seeds'])} runs. The median paired difference (Logistic minus Rules) was {fmt_money(median_delta)}, with observed seed-to-seed differences from {fmt_money(delta_min)} to {fmt_money(delta_max)}. These are scenario-conditional simulation results, not real-world savings or formal confidence intervals.",
        "",
        "## Context and decision problem",
        "TrustHold models a digital-payments environment where each event can be approved, challenged, reviewed, or declined. The business objective is to balance fraud loss, customer friction, finite review capacity, and payment margin.",
        "",
        "## Data and method",
        f"The generated world contains {row_count:,} timestamped transactions. A later time period beginning {split_date} is held out for evaluation. Fraud truth is stored separately and is joined only for model training and offline evaluation.",
        f"The default book uses 2,000 customers, 800 merchants, 1,200 terminals, 60 days, and 10 separately sampled attacks per typology across four documented patterns. This yields {int(logistic['Holdout_Fraud_Events_Mean']):,} simulated fraud cases in each later-period holdout. Legitimate event volume, attack count, and review capacity are scaled together so the modeled fraud share and investigator-to-volume ratio stay near the earlier version.",
        "Behavioral features use only information available before each transaction. A transparent rule score and a NumPy logistic-regression baseline are compared with the same four payment actions. A campaign-stratified validation sample is kept out of model fitting and is used to select action thresholds; the later-date holdout remains untouched until evaluation.",
        "",
        "## Results across seeds",
        f"Each of the {int(paired['Seeds'])} runs changes the random draws for customers, legitimate events, terminals, and attack campaigns. The paired comparison keeps the same fictional economics and 250-case daily review capacity. The ranges below are the observed minimum and maximum across those seeds; they summarize simulator variation and are not confidence intervals for real payment populations.",
        *summary_lines,
        "",
        f"Logistic captured a median {paired['Fraud_Capture_Delta_Pct_Points_Median']:+.2f} percentage points of fraud value relative to Rules (range {paired['Fraud_Capture_Delta_Pct_Points_Min']:+.2f} to {paired['Fraud_Capture_Delta_Pct_Points_Max']:+.2f}). It sent a median {fmt_count(abs(paired['Legitimate_Challenge_Delta_Median']))} fewer legitimate events to challenge (range {fmt_count(abs(paired['Legitimate_Challenge_Delta_Max']))} to {fmt_count(abs(paired['Legitimate_Challenge_Delta_Min']))} fewer), while sending a median {fmt_count(abs(review_delta))} {review_direction} legitimate events to investigator review (range {review_range} {review_direction}). Fewer challenges do not mean that every case disappears from the operating queue.",
        f"The false-decline trade-off is also retained: the paired Logistic-minus-Rules median was {fmt_signed_count(false_decline_median)} legitimate declines, with an observed range of {fmt_signed_count(false_decline_min)} to {fmt_signed_count(false_decline_max)}. A positive value means Logistic declined more legitimate payments in that seed.",
        "",
        "## Separate campaign-generalization check",
        f"A nested campaign-identity check on the default seed isolates later-period fraud from half of the numbered synthetic campaigns; those campaign labels were excluded from model fitting and threshold selection. It contains {int(campaign_logistic['Holdout_Fraud_Events_Mean']):,} held-out fraud events. In this single check, Logistic's modeled cost was {fmt_money(campaign_logistic['Net_Economic_Cost_Mean'])}, versus {fmt_money(campaign_rules['Net_Economic_Cost_Mean'])} for Rules. This is a focused one-seed diagnostic, not multi-seed evidence. It tests withheld campaign identities within the same four designed typologies; it does not test unseen fraud mechanisms or real-world generalization.",
        f"Mean fraud-value capture in this check was {campaign_logistic['Fraud_Value_Captured_Pct_Mean']:.2f}% for Logistic and {campaign_rules['Fraud_Value_Captured_Pct_Mean']:.2f}% for Rules. This result is a focused subset of the later-date test, not a statistically independent experiment.",
        "",
        "## Evaluation split audit",
        "Counts below make the fitting, threshold-validation, and final evaluation samples explicit for the default seed.",
        "```text",
        evaluation_design.to_string(index=False),
        "```",
        "",
        "## Held-out strategy comparison",
        f"The table below is the single default seed ({int(metrics['Seed'].iloc[0]) if 'Seed' in metrics.columns else 'configured seed'}), not the multi-seed summary. The fictional cost assumptions are documented in `docs/simulation_assumptions.md`. Lower net economic cost is better under those settings. The lowest cost in this base run is **{best['Strategy']}**, at {fmt_money(best['Net_Economic_Cost'])}.",
        "",
        "```text",
        display_metrics.to_string(index=False),
        "```",
        "Complete temporal-holdout per-seed rows are available in `data/synthetic/run/seed_stability_by_run.csv`; summary and paired-difference tables are also stored in SQLite.",
        "",
        "## Capacity sensitivity",
        "The same score bands were evaluated with different daily review limits. Overflow cases are routed to challenge.",
        "```text",
        capacity_sensitivity[["Strategy", "Review_Capacity_Per_Day", "Fraud_Value_Captured_Pct", "Review_Overflow_Count", "Net_Economic_Cost"]].to_string(index=False),
        "```",
        "",
        "## Economic assumption sensitivity",
        "The action decisions are held fixed while challenge effectiveness, false-decline attrition, and review recovery assumptions change.",
        "```text",
        economic_sensitivity[["Strategy", "Economic_Scenario", "Fraud_Loss_After_Intervention", "False_Declines", "Net_Economic_Cost"]].to_string(index=False),
        "```",
        "",
        "## Business break-even analysis",
        "The next view varies one fictional cost assumption at a time while holding the base-seed decisions fixed. Capacity scenarios recalculate routing with the existing thresholds. A crossover is an approximate modeled point where Logistic and Rules exchange lower net cost; it is not a forecast or a confidence interval.",
        "```text",
        business_break_even_summary.to_string(index=False),
        "```",
        "Detailed one-variable-at-a-time scenario rows are available in `business_sensitivity.csv` and SQLite.",
        "",
        "## Descriptive customer-group impact",
        "The following rates are descriptive diagnostics over synthetic data, not a fairness certification. Small group counts and the intentionally fictional population limit interpretation.",
        "```text",
        impact_by_group.to_string(index=False),
        "```",
        "",
        "## Typology-level fraud value capture",
        "These are offline evaluation summaries using the restricted planted labels after decisions were made.",
        "```text",
        typology_metrics.to_string(index=False),
        "```",
        "",
        "## Limitations and interpretation",
        "More planted events and repeatable seeds reduce run-to-run noise inside this simulator; they do not make synthetic data representative or establish a statistically reliable real-world ranking. Fraud patterns, labels, intervention effects, and unit economics are still designed assumptions. Results do not establish causal impact, expected savings, or production performance. Thresholds, capacity, and assumptions should be validated against real labeled payment data before operational use.",
        "",
        "## Next questions",
        "Vary attack signatures and prevalence, validate the simulator assumptions with fraud operations, and test the workflow on representative labeled payment data before drawing operational conclusions.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_project_site(path: Path, row_count: int, metrics: pd.DataFrame,
                        stability_summary: pd.DataFrame,
                        stability_comparison: pd.DataFrame) -> None:
    """Refresh the portfolio site's headline, scale, and findings from saved results."""
    html = path.read_text(encoding="utf-8")
    summary = stability_summary.set_index("Strategy")
    paired = stability_comparison.iloc[0]
    rules = summary.loc["Rules"]
    logistic = summary.loc["Logistic"]
    seeds = int(paired["Seeds"])
    wins = int(paired["Logistic_Lower_Cost_Wins"])
    holdout_rows = int(metrics.loc[metrics["Strategy"] == "Rules", "Transactions"].iloc[0])

    money = lambda value: f"−${abs(value):,.0f}" if value < 0 else f"${value:,.0f}"
    count = lambda value: f"{value:,.1f}".rstrip("0").rstrip(".")

    def replace_fragment(source: str, name: str, body: str) -> str:
        pattern = rf"(<!-- GENERATED:{name}:START -->).*?(<!-- GENERATED:{name}:END -->)"
        updated, replacements = re.subn(
            pattern,
            lambda match: f"{match.group(1)}{body}{match.group(2)}",
            source,
            count=1,
            flags=re.DOTALL,
        )
        if replacements != 1:
            raise ValueError(f"Expected one GENERATED:{name} region in {path}")
        return updated

    hero = (
        f"<p id=\"hero-finding\">Logistic had lower modeled cost in {wins}/{seeds} synthetic runs. "
        f"Its average fraud-value capture was {logistic['Fraud_Value_Captured_Pct_Mean']:.2f}%, "
        f"while the capture lift ranged from {paired['Fraud_Capture_Delta_Pct_Points_Min']:+.2f} "
        f"to {paired['Fraud_Capture_Delta_Pct_Points_Max']:+.2f} percentage points.</p>"
    )
    html = replace_fragment(html, "HERO", hero)

    rules_width = round(365 * float(rules["Fraud_Value_Captured_Pct_Mean"]) / 100)
    logistic_width = round(365 * float(logistic["Fraud_Value_Captured_Pct_Mean"]) / 100)
    chart = f"""
              <rect x="42" y="48" width="636" height="294" fill="#f7f6f3"/>
              <text x="76" y="104" fill="#26332e" font-family="Georgia,serif" font-size="25">Fraud value captured</text>
              <text x="76" y="135" fill="#4e5953" font-family="Segoe UI,sans-serif" font-size="13">Mean across {seeds} seeds · 350 simulated fraud cases per test period</text>
              <text x="76" y="204" fill="#44514b" font-family="Segoe UI,sans-serif" font-size="15">Rules</text>
              <rect x="166" y="180" width="365" height="32" fill="#d8ddd6"/><rect x="166" y="180" width="{rules_width}" height="32" fill="#738875"/>
              <text x="548" y="203" fill="#26332e" font-family="Segoe UI,sans-serif" font-size="18" font-weight="700">{rules['Fraud_Value_Captured_Pct_Mean']:.2f}%</text>
              <text x="76" y="265" fill="#44514b" font-family="Segoe UI,sans-serif" font-size="15">Logistic</text>
              <rect x="166" y="241" width="365" height="32" fill="#d8ddd6"/><rect x="166" y="241" width="{logistic_width}" height="32" fill="#254f45"/>
              <text x="548" y="264" fill="#26332e" font-family="Segoe UI,sans-serif" font-size="18" font-weight="700">{logistic['Fraud_Value_Captured_Pct_Mean']:.2f}%</text>
              <text x="166" y="310" fill="#4e5953" font-family="Segoe UI,sans-serif" font-size="12">0</text><text x="507" y="310" fill="#4e5953" font-family="Segoe UI,sans-serif" font-size="12">100%</text>
    """.strip()
    html = replace_fragment(html, "CAPTURE-CHART", chart)

    proof = f"""
        <div class="proof"><strong>{row_count:,}</strong><span>synthetic events in the default run</span></div>
        <div class="proof"><strong>{holdout_rows:,}</strong><span>events in the default seed test period</span></div>
        <div class="proof"><strong>350</strong><span>simulated fraud cases per test period</span></div>
        <div class="proof"><strong>{seeds}</strong><span>seeds compared · four attack patterns</span></div>
    """.strip()
    html = replace_fragment(html, "PROOF", proof)

    table_rows = []
    for strategy, row in [("Rules", rules), ("Logistic", logistic)]:
        featured = ' class="featured"' if strategy == "Logistic" else ""
        table_rows.append(
            f"<tr{featured}><td>{strategy}</td>"
            f"<td>{row['Fraud_Value_Captured_Pct_Mean']:.2f}% "
            f"({row['Fraud_Value_Captured_Pct_Min']:.2f}–{row['Fraud_Value_Captured_Pct_Max']:.2f}%)</td>"
            f"<td>{count(row['False_Declines_Median'])} "
            f"({count(row['False_Declines_Min'])}–{count(row['False_Declines_Max'])})</td>"
            f"<td>{count(row['Legitimate_Challenges_Median'])} "
            f"({count(row['Legitimate_Challenges_Min'])}–{count(row['Legitimate_Challenges_Max'])})</td>"
            f"<td>{count(row['Legitimate_Reviews_Median'])} "
            f"({count(row['Legitimate_Reviews_Min'])}–{count(row['Legitimate_Reviews_Max'])})</td>"
            f"<td>{money(row['Net_Economic_Cost_Mean'])} mean; "
            f"{money(row['Net_Economic_Cost_Median'])} median "
            f"({money(row['Net_Economic_Cost_Min'])} to {money(row['Net_Economic_Cost_Max'])})</td></tr>"
        )

    challenge_median = float(paired["Legitimate_Challenge_Delta_Median"])
    review_median = float(paired["Legitimate_Review_Delta_Median"])
    delta_cost = float(paired["Net_Cost_Delta_Logistic_Minus_Rules_Median"])
    finding = f"""
        <div class="section-head">
          <div class="section-index">02 / THE FINDINGS</div>
          <div><h2>Lower modeled cost repeated; fraud-capture lift varied.</h2><p class="section-intro">The comparison covers {seeds} paired later-date test periods, each with 350 simulated fraud cases. Both strategies use the same fictional economics and 250-case daily review capacity.</p></div>
        </div>
        <div class="results-wrap">
          <table>
            <thead><tr><th scope="col">Strategy</th><th scope="col">Fraud value captured · mean (range)</th><th scope="col">Good payments declined · median (range)</th><th scope="col">Good payments challenged · median (range)</th><th scope="col">Good payments reviewed · median (range)</th><th scope="col">Modeled net cost · mean / median (range)</th></tr></thead>
            <tbody>{''.join(table_rows)}</tbody>
          </table>
        </div>
        <p class="result-note">A negative modeled net cost includes assumed contribution from approved legitimate payments; it is not measured profit. Good-payment counts exclude simulated fraud cases.</p>
        <div class="finding-grid">
          <article class="finding"><span class="number">OBSERVATION 01</span><h3>Fraud capture improved on average</h3><p>Logistic captured {logistic['Fraud_Value_Captured_Pct_Mean']:.2f}% of simulated fraud value versus {rules['Fraud_Value_Captured_Pct_Mean']:.2f}% for Rules. Its paired capture lift ranged from {paired['Fraud_Capture_Delta_Pct_Points_Min']:+.2f} to {paired['Fraud_Capture_Delta_Pct_Points_Max']:+.2f} percentage points, so the lift was not present in every run.</p></article>
          <article class="finding"><span class="number">OBSERVATION 02</span><h3>Less challenge friction in this model</h3><p>Logistic challenged a median {count(abs(challenge_median))} fewer good payments (observed range {count(abs(paired['Legitimate_Challenge_Delta_Max']))}–{count(abs(paired['Legitimate_Challenge_Delta_Min']))} fewer) and sent a median {count(abs(review_median))} fewer to review. The queue difference matters operationally, even in this fictional book.</p></article>
          <article class="finding"><span class="number">OBSERVATION 03</span><h3>The modeled cost ranking repeated</h3><p>Logistic had lower modeled net cost in {wins}/{seeds} seed pairs. The median paired difference was {money(delta_cost)} per test period; the observed range was {money(paired['Net_Cost_Delta_Logistic_Minus_Rules_Min'])} to {money(paired['Net_Cost_Delta_Logistic_Minus_Rules_Max'])}.</p></article>
        </div>
        <div class="assumption-band"><strong>Uncertainty note:</strong> lower modeled cost occurred in {wins}/{seeds} seeds; the paired Logistic-minus-Rules difference had a median of {money(delta_cost)} and an observed range of {money(paired['Net_Cost_Delta_Logistic_Minus_Rules_Min'])} to {money(paired['Net_Cost_Delta_Logistic_Minus_Rules_Max'])}. Fraud-capture lift ranged from {paired['Fraud_Capture_Delta_Pct_Points_Min']:+.2f} to {paired['Fraud_Capture_Delta_Pct_Points_Max']:+.2f} percentage points. These simulator ranges are not confidence intervals or proof of real-world performance; the data, labels, interventions, and dollars are synthetic.</div>
    """.strip()
    html = replace_fragment(html, "FINDINGS", finding)
    path.write_text(html, encoding="utf-8")


def write_dashboard(
    path: Path,
    metrics: pd.DataFrame,
    daily: pd.DataFrame,
    scenario_surface: pd.DataFrame,
    stability_summary: pd.DataFrame,
    stability_comparison: pd.DataFrame,
    campaign_stability_summary: pd.DataFrame,
    campaign_stability_comparison: pd.DataFrame,
    business_sensitivity: pd.DataFrame,
    business_break_even_summary: pd.DataFrame,
):
    payload = {
        "metrics": json.loads(metrics.to_json(orient="records")),
        "daily": json.loads(daily.to_json(orient="records")),
        "surface": json.loads(scenario_surface.to_json(orient="records")),
        "stability": json.loads(stability_summary.to_json(orient="records")),
        "comparison": json.loads(stability_comparison.to_json(orient="records")),
        "campaign_stability": json.loads(campaign_stability_summary.to_json(orient="records")),
        "campaign_comparison": json.loads(campaign_stability_comparison.to_json(orient="records")),
        "business": json.loads(business_sensitivity.to_json(orient="records")),
        "break_even": json.loads(business_break_even_summary.to_json(orient="records")),
    }
    data = json.dumps(payload, allow_nan=False)
    capacities = sorted(int(value) for value in scenario_surface["Review_Capacity_Per_Day"].unique())
    economics = list(scenario_surface["Economic_Scenario"].drop_duplicates())
    html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="A synthetic payments fraud analysis with seed-to-seed ranges and scenario controls.">
  <title>TrustHold Strategy Dashboard</title>
  <style>
    :root{color-scheme:light;--paper:#f4f0e8;--panel:#fffdf8;--ink:#202b2a;--muted:#4c5953;--line:#c9c4b8;--forest:#173c34;--forest-light:#dce8df;--copper:#a94d32;--sans:"Segoe UI",Tahoma,sans-serif;--serif:Georgia,"Times New Roman",serif}
    *{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 var(--sans)}header{padding:2.4rem max(1.2rem,calc((100vw - 72rem)/2));background:var(--forest);color:var(--panel)}header h1{margin:0;font:500 clamp(2.4rem,6vw,4.3rem)/1.05 var(--serif);letter-spacing:-.04em}header p{margin:.65rem 0 0;color:#f2eee5}main{max-width:72rem;margin:2rem auto 5rem;padding:0 1.25rem}.notice{padding:.9rem 1rem;border-left:3px solid var(--copper);background:var(--panel);color:var(--ink)}section{margin:1.4rem 0 2rem;padding:clamp(1rem,3vw,2rem);background:var(--panel);border:1px solid var(--line)}h2{margin:0 0 .35rem;font:500 clamp(1.7rem,4vw,2.5rem)/1.1 var(--serif)}.lede{max-width:72ch;color:var(--muted)}.result-line{margin:1rem 0;padding:1rem;background:var(--forest-light);font-weight:650}.table-wrap{overflow-x:auto;margin-top:1rem}table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}th,td{padding:.75rem .8rem;border-bottom:1px solid var(--line);text-align:right;vertical-align:top;white-space:nowrap}th{color:#394740;font-size:.77rem;text-transform:uppercase;letter-spacing:.035em}th:first-child,td:first-child{text-align:left}tbody tr:nth-child(2){background:var(--forest-light)}.note{margin:.8rem 0 0;color:var(--muted);font-size:.9rem}.controls{display:flex;flex-wrap:wrap;gap:1rem;align-items:end;margin:1.2rem 0}.controls label{display:grid;gap:.35rem;font-weight:650}.controls select{min-height:2.7rem;min-width:13rem;padding:.45rem .6rem;border:1px solid #53625a;border-radius:0;background:#fff;color:var(--ink);font:inherit}.capture-list{display:grid;gap:.65rem;margin:1.2rem 0}.capture-row{display:grid;grid-template-columns:minmax(6rem,10rem) 1fr 5rem;gap:.8rem;align-items:center}.capture-row meter{width:100%;height:1rem}.capture-row output{text-align:right;font-variant-numeric:tabular-nums;font-weight:700}.daily{height:14rem;width:100%;display:block}.daily polyline{fill:none;stroke:var(--forest);stroke-width:3}.daily circle{fill:var(--copper)}.axis-note{display:flex;justify-content:space-between;color:var(--muted);font-size:.84rem}@media(max-width:640px){.capture-row{grid-template-columns:7rem 1fr 4rem;gap:.45rem}th,td{padding:.65rem .5rem;font-size:.85rem}}
  </style>
</head>
<body>
  <header><h1>TrustHold</h1><p>The Cost of Fraud · synthetic payments decision analysis</p></header>
  <main>
    <p class="notice"><strong>Evidence boundary:</strong> every event, fraud label, and dollar amount is synthetic. Results describe the simulator's assumptions, not a real processor, savings forecast, or production model.</p>
    <section aria-labelledby="stability-title">
      <h2 id="stability-title">Does the comparison repeat across seeds?</h2>
      <p class="lede">Each run changes the generated customers, payment events, endpoints, and attack campaigns; every later-date test period includes 350 simulated fraud cases. Thresholds are selected using separate earlier rows, then compared on later dates. The same fictional economics and review capacity apply to both strategies.</p>
      <div id="seed-result" class="result-line" aria-live="polite"></div>
      <div class="table-wrap" id="stability-table"></div>
      <p class="note">Ranges show the smallest and largest results among the simulated seeds. They are not statistical confidence intervals and do not establish real-world performance.</p>
    </section>
    <section aria-labelledby="campaign-title">
      <h2 id="campaign-title">What does a campaign-held-out check show?</h2>
      <p class="lede">In the default seed, half of the numbered campaigns are kept out of model fitting and threshold selection. The later-date check then evaluates those campaigns within the same four designed fraud patterns.</p>
      <div id="campaign-result" class="result-line" aria-live="polite"></div>
      <div class="table-wrap" id="campaign-stability-table"></div>
      <p class="note">This is a nested, single-seed diagnostic with fewer fraud events. It tests withheld campaign identities, not new fraud mechanisms, real payment populations, or production outcomes.</p>
    </section>
    <section aria-labelledby="scenario-title">
      <h2 id="scenario-title">Explore the operating trade-off</h2>
      <p class="lede">Change the daily investigator limit and modeled cost assumptions. This view reuses precomputed results from one base seed; it does not retrain the model or make live payment decisions.</p>
      <div class="controls">
        <label for="capacity">Cases investigators can review each day<select id="capacity"></select></label>
        <label for="economics">Fictional cost assumptions<select id="economics"></select></label>
      </div>
      <div id="capture-chart" class="capture-list" aria-label="Share of fraud value the strategy is modeled to stop"></div>
      <div class="table-wrap" id="scenario-table"></div>
      <p class="note">A negative modeled cost is not measured profit. It reflects assumed payment margin from approved legitimate payments. Cases above the daily review limit are routed to challenge.</p>
    </section>
    <section aria-labelledby="break-even-title">
      <h2 id="break-even-title">Where could the cost ranking change?</h2>
      <p class="lede">Choose one fictional assumption to vary. The chart shows Logistic cost minus Rules cost on the base-seed holdout with decisions fixed; below zero favors Logistic, and above zero favors Rules. The summary reports any approximate crossover in the tested range.</p>
      <div class="controls"><label for="business-parameter">Assumption to vary<select id="business-parameter"></select></label></div>
      <div id="break-even-summary" class="result-line" aria-live="polite"></div>
      <svg class="daily" id="break-even-chart" viewBox="0 0 1000 260" role="img" aria-label="Modeled net-cost difference under changing fictional business assumptions"></svg>
      <div class="axis-note"><span id="business-min"></span><span>Logistic minus Rules modeled net cost</span><span id="business-max"></span></div>
      <div class="table-wrap" id="business-table"></div>
      <p class="note">This is a one-variable-at-a-time scenario, not an estimate of actual costs or a statistical uncertainty interval. Capacity changes recalculate routing with fixed thresholds.</p>
    </section>
    <section aria-labelledby="daily-title">
      <h2 id="daily-title">Daily payment volume</h2>
      <p class="lede">Observable transaction volume by simulated date. Fraud labels are excluded from this operational monitoring view.</p>
      <svg class="daily" id="daily-chart" viewBox="0 0 1000 220" role="img" aria-label="Line chart of daily synthetic payment event volume"></svg>
      <div class="axis-note"><span id="daily-start"></span><span id="daily-end"></span></div>
    </section>
  </main>
    <script>
    const d=""" + data + """;
    const money = value => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(value);
    const pct = value => `${Number(value).toFixed(2)}%`;
    const stability = document.querySelector('#stability-table');
    const compare = d.comparison[0];
    const count = value => Number(value).toLocaleString('en-US',{maximumFractionDigits:1});
    const challengeDelta = Math.abs(compare.Legitimate_Challenge_Delta_Median);
    document.querySelector('#seed-result').textContent = `Logistic had lower modeled cost in ${compare.Logistic_Lower_Cost_Wins}/${compare.Seeds} runs. Median paired cost difference: ${money(compare.Net_Cost_Delta_Logistic_Minus_Rules_Median)} (range ${money(compare.Net_Cost_Delta_Logistic_Minus_Rules_Min)} to ${money(compare.Net_Cost_Delta_Logistic_Minus_Rules_Max)}). It captured ${compare.Fraud_Capture_Delta_Pct_Points_Median.toFixed(2)} percentage points more fraud value, challenged about ${count(Math.round(challengeDelta))} fewer good payments, and sent about ${count(Math.round(compare.Legitimate_Review_Delta_Median))} more to human review.`;
    const rangeCell = (row, center, minimum, maximum, format) => `${format(row[center])} (${format(row[minimum])} ${format===money?'to':'–'} ${format(row[maximum])})`;
    const columns = [
      ['Strategy','Strategy'],
      ['Fraud_Value_Captured_Pct_Mean','Fraud value captured · mean (range)','Fraud_Value_Captured_Pct_Min','Fraud_Value_Captured_Pct_Max',pct],
      ['False_Declines_Median','Good payments declined · median (range)','False_Declines_Min','False_Declines_Max',count],
      ['Legitimate_Challenges_Median','Good payments challenged · median (range)','Legitimate_Challenges_Min','Legitimate_Challenges_Max',count],
      ['Legitimate_Reviews_Median','Good payments reviewed · median (range)','Legitimate_Reviews_Min','Legitimate_Reviews_Max',count],
      ['Net_Economic_Cost_Median','Modeled net cost · median (range)','Net_Economic_Cost_Min','Net_Economic_Cost_Max',money],
    ];
    const summary = d.stability;
    stability.innerHTML = `<table><thead><tr>${columns.map((column)=>`<th scope="col">${column[1]}</th>`).join('')}</tr></thead><tbody>${summary.map(row=>`<tr>${columns.map(([center,,minimum,maximum,format])=>`<td>${minimum?rangeCell(row,center,minimum,maximum,format):row[center]}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
    const campaignCompare = d.campaign_comparison[0];
    const campaignSummary = d.campaign_stability;
    const campaignRules = campaignSummary.find(row=>row.Strategy==='Rules');
    const campaignLogistic = campaignSummary.find(row=>row.Strategy==='Logistic');
    document.querySelector('#campaign-result').textContent = `Default seed only: Logistic modeled net cost ${money(campaignLogistic.Net_Economic_Cost_Mean)}; Rules ${money(campaignRules.Net_Economic_Cost_Mean)}. This is not a multi-seed stability claim.`;
    document.querySelector('#campaign-stability-table').innerHTML = `<table><thead><tr>${columns.map(column=>`<th scope="col">${column[1]}</th>`).join('')}</tr></thead><tbody>${campaignSummary.map(row=>`<tr>${columns.map(([center,,minimum,maximum,format])=>`<td>${minimum?rangeCell(row,center,minimum,maximum,format):row[center]}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
    const capacity = document.querySelector('#capacity');
    const economics = document.querySelector('#economics');
    const capacities = [...new Set(d.surface.map(row=>Number(row.Review_Capacity_Per_Day)))].sort((a,b)=>a-b);
    capacities.forEach(value=>capacity.add(new Option(`${value} cases per day`,value)));
    capacity.value = String(""" + str(REVIEW_CAPACITY_PER_DAY) + """ );
    [...new Set(d.surface.map(row=>row.Economic_Scenario))].forEach(value=>economics.add(new Option(value,value)));
    const displayColumns = [
      ['Strategy','Strategy'],['Fraud_Value_Captured_Pct','Fraud value captured'],['False_Declines','Good payments declined'],['Legitimate_Challenge_Count','Good payments challenged'],['Legitimate_Review_Count','Good payments reviewed'],['Review_Overflow_Count','Cases above daily review limit'],['Net_Economic_Cost','Modeled net cost']
    ];
    function renderScenario(){
      const rows=d.surface.filter(row=>Number(row.Review_Capacity_Per_Day)===Number(capacity.value)&&row.Economic_Scenario===economics.value);
      const chart=document.querySelector('#capture-chart');
      chart.innerHTML=rows.map(row=>`<div class="capture-row"><strong>${row.Strategy}</strong><meter min="0" max="100" value="${row.Fraud_Value_Captured_Pct}" aria-label="${row.Strategy}: ${pct(row.Fraud_Value_Captured_Pct)} fraud value captured"></meter><output>${pct(row.Fraud_Value_Captured_Pct)}</output></div>`).join('');
      document.querySelector('#scenario-table').innerHTML=`<table><thead><tr>${displayColumns.map(([,label])=>`<th scope="col">${label}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${displayColumns.map(([key])=>`<td>${key==='Strategy'?row[key]:key==='Net_Economic_Cost'?money(row[key]):key==='Fraud_Value_Captured_Pct'?pct(row[key]):Number(row[key]).toLocaleString('en-US')}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
    }
    capacity.addEventListener('change',renderScenario);economics.addEventListener('change',renderScenario);renderScenario();
    const businessParameter=document.querySelector('#business-parameter');
    const parameters=[...new Set(d.business.map(row=>row.Parameter))];
    parameters.forEach(value=>businessParameter.add(new Option(value,value)));
    function renderBusiness(){
      const name=businessParameter.value;
      const allRows=d.business.filter(row=>row.Parameter===name);
      const rows=allRows.filter(row=>row.Strategy==='Rules');
      const summary=d.break_even.find(row=>row.Parameter===name);
      const fmtValue=value=>summary.Unit==='USD per case'||summary.Unit==='USD per event'?money(value):summary.Unit==='rate'?`${(Number(value)*100).toFixed(1)}%`:summary.Unit==='probability'?`${(Number(value)*100).toFixed(0)}%`:Number(value).toLocaleString('en-US');
      document.querySelector('#break-even-summary').textContent=summary.Ranking_Changes_In_Tested_Range?`The modeled ranking changes near ${fmtValue(summary.Break_Even_Value)}. ${summary.Preferred_At_Min} has lower modeled cost at the low end; ${summary.Preferred_At_Max} is lower at the high end.`:`No ranking change in the tested range (${fmtValue(summary.Tested_Min)} to ${fmtValue(summary.Tested_Max)}). Logistic-minus-Rules cost ranges from ${money(Math.min(summary.Cost_Delta_At_Min,summary.Cost_Delta_At_Max))} to ${money(Math.max(summary.Cost_Delta_At_Min,summary.Cost_Delta_At_Max))}.`;
      const values=rows.map(row=>Number(row.Value));
      const deltas=rows.map(row=>Number(row.Cost_Delta_Logistic_Minus_Rules));
      const low=Math.min(0,...deltas),high=Math.max(0,...deltas),span=Math.max(1,high-low);
      const x=value=>60+(value-values[0])/Math.max(1e-9,values[values.length-1]-values[0])*880;
      const y=value=>225-(value-low)/span*190;
      const points=values.map((value,index)=>`${x(value)},${y(deltas[index])}`).join(' ');
      const zeroY=y(0);
      const chart=document.querySelector('#break-even-chart');
      chart.innerHTML=`<line x1="60" y1="${zeroY}" x2="940" y2="${zeroY}" stroke="#9b6b4c" stroke-dasharray="8 7"/><polyline points="${points}" fill="none" stroke="#173c34" stroke-width="4"/>`;
      chart.setAttribute('aria-label',`Modeled Logistic minus Rules cost across ${name}; values below zero favor Logistic and above zero favor Rules.`);
      document.querySelector('#business-min').textContent=fmtValue(values[0]);document.querySelector('#business-max').textContent=fmtValue(values[values.length-1]);
      const tableRows=rows.map(row=>{const logistic=allRows.find(other=>other.Value===row.Value&&other.Strategy==='Logistic');return `<tr><td>${fmtValue(row.Value)}</td><td>${money(row.Net_Economic_Cost)}</td><td>${money(logistic.Net_Economic_Cost)}</td><td>${money(row.Cost_Delta_Logistic_Minus_Rules)}</td><td>${row.Preferred_Strategy}</td></tr>`}).join('');
      document.querySelector('#business-table').innerHTML=`<table><thead><tr><th scope="col">Assumption</th><th scope="col">Rules net cost</th><th scope="col">Logistic net cost</th><th scope="col">Logistic minus Rules</th><th scope="col">Lower modeled cost</th></tr></thead><tbody>${tableRows}</tbody></table>`;
    }
    businessParameter.addEventListener('change',renderBusiness);renderBusiness();
    const daily=[...d.daily].sort((a,b)=>a.Date.localeCompare(b.Date));
    if(daily.length){const maximum=Math.max(...daily.map(row=>Number(row.Transaction_Count)));const points=daily.map((row,index)=>`${10+index*980/Math.max(1,daily.length-1)},${200-Number(row.Transaction_Count)/maximum*170}`).join(' ');const svg=document.querySelector('#daily-chart');svg.innerHTML=`<polyline points="${points}"/>`;svg.setAttribute('aria-label',`Line chart of daily synthetic payment volume from ${daily[0].Date} to ${daily[daily.length-1].Date}.`);document.querySelector('#daily-start').textContent=daily[0].Date;document.querySelector('#daily-end').textContent=daily[daily.length-1].Date;}
  </script>
</body>
</html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
