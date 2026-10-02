from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import pandas as pd


OUT = Path(__file__).parent
W, H = 1600, 900
PAPER = "#F4F0E8"
INK = "#202B2A"
MUTED = "#5D6964"
LINE = "#C9C4B8"
FOREST = "#173C34"
FOREST_LIGHT = "#DCE8DF"
COPPER = "#A94D32"
COPPER_PALE = "#F3DFD5"
GOLD = "#C29542"
WHITE = "#FFFDF8"
BAR_BG = "#E7E3DA"


def font(size, face="sans", bold=False):
    paths = {
        ("sans", False): r"C:\Windows\Fonts\segoeui.ttf",
        ("sans", True): r"C:\Windows\Fonts\segoeuib.ttf",
        ("serif", False): r"C:\Windows\Fonts\georgia.ttf",
        ("serif", True): r"C:\Windows\Fonts\georgiab.ttf",
    }
    try:
        return ImageFont.truetype(paths[(face, bold)], size)
    except OSError:
        return ImageFont.load_default(size=size)


def rounded(draw, box, fill, radius=22, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def header(draw, right_label):
    draw.text((92, 58), "QUEST OF TRUST", font=font(24, bold=True), fill=FOREST)
    draw.text((W - 92, 61), right_label, font=font(17, bold=True), fill=MUTED, anchor="ra")
    draw.line((92, 110, W - 92, 110), fill=LINE, width=2)


def footer(draw, line1, line2):
    draw.line((92, 824, W - 92, 824), fill=LINE, width=2)
    draw.text((92, 842), line1, font=font(17, bold=True), fill=FOREST)
    draw.text((92, 870), line2, font=font(15), fill=MUTED)


def strategy_results():
    run = OUT / "data" / "synthetic" / "run"
    summary = pd.read_csv(run / "seed_stability_summary.csv").set_index("Strategy")
    paired = pd.read_csv(run / "seed_stability_comparison.csv").iloc[0]
    rules = summary.loc["Rules"]
    logistic = summary.loc["Logistic"]
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    header(d, "QUEST OF TRUST · 30-SEED DECISION ANALYSIS")

    d.text((92, 145), "A repeatable cost ranking", font=font(49, "serif", True), fill=INK)
    d.text((92, 207), "with variable fraud capture", font=font(49, "serif", True), fill=INK)
    d.text((96, 280), f"Later-date test · {int(logistic['Holdout_Fraud_Events_Mean'])} simulated fraud cases per seed · {int(paired['Seeds'])} seeds", font=font(20), fill=MUTED)

    rounded(d, (92, 330, 1025, 778), WHITE, 24, LINE, 2)
    d.text((132, 365), "FRAUD VALUE CAPTURED · MEAN ACROSS SEEDS", font=font(17, bold=True), fill=MUTED)
    d.text((132, 395), "The observed capture lift varied by run; it was not positive in every seed.", font=font(16), fill=MUTED)

    rows = [
        ("Rules", float(rules["Fraud_Value_Captured_Pct_Mean"]), "#80958C"),
        ("Logistic", float(logistic["Fraud_Value_Captured_Pct_Mean"]), FOREST),
    ]
    label_x, bar_x, bar_w = 132, 365, 475
    y0, row_gap, bar_h = 490, 105, 30
    for i, (name, value, color) in enumerate(rows):
        y = y0 + i * row_gap
        is_best = name == "Logistic"
        d.text((label_x, y + 1), name, font=font(22, bold=is_best), fill=INK if is_best else MUTED)
        rounded(d, (bar_x, y, bar_x + bar_w, y + bar_h), BAR_BG, 15)
        width = max(0, int(bar_w * value / 100))
        if width:
            rounded(d, (bar_x, y, bar_x + width, y + bar_h), color, 15)
        d.text((bar_x + bar_w + 20, y + 1), f"{value:.2f}%", font=font(22, bold=is_best), fill=INK)

    d.text((132, 730), f"Paired fraud-capture lift: {paired['Fraud_Capture_Delta_Pct_Points_Median']:+.2f} pp median · {paired['Fraud_Capture_Delta_Pct_Points_Min']:+.2f} to {paired['Fraud_Capture_Delta_Pct_Points_Max']:+.2f} pp", font=font(16, bold=True), fill=FOREST)

    rounded(d, (1055, 330, 1508, 778), FOREST, 24)
    d.text((1095, 365), "BUSINESS RESULT · SYNTHETIC", font=font(16, bold=True), fill=FOREST_LIGHT)
    d.text((1095, 410), f"{int(paired['Logistic_Lower_Cost_Wins'])}/{int(paired['Seeds'])}", font=font(50, "serif", True), fill=WHITE)
    d.text((1097, 466), "runs with lower modeled net cost", font=font(16), fill=FOREST_LIGHT)
    delta = float(paired["Net_Cost_Delta_Logistic_Minus_Rules_Median"])
    d.text((1095, 511), f"−${abs(delta):,.0f}", font=font(38, "serif", True), fill=WHITE)
    d.text((1097, 557), "median cost difference per test period", font=font(15), fill=FOREST_LIGHT)
    d.text((1097, 583), f"Range: −${abs(paired['Net_Cost_Delta_Logistic_Minus_Rules_Min']):,.0f} to −${abs(paired['Net_Cost_Delta_Logistic_Minus_Rules_Max']):,.0f}", font=font(14), fill=FOREST_LIGHT)
    d.line((1095, 623, 1467, 623), fill="#66877B", width=2)
    d.text((1095, 642), f"{abs(paired['Legitimate_Challenge_Delta_Median']):,.0f} fewer good payments challenged", font=font(17, bold=True), fill=WHITE)
    d.text((1097, 677), f"{abs(paired['Legitimate_Review_Delta_Median']):,.0f} fewer sent to human review", font=font(16), fill=FOREST_LIGHT)

    footer(
        d,
        "SYNTHETIC STRATEGY EVALUATION · NOT LIVE PROCESSOR PERFORMANCE",
        "Thirty-seed ranges describe this simulator only; they are not confidence intervals or real-world savings claims.",
    )
    path = OUT / "quest_of_trust_strategy_results.png"
    im.save(path, optimize=True)
    return path


def decision_flow():
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    header(d, "TRUSTHOLD · FRAUD DECISION FLOW")

    d.text((92, 150), "A fraud score becomes an", font=font(53, "serif", True), fill=INK)
    d.text((92, 212), "authorization decision", font=font(53, "serif", True), fill=INK)
    d.text((96, 289), "Risk signals inform the policy; the policy determines the payment action.", font=font(21), fill=MUTED)

    cards = [
        (92, 365, 526, 520, "01  ·  PAYMENT SIGNALS", "Prior behavior", "Point-in-time event features", FOREST_LIGHT),
        (583, 365, 1035, 520, "02  ·  FRAUD RISK", "Rules + logistic score", "Patterns and model signal", COPPER_PALE),
        (1092, 365, 1508, 520, "03  ·  AUTHORIZATION POLICY", "Threshold + capacity", "Fraud exposure and queue limit", WHITE),
    ]
    for x1, y1, x2, y2, kicker, title, detail, fill in cards:
        rounded(d, (x1, y1, x2, y2), fill, 22, LINE, 2)
        d.text((x1 + 28, y1 + 24), kicker, font=font(15, bold=True), fill=MUTED)
        d.text((x1 + 28, y1 + 66), title, font=font(25, bold=True), fill=INK)
        d.text((x1 + 28, y1 + 112), detail, font=font(17), fill=MUTED)
    for x in (548, 1055):
        d.line((x - 20, 443, x + 20, 443), fill=COPPER, width=4)
        d.polygon([(x + 22, 435), (x + 36, 443), (x + 22, 451)], fill=COPPER)

    d.text((94, 567), "FOUR PAYMENT ACTIONS", font=font(17, bold=True), fill=MUTED)
    actions = [
        (92, "APPROVE", "Preserve legitimate\npayment contribution", FOREST_LIGHT),
        (451, "CHALLENGE", "Add step-up friction;\nstop assumed fraud share", COPPER_PALE),
        (810, "REVIEW", "Use finite investigator\ncapacity and recovery", WHITE),
        (1169, "DECLINE", "Stop the payment; risk a\nfalse decline if legitimate", WHITE),
    ]
    for x, title, body, fill in actions:
        rounded(d, (x, 610, x + 333, 754), fill, 20, LINE, 2)
        d.text((x + 24, 631), title, font=font(18, bold=True), fill=FOREST if title != "CHALLENGE" else COPPER)
        d.multiline_text((x + 24, 673), body, font=font(17), fill=INK, spacing=5)

    footer(
        d,
        "MEASURE THE PORTFOLIO IMPACT",
        "Fraud loss · legitimate approvals · customer friction · investigator workload · modeled economics",
    )
    path = OUT / "quest_of_trust_decision_flow.png"
    im.save(path, optimize=True)
    return path


if __name__ == "__main__":
    for asset in (strategy_results(), decision_flow()):
        print(asset)
