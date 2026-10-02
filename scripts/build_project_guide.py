"""Build the full Word guide for the TrustHold project."""

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "TrustHold_Project_Guide.docx"
NAVY = "18364D"
PALE_BLUE = "EAF1F6"
PALE_GRAY = "F4F6F8"
GRID = "D9E0E5"
TEXT = "202A33"
MUTED = "536471"


def set_cell_shading(cell, fill):
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)
    shading.set(qn("w:val"), "clear")


def set_cell_margins(cell, top=95, start=110, bottom=95, end=110):
    properties = cell._tc.get_or_add_tcPr()
    margins = properties.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        properties.append(margins)
    for edge, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = margins.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            margins.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table):
    properties = table._tbl.tblPr
    borders = properties.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        properties.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = qn(f"w:{edge}")
        element = borders.find(tag)
        if element is None:
            element = OxmlElement(f"w:{edge}")
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "5")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), GRID)


def set_repeat_table_header(row):
    properties = row._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    properties.append(repeat)


def set_keep_row_together(row):
    properties = row._tr.get_or_add_trPr()
    properties.append(OxmlElement("w:cantSplit"))


def set_run_font(run, name="Aptos", size=None, color=TEXT, bold=None, italic=None):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    run.font.color.rgb = RGBColor.from_string(color)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def plain_text(value):
    """Remove Markdown delimiters because this builder writes formatted DOCX directly."""
    return str(value).replace("`", "")


def add_body(doc, text, style=None, after=6, before=0, keep=False):
    paragraph = doc.add_paragraph(style=style)
    paragraph.paragraph_format.space_after = Pt(after)
    paragraph.paragraph_format.space_before = Pt(before)
    paragraph.paragraph_format.line_spacing = 1.08
    paragraph.paragraph_format.keep_together = keep
    run = paragraph.add_run(plain_text(text))
    set_run_font(run, size=10.2)
    return paragraph


def add_rich_paragraph(doc, segments, style=None, after=6, before=0):
    paragraph = doc.add_paragraph(style=style)
    paragraph.paragraph_format.space_after = Pt(after)
    paragraph.paragraph_format.space_before = Pt(before)
    paragraph.paragraph_format.line_spacing = 1.08
    for text, options in segments:
        run = paragraph.add_run(plain_text(text))
        set_run_font(run, size=10.2, **options)
    return paragraph


def add_bullet(doc, text, level=0):
    paragraph = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    paragraph.paragraph_format.space_after = Pt(3)
    paragraph.paragraph_format.line_spacing = 1.05
    set_run_font(paragraph.add_run(plain_text(text)), size=10.0)
    return paragraph


def add_number(doc, text):
    paragraph = doc.add_paragraph(style="List Number")
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.line_spacing = 1.05
    set_run_font(paragraph.add_run(plain_text(text)), size=10.0)
    return paragraph


def add_heading(doc, text, level=1):
    paragraph = doc.add_paragraph(style=f"Heading {level}")
    paragraph.paragraph_format.keep_with_next = True
    paragraph.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    paragraph.paragraph_format.space_after = Pt(5)
    set_run_font(paragraph.add_run(text), size=17 if level == 1 else 12.5, color="000000", bold=True)
    return paragraph


def add_code(doc, text):
    for line in text.strip("\n").splitlines():
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.left_indent = Inches(0.18)
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.line_spacing = 1.0
        ppr = paragraph._p.get_or_add_pPr()
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), PALE_GRAY)
        ppr.append(shading)
        set_run_font(paragraph.add_run(line or " "), name="Consolas", size=8.3, color="293844")


def add_table(doc, headers, rows, widths, font_size=8.3):
    table = doc.add_table(rows=1, cols=len(headers))
    table.autofit = False
    table.allow_autofit = False
    total_width = sum(widths)
    for col, width in zip(table.columns, widths):
        col.width = Inches(width)
    set_table_borders(table)
    header = table.rows[0]
    set_repeat_table_header(header)
    set_keep_row_together(header)
    for cell, label, width in zip(header.cells, headers, widths):
        cell.width = Inches(width)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_shading(cell, NAVY)
        set_cell_margins(cell)
        paragraph = cell.paragraphs[0]
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.line_spacing = 1.0
        run = paragraph.add_run(plain_text(label))
        set_run_font(run, size=font_size, color="FFFFFF", bold=True)
    for index, row_data in enumerate(rows):
        row = table.add_row()
        set_keep_row_together(row)
        for cell, value, width in zip(row.cells, row_data, widths):
            cell.width = Inches(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            if index % 2:
                set_cell_shading(cell, PALE_BLUE)
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.line_spacing = 1.0
            run = paragraph.add_run(plain_text(value))
            set_run_font(run, size=font_size)
    table_width = OxmlElement("w:tblW")
    table_width.set(qn("w:w"), str(round(total_width * 1440)))
    table_width.set(qn("w:type"), "dxa")
    table._tbl.tblPr.append(table_width)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("TrustHold Project Guide  |  ")
    set_run_font(run, size=8, color=MUTED)
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    displayed = OxmlElement("w:t")
    displayed.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for element in (begin, instruction, separate, displayed, end):
        run._r.append(element)


def configure_document(doc):
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.72)
    section.bottom_margin = Inches(0.72)
    section.left_margin = Inches(0.78)
    section.right_margin = Inches(0.78)
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(10.2)
    normal.font.color.rgb = RGBColor.from_string(TEXT)
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    for name, size in (("Title", 29), ("Heading 1", 17), ("Heading 2", 12.5)):
        style = styles[name]
        style.font.name = "Aptos Display" if name != "Title" else "Aptos Display"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string("000000")
        style._element.rPr.rFonts.set(qn("w:ascii"), "Aptos Display")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos Display")
    title_style_properties = styles["Title"]._element.pPr
    if title_style_properties is not None:
        border = title_style_properties.find(qn("w:pBdr"))
        if border is not None:
            title_style_properties.remove(border)
    footer = section.footer.paragraphs[0]
    add_page_number(footer)
    doc.core_properties.title = "TrustHold Project Guide"
    doc.core_properties.subject = "Complete explanation of the TrustHold synthetic fraud decision project"
    doc.core_properties.keywords = "TrustHold, fraud, synthetic data, SQLite, model governance"


def build():
    doc = Document()
    configure_document(doc)

    # Cover
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before = Pt(82)
    title = doc.add_paragraph(style="Title")
    title.paragraph_format.space_after = Pt(8)
    set_run_font(title.add_run("TrustHold Project Guide"), size=29, color="000000", bold=True)
    title_properties = title._p.pPr
    if title_properties is not None:
        border = title_properties.find(qn("w:pBdr"))
        if border is not None:
            title_properties.remove(border)
    subtitle = doc.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(22)
    set_run_font(subtitle.add_run("The Cost of Fraud"), size=18, color=NAVY, bold=True)
    add_body(doc, "A complete explanation of the synthetic data, investigation tools, models, decisions, economics, and results.", after=22)
    add_body(doc, "Version 1.0  |  September 30, 2026", after=2)
    add_body(doc, "Project repository  |  github.com/YvonneTsa/Quest-of-Trust", after=0)
    doc.add_page_break()

    add_heading(doc, "How to Use This Guide", 1)
    add_body(doc, "This guide explains how TrustHold works from the first generated customer through the final decision comparison. It is written for both someone learning the concepts and someone reviewing the project as a portfolio artifact. Start with the quick start if you want to run it; use the code map and table inventory when you want to inspect a specific part.")
    add_body(doc, "The project is a reproducible educational simulation. It does not use real customer or fraud data. All business costs, fraud patterns, customer profiles, and outcomes are fictional assumptions. Thirty generated seeds show run-to-run variation inside this simulator, not uncertainty for a real payments population.")
    add_heading(doc, "Contents", 2)
    for item in [
        "1  Project purpose and design",
        "2  Quick start and ways to use the project",
        "3  System flow and code map",
        "4  How the synthetic world is generated",
        "5  Fraud scenarios and evaluation labels",
        "6  Data inventory and field meanings",
        "7  Point-in-time features and leakage controls",
        "8  Rules and logistic regression",
        "9  Decisions, capacity, and economics",
        "10  Evaluation results and how to read them",
        "11  SQL investigations, network analysis, and monitoring",
        "12  Dashboard, reports, notebook, and dataset tools",
        "13  Storage choice and reproducibility",
        "14  Limits, governance, and roadmap",
        "15  Glossary and reference map",
        "Appendix A  Worked transaction example",
        "Appendix B  SQL examples and interpretation",
        "Appendix C  Complete module reference",
        "Appendix D  Troubleshooting and next experiments",
    ]:
        add_body(doc, item, after=2)
    doc.add_page_break()

    add_heading(doc, "1  Project Purpose and Design", 1)
    add_body(doc, "TrustHold asks a practical payments question: for each transaction, when should a business approve it, ask the customer for more proof, send it to an investigator, or decline it? A useful fraud system must reduce fraud losses while considering the cost of customer friction, the limited size of a human review team, and the revenue earned on legitimate activity.")
    add_body(doc, "The project follows each decision through a full analytical workflow. It creates a fictional customer and merchant population, generates ordinary transactions, injects known fraud patterns, builds signals using only past information, compares a transparent score with a simple model, converts scores into operating actions, and measures the resulting costs and trade-offs.")
    add_table(doc, ["Design choice", "What it means in TrustHold"], [
        ("Synthetic by design", "Every entity, event, label, cost, and result is fictional and repeatable from a fixed seed."),
        ("Investigation before automation", "SQL queries and readable rule reasons expose patterns before the model is considered."),
        ("Past-only features", "Rolling behavior counts are computed before the current transaction is added to history."),
        ("Future-period evaluation", "The latest dates form a time holdout; rows are not randomly mixed across time."),
        ("Business outcome", "The comparison includes losses, good-customer friction, review load, and payment margin."),
        ("Inspectable choices", "Assumptions, threshold bands, costs, and model coefficients are saved for review."),
    ], [1.65, 5.25], font_size=8.7)
    add_heading(doc, "What the project demonstrates", 2)
    add_body(doc, "The project demonstrates data simulation, SQL investigation, feature design, rule construction, basic statistical learning, threshold selection, queue capacity handling, cost modeling, temporal evaluation, monitoring, customer-group diagnostics, and communication through a report and interactive dashboard. It is a complete portfolio prototype, not a live authorization service.")

    add_heading(doc, "2  Quick Start and Ways to Use the Project", 1)
    add_heading(doc, "Set up the environment", 2)
    add_body(doc, "Run these commands in PowerShell from the repository root. Python 3.10 or newer is suitable; the project dependencies are NumPy and pandas. SQLite is included with Python, so no database server is needed.")
    add_code(doc, "python -m venv .venv\n.\\.venv\\Scripts\\Activate.ps1\npython -m pip install -r requirements.txt")
    add_heading(doc, "Run the full pipeline", 2)
    add_code(doc, "python -m src.run_project")
    add_body(doc, "The default run creates 2,000 customers, 800 merchants, 1,200 terminals, and 60 days of activity. It injects ten sampled attack campaigns for each of four typologies and evaluates ten consecutive seeds. Each holdout contains 350 planted fraud events. The run writes CSV outputs and `trusthold.sqlite` under `data/synthetic/run/`, refreshes the case study, and rebuilds the dashboard. Repeating a run with the same code and settings produces the same fictional scenarios.")
    add_heading(doc, "Run a smaller learning example", 2)
    add_code(doc, "python -m src.run_project --customers 20 --days 30")
    add_body(doc, "The command accepts `--customers`, `--days`, `--merchants`, `--terminals`, `--review-capacity`, `--seed`, `--fraud-campaigns`, `--stability-runs`, and `--output-dir`. The horizon must be long enough for fraud examples to occur on both sides of the temporal split. The default start date is January 1, 2026.")
    add_heading(doc, "Restore the published data snapshot", 2)
    add_code(doc, "python -m scripts.assemble_dataset\npython sql/run_investigation.py")
    add_body(doc, "The first command joins versioned CSV parts, checks the original SHA-256 checksums, and writes restored tables into `data/synthetic/run/`. The planted labels are restored under `data/synthetic/run/restricted/`. The second command runs each read-only SQL investigation against the local SQLite database; if the database is absent, run the complete project first.")
    add_heading(doc, "Open the tools", 2)
    add_bullet(doc, "Open `reports/dashboard.html` in a browser for the local economics and review-capacity selectors.")
    add_bullet(doc, "Read `reports/case_study.md` for the generated holdout comparison and its caveats.")
    add_bullet(doc, "Open `notebooks/01_investigation.ipynb` for guided data exploration without joining the hidden labels.")

    add_heading(doc, "3  System Flow and Code Map", 1)
    add_body(doc, "`src/run_project.py` coordinates the workflow. Each stage receives an explicit table or configuration value and returns a result used by the next stage. Keeping the generator, feature code, scoring, policy, evaluation, and reporting separate makes the project easier to inspect and easier to move to another storage engine later.")
    add_table(doc, ["Stage", "Main code", "Input and output"], [
        ("Settings", "`src/config.py`", "Seed, population size, dates, and fictional economics."),
        ("World generation", "`src/simulation/`", "Customers and linked accounts, merchants, terminals, and baseline transactions."),
        ("Fraud injection", "`inject_fraud.py`", "Transactions plus a separate ground-truth table."),
        ("Features", "`src/features/build_features.py`", "Timestamped transactions become point-in-time numeric signals."),
        ("Scoring", "`src/rules/` and `src/models/`", "Readable rule score, logistic score, and hybrid score."),
        ("Operating policy", "`src/decisions/policies.py`", "Scores become actions with daily review limits."),
        ("Evaluation", "`src/evaluation/metrics.py` and `run_project.py`", "Holdout metrics, costs, sensitivities, and group summaries."),
        ("Persistence and outputs", "`src/storage.py`, `src/reporting.py`", "CSV, SQLite, case study, and HTML dashboard."),
        ("Investigation and operations", "`sql/`, `src/monitoring.py`, `src/network_intelligence.py`", "Read-only SQL summaries, daily alerts, and terminal connectivity."),
    ], [1.35, 2.4, 3.15], font_size=8.1)
    add_body(doc, "The data flow is: generate entities → create ordinary transactions → inject labeled events → build past-only features → create temporary evaluation labels → split by date → fit scores and choose thresholds on training history → evaluate future-period actions → save label-free tables and reports. The label join occurs only after feature construction, which is central to the leakage control.")

    add_heading(doc, "4  How the Synthetic World Is Generated", 1)
    add_heading(doc, "Customer profiles", 2)
    add_body(doc, "The customer generator samples one of three fictional segments: Standard, Premium, and Business, using probabilities 70%, 20%, and 10%. Segment-specific reference medians define typical spend and daily transaction rates. Log-normal draws create positive, right-skewed profiles. The configured dollar and activity values are medians, not industry estimates. Region and KYC band are sampled separately; KYC band is not a fraud proxy and is excluded from the model inputs.")
    add_table(doc, ["Segment", "Median spend", "Median transactions per day"], [
        ("Standard", "$45", "1.5"),
        ("Premium", "$100", "2.5"),
        ("Business", "$180", "4.0"),
    ], [2.3, 2.3, 2.3], font_size=9)
    add_heading(doc, "Linked entities", 2)
    add_body(doc, "Each customer receives one account in this first version. Merchants have a category and region, and every terminal belongs to one merchant. A customer is assigned a small set of familiar terminals, usually from their home region. The generator keeps these IDs linked so analysts can follow a transaction from customer to account to merchant and terminal.")
    add_heading(doc, "Ordinary transactions", 2)
    add_body(doc, "For each customer and simulated date, a Poisson draw determines the number of events using that customer's latent daily rate. The generator places those events at random ordered seconds within the day. Amounts are log-normal around the customer's typical spend. Channel and authentication types are sampled from configured fictional probabilities. Most activity uses familiar terminals; a small share uses another endpoint to avoid making every unfamiliar event inherently abnormal.")
    add_table(doc, ["Default setting", "Value"], [
        ("Random seed", "20260915; separate offsets isolate generation layers."),
        ("Simulation horizon", "60 days starting 2026-01-01."),
        ("Customer / merchant / terminal count", "2,000 / 800 / 1,200."),
        ("Baseline channel share", "52% card present, 33% ecommerce, 15% mobile wallet."),
        ("Authentication soft-decline rate", "1.5% in the ordinary event generator."),
        ("Familiar terminal behavior", "95% uses habitual endpoint set; 5% can use any endpoint."),
        ("Crisis onset", "About 58% into the horizon; scenario bursts are split across periods."),
    ], [2.45, 4.45], font_size=8.5)

    add_heading(doc, "5  Fraud Scenarios and Evaluation Labels", 1)
    add_body(doc, "The simulator adds 700 events across four designed typologies and ten separately sampled campaigns per typology. Events are placed in earlier and later portions of the time horizon so both training and holdout periods contain examples. The scenarios are simplified signatures for learning and are not descriptions of real attack rates or tactics.")
    add_table(doc, ["Scenario", "Events", "Constructed signal"], [
        ("Terminal compromise", "320", "Repeated bursts at one endpoint across several customers."),
        ("Card testing", "240", "Low-value, rapid sequences at shared endpoints."),
        ("Credential compromise", "80", "Larger purchases at unfamiliar terminals for one customer."),
        ("Account takeover", "60", "Shifted channel/authentication context at new endpoints."),
        ("Total", "700", "Ten sampled campaigns per typology, spanning earlier and later dates."),
    ], [1.8, 0.8, 4.3], font_size=8.5)
    add_heading(doc, "Where labels live", 2)
    add_body(doc, "The generator returns the transaction table and a distinct ground-truth table keyed by transaction ID. The feature builder sees no label column. The pipeline joins the IDs afterward to construct a temporary `Fraud_Label` for model training and offline evaluation. It writes the labels under `data/synthetic/run/restricted/` and excludes them from transaction, feature, decision, monitoring, and SQLite tables. For reproducibility, the public repository also contains the synthetic evaluation labels as a separate, clearly named CSV table. Anyone exploring transactions should keep that table out of SQL investigations and model inputs.")

    add_heading(doc, "6  Data Inventory and Field Meanings", 1)
    add_body(doc, "The published run snapshot contains 29 CSV tables and 1,094,394 row records: 28 public analytical tables with 1,093,694 rows, plus 700 separate synthetic fraud labels. The totals include multiple analytical views of the same events; they are not unique-transaction counts. The core `transactions` and `behavior_features` tables each have 246,314 rows. The default-seed decision table has one row per later-date holdout event per strategy.")
    table_rows = [
        ("accounts", "2,000", "Account linked to customer."),
        ("action_counts", "16", "Counts by operating action and strategy."),
        ("behavior_features", "246,314", "One timestamped event with observable features and rule score."),
        ("business_break_even_summary", "7", "One summary for each fictional business assumption tested."),
        ("business_sensitivity", "282", "Strategy outcomes across one-at-a-time economic scenarios."),
        ("campaign_holdout_decisions", "296,248", "74,062 campaign-check events times four strategies."),
        ("campaign_holdout_metrics", "4", "One result per strategy in the single-seed campaign check."),
        ("campaign_stability_by_run", "2", "Rules and Logistic outcomes in the one campaign-check seed."),
        ("campaign_stability_comparison", "1", "Paired Rules-versus-Logistic campaign-check result."),
        ("campaign_stability_summary", "2", "Per-strategy campaign-check metrics."),
        ("capacity_sensitivity", "15", "Strategy outcomes at five review-capacity settings."),
        ("customers", "2,000", "Fictional customer profile and segment."),
        ("daily_monitoring", "60", "One day of label-free operating signals."),
        ("economic_sensitivity", "24", "Four strategies under six economic assumptions."),
        ("fraud_ground_truth", "700", "Separate synthetic labels for offline evaluation only."),
        ("evaluation_design", "2", "Fit, validation, and holdout partitions in the default seed."),
        ("impact_by_customer_group", "40", "Held-out outcomes grouped by strategy and customer descriptor."),
        ("merchants", "800", "Fictional business endpoint owner, category, and region."),
        ("model_coefficients", "12", "One coefficient per numeric model feature."),
        ("scenario_surface", "120", "Strategies across capacity and economic assumption combinations."),
        ("seed_stability_by_run", "60", "Rules and Logistic metrics for each of 30 seeds."),
        ("seed_stability_comparison", "1", "Paired Logistic-minus-Rules ranges and cost win count."),
        ("seed_stability_summary", "2", "Per-strategy means, medians, and observed ranges."),
        ("strategy_metrics", "4", "One held-out summary per strategy."),
        ("terminal_network_summary", "1,200", "Endpoint connectivity over the complete event history."),
        ("terminals", "1,200", "Endpoint with merchant ownership and region."),
        ("test_decisions", "296,948", "74,237 default-seed holdout events times four strategies."),
        ("transactions", "246,314", "Raw synthetic event record, before derived features."),
        ("typology_metrics", "16", "Four strategy summaries by four fraud typologies."),
    ]
    add_table(doc, ["Table", "Rows", "What one row represents"], table_rows, [2.15, 0.8, 3.95], font_size=7.9)
    add_heading(doc, "Important transaction fields", 2)
    add_table(doc, ["Field group", "Fields", "How to interpret them"], [
        ("Identifiers", "Transaction_ID, Customer_ID, Account_ID", "Stable synthetic IDs; transaction ID is the join key for offline labels."),
        ("Time", "Timestamp", "Synthetic event time; stored without a timezone offset."),
        ("Network", "Merchant_ID, Terminal_ID", "The terminal belongs to a merchant; repeated customer-terminal pairs show familiarity."),
        ("Context", "Customer_Region, Merchant_Region, Channel, Auth_Type, Auth_Result", "Observable transaction context used by investigations and selected features."),
        ("Value and baseline", "Amount, Currency, Incumbent_Decision", "Synthetic amount in USD and a simple pre-existing action for comparison."),
    ], [1.2, 2.65, 3.05], font_size=8)
    add_body(doc, "`data/synthetic/customers.csv` is the recovered 20-customer seed sample. `data/synthetic/run/customers.csv` belongs to the full 2,000-customer run. Use the latter when interpreting the published project output.")

    add_heading(doc, "7  Point-in-Time Features and Leakage Controls", 1)
    add_body(doc, "A feature is information the policy or model can observe when a transaction arrives. TrustHold sorts events by timestamp and transaction ID, calculates each row's historical context, and only then adds the current event to its history. This ordering prevents the event from increasing its own prior count.")
    add_table(doc, ["Feature", "Construction", "Why it may help"], [
        ("Amount_To_Typical_Spend", "Current amount divided by the customer's profile spend.", "Find unusually large purchases for that person."),
        ("Tx_Count_Prior_24h", "Earlier customer events in the rolling 24-hour window.", "Find sudden activity bursts."),
        ("Terminal_Prior_Tx_Count", "Earlier events at the terminal.", "Describe endpoint activity volume."),
        ("Terminal_Prior_Distinct_Customers", "Earlier distinct customers at the terminal.", "Find endpoints used across many customer profiles."),
        ("Customer_Terminal_Prior_Count", "Earlier uses of the same customer-terminal pair.", "Separate familiar from first-seen endpoint pairs."),
        ("Is_Night / Is_Weekend", "Flags from event timestamp.", "Describe timing context."),
        ("Auth_Soft_Decline", "Current event's soft-decline result.", "Describe authentication outcome."),
        ("Is_Ecommerce / Is_Magstripe / Is_Mobile_Wallet", "Flags from channel and authentication type.", "Represent selected channel/authentication context."),
        ("Region_Mismatch", "Customer home region differs from merchant region.", "Provide a location mismatch signal; not proof of fraud."),
    ], [2.0, 2.65, 2.25], font_size=7.8)
    add_heading(doc, "Leakage boundary", 2)
    add_body(doc, "Leakage occurs when a model receives information that would not be known at decision time, such as a planted fraud label, future review outcome, or data from after the event. TrustHold builds features from the transactions first, then joins labels by transaction ID only for fitting and evaluating the offline model. KYC risk is generated independently and omitted from the model feature list. The terminal network summary is a full-history investigation output, so it must not be fed back into point-in-time prediction.")

    add_heading(doc, "8  Rules and Logistic Regression", 1)
    add_heading(doc, "Explainable rules", 2)
    add_body(doc, "Each rule adds a visible number of points and a text reason. Several signals may accumulate on the same event. The final score is capped at 100; it is an alert score, not a calibrated probability.")
    add_table(doc, ["Signal condition", "Points", "Reason code"], [
        ("Amount is at least 3× typical spend", "30", "amount_vs_profile"),
        ("Amount is at least 6× typical spend", "+25", "extreme_amount_vs_profile"),
        ("At least 5 prior events in 24 hours", "25", "customer_velocity"),
        ("At least 10 prior events in 24 hours", "+20", "high_customer_velocity"),
        ("New customer-terminal pair", "15", "new_customer_terminal_pair"),
        ("Terminal previously used by at least 8 customers", "18", "terminal_customer_network_burst"),
        ("Amount ≤ $5 and at least 2 prior events", "35", "low_value_testing_velocity"),
        ("Ecommerce, magstripe, and night activity", "20", "ecommerce_authentication_shift"),
        ("Night activity", "8", "night_activity"),
        ("Authentication soft decline", "8", "authentication_soft_decline"),
        ("Customer and merchant regions differ", "12", "home_region_mismatch"),
    ], [3.2, 0.8, 2.9], font_size=7.9)
    add_body(doc, "The bands are cumulative. For example, an amount six times the customer's typical spend receives both amount rules. Rule reasons make it possible to explain why a row scored highly and to investigate false alerts.")
    add_heading(doc, "Logistic baseline", 2)
    add_body(doc, "The logistic model estimates a score using a weighted linear combination of the 12 numeric features followed by a sigmoid transformation. It is implemented with NumPy and full-batch gradient descent rather than a machine-learning library. Before fitting, it standardizes each feature using the training mean and standard deviation. A zero standard deviation is replaced by 1 so the calculation remains defined. Standardized values are clipped to keep extreme values from dominating.")
    add_body(doc, "Because fraud is rare, positive rows receive a larger training weight than negative rows. The positive weight is the negative-to-positive ratio capped at 12 and normalized to an average weight of 1. The default optimizer runs 1,200 epochs with learning rate 0.08 and L2 regularization 0.001. Saved coefficients make the fitted feature weights inspectable. The weighted scores are useful for ranking, but the project does not claim they are calibrated real-world probabilities.")
    add_heading(doc, "Three score strategies", 2)
    add_bullet(doc, "Rules uses `Rule_Risk`, the rule score divided by 100.")
    add_bullet(doc, "Logistic uses the model score from the NumPy baseline.")
    add_bullet(doc, "Rules + logistic uses the higher of the two scores for each event.")

    add_heading(doc, "9  Decisions, Capacity, and Economics", 1)
    add_heading(doc, "Four operating actions", 2)
    add_table(doc, ["Action", "Meaning", "Modeled effect"], [
        ("APPROVE", "Release the payment.", "Fraud can create loss and a chargeback fee; legitimate payment earns a margin."),
        ("CHALLENGE", "Ask the customer to complete step-up verification.", "Costs $0.40; the base scenario assumes it stops 80% of challenged fraud."),
        ("REVIEW", "Place the event in an investigator queue.", "Costs $4.50; the base scenario assumes 90% recovery for reviewed fraud."),
        ("DECLINE", "Block the payment.", "Stops fraud loss; a legitimate false decline has an assumed customer attrition cost."),
    ], [1.05, 2.45, 3.4], font_size=8.1)
    add_heading(doc, "Thresholds and review queue", 2)
    add_body(doc, "For each score strategy, the pipeline considers four threshold sets. Values define the boundaries for challenge, review, and decline. The pipeline evaluates candidates on the training period and selects the one with the lowest modeled net economic cost. It then applies that chosen set once to the future holdout.")
    add_table(doc, ["Candidate", "Challenge at", "Review at", "Decline at"], [
        ("1", "0.20", "0.50", "0.80"),
        ("2", "0.30", "0.60", "0.90"),
        ("3", "0.40", "0.70", "0.95"),
        ("4", "0.50", "0.80", "0.97"),
    ], [2.5, 1.45, 1.45, 1.5], font_size=8.5)
    add_body(doc, "On each day, the highest-scoring review candidates are sent to the human queue up to the daily capacity, which defaults to 250. Lower-ranked candidates that would have been reviewed are changed to CHALLENGE and marked as capacity overflow. Capacity sensitivity reruns decisions with limits of 10, 50, 150, 250, and 500 cases per day.")
    add_heading(doc, "Fictional cost model", 2)
    add_table(doc, ["Outcome", "Modeled cost"], [
        ("Fraud approved", "Amount + $25 chargeback fee."),
        ("Fraud challenged", "Amount × (1 − challenge stop probability) + $0.40."),
        ("Fraud reviewed", "Amount × (1 − review recovery probability) + $4.50."),
        ("Fraud declined", "$0 fraud cost in this simplified model."),
        ("Legitimate approved", "Negative cost equal to amount × 1.1% margin."),
        ("Legitimate challenged or reviewed", "$0.40 challenge cost or $4.50 review cost."),
        ("Legitimate declined", "5% × $500 customer lifetime value + lost 1.1% margin."),
    ], [2.35, 4.55], font_size=8.2)
    add_body(doc, "A negative net cost means that modeled payment margin exceeds the modeled losses and friction costs in this scenario. It is not a claim that the real business would earn that profit. Challenge success, fraud recovery, customer attrition, lifetime value, and margin are uncalibrated assumptions.")

    add_heading(doc, "10  Evaluation Results and How to Read Them", 1)
    add_heading(doc, "Temporal split", 2)
    add_body(doc, "The pipeline sorts the unique dates, assigns the first 70% to training, and reserves the latest 30% for holdout evaluation. In the published 60-day run, the holdout starts February 12, 2026. The default seed's test set contains 74,237 events and 350 simulated fraud cases. The full run has 246,314 transactions and 700 simulated fraud cases. Using a future period helps reflect changes over time better than a random row split would.")
    add_heading(doc, "Main held-out comparison", 2)
    add_table(doc, ["Strategy", "Fraud value captured", "False declines", "Net modeled cost", "PR-AUC"], [
        ("Incumbent", "0.00%", "0", "−$15,477.19", "N/A for a score ranking"),
        ("Rules", "73.09%", "30", "−$56,248.77", "0.2655"),
        ("Logistic", "78.37%", "1", "−$73,729.50", "0.5826"),
        ("Rules + logistic", "76.26%", "30", "−$58,811.13", "0.2981"),
    ], [1.25, 1.25, 0.9, 1.4, 1.2], font_size=7.6)
    add_body(doc, "Under the base fictional economics and the default 250-case daily review capacity, Logistic has the lowest modeled cost among these strategies. In this seed's holdout it captures 78.37% of simulated fraud value, records one false decline, sends 21 good payments to review, and challenges 740. Rules captures 73.09%, records 30 false declines, reviews 140 good payments, and challenges 5,305. These single-seed outcomes are shown separately from the 30-seed comparison later in this guide.")
    add_heading(doc, "What each metric means", 2)
    add_table(doc, ["Metric", "Interpretation"], [
        ("Fraud value captured", "Fraud amount multiplied by assumed intervention effectiveness: 0% approve, 80% challenge, 90% review, 100% decline."),
        ("Fraud recall", "Share of planted fraud events that receive any action other than approve."),
        ("Precision among interventions", "Share of challenged, reviewed, or declined events that are planted fraud."),
        ("False declines", "Legitimate holdout events that the policy declined."),
        ("Review overflow", "Review candidates moved to challenge because daily capacity was full."),
        ("PR-AUC", "Ranking quality across precision and recall; useful when positive events are rare."),
        ("Net economic cost", "Sum of the fictional unit costs over the selected holdout policy actions; lower is better under those assumptions."),
    ], [1.8, 5.1], font_size=8.0)
    add_body(doc, "PR-AUC applies only when a strategy produces a continuous risk score. The incumbent has no ranking score, so its PR-AUC is reported as not applicable; this does not affect its action or cost totals.")
    add_heading(doc, "Sensitivity results", 2)
    add_body(doc, "Review-capacity sensitivity tests how many cases the queue can absorb. The evaluated limits are 10, 50, 150, 250, and 500 cases per day. Overflow candidates are routed to CHALLENGE, so changing the limit can change fraud capture, customer friction, and modeled cost.")
    add_body(doc, "Economic sensitivity changes challenge success, false-decline attrition, or review recovery. In the generated output, Logistic remains lowest-cost in the listed scenarios, including lower challenge effectiveness and lower review recovery. That stability is only across the limited assumptions that were tested; it is not a statistical confidence interval or proof of robustness to unmodeled conditions.")
    add_heading(doc, "Across-seed results and uncertainty", 2)
    add_body(doc, "The pipeline repeats generation, feature construction, model fitting, threshold selection, and holdout evaluation for 30 consecutive seeds. Each Rules result is compared with the Logistic result from the same seed, so the cost difference is paired. The table shows means for value capture and medians for event counts and modeled cost, with the observed minimum-to-maximum range across those runs.")
    add_table(doc, ["Strategy", "Fraud value captured mean (range)", "False declines median (range)", "Good payments challenged median (range)", "Good payments reviewed median (range)", "Net modeled cost median (range)"], [
        ("Rules", "73.73% (68.29–81.25%)", "31 (19–52)", "5,139 (4,552–5,764)", "126 (88–155)", "−$52,948 (−$58,036 to −$47,036)"),
        ("Logistic", "77.51% (69.76–87.21%)", "0 (0–2)", "598.5 (181–930)", "19 (7–37)", "−$68,082 (−$73,730 to −$60,293)"),
    ], [0.8, 1.25, 1.05, 1.25, 1.15, 1.4], font_size=7.2)
    add_body(doc, "Logistic had lower modeled net cost than Rules in 30 of 30 runs. The paired median cost difference was −$15,501.82, with an observed range from −$22,482.27 to −$11,207.82. Logistic's median fraud-value-capture lift was 3.66 percentage points (range −1.86 to +14.31), so capture did not improve in every seed. It sent a median 4,463.5 fewer good payments to challenge (range 3,988–5,342 fewer), 108 fewer to review (range 65–138 fewer), and 31 fewer to decline (range 19–51 fewer). In this simulation, the lower modeled cost coincides with fewer interventions and a smaller investigator queue.")
    add_body(doc, "These ranges describe only the 30 random draws under the same fictional generator, attack patterns, review capacity, and unit economics. They are observed simulator ranges, not confidence intervals, significance tests, or estimates of uncertainty for a real book. Repeated seeds show how results vary under these assumptions; evaluating a real strategy would require representative labeled data and measured intervention outcomes.")

    add_heading(doc, "11  SQL Investigations, Network Analysis, and Monitoring", 1)
    add_heading(doc, "SQL investigation files", 2)
    add_body(doc, "Each SQL file asks an observable-data question and contains no reference to fraud labels. The runner opens the SQLite database, executes each query, and prints up to twelve rows for inspection.")
    add_table(doc, ["Query file", "Question it helps answer"], [
        ("01_daily_landscape.sql", "How do transaction count, value, and average amount change by day?"),
        ("02_terminal_concentration.sql", "Which terminals have the most transactions and customers?"),
        ("03_velocity_and_testing.sql", "Which low-value events follow rapid customer activity?"),
        ("04_amount_deviation.sql", "Which events are large relative to the customer profile?"),
        ("05_authentication_and_channel.sql", "How do channel, authentication result, amount, and night activity combine?"),
        ("06_network_connections.sql", "Which endpoints connect the most customers over the full dataset?"),
    ], [2.55, 4.35], font_size=8.1)
    add_body(doc, "A high volume, unfamiliar endpoint, or unusual amount is a lead for investigation. It is not proof that a payment is fraudulent. Query results describe the constructed population, and the full-history endpoint summary is intended for offline exploration rather than real-time scoring.")
    add_heading(doc, "Network summary", 2)
    add_body(doc, "`terminal_network_summary` aggregates each terminal and merchant pair. It reports transaction count, distinct customers, distinct days, total amount, and customers per transaction. This is a first customer-terminal connectivity layer. Device, IP, login, and richer account relationships are not represented.")
    add_heading(doc, "Daily monitoring", 2)
    add_body(doc, "The monitoring output uses observable transaction count, value, average amount, soft-decline rate, and share of model scores at or above 0.5. For volume and high-risk-score rate, it computes a z-score against the previous 14 days, requiring at least seven prior days. Alerts are raised when the absolute z-score reaches three. The current day is not included in its own baseline. Alerts are screening signals; seasonality and small samples can make them unstable.")
    add_heading(doc, "Group impact diagnostics", 2)
    add_body(doc, "The report compares action rates and planted fraud rates across fictional segment, KYC-band, and home-region groups. Those tables can reveal that a strategy creates different burdens across groups in this simulator. They do not certify fairness or indicate how a real protected group would be affected. Small sample sizes and independently generated descriptors limit interpretation.")

    add_heading(doc, "12  Dashboard, Reports, Notebook, and Dataset Tools", 1)
    add_table(doc, ["Artifact", "Purpose", "How to use it"], [
        ("`reports/dashboard.html`", "Interactive strategy economics view.", "Choose a daily review capacity and fictional economic scenario. It selects from precomputed holdout outcomes."),
        ("`reports/case_study.md`", "Narrative summary of the generated evaluation.", "Read the results, sensitivities, group diagnostics, typology results, and caveats."),
        ("`notebooks/01_investigation.ipynb`", "Guided exploratory analysis.", "Inspect the generated data without bringing labels into the feature or query layer."),
        ("`data/synthetic/published_run/manifest.json`", "Inventory of the published run snapshot.", "See every table part, row count, checksum, and ground-truth status."),
        ("`scripts/assemble_dataset.py`", "Restores the published CSV tables.", "Joins parts and checks SHA-256 against the original table files."),
        ("`scripts/package_dataset.py`", "Packages a new run for repository sharing.", "Splits current CSV outputs into smaller parts and writes a new manifest."),
        ("`data/synthetic/run/trusthold.sqlite`", "Local analytical database.", "Query observable transaction, feature, decision, and summary tables with SQLite."),
    ], [2.05, 2.05, 2.8], font_size=7.8)
    add_body(doc, "The dashboard does not calculate a new model score when a user changes a selector. It filters the already calculated scenario surface by capacity and economic assumption. This makes it a fast explanation tool, but not an unrestricted policy simulator.")
    add_body(doc, "The packaged data tools publish synthetic labels separately for transparent replication. The assembly command puts those labels under a restricted folder locally. Keep the label file separate from SQL investigations, feature generation, and live monitoring.")

    add_heading(doc, "13  Storage Choice and Reproducibility", 1)
    add_heading(doc, "Why SQLite is suitable now", 2)
    add_body(doc, "SQLite fits the current learning build because Python includes it, the project needs no server, and the database is easy to distribute and inspect. pandas writes each public output table through `to_sql`. The SQL investigations use ordinary SQLite syntax and operate on the generated database. This keeps setup friction low while the project is small and focused on concepts.")
    add_heading(doc, "When DuckDB and Parquet may be better", 2)
    add_body(doc, "The earlier roadmap proposed DuckDB with Parquet for larger analytical data. DuckDB is designed for analytical scans and Parquet stores column-oriented files compactly. As the simulator grows from tens of thousands of rows toward millions, those formats may improve query speed and storage efficiency. SQLite can still handle many larger projects, so a migration should follow measured need rather than a row-count rule alone.")
    add_body(doc, "The current code already separates generation and transformations from `storage.py`, which reduces migration effort. A future design could write Parquet from the pipeline, query it with DuckDB, and keep CSV exports only for interchange. The SQL syntax and query runner would need targeted changes, and any migration should verify table parity and expected outputs.")
    add_heading(doc, "Repeatability", 2)
    add_body(doc, "The seed is 20260915. Independent seed offsets are used for customer profiles, world entities and ordinary activity, and fraud injection so a change in one random draw sequence is less likely to alter unrelated layers. Reproducibility still depends on code, library versions, and configuration remaining compatible. Record changes to assumptions and versions when making a new release.")

    add_heading(doc, "14  Limits, Governance, and Roadmap", 1)
    add_heading(doc, "What this version does not establish", 2)
    for text in [
        "The synthetic population, event counts, and financial assumptions are not calibrated to a real payments processor.",
        "The fraud scenarios are planted and predictable patterns; real attackers adapt and produce broader behavior.",
        "There is one account per customer and no device, IP, login, chargeback-delay, or real investigator workflow data.",
        "The logistic model is a teaching baseline. There is no production calibration, drift certification, or model validation on real outcomes.",
        "The customer-group outputs are descriptive checks, not fairness certification or causal evidence.",
        "The dashboard shows precomputed scenarios, not a live scoring service or arbitrary threshold experiment.",
        "The assumed challenge stop, review recovery, and customer attrition rates simplify complex behavior and may bias the economic ranking.",
    ]:
        add_bullet(doc, text)
    add_heading(doc, "Governance guardrails", 2)
    add_body(doc, "Keep truth labels and typology names away from model inputs. Build every rolling signal with information available before the current event. Use chronological holdouts for changing behavior. Report more than accuracy: include precision-recall behavior, dollar capture, false declines, customer friction, review capacity, and sensitivity. Treat anomaly signals as investigation leads, not guilt decisions. Any real deployment would need approved data, calibrated economics, accountable human oversight, review and appeal mechanisms, fairness analysis, privacy controls, security review, and business and compliance approval.")
    add_heading(doc, "Roadmap state", 2)
    add_table(doc, ["Area", "Current state", "Reasonable next step"], [
        ("SQL and reporting", "Complete learning prototype.", "Add more investigative queries as hypotheses arise."),
        ("Storage", "SQLite and CSV outputs.", "Benchmark DuckDB plus Parquet before scaling data."),
        ("Models", "Transparent rules and NumPy logistic baseline.", "Compare a tree-based model using the same temporal protocol and costs."),
        ("Signals", "Customer-terminal and channel/authentication context.", "Add simulated device, IP, and login relationships."),
        ("Monitoring", "Daily rolling z-scores and group summaries.", "Evaluate seasonal baselines, stability, and clearer alert operations."),
        ("Dashboard", "Standalone HTML view over saved scenarios.", "Build a richer live threshold simulator or Power BI presentation if useful."),
        ("Deployment", "Portfolio simulation only.", "Do not deploy without real-data governance and production controls."),
    ], [1.3, 2.8, 2.8], font_size=7.8)

    add_heading(doc, "15  Glossary and Reference Map", 1)
    add_table(doc, ["Term", "Meaning in this project"], [
        ("Baseline", "The ordinary synthetic activity or existing simple decision behavior used for comparison."),
        ("Ground truth", "The generator's known record of which synthetic events it planted as fraud."),
        ("Leakage", "Using information that would be unknown at the time a transaction is scored."),
        ("Point-in-time feature", "A feature calculated only from event context available at the current decision time."),
        ("Temporal holdout", "A future block of dates held out to evaluate how a strategy handles later events."),
        ("Precision", "Among events that received an intervention, the share that were planted fraud."),
        ("Recall", "Among planted fraud events, the share that received an intervention."),
        ("PR-AUC", "Area under the precision-recall ranking curve; summarizes rare-event ranking behavior."),
        ("Capture", "Fraud value multiplied by the assumed success fraction of the selected action."),
        ("False decline", "A legitimate event that the strategy declines."),
        ("Review overflow", "A review candidate rerouted to challenge because the daily queue limit was reached."),
        ("Net economic cost", "The sum of modeled losses, unit costs, and margin effects; negative values imply modeled benefit."),
        ("Synthetic", "Generated fictional data used for simulation, not observed customer or company records."),
    ], [1.75, 5.15], font_size=8.0)
    add_heading(doc, "Project files to consult", 2)
    add_table(doc, ["Question", "Start here"], [
        ("What settings produce the data?", "`docs/simulation_assumptions.md` and `src/config.py`."),
        ("How is each fraud typology represented?", "`docs/fraud_scenarios.md` and `src/simulation/inject_fraud.py`."),
        ("What does each field mean?", "`docs/data_dictionary.md`."),
        ("How are actions and costs calculated?", "`docs/decision_policy.md`, `src/decisions/policies.py`, and `src/evaluation/metrics.py`."),
        ("How does each module work?", "`docs/implementation_walkthrough.md` and the `src/` modules."),
        ("What is implemented or deferred?", "`docs/roadmap.md`."),
        ("What did this run find?", "`reports/case_study.md`, `reports/dashboard.html`, and the CSV outputs."),
        ("How do I investigate the database?", "`sql/` and `sql/run_investigation.py`."),
    ], [2.6, 4.3], font_size=8.1)

    add_heading(doc, "Appendix A  Worked Transaction Example", 1)
    add_body(doc, "This example uses invented values to show how one record moves through the pipeline. It is not a row from the published run. Assume a customer's typical spend is $50 and the customer makes a $260 ecommerce purchase at 11:30 p.m. The event uses magstripe authentication, differs from the customer's home region, follows six earlier customer events in 24 hours, arrives at a terminal used by nine distinct customers, and is the customer's first event at that terminal.")
    add_table(doc, ["Signal", "Calculation", "Points"], [
        ("Amount to profile", "$260 ÷ $50 = 5.2; meets at least 3× threshold.", "30"),
        ("Customer velocity", "6 prior events; meets at least 5 threshold.", "25"),
        ("First customer-terminal pair", "Prior pair count is zero.", "15"),
        ("Shared terminal", "9 prior distinct customers; meets at least 8 threshold.", "18"),
        ("Ecommerce/auth/night combination", "Ecommerce + magstripe + night are all true.", "20"),
        ("Night activity", "23:30 is within the configured night hours.", "8"),
        ("Region mismatch", "Merchant region differs from home region.", "12"),
        ("Total", "128 raw points, capped at 100.", "100"),
    ], [2.15, 3.95, 0.8], font_size=8.2)
    add_body(doc, "With the candidate threshold set (0.30, 0.60, 0.90), the 1.00 rule risk would meet the decline threshold. If the event is fraud, modeled decline cost is zero because it prevents the fraud amount and chargeback in this simplified scenario. If it is legitimate, the false-decline cost is 5% × $500 plus the lost 1.1% margin on $260, or $27.86. This example shows why high scores can protect against fraud but still need review of false declines and customer impact.")
    add_body(doc, "The production run does not decide from this example alone. It selects among four threshold sets using historical training outcomes, then applies the selected set to the later holdout. The actual cost depends on the label used only after scoring, the chosen action, the configured assumptions, and the daily review queue.")

    add_heading(doc, "Appendix B  SQL Examples and Interpretation", 1)
    add_body(doc, "The SQL runner executes all six query files against SQLite. The examples below illustrate how an analyst can move from overall volume to a more specific lead. Neither query reads ground-truth labels.")
    add_heading(doc, "Daily event landscape", 2)
    add_code(doc, "SELECT date(Timestamp) AS transaction_date,\n       COUNT(*) AS transaction_count,\n       ROUND(SUM(Amount), 2) AS transaction_value\nFROM transactions\nGROUP BY date(Timestamp)\nORDER BY transaction_date;")
    add_body(doc, "This query establishes the ordinary daily scale and flags dates worth inspecting. A rise may come from the designed crisis period, random variation, or the synthetic injection. It does not identify why volume changed.")
    add_heading(doc, "Endpoint concentration", 2)
    add_code(doc, "SELECT Terminal_ID,\n       COUNT(*) AS transaction_count,\n       COUNT(DISTINCT Customer_ID) AS distinct_customers\nFROM transactions\nGROUP BY Terminal_ID\nORDER BY transaction_count DESC\nLIMIT 20;")
    add_body(doc, "This ranks terminals by activity. A high transaction count may be normal for a popular endpoint. The distinct-customer count adds a second view of concentration; both should be compared with context and time before someone calls the endpoint suspicious.")
    add_heading(doc, "Rapid low-value events", 2)
    add_code(doc, "SELECT Transaction_ID, Timestamp, Customer_ID, Terminal_ID, Amount,\n       Tx_Count_Prior_24h, Customer_Terminal_Prior_Count\nFROM behavior_features\nWHERE Amount <= 5 AND Tx_Count_Prior_24h >= 2\nORDER BY Tx_Count_Prior_24h DESC, Timestamp;")
    add_body(doc, "This query combines low amount and velocity, which is a useful hypothesis for card testing in this simulator. The result is a review list, not a fraud confirmation. An analyst could next check whether the endpoint is shared, when the events happened, and whether authentication context changed.")
    add_body(doc, "`04_amount_deviation.sql` compares each amount with the customer profile. `05_authentication_and_channel.sql` summarizes channel and authentication combinations. `06_network_connections.sql` ranks the full-run endpoint summary. The queries are intentionally small enough to read and modify.")

    add_heading(doc, "Appendix C  Complete Module Reference", 1)
    add_table(doc, ["File or folder", "Responsibility", "Typical reason to open it"], [
        ("src/config.py", "Default seed, counts, start date, and fictional unit economics.", "Change a named assumption used throughout the run."),
        ("src/simulation/generate_customers.py", "Customer profile sampling and the 20-customer seed sample.", "Understand segment, spend, rate, region, and KYC draws."),
        ("src/simulation/generate_world.py", "Accounts, merchants, terminals, familiarity, and baseline events.", "Change ordinary activity generation or entity relationships."),
        ("src/simulation/inject_fraud.py", "Four planted typologies and separate evaluation truth.", "Change injection counts, timings, or signatures."),
        ("src/features/build_features.py", "Ordered event histories and the 12 point-in-time features.", "Inspect event-time safety or add an observable signal."),
        ("src/rules/score_rules.py", "Readable points and reason codes.", "Review or revise transparent signals."),
        ("src/models/logistic_baseline.py", "NumPy model fitting, standardization, and score prediction.", "Inspect model optimization and saved coefficients."),
        ("src/decisions/policies.py", "Thresholds, daily review queue, per-event cost, and strategy metrics.", "Change actions, queue behavior, or cost formulas."),
        ("src/evaluation/metrics.py", "Average precision and action counts.", "Understand rare-event ranking and action summaries."),
        ("src/run_project.py", "End-to-end orchestration, temporal split, and sensitivity work.", "Follow the whole run or add an evaluation output."),
        ("src/storage.py", "Writes CSV outputs and public tables into SQLite.", "Change persistence without changing the generator."),
        ("src/monitoring.py", "Daily observable rates and lagged z-score alerts.", "Modify the operating signal baselines."),
        ("src/network_intelligence.py", "Full-run customer-terminal connectivity summary.", "Extend offline network investigation."),
        ("src/reporting.py", "Generated case study and standalone HTML dashboard.", "Change presentation or dashboard controls."),
        ("sql/*.sql and sql/run_investigation.py", "Six observable investigation queries and their runner.", "Ask or revise a specific SQL question."),
        ("scripts/package_dataset.py", "Splits output CSVs and records checksums in a manifest.", "Prepare a new synthetic run for sharing."),
        ("scripts/assemble_dataset.py", "Rejoins published CSV parts and verifies checksums.", "Restore the repository snapshot locally."),
        ("notebooks/01_investigation.ipynb", "Guided table exploration without early label joins.", "Explore intermediate outputs interactively."),
    ], [2.35, 2.85, 1.7], font_size=7.3)

    add_heading(doc, "Appendix D  Troubleshooting and Next Experiments", 1)
    add_table(doc, ["Symptom", "Likely cause", "What to do"], [
        ("Import cannot find src", "Python was run from a subfolder or as a direct file path.", "Return to the repository root and use `python -m src.run_project`."),
        ("NumPy or pandas is missing", "The active interpreter does not have project dependencies.", "Activate `.venv`, then install `requirements.txt` in that same interpreter."),
        ("SQL runner says database is absent", "No full project run has created the SQLite file at its default path.", "Run `python -m src.run_project` or pass the desired path with `--database`."),
        ("Run stops because fraud is missing in one period", "A short or unusual date horizon did not put examples on both sides of the split.", "Increase `--days`; both training history and holdout need planted examples."),
        ("Restoring snapshot gives a checksum error", "A part is missing, edited, truncated, or from a different manifest.", "Re-fetch all listed parts together; do not edit published parts by hand."),
        ("Dashboard does not reflect a parameter change", "The dashboard uses generated scenario outcomes from the last full run.", "Rerun the pipeline; the browser selector only filters precomputed results."),
        ("An experiment overwrote the last CSVs", "The default run writes into `data/synthetic/run/`.", "Choose a separate `--output-dir` before the next experiment."),
    ], [2.0, 2.35, 2.55], font_size=7.4)
    add_heading(doc, "Suggested next investigations", 2)
    add_number(doc, "Vary fraud prevalence and burst timing, then compare capture, false declines, and PR-AUC on the same chronological protocol.")
    add_number(doc, "Change one unit-cost assumption at a time and identify the values at which the preferred strategy changes.")
    add_number(doc, "Inspect false-decline and review rates by segment, region, and KYC band; investigate small group counts before interpreting rates.")
    add_number(doc, "Add one tree-based baseline and compare it with rules and logistic using the same train dates, future holdout, capacity, and cost model.")
    add_number(doc, "When data size makes SQLite cumbersome, benchmark DuckDB and Parquet on identical tables and queries before migrating storage.")
    add_body(doc, "For a portfolio presentation, lead with the operating problem, show how observable behavior creates signals, explain the holdout result under stated fictional economics, and state why the result does not transfer to a real processor without validation.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
