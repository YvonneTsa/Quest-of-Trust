"""Write a factual case-study summary and a lightweight interactive dashboard."""

import json
from pathlib import Path

import pandas as pd


def write_case_study(
    path: Path,
    metrics: pd.DataFrame,
    split_date: str,
    row_count: int,
    capacity_sensitivity: pd.DataFrame,
    economic_sensitivity: pd.DataFrame,
    impact_by_group: pd.DataFrame,
    typology_metrics: pd.DataFrame,
):
    ranked = metrics.sort_values("Net_Economic_Cost")
    best = ranked.iloc[0]
    lines = [
        "# TrustHold — The Cost of Fraud: simulation case study",
        "",
        "> All numbers below are outputs of this fictional synthetic simulation, not claims about a real company.",
        "",
        "## Context and decision problem",
        "TrustHold models a digital-payments environment where each event can be approved, challenged, reviewed, or declined. The business objective is to balance fraud loss, customer friction, finite review capacity, and payment margin.",
        "",
        "## Data and method",
        f"The generated world contains {row_count:,} timestamped transactions. A later time period beginning {split_date} is held out for evaluation. Fraud truth is stored separately and is joined only for model training and offline evaluation.",
        "The simulation plants four documented typologies. Behavioral features use only data available before each transaction. A transparent rule score and a NumPy logistic-regression baseline are compared with the incumbent challenge behavior.",
        "",
        "## Held-out strategy comparison",
        "The fictional cost assumptions are documented in `docs/simulation_assumptions.md`. Lower net economic cost is better under those settings. The best strategy under these assumptions is **" + str(best["Strategy"]) + f"**, with held-out net economic cost ${best['Net_Economic_Cost']:,.2f}.",
        "",
        "```text",
        metrics.to_string(index=False),
        "```",
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
        "Synthetic event injection makes ground truth known but simplifies real fraud, customer behavior, intervention effectiveness, and selection effects. Economic inputs are assumptions, not empirical estimates. This comparison does not establish causal impact or production performance. Thresholds and review capacity should be stress-tested before drawing portfolio recommendations.",
        "",
        "## Next questions",
        "Test sensitivity to fraud prevalence and chargeback cost. Then inspect typology-level performance, validate the simulator assumptions with domain experts, and expand the portfolio presentation.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_dashboard(path: Path, metrics: pd.DataFrame, daily: pd.DataFrame, scenario_surface: pd.DataFrame):
    payload = {
        "metrics": json.loads(metrics.to_json(orient="records")),
        "daily": json.loads(daily.to_json(orient="records")),
        "surface": json.loads(scenario_surface.to_json(orient="records")),
    }
    data = json.dumps(payload, allow_nan=False)
    html = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TrustHold | The Cost of Fraud</title>
<style>body{font:16px/1.5 system-ui,sans-serif;margin:0;background:#f4f6f8;color:#15202b}header{background:#112b3c;color:#fff;padding:28px max(24px,calc((100vw - 1100px)/2))}main{max-width:1100px;margin:28px auto;padding:0 20px}.card{background:white;border:1px solid #dce3e8;border-radius:12px;padding:20px;margin:18px 0;overflow:auto}.muted{color:#526575}.chart{display:flex;align-items:end;gap:14px;height:220px;border-bottom:1px solid #9aa9b4;padding:8px}.bar{min-width:50px;flex:1;background:#1f7892;border-radius:6px 6px 0 0;position:relative}.bar span{position:absolute;bottom:-46px;left:0;font-size:12px;transform:rotate(-25deg);transform-origin:top left;white-space:nowrap}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:right;padding:8px;border-bottom:1px solid #e1e6ea}th:first-child,td:first-child{text-align:left}svg{width:100%;height:220px}.note{border-left:4px solid #f0a83b;padding-left:12px}</style></head><body>
<header><h1>TrustHold</h1><div>The Cost of Fraud · Synthetic decision strategy simulator</div></header><main><p class="note">Illustrative output from fictional synthetic data. Not a real-world performance claim.</p>
<section class="card"><h2>Strategy economics simulator</h2><p class="muted">Choose a daily review limit and cost assumptions. This re-renders precomputed holdout outcomes; lower modeled cost is better under the selected fictional assumptions.</p><label>Review capacity <select id="capacity"><option>1</option><option>5</option><option>15</option><option selected>25</option><option>50</option></select></label> &nbsp; <label>Economic assumptions <select id="economics"></select></label><div id="bars" class="chart"></div><div id="table"></div></section>
<section class="card"><h2>Daily observable signals</h2><p class="muted">Transaction volume and model score rates; fraud labels are not used in live monitoring summaries.</p><svg id="daily" viewBox="0 0 1000 220" role="img" aria-label="Daily transaction volume trend"></svg></section></main>
<script>const d=""" + data + """;const econ=document.querySelector('#economics');[...new Set(d.surface.map(x=>x.Economic_Scenario))].forEach(x=>econ.add(new Option(x,x)));const cols=['Strategy','Fraud_Value_Captured_Pct','False_Declines','Legitimate_Challenge_Count','Legitimate_Review_Count','Review_Overflow_Count','Net_Economic_Cost'];function render(){const cap=Number(document.querySelector('#capacity').value),assumption=econ.value;const m=d.surface.filter(x=>Number(x.Review_Capacity_Per_Day)===cap&&x.Economic_Scenario===assumption);const vals=m.map(x=>Number(x.Net_Economic_Cost)),lo=Math.min(...vals),hi=Math.max(...vals);document.querySelector('#bars').innerHTML=m.map(x=>{let h=25+150*(hi-Number(x.Net_Economic_Cost))/(Math.max(1,hi-lo));return `<div class=bar style="height:${h}px" title="${x.Strategy}: $${Number(x.Net_Economic_Cost).toLocaleString()}"><span>${x.Strategy}</span></div>`}).join('');document.querySelector('#table').innerHTML='<table><thead><tr>'+cols.map(c=>`<th>${c.replaceAll('_',' ')}</th>`).join('')+'</tr></thead><tbody>'+m.map(r=>'<tr>'+cols.map(c=>`<td>${c==='Net_Economic_Cost'?'$':''}${typeof r[c]==='number'?r[c].toLocaleString():r[c]}</td>`).join('')+'</tr>').join('')+'</tbody></table>'}document.querySelector('#capacity').addEventListener('change',render);econ.addEventListener('change',render);render();const a=d.daily,svg=document.querySelector('#daily');const max=Math.max(...a.map(x=>x.Transaction_Count));const pts=a.map((x,i)=>`${i*980/Math.max(1,a.length-1)+10},${200-x.Transaction_Count/max*170}`).join(' ');svg.innerHTML=`<polyline points="${pts}" fill="none" stroke="#1f7892" stroke-width="3"/>`;</script></body></html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
