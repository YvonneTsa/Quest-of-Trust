"""Create a template-derived, step-by-step TrustHold build tutorial."""

from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = Path(r"C:\Users\yvonn\Downloads\TrustHold_Master_Project_Documentation.docx")
OUTPUT = ROOT / "docs" / "TrustHold_Build_Along_Tutorial.docx"
FOOTER_LABEL = "TrustHold | Build Along Technical Tutorial"
CORE_TITLE = "TrustHold Build Along Technical Tutorial"
CORE_SUBJECT = "Step by step guide to building, understanding, and evaluating the TrustHold synthetic fraud decision project"


def body_clear(document):
    body = document._element.body
    section_properties = body.sectPr
    for child in list(body):
        if child is not section_properties:
            body.remove(child)


def add_text(document, text, style=None, keep=False, after=5):
    paragraph = document.add_paragraph(style=style)
    paragraph.paragraph_format.keep_together = keep
    paragraph.paragraph_format.space_after = Pt(after)
    paragraph.add_run(str(text).replace("`", ""))
    return paragraph


def add_heading(document, text, level=1):
    paragraph = document.add_paragraph(style=f"Heading {level}")
    paragraph.paragraph_format.keep_with_next = True
    paragraph.add_run(text)
    return paragraph


def add_bullet(document, text, level=0):
    return add_text(document, text, style="List Bullet" if level == 0 else "List Bullet 2", after=2)


def add_number(document, text):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.left_indent = Inches(0.28)
    paragraph.paragraph_format.first_line_indent = Inches(-0.28)
    paragraph.paragraph_format.space_after = Pt(3)
    paragraph.add_run(f"{number}. {str(text).replace('`', '')}")
    return paragraph


def add_code(document, text):
    lines = text.strip("\n").splitlines()
    for index, line in enumerate(lines):
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.left_indent = Inches(0.20)
        paragraph.paragraph_format.first_line_indent = Inches(0)
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.line_spacing = 1.0
        paragraph.paragraph_format.keep_with_next = index < len(lines) - 1
        paragraph.paragraph_format.keep_together = True
        run = paragraph.add_run(line if line else " ")
        run.font.name = "Consolas"
        run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), "Consolas")
        run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), "Consolas")
        run.font.size = Pt(8.0)
        run.font.color.rgb = RGBColor(35, 48, 58)


def set_cell_text(cell, text, bold=False):
    cell.text = str(text).replace("`", "")
    for paragraph in cell.paragraphs:
        paragraph.paragraph_format.space_after = Pt(1)
        for run in paragraph.runs:
            run.bold = bold
            run.font.size = Pt(8.5)


def add_table(document, headers, rows, widths=None):
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    if widths:
        table.autofit = False
        for col, width in zip(table.columns, widths):
            col.width = Inches(width)
        total_width = round(sum(widths) * 1440)
        table_width = table._tbl.tblPr.find(qn("w:tblW"))
        if table_width is None:
            table_width = OxmlElement("w:tblW")
            table._tbl.tblPr.append(table_width)
        table_width.set(qn("w:w"), str(total_width))
        table_width.set(qn("w:type"), "dxa")
    for i, label in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], label, bold=True)
    header_properties = table.rows[0]._tr.get_or_add_trPr()
    repeated_header = OxmlElement("w:tblHeader")
    repeated_header.set(qn("w:val"), "true")
    header_properties.append(repeated_header)
    for values in rows:
        cells = table.add_row().cells
        for i, value in enumerate(values):
            set_cell_text(cells[i], value)
    if widths:
        for row in table.rows:
            for i, (cell, width) in enumerate(zip(row.cells, widths)):
                cell.width = Inches(width)
                cell_width = cell._tc.get_or_add_tcPr().find(qn("w:tcW"))
                if cell_width is None:
                    cell_width = OxmlElement("w:tcW")
                    cell._tc.get_or_add_tcPr().append(cell_width)
                cell_width.set(qn("w:w"), str(round(width * 1440)))
                cell_width.set(qn("w:type"), "dxa")
    for row in table.rows:
        trpr = row._tr.get_or_add_trPr()
        trpr.append(OxmlElement("w:cantSplit"))
    document.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def readable_name(name):
    """Turn a Python identifier into words for a line-by-line explanation."""
    import re

    return re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name).replace("_", " ").strip()


def explain_source_line(line, prior_line, next_line, path):
    """Give every literal source line a syntax-aware teaching note."""
    import ast
    import re

    s = line.strip()
    if not s:
        return "Blank line: it separates adjacent statements or blocks so the reader can see the program's structure."
    if path.endswith("requirements.txt") and s and not s.startswith("#"):
        package, _, minimum = s.partition(">=")
        return f"Dependency declaration: asks pip to install `{package}` at version `{minimum}` or newer. This makes the package needed by the project available in the active virtual environment."
    if s.startswith("#"):
        return "Comment: it records the author's intent for a person reading the code; Python does not execute this line."
    if s.startswith(('"""', "'''")):
        return "Docstring text: Python stores this human-readable description on the module, class, or function immediately above it."
    if s in ("(", ")", "]", "},", "):", "...):") or s.startswith(("(", "[")) and s.endswith((",", ")")):
        return "Continuation or closing delimiter: it groups the expression started on a nearby line. The indentation and matching bracket show which call, list, tuple, or dictionary this belongs to."
    if s.startswith("import ") or s.startswith("from "):
        return f"Import: makes {s.removeprefix('import ').removeprefix('from ').split()[0]} available in this file. The imported helper is used by later code in this module; imports do not run the project pipeline by themselves."
    if s.startswith("def ") or s.startswith("async def "):
        m = re.match(r"(?:async )?def\s+(\w+)\((.*)\)", s)
        if m:
            name, params = m.groups()
            params = params or "no explicit parameters"
            return f"Function definition: starts `{name}`. Its inputs are `{params}`; the indented body below runs when another part of the program calls it."
        return "Function definition: names a reusable block of work; the indented lines below form its body."
    if s.startswith("class "):
        name = s.split()[1].split("(")[0].rstrip(":")
        return f"Class definition: introduces `{name}`, a type that groups related behavior and state for the rest of this module."
    if s.startswith("@"):
        return f"Decorator `{s}`: modifies or registers the function/class defined immediately below it."
    if s.startswith("if ") or s.startswith("elif ") or s.startswith("while "):
        condition = s.split(None, 1)[1].rstrip(":")
        return f"Conditional: tests `{condition}`. Python runs the indented block only while this condition is true; comparison operators (`==`, `>=`, `<`) and boolean operators (`and`, `or`) combine the checks."
    if s.startswith("else:") or s.startswith("finally:"):
        return "Branch boundary: this starts the alternate/finally block paired with the preceding conditional or try statement."
    if s.startswith("for "):
        body = s[4:].rstrip(":")
        return f"Loop: iterates `{body}` one item at a time. Each indented statement runs once for each value yielded by the iterable."
    if s.startswith("with "):
        return f"Managed-resource block: `{s[5:].rstrip(':')}` is entered, and Python automatically closes/releases the resource when the indented block ends, including after an error."
    if s.startswith("try:") or s.startswith("except"):
        return f"Error-handling boundary: `{s}` selects code that catches or handles a failure instead of letting it pass silently."
    if s.startswith("return"):
        value = s.removeprefix("return").strip()
        return "Return: ends this function and hands its result back to the caller" + (f"; the returned expression is `{value}`." if value else ".")
    if s.startswith("raise "):
        return f"Raises `{s.removeprefix('raise ')}` to stop this operation with an explicit error; this prevents invalid inputs from being mistaken for successful results."
    if s.startswith("assert "):
        return f"Assertion: checks `{s.removeprefix('assert ')}` and stops with an error if the claimed invariant is false."
    if s.startswith("yield"):
        return f"Yield: exposes `{s.removeprefix('yield').strip()}` as the next value from this generator without ending the function."
    if s.startswith("nonlocal "):
        return f"Scope declaration: `{s.removeprefix('nonlocal ')}` refers to a variable in the nearest enclosing function, so assignment updates that shared value."
    if s.startswith("return"):
        return "Returns the computed value to the calling function."
    if s.startswith("elif "):
        return "Checks an additional condition only when the previous `if`/`elif` conditions were false."
    if s in ("pass", "continue", "break"):
        return {"pass": "Placeholder statement; it intentionally does nothing.", "continue": "Skips to the next loop item.", "break": "Exits the nearest loop."}[s]
    if " = " in s or s.startswith(("self.", "frame[", "daily[", "out[", "scored[", "metrics[", "costs.", "manifest[", "parser.")):
        left, sep, right = s.partition(" = ")
        if sep:
            target = left.strip()
            rhs = right.strip()
            rhs_short = rhs[:180]
            target_words = readable_name(target.replace("self.", "").strip("[]\"'"))
            operation = "creates or updates"
            if target.startswith("self."):
                operation = "stores on this object"
            return f"Assignment: {operation} `{target}` ({target_words}) using `{rhs_short}`. Read the right side as the recipe and the left side as the name/column that receives its result."
    if s.startswith("return"):
        return "Returns the result from this function."
    if s.endswith(":"):
        return f"Starts a nested Python block: `{s[:-1]}` determines whether/when the following indented statements execute."
    if path.endswith(".sql"):
        keyword = s.split()[0].upper()
        return {
            "SELECT": "SQL projection: names the output columns or calculations returned for each result row.",
            "FROM": "SQL source: chooses the input table/view from which rows are read.",
            "WHERE": "SQL row filter: keeps only records satisfying the stated condition before aggregation.",
            "GROUP": "SQL aggregation boundary: combines rows sharing the listed key(s), allowing COUNT/SUM/AVG to summarize them.",
            "ORDER": "SQL sort: orders the final result so the most useful rows appear first.",
            "LIMIT": "SQL row cap: restricts how many result rows are returned.",
        }.get(keyword, "SQL clause/expression: contributes a selected field, calculation, filter, grouping key, or sort key to the query being assembled.")
    return f"Expression: this line contributes `{s[:180]}` to the current block. Follow its indentation to see which function/loop/condition owns it; names and punctuation refer to the variables and operations introduced nearby."


def add_annotated_source(document, path, display_name):
    """Print exact lines from one repository file and explain each line."""
    import json

    full_path = ROOT / path
    if not full_path.is_file():
        return
    add_heading(document, display_name, 2)
    add_text(document, f"Source of truth: `{path}`. The code text below is read directly from the project file when this tutorial is built, so line numbers and examples stay aligned with the implementation. Every physical line is represented. Comments and blank lines are included so the listing matches the editor exactly.")
    if full_path.suffix == ".ipynb":
        notebook = json.loads(full_path.read_text(encoding="utf-8"))
        entries = []
        for cell_index, cell in enumerate(notebook.get("cells", []), 1):
            if cell.get("cell_type") == "code":
                source = "".join(cell.get("source", []))
                for code_line, line in enumerate(source.splitlines(), 1):
                    entries.append((f"Cell {cell_index}, line {code_line}", line))
    else:
        lines = full_path.read_text(encoding="utf-8").splitlines()
        entries = [(f"Line {i:03}", line) for i, line in enumerate(lines, 1)]
    rows = []
    for idx, (label, line) in enumerate(entries):
        prior = entries[idx - 1][1] if idx else ""
        following = entries[idx + 1][1] if idx + 1 < len(entries) else ""
        note = explain_source_line(line, prior, following, str(full_path))
        rows.append((f"{label}\n{line if line else ' '}", note))
    add_table(document, ["Exact source line", "What this line teaches / does"], rows, [2.8, 4.2])


def add_deep_course(document):
    """Expand the overview into executable lessons and exhaustive code annotations."""
    add_heading(document, "The complete build, one decision at a time", 1)
    add_text(document, "This section is the hands-on route from an empty project folder to a reviewed result. The code appendix later reproduces every line of the active Python modules, SQL files, packaging scripts, investigation runner, and notebook code. Use it as a companion while you work through these steps in order.")
    add_heading(document, "Lesson 0 — Know the tools before building", 2)
    add_table(document, ["Tool", "What it does here", "Where you use it"], [
        ("File Explorer", "Shows the project folders and generated files.", "Confirm the repository contains `src`, `sql`, `data`, `docs`, and `reports`."),
        ("VS Code", "Editor for reading and changing `.py`, `.sql`, `.md`, and `.ipynb` files.", "Open the project folder; select Python interpreter `.venv`."),
        ("PowerShell terminal", "Runs commands with the project as the working directory.", "Create the environment, install packages, run modules and inspect files."),
        ("Python", "Executes the pipeline and helper scripts.", "`python -m ...` uses the selected interpreter and package context."),
        ("NumPy", "Seeded random draws, arrays and the logistic math.", "Simulation and the baseline model."),
        ("pandas", "Labeled tables, joins, groups, CSV IO and rolling summaries.", "Feature, decision, evaluation and persistence steps."),
        ("SQLite", "Single local database file with SQL tables.", "Inspect generated observable tables without running a server."),
        ("SQL", "Declarative queries over saved tables.", "`sql/*.sql` and the investigation runner."),
        ("Jupyter", "Runs the notebook cells interactively and displays tables/plots.", "Open `notebooks/01_investigation.ipynb` after data exists."),
        ("Git", "Records changes in local history.", "Inspect state before staging/committing; the remote is a separate destination."),
        ("Microsoft Word", "Displays the roadmap and this tutorial as paginated manuals.", "Use the provided `.docx`; source code remains in the repository."),
    ], [1.25, 2.65, 3.1])
    add_heading(document, "Lesson 1 — Start from a clean folder", 2)
    add_text(document, "When building a project from scratch, create the project root first and make it the terminal's current directory. In this existing repository, the root is already open; use `Get-Location` to prove where a command will write files. A wrong working directory is a common source of ‘file not found’ errors.")
    add_code(document, """
Get-Location
Get-ChildItem -Name
python --version
git status --short
""")
    add_text(document, "`Get-Location` prints the current folder. `Get-ChildItem -Name` lists only its immediate children. `python --version` tells you which interpreter answers the command. `git status --short` is a read-only snapshot of tracked/untracked changes. Confirm you see the project root and the source folders before continuing.")
    add_heading(document, "Lesson 2 — Create and select the Python environment", 2)
    add_code(document, """
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python -m pip show numpy pandas
""")
    add_text(document, "The first command asks the chosen Python interpreter to create an isolated environment at `.venv`. Activation changes this PowerShell session's PATH so `python` and `pip` resolve to that environment. The install command reads exact dependency names/ranges from `requirements.txt`; the last command verifies the installed package metadata. If PowerShell blocks activation, VS Code may use the interpreter directly at `.venv\\Scripts\\python.exe`; do not change global execution policy just for this project.")
    add_heading(document, "Lesson 3 — Understand the run command", 2)
    add_code(document, """
python -m src.run_project --help
python -m src.run_project --customers 2000 --days 60 --merchants 800 --terminals 1200 --review-capacity 250 --fraud-campaigns 10 --stability-runs 10 --output-dir data/synthetic/tutorial_run
""")
    add_text(document, "`-m` tells Python to locate and execute the named module from the repository. The flags are parsed by `argparse`: counts set simulation size, review capacity limits the daily queue, and `--output-dir` chooses where CSV and SQLite outputs are written. The separate tutorial output directory prevents accidental replacement of the standard run. Read the console step markers in order, then check the named output directory in Explorer.")
    add_heading(document, "Lesson 4 — Build the world and define the row grains", 2)
    add_text(document, "A table's grain is what one row means. The generator builds customer, account, merchant, and terminal entity tables before transaction events. IDs are keys: a customer ID should identify one customer row, while many transactions can reuse that customer ID. An event's terminal links to its merchant. This lets SQL aggregate events by endpoint and return to owner context.")
    add_table(document, ["Table", "One row means", "Key relationship"], [
        ("customers", "one fictional cardholder", "Customer_ID primary key"),
        ("accounts", "one fictional payment account", "Customer_ID points to customers"),
        ("merchants", "one fictional merchant", "Merchant_ID primary key"),
        ("terminals", "one payment endpoint", "Merchant_ID points to merchants"),
        ("transactions", "one payment attempt/event", "Customer, account, merchant and terminal IDs reference entities"),
    ], [1.4, 2.3, 3.3])
    add_code(document, """
python -c "import pandas as pd; p='data/synthetic/tutorial_run'; print(pd.read_csv(p+'/customers.csv').head(3).to_string(index=False)); print(pd.read_csv(p+'/transactions.csv').shape)"
""")
    add_text(document, "This one-line check loads the customer CSV, prints three records, then prints the transaction table's `(rows, columns)` shape. `-c` executes a short Python statement directly; do not paste this command inside a `.py` file. Read the IDs, types, timestamp, amount, channel, and authentication fields before treating a row as an abstract model input.")
    add_heading(document, "Lesson 5 — Generate ordinary events and then fraud events", 2)
    add_text(document, "Ordinary event generation samples a daily count from a Poisson distribution using each customer's latent rate. The event timestamp is a day plus a random second; amount is positive and skewed; channel and authentication are sampled from configured categories. Fraud injection then adds four scripted patterns. Its private truth table is an answer key, not an observable transaction field.")
    add_table(document, ["Pattern", "What is planted", "Signal idea"], [
        ("Compromised terminal", "Two bursts of events at an endpoint with unusual customer sharing.", "Endpoint concentration / new customer-terminal links."),
        ("Card testing", "Many small attempts clustered in short sequences.", "Low amount plus prior velocity."),
        ("Credential compromise", "Events differ from account-holder context.", "Amount, time and region mismatch features."),
        ("Account takeover", "Short activity burst after the simulated crisis date.", "Velocity, endpoint novelty and authentication changes."),
    ], [1.65, 2.8, 2.55])
    add_text(document, "Never add `Typology`, `Fraud_Label`, or `fraud_ground_truth.csv` to the predictor columns. The correct sequence is: create observable transaction behavior, calculate features, then join the answer key only into the separate training/evaluation frame. A random split could put closely related events on both sides; the project instead reserves the later dates.")
    add_heading(document, "Lesson 6 — Reconstruct one rolling feature by hand", 2)
    add_text(document, "For `Tx_Count_Prior_24h`, choose one customer and sort their transactions by timestamp. For a current event at time t, set cutoff = t minus 24 hours. Count only that customer's already-seen rows with timestamp at or after cutoff and strictly earlier than t. The current row must not count itself. The code removes old events before reading the deque length, writes that count, and appends the current timestamp afterward. This order is the point-in-time guarantee.")
    add_code(document, """
python -c "import pandas as pd; p='data/synthetic/tutorial_run/behavior_features.csv'; d=pd.read_csv(p); cols=['Timestamp','Customer_ID','Tx_Count_Prior_24h','Terminal_Prior_Tx_Count','Customer_Terminal_Prior_Count']; print(d[cols].head(12).to_string(index=False))"
""")
    add_text(document, "Inspect a short slice and manually verify that the first event for a customer has zero prior customer activity and a first-time customer-terminal pair has count zero. A feature computed with the current row already appended would create look-ahead leakage.")
    add_heading(document, "Lesson 7 — Explain a rules score and the model", 2)
    add_text(document, "Rules add visible points when conditions hold; overlapping rules can intentionally accumulate. A score is clipped at 100 and each triggered rule contributes a reason string. The logistic baseline converts the same allow-listed feature columns to standardized numbers, then repeats a gradient update for 1,200 epochs. It gives more weight to positive examples because planted fraud is rare. Fit uses the earlier period only; predict transforms future rows using the training mean and standard deviation, never future-fitted scaling.")
    add_text(document, "Inspect `Rule_Score`, `Rule_Reasons`, `Model_Score` and `Hybrid_Score` together for a few rows. A score is not a decision: thresholds and a capacity-aware queue determine the eventual action. A coefficient sign describes direction conditional on the model's correlated inputs; it is not proof of causation.")
    add_heading(document, "Lesson 8 — Turn a score into actions and a queue", 2)
    add_text(document, "The chosen tuple supplies challenge, review and decline cutoffs. The code assigns APPROVE first, then overwrites with successively higher-severity bands. Each date's REVIEW cases are sorted from highest score downward; rows after daily capacity spill into CHALLENGE. This represents a real operational constraint: a policy cannot promise a human review to more cases than staff can handle.")
    add_text(document, "Threshold search compares a short, predeclared candidate list on training history using the fictional cost function. The future holdout is not used to select thresholds. This distinction protects the holdout from tuning leakage, though the candidate list and synthetic assumptions still constrain what conclusions can be drawn.")
    add_heading(document, "Lesson 9 — Translate the outcome into business language", 2)
    add_table(document, ["Metric", "Meaning", "Decision implication"], [
        ("Fraud value captured %", "Estimated fraction stopped/recovered under action-effectiveness assumptions.", "Higher may reduce loss, but depends on challenge/review success assumptions."),
        ("False declines", "Legitimate events sent to DECLINE.", "Direct risk of customer harm and lost relationship value."),
        ("Review overflow", "Review candidates that exceed daily capacity.", "Shows a strategy is demanding more labor than available."),
        ("PR-AUC / average precision", "Ranking quality across thresholds for a rare positive class.", "Useful for ranking; it does not choose operating actions or measure dollars."),
        ("Net Economic Cost", "Sum of modeled event costs, with approved legitimate margin as a negative cost.", "Lower is better only under the stated synthetic assumptions."),
    ], [1.7, 2.9, 2.4])
    add_text(document, "In the default seed, the later holdout includes 74,237 transactions and 350 simulated fraud cases. Under the base fictional economics and 250-case daily review capacity, Logistic captures 78.37% of fraud value, has one false decline, and modeled net cost −$73,729.50. This is one synthetic run, not observed profit, verified savings, or a forecast for a real processor. The multi-seed comparison later in the tutorial shows variation across 30 generated books.")
    add_text(document, "PR-AUC is not applicable for the Incumbent because it has no continuous ranking score. The current pipeline leaves that metric blank rather than copying the Rules score. This illustrates a general rule: only report a ranking metric when the strategy actually produces a ranking score.")
    add_table(document, ["Strategy", "Fraud value captured · mean (range)", "Good payments declined · median (range)", "Good payments challenged · median (range)", "Good payments reviewed · median (range)", "Modeled net cost · median (range)"], [
        ("Rules", "73.73% (68.29–81.25%)", "31 (19–52)", "5,139 (4,552–5,764)", "126 (88–155)", "−$52,948 (−$58,036 to −$47,036)"),
        ("Logistic", "77.51% (69.76–87.21%)", "0 (0–2)", "598.5 (181–930)", "19 (7–37)", "−$68,082 (−$73,730 to −$60,293)"),
    ], [0.75, 1.15, 1.05, 1.2, 1.0, 1.75])
    add_text(document, "Across 30 seeds, Logistic had lower modeled net cost in 30/30 comparisons. Its paired median cost difference was −$15,501.82 per holdout, with an observed range from −$22,482.27 to −$11,207.82. The median fraud-value-capture lift was 3.66 percentage points (range −1.86 to +14.31), so the lift was not positive in every run. Logistic challenged a median 4,463.5 fewer good payments (range 3,988–5,342 fewer), reviewed 108 fewer (65–138 fewer), and declined 31 fewer (19–51 fewer). These observed seed ranges describe variation inside the same synthetic design; they are not confidence intervals or evidence of real-world performance.")
    add_heading(document, "Lesson 10 — Investigate with SQL and SQLite", 2)
    add_code(document, """
python sql/run_investigation.py
""")
    add_text(document, "The runner opens the local SQLite database, reads each `.sql` file, executes it, prints returned column names and at most 12 result rows, then prints the shown/total count. The six queries describe daily landscape, endpoint concentration, rapid low-value activity, amount deviations, authentication/channel patterns, and endpoint network summaries. They intentionally avoid the answer key. A high count, unusual amount, or shared endpoint is a lead to investigate—not a fraud label.")
    add_heading(document, "Lesson 11 — Review monitoring and sensitivity", 2)
    add_text(document, "Daily monitoring aggregates transaction volume, value, average amount, soft-decline rate and high-score rate. For each day, its comparison baseline shifts the series by one day and rolls over up to the previous 14 days, with at least seven observations. A three-standard-deviation flag is a simple alerting demonstration, not a calibrated production control. Early dates have insufficient history; a zero standard deviation becomes missing rather than infinite.")
    add_text(document, "Capacity sensitivity changes the maximum review queue to 10, 50, 150, 250 and 500 cases per day. Economic sensitivity holds decisions fixed while challenge-stop, review-recovery and attrition assumptions vary. These answer two distinct questions: ‘What if staffing changes?’ and ‘What if our unit economics assumptions are wrong?’ Do not conflate the two.")
    add_heading(document, "Lesson 12 — Rebuild, package, and verify", 2)
    add_code(document, """
python -m src.run_project
python -m scripts.package_dataset
python -m scripts.assemble_dataset --source data/synthetic/published_run --destination data/synthetic/restored_check
python -m src.run_project --output-dir data/synthetic/restored_check_run
python sql/run_investigation.py --database data/synthetic/restored_check_run/trusthold.sqlite
""")
    add_text(document, "The packaging script splits generated CSV tables into size-bounded parts and records a manifest with row counts and SHA-256 checksums. Assembly joins parts, checks each reconstructed CSV against its checksum, and moves the truth file into a restricted subfolder. The final two commands create a fresh local SQLite database from a new run and execute SQL against that explicit database path. A successful reconstruction means the snapshot contents match the recorded bytes; it does not prove the synthetic assumptions are realistic.")
    add_heading(document, "Lesson 13 — Use Git safely and publish deliberately", 2)
    add_code(document, """
git status --short
git diff -- README.md src/config.py
git remote -v
git branch --show-current
""")
    add_text(document, "These commands inspect; they do not commit or push. Before publishing changes, inspect ignored files and verify the local truth file and SQLite file stay excluded by `.gitignore`. Then stage specific reviewed files, inspect `git diff --cached`, create a commit, and push only after verifying the destination and branch. GitHub is the remote host; Git is the local version-control tool. Do not infer that code is already on GitHub from a remote's presence.")
    add_heading(document, "What can be improved next—and how to choose", 2)
    add_text(document, "The next meaningful step is not automatically a more complex model. First correct the incumbent PR-AUC row and rerun the generated report; then test feature leakage and threshold behavior; then add empirical calibration only if real representative data becomes available. Add devices/IP/login signals only when the simulator supplies those events and their timestamps. Consider DuckDB/Parquet only after a measured query/runtime or sharing requirement makes SQLite/CSV insufficient. The current database is a good local prototype because it is serverless, built into Python, and easy to inspect.")
    add_heading(document, "Appendix D — Exact code, explained line by line", 1)
    add_text(document, "The listings that follow are generated from the project files, with every source line paired to an explanation. Read them in pipeline order. A line number identifies the current repository file at tutorial-generation time. If you edit that file, the number may move; rebuild this guide to refresh the listing.")
    sources = [
        ("requirements.txt", "D0. Python dependencies"),
        ("src/__init__.py", "D0a. Top-level Python package marker"),
        ("src/simulation/__init__.py", "D0b. Simulation package marker"),
        ("src/features/__init__.py", "D0c. Feature package marker"),
        ("src/rules/__init__.py", "D0d. Rules package marker"),
        ("src/models/__init__.py", "D0e. Model package marker"),
        ("src/decisions/__init__.py", "D0f. Decision package marker"),
        ("src/evaluation/__init__.py", "D0g. Evaluation package marker"),
        ("src/config.py", "D1. Configuration and economics"),
        ("src/simulation/generate_customers.py", "D2. Customer generator"),
        ("src/simulation/generate_world.py", "D3. Entity and legitimate-event generator"),
        ("src/simulation/inject_fraud.py", "D4. Fraud scenario injection and truth isolation"),
        ("src/features/build_features.py", "D5. Point-in-time features"),
        ("src/rules/score_rules.py", "D6. Explainable rules"),
        ("src/models/logistic_baseline.py", "D7. NumPy logistic regression"),
        ("src/decisions/policies.py", "D8. Thresholds, actions, capacity, costs"),
        ("src/evaluation/metrics.py", "D9. Ranking and action metrics"),
        ("src/run_project.py", "D10. End-to-end orchestration"),
        ("src/monitoring.py", "D11. Label-free monitoring"),
        ("src/network_intelligence.py", "D12. Endpoint network summary"),
        ("src/storage.py", "D13. CSV and SQLite persistence"),
        ("src/reporting.py", "D14. Generated report and dashboard"),
        ("sql/run_investigation.py", "D15. SQL investigation runner"),
        ("sql/01_daily_landscape.sql", "D16. Daily landscape query"),
        ("sql/02_terminal_concentration.sql", "D17. Endpoint concentration query"),
        ("sql/03_velocity_and_testing.sql", "D18. Velocity query"),
        ("sql/04_amount_deviation.sql", "D19. Amount deviation query"),
        ("sql/05_authentication_and_channel.sql", "D20. Authentication/channel query"),
        ("sql/06_network_connections.sql", "D21. Network query"),
        ("scripts/package_dataset.py", "D22. Snapshot packager"),
        ("scripts/assemble_dataset.py", "D23. Snapshot assembler and checksum verifier"),
        ("notebooks/01_investigation.ipynb", "D24. Notebook code cells"),
    ]
    for path, label in sources:
        add_annotated_source(document, path, label)
    add_heading(document, "Appendix E — Data dictionary and evidence map", 1)
    add_text(document, "For exact column descriptions, use `docs/data_dictionary.md`; for population distributions and dollar assumptions, use `docs/simulation_assumptions.md`; for each planted sequence, use `docs/fraud_scenarios.md`; for leakage controls and evaluation protocol, use `docs/model_governance.md`; for the original project stage mapping, use `docs/roadmap.md`. These documents are the local evidence behind this tutorial. No external benchmark has been used to convert the fictional findings into a business forecast.")


def add_lesson(document, purpose, location, do, terms, inspect, business):
    add_heading(document, "What you are building", 2)
    add_text(document, purpose)
    add_heading(document, "Files to open", 2)
    add_text(document, location)
    add_heading(document, "Build it", 2)
    for index, step in enumerate(do, 1):
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.left_indent = Inches(0.28)
        paragraph.paragraph_format.first_line_indent = Inches(-0.28)
        paragraph.paragraph_format.space_after = Pt(3)
        paragraph.add_run(f"{index}. {str(step).replace('`', '')}")
    add_heading(document, "Read the code", 2)
    for term in terms:
        add_bullet(document, term)
    add_heading(document, "Check your work", 2)
    for item in inspect:
        add_bullet(document, item)
    add_heading(document, "Why the business should care", 2)
    add_text(document, business)


def update_footer(document):
    paragraph = document.sections[0].footer.paragraphs[0]
    if paragraph.runs:
        paragraph.runs[0].text = FOOTER_LABEL
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.add_run(FOOTER_LABEL)


def update_core_properties(document):
    document.core_properties.title = CORE_TITLE
    document.core_properties.subject = CORE_SUBJECT
    document.core_properties.keywords = "TrustHold, fraud analytics, build along, Python, SQLite, decision strategy"


def replace_package_parts(generated_docx, output_docx):
    """Keep the source package intact outside its intended content and footer slots."""
    replacements = {"word/document.xml", "word/footer1.xml", "docProps/core.xml"}
    with ZipFile(TEMPLATE, "r") as source, ZipFile(generated_docx, "r") as generated:
        changed = {name: generated.read(name) for name in replacements}
        with ZipFile(output_docx, "w", ZIP_DEFLATED) as output:
            for item in source.infolist():
                output.writestr(item, changed.get(item.filename, source.read(item.filename)))


def build():
    if not TEMPLATE.is_file():
        raise FileNotFoundError(f"Reference template not found: {TEMPLATE}")
    document = Document(TEMPLATE)
    body_clear(document)
    update_footer(document)
    update_core_properties(document)

    title = document.add_paragraph(style="Title")
    title.add_run("TrustHold Build Along Technical Tutorial")
    subtitle = add_text(document, "A step by step course for building the fraud decision project", keep=True)
    subtitle.runs[0].bold = True
    add_text(document, "This tutorial teaches the project from the first reproducible customer profile through the final business decision, SQL investigations, monitoring, and portfolio outputs. It follows the supplied master roadmap’s progression and uses the repository’s real modules, data, assumptions, and generated result tables as its teaching material.")
    add_text(document, "The learning cycle repeats throughout: understand the business question, read the relevant code, run one step, inspect its output, explain the result in plain language, and only then add the next layer.")
    add_text(document, "All customers, transactions, outcomes, costs, and findings described here are synthetic. Dollar figures explain how the simulator works; they are not estimates of a real processor’s economics.")

    add_heading(document, "How to use this tutorial", 2)
    add_text(document, "Work in the repository root in VS Code. Keep one terminal open in PowerShell and keep the named Python files open in the editor. A command belongs in the terminal; Python statements belong in a .py file or a Python prompt. Each lesson identifies the code to read, the order to follow, what the outputs should mean, and a checkpoint before proceeding.")
    add_table(document, ["Mark", "Meaning"], [
        ("Build", "A practical action to take in the existing project."),
        ("Inspect", "A concrete output to open or query before moving forward."),
        ("Business meaning", "How the technical output informs a payment decision."),
        ("Guardrail", "A limitation that prevents an incorrect conclusion."),
    ], [1.2, 5.8])
    add_heading(document, "Contents", 2)
    for label in [
        "1. Start with the decision problem", "2. Understand the repository and pipeline", "3. Set up the environment and reproduce a run",
        "4. Build customers and linked payment entities", "5. Simulate legitimate transactions", "6. Inject fraud while protecting ground truth",
        "7. Investigate events with SQL and SQLite", "8. Build point in time behavior features", "9. Create an explainable rules score",
        "10. Fit a time aware logistic baseline", "11. Turn scores into actions under capacity", "12. Measure business outcomes and stress assumptions",
        "13. Add network intelligence and monitoring", "14. Produce the case study and dashboard", "15. Explain the current findings correctly",
        "16. Package, verify, and extend the project", "Appendix A. Code reading map", "Appendix B. Project table and output guide",
        "Appendix C. Glossary, checkpoints, and practice exercises",
        "Complete build course: tools, commands, pipeline, findings, and business interpretation",
        "Appendix D. Exact source lines paired with explanations",
        "Appendix E. Data dictionary and evidence map",
    ]:
        add_bullet(document, label)

    add_heading(document, "1. Start with the decision problem", 1)
    add_text(document, "TrustHold asks: when should a payments business approve, challenge, review, or decline a transaction? The central job is not simply to predict whether a row is fraudulent. It is to choose actions that balance fraud loss, customer friction, payment margin, and the limited number of cases investigators can review.")
    add_table(document, ["Decision", "Operational meaning", "Typical trade off"], [
        ("APPROVE", "Let the payment proceed.", "Preserves convenience and margin; fraud may be lost."),
        ("CHALLENGE", "Ask for additional verification.", "Can stop some fraud; adds friction and per-event cost."),
        ("REVIEW", "Send the case to a human queue.", "May recover more fraud; costs time and is capacity limited."),
        ("DECLINE", "Stop the payment immediately.", "Prevents the modeled fraud loss; a legitimate customer may be lost."),
    ], [1.0, 2.5, 3.5])
    add_text(document, "A risk score is an intermediate signal. The strategy layer maps it into an action, and the economics layer measures what that action costs under explicit assumptions. This is why an accuracy score alone cannot answer the project question.")
    add_heading(document, "The learning protocol", 2)
    for index, item in enumerate([
        "State the business question before writing code.",
        "Define the grain: what does one row represent? Name identifiers and timing.",
        "Read and explain each new Python, SQL, or PowerShell construct before using it.",
        "Run a small, reproducible example and inspect rows manually.",
        "Compare output with the expected behavior and record assumptions.",
        "Connect the result to customer impact, operational capacity, and economics.",
        "Scale only after the small case behaves as expected.",
    ], 1):
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.left_indent = Inches(0.28)
        paragraph.paragraph_format.first_line_indent = Inches(-0.28)
        paragraph.paragraph_format.space_after = Pt(3)
        paragraph.add_run(f"{index}. {item}")

    add_heading(document, "2. Understand the repository and pipeline", 1)
    add_text(document, "The project is organized as a sequence of modules rather than one giant script. `src/run_project.py` orchestrates those modules. Each module owns a clear responsibility, so a generator can change without silently changing the cost formula or report writer.")
    add_code(document, """
src/
  config.py                    assumptions and default sizes
  simulation/                  customers, entities, ordinary activity, fraud injection
  features/build_features.py   timestamp-safe behavioral measures
  rules/score_rules.py         visible risk points and reason codes
  models/logistic_baseline.py  NumPy logistic model
  decisions/policies.py       actions, review queue, and unit costs
  evaluation/metrics.py        PR-AUC and action counts
  monitoring.py                daily observable rates and alerts
  network_intelligence.py     terminal/customer connectivity summary
  storage.py                   CSV and SQLite persistence
  reporting.py                 Markdown case study and HTML dashboard
  run_project.py               end-to-end orchestration
sql/                           six SQLite investigations and a runner
data/synthetic/published_run/ versioned, checksum-listed CSV snapshot
data/synthetic/run/           regenerated local outputs and SQLite file
docs/                          assumptions, scenarios, field definitions, roadmap
reports/                       case study and standalone dashboard
notebooks/                     guided investigation after dataset assembly
""")
    add_table(document, ["Pipeline stage", "Input", "Output", "Question answered"], [
        ("Simulation", "Settings and random seed", "Entities, baseline events, planted fraud", "What synthetic world are we evaluating?"),
        ("Feature engineering", "Observable event history", "Point in time feature rows", "What was knowable at this event?"),
        ("Detection", "Features and training labels", "Rule and model risk scores", "Which events deserve attention?"),
        ("Decision policy", "Risk score, thresholds, capacity", "Four actions and overflow flags", "What should operations do?"),
        ("Evaluation", "Holdout actions plus offline truth", "Capture, friction, cost, and sensitivity", "Which strategy works under these assumptions?"),
        ("Delivery", "Tables and summary measures", "SQLite, CSV, report, dashboard", "Can another person inspect and reproduce it?"),
    ], [1.25, 1.7, 1.9, 2.15])

    add_heading(document, "3. Set up the environment and reproduce a run", 1)
    add_lesson(document,
        "A reproducible environment lets you distinguish a code change from a dependency or configuration change. The repository needs NumPy and pandas for the first build; SQLite is provided by Python.",
        "Open `README.md`, `requirements.txt`, `src/config.py`, and `src/run_project.py`.",
        [
            "Open the repository folder in VS Code. Confirm the terminal starts in the folder containing `src/`, `sql/`, and `README.md`.",
            "Create an isolated virtual environment with `python -m venv .venv`, then activate it in PowerShell with `.\\.venv\\Scripts\\Activate.ps1`.",
            "Install only declared dependencies with `python -m pip install -r requirements.txt`.",
            "For a learning run, execute `python -m src.run_project --customers 20 --days 30 --output-dir data/synthetic/tutorial_run`. Use a separate output folder so you do not overwrite the default run.",
            "After the small run succeeds, run the default with `python -m src.run_project` to regenerate the main output set.",
        ],
        ["`python -m` runs a module within the current interpreter and makes package imports predictable from the repository root.", "A virtual environment is an isolated package directory for this project; it is not a separate Python installation.", "The seed is fixed in `src/config.py`. A fixed seed reproduces pseudo-random draws when code and parameters remain fixed.", "The command-line parser exposes population, days, merchant/terminal counts, review capacity, and output path."],
        ["Read the final console summary: held-out strategy metrics, SQLite path, train/test date boundary, and the label-isolation message.", "Check that `data/synthetic/tutorial_run/` contains CSV outputs, `trusthold.sqlite`, and a restricted subfolder for the truth file.", "The 20-customer walkthrough may be too short for the fixed fraud schedule and the temporal split. If it stops because one period has no planted fraud, use the default run or increase the horizon; this is a data design requirement, not a broken package install."],
        "The environment is part of the evidence chain. Reproducible settings make changes interpretable and let a reviewer recreate results without relying on a long sequence of undocumented clicks.",
    )
    add_heading(document, "How to read the main function", 2)
    add_text(document, "`parse_args()` declares command-line options and defaults. `main()` calls the pipeline in order. The numbered print statements are progress messages; they do not compute results. The imports at the top show the module boundaries. When you see `Path`, the code is building file-system paths in a platform-aware way. When you see `DataFrame`, the code is manipulating a table in memory.")

    add_heading(document, "4. Build customers and linked payment entities", 1)
    add_lesson(document,
        "The simulator needs a fictional population with customer baselines, accounts, merchants, and payment terminals. These tables have different grains and stable IDs so transaction records can be joined back to their entities.",
        "Read `src/config.py`, `src/simulation/generate_customers.py`, and `src/simulation/generate_world.py`.",
        [
            "Set population sizes in `src/config.py`: 2,000 customers, 800 merchants, and 1,200 terminals for the default project.",
            "In `generate_customers.py`, read the segment names and probabilities before reading the random draws. Probabilities line up by list position and sum to one.",
            "Trace one customer ID from the list comprehension into the returned pandas DataFrame. Each customer row stores segment, typical spend, latent event rate, region, and a separately sampled KYC band.",
            "Read `generate_entities()` and verify that every account points to one generated customer and each terminal points to a merchant.",
            "Inspect the local `customers.csv`, `accounts.csv`, `merchants.csv`, and `terminals.csv`. Test uniqueness of each primary key and check the joins before generating transactions.",
        ],
        ["`np.random.default_rng(SEED)` creates a modern pseudo-random number generator.", "`rng.choice(values, size=n, p=probabilities)` samples categories; `size` is the number of draws and `p` gives the probability for each corresponding category.", "`f\"C{i:06d}\"` is an f-string; `:06d` renders an integer as six digits with leading zeroes.", "A DataFrame is a labeled 2D table. A dictionary passed to `pd.DataFrame` maps each column name to its column values.", "The segment spend levels and customer mix are assumptions. They are not estimates from a bank's customers.", "KYC risk is intentionally sampled independently of fraud truth and is excluded from baseline model features."],
        ["`Customer_ID`, `Account_ID`, `Merchant_ID`, and `Terminal_ID` should each be unique in their own table.", "Every terminal's `Merchant_ID` should be present in `merchants.csv`; every account's `Customer_ID` should be present in `customers.csv`.", "The account table has one account per customer in this version; that simplification is explicitly documented."],
        "Profiles allow the project to ask whether an event is unusual for a specific customer rather than simply large in dollars. Entity relationships also let investigators ask whether a terminal is shared across many customers. A clean relational structure prevents false insights caused by broken joins.",
    )
    add_heading(document, "Core customer-generation code", 2)
    add_code(document, """
customer_rng = np.random.default_rng(SEED)
segments = customer_rng.choice(
    SEGMENTS, size=n_customers, p=SEGMENT_PROBABILITIES
)
median_spend = [SEGMENT_MEDIAN_SPEND[s] for s in segments]
typical_spend = customer_rng.lognormal(
    mean=np.log(median_spend), sigma=SPEND_LOG_SIGMA
)
""")
    add_text(document, "Read the assignment from right to left. First the seeded generator samples one segment per customer. The list comprehension looks up the configured median for each sampled segment in the same order. The log-normal call then produces one positive profile amount per customer. `np.log` transforms the dollar medians to the normal distribution's log scale. `size` follows the number of segment draws, so all columns line up row by row.")
    add_heading(document, "Why the spend generator uses a log-normal distribution", 2)
    add_text(document, "Spending must be positive and often has a long right tail. A normal distribution is symmetric and can generate negative values. A log-normal distribution is positive and skewed. NumPy's `lognormal(mean, sigma)` expects the mean of the underlying normal distribution in log space. Passing `np.log(45)` makes 45 the median, not the arithmetic mean, of the resulting dollar distribution. The sigma controls spread in log space. This is a defensible teaching choice, not a fitted empirical distribution.")
    add_heading(document, "Latent rate versus daily count", 2)
    add_text(document, "`Typical_Transactions_Per_Day` is a positive decimal rate, such as 1.7 expected events per day. It is not itself a daily event count. The count generator later samples an integer from a Poisson distribution using that rate. Poisson is used because transaction counts are nonnegative integers; it is a simple starting point that can later be replaced if the simulated pattern needs stronger burstiness.")

    add_heading(document, "5. Simulate legitimate transactions", 1)
    add_lesson(document,
        "The first event population represents ordinary behavior. It gives each customer a baseline of amount, timing, endpoint, channel, and authentication against which unusual events can be compared.",
        "Read `generate_legitimate_transactions()` in `src/simulation/generate_world.py`.",
        [
            "Trace the nested loop: one customer, each day, then each event generated for that customer-day.",
            "Read the Poisson draw. If the customer's expected rate is 2.4, the generator may produce 0, 1, 2, 3, or more events for a particular day.",
            "Check how seconds are sampled and sorted. Sorting ensures the events generated for the customer-day are chronological.",
            "Follow the terminal-to-merchant dictionary. A selected terminal determines its merchant and merchant region, preventing an inconsistent link.",
            "Read how channel, auth type, auth result, and incumbent action are sampled. The incumbent is a simple comparator, not an optimized policy.",
            "Inspect several event rows and compare each with its customer profile and terminal record.",
        ],
        ["`itertuples(index=False)` iterates through table rows as named tuples; it avoids some of the overhead of row-wise pandas Series.", "`rng.poisson(rate)` samples integer activity around the latent average rate.", "`rng.integers(0, 86400)` chooses a second within a day; 86,400 is the number of seconds per 24-hour day.", "A dictionary such as `terminal_merchant` supports a direct key-to-value lookup.", "The incumbent approves approved authentication and challenges a soft decline. It is deliberately rudimentary."],
        ["A transaction ID is unique and transaction timestamps stay within the configured horizon.", "The merchant on an event matches the merchant that owns its terminal.", "Amounts are positive; currency is USD; event fields have the names listed in `docs/data_dictionary.md`.", "The number of events is random around the customer rates, so the realized total need not equal a simple rate multiplied by the number of days."],
        "The baseline is needed to define normal variation. Without it, the project cannot quantify a new terminal relationship, a burst of events, a large deviation from typical spend, or a shift in channel and authentication behavior.",
    )
    add_heading(document, "Core baseline-event loop", 2)
    add_code(document, """
for customer in customers.itertuples(index=False):
    for day in range(days):
        event_count = rng.poisson(
            customer.Typical_Transactions_Per_Day
        )
        seconds = np.sort(
            rng.integers(0, 86400, size=event_count)
        )
        for second in seconds:
            # select endpoint, amount, channel, and authentication
            # append one transaction dictionary to rows
""")
    add_text(document, "The outer loop changes the customer. The middle loop moves through simulated days. The Poisson draw decides how many events happen that day. `seconds` chooses an event time and sorts those times. The inner loop creates one transaction per sampled time. The comment summarizes existing logic; the runnable implementation is the full function in `generate_world.py`.")

    add_heading(document, "6. Inject fraud while protecting ground truth", 1)
    add_lesson(document,
        "Fraud is planted as controlled event patterns so the simulation has a known answer key. That answer key must not enter feature creation, investigative SQL, monitoring, or model inputs before the evaluation stage.",
        "Read `src/simulation/inject_fraud.py`, `docs/fraud_scenarios.md`, and the restricted truth output under `data/synthetic/run/restricted/`.",
        [
            "Read the `add_event()` helper first. It creates event rows and truth rows together but keeps them in separate lists.",
            "Inspect each typology block: terminal compromise, card testing, credential compromise, and account takeover.",
            "Trace the crisis timing: planted events occur after baseline history and are repeated in two later phases so both training and holdout can include examples.",
            "Confirm the combined transaction table contains no fraud flag. The separate truth table maps a transaction ID to a scenario event and typology.",
            "Inspect `run_project.py` to find where the truth IDs are joined after `build_features()` and `score_rules()`.",
        ],
        ["`nonlocal` lets the nested helper update the ID counters owned by its outer function.", "A typology is a named fraud mechanism. Here the scenarios are generated patterns rather than observations of actual criminal behavior.", "The `fraud_ground_truth` table is an evaluation answer key. It is kept under `restricted/` locally and omitted from the public SQLite database.", "A transaction ID is the safe join key for the post-feature label. The model sees only `Fraud_Label` after the feature matrix has been constructed."],
        ["The synthetic run has four named typologies and 700 planted fraud transactions in the full run; each holdout contains 350 of them.", "The restricted file exists, but it should never be among columns given to `build_features()` or `LogisticBaseline`.", "The `FEATURE_COLUMNS` allow-list should contain no label, event ID, typology, or KYC band."],
        "The separate truth boundary is what makes offline evaluation possible without turning the simulator into a model that already knows the answers. A production system would not have ground truth at decision time either; labels arrive later through investigations and chargebacks.",
    )
    add_heading(document, "The truth boundary in the orchestrator", 2)
    add_code(document, """
features = build_features(transactions, customers)
scored = score_rules(features)
truth_ids = set(truth["Transaction_ID"])
labeled = scored.copy()
labeled["Fraud_Label"] = (
    labeled["Transaction_ID"].isin(truth_ids).astype(int)
)
""")
    add_text(document, "The first two calls only receive observable transaction and customer data. `truth_ids` is created after scoring. `.isin()` returns True where a transaction ID is in that private set, and `.astype(int)` turns those booleans into zero/one labels for training and evaluation. The labeled copy is temporary and does not replace the observable transaction or feature tables.")
    add_heading(document, "Four scenario patterns and what they teach", 2)
    add_table(document, ["Typology", "Planted behavior", "Potential observable signal", "Important caveat"], [
        ("Terminal compromise", "Many unrelated customers transact at one compromised terminal.", "Growing terminal volume and distinct-customer count.", "A busy legitimate terminal can also be highly connected."),
        ("Card testing", "Short sequences of low-value payments at a shared endpoint.", "Low amount combined with velocity and new customer-terminal pairs.", "Small purchases can be legitimate; the conjunction is the clue."),
        ("Credential compromise", "One customer's unusual higher-value activity.", "Amount relative to profile and endpoint familiarity.", "A genuine large purchase can look unusual."),
        ("Account takeover", "Rapid shifted channel/authentication behavior.", "Velocity, channel, time, authentication, and endpoint changes.", "This version has no device, login, or recovery telemetry."),
    ], [1.25, 1.8, 2.0, 1.95])

    add_heading(document, "7. Investigate events with SQL and SQLite", 1)
    add_text(document, "SQLite is the local analytical database for this prototype. It needs no separate service and works well for the current dataset size. CSV files remain portable and easy to inspect. The project can change storage later if measured scale or query needs justify it.")
    add_lesson(document,
        "Investigation starts with observable event data and simple questions: when did volume change, which endpoints are unusually concentrated, and what sequences deserve a closer look? SQL aggregates help an analyst reduce millions of raw events to manageable summaries.",
        "Read `src/storage.py`, `sql/01_daily_landscape.sql` through `sql/06_network_connections.sql`, and `sql/run_investigation.py`.",
        [
            "Run the project once so `data/synthetic/run/trusthold.sqlite` exists.",
            "Run `python sql/run_investigation.py` from the repository root.",
            "Open `sql/01_daily_landscape.sql`. Identify the selected fields, source table, group, aggregation, and sort order.",
            "Read each other SQL file and write the business question it answers before looking at its results.",
            "Compare one query result with a direct CSV filter or count to build trust in the database load.",
        ],
        ["`SELECT` chooses result columns; `FROM` names the table; `WHERE` filters rows; `GROUP BY` defines summary groups; `ORDER BY` ranks or sequences results; `LIMIT` restricts displayed rows.", "`COUNT(DISTINCT Customer_ID)` counts unique customers rather than transactions.", "`ROUND(SUM(Amount), 2)` totals transaction amount and formats it to cents.", "`sqlite3.connect()` opens the local database; a context manager closes the connection even if a query fails.", "The runner discovers `.sql` files in sorted name order and prints up to twelve rows per query."],
        ["The six investigations cover daily landscape, terminal concentration, rapid low-value events, amount deviation, authentication/channel behavior, and network connections.", "The queries do not read hidden fraud truth. High volume or a rare pattern creates a review hypothesis, not a fraud verdict.", "`src/storage.py` writes each public table to CSV and replaces the corresponding SQLite table on each run."],
        "SQL helps an investigator decide where to look first and what pattern to test. Endpoint volume and customer diversity can reveal concentration, but only operational context can establish whether a terminal is expected to serve many customers.",
    )
    add_heading(document, "A query from the project", 2)
    add_code(document, """
SELECT Terminal_ID,
       COUNT(*) AS transaction_count,
       COUNT(DISTINCT Customer_ID) AS distinct_customers
FROM transactions
GROUP BY Terminal_ID
ORDER BY transaction_count DESC
LIMIT 20;
""")
    add_text(document, "Read it from the bottom upward if that is easier: choose the transactions table, group records by endpoint, calculate total events and unique customers, sort busiest endpoints first, and return twenty. This query measures concentration; it does not say that the busiest terminal is compromised.")
    add_heading(document, "Why SQLite fits this build", 2)
    add_table(document, ["Choice", "Use now", "Reconsider when"], [
        ("CSV", "Portable exchange, snapshot packaging, manual inspection.", "Tables become too large or repeated joins become cumbersome."),
        ("SQLite", "Local SQL investigation with no server setup.", "A benchmark shows the workload outgrows local file analytics or concurrent write needs appear."),
        ("DuckDB and Parquet", "A possible columnar analytics extension.", "Large scans and compressed columnar files offer a measured benefit."),
        ("PostgreSQL", "Not required by the current single-user simulation.", "A real multi-user service needs central transactional access and operational controls."),
    ], [1.2, 2.8, 3.0])

    add_heading(document, "8. Build point in time behavior features", 1)
    add_lesson(document,
        "Features convert raw events into signals that describe the event in its context. The key rule is that a feature for transaction t may use only information available before t and fields available at t. This prevents future information from leaking backward.",
        "Read `src/features/build_features.py` and the `FEATURE_COLUMNS` list at the top.",
        [
            "Sort transactions by timestamp and transaction ID. A stable sort preserves a predictable ordering when timestamps tie.",
            "Map each customer to their typical spend, then divide the current amount by that profile amount.",
            "Translate timestamp, channel, authentication, and region context into numeric indicator columns.",
            "Walk rows chronologically. Remove customer events older than the prior-24-hour window, read counts, calculate the current row's prior history, and only then append the current event to history.",
            "Inspect first-use cases: the first event for a customer-terminal pair should have prior-pair count zero; subsequent events should increase it.",
            "Confirm `frame[FEATURE_COLUMNS]` contains finite numbers and missing values become zero under the current documented behavior.",
        ],
        ["A point-in-time feature is calculated using an as-of timestamp. It is not just a column that looks predictive.", "`defaultdict(deque)` creates a queue of timestamps per customer; old timestamps can be removed from the left as time advances.", "A `set` records unique customers already seen at a terminal; a dictionary of counters records prior events.", "The order of statements matters: values are read before the current event increments the histories.", "`clip(lower=1)` prevents division by zero in the baseline spend ratio.", "`replace([np.inf, -np.inf], np.nan).fillna(0)` converts invalid numerical values into missing values and then replaces missing feature values with zero."],
        ["`Tx_Count_Prior_24h` excludes the current event. At exactly the 24-hour cutoff, the implementation retains the boundary event because it removes timestamps strictly earlier than the cutoff.", "Endpoint counts and distinct-customer counts also exclude the current row.", "The baseline has twelve features: amount ratio, velocity, endpoint history, pair familiarity, time, auth, channel, and home-region mismatch.", "There are no device, IP, login, password-reset, chargeback-delay, or investigator case-history features."],
        "Point-in-time correctness is essential to an honest estimate of what a live strategy could have known. A model that accidentally uses later transactions can appear powerful in a notebook and fail when deployed.",
    )
    add_heading(document, "The critical history update order", 2)
    add_code(document, """
now = pd.Timestamp(row.Timestamp)
cutoff = now - pd.Timedelta(hours=24)
while history and history[0] < cutoff:
    history.popleft()
prior_count = len(history)
# calculate this event's output using prior_count
history.append(now)
""")
    add_text(document, "`history[0]` is the oldest saved timestamp. `popleft()` discards one timestamp from the front of the deque, so the loop removes all observations outside the current window. `prior_count` is measured before `history.append(now)`. If append ran first, the current transaction would count itself and the velocity feature would be off by one.")
    add_heading(document, "Hand-check a velocity feature", 2)
    add_table(document, ["Prior events for a customer", "Current event", "Expected prior-24h count"], [
        ("10:00 Monday", "10:05 Monday", "1"),
        ("10:00 Monday and 10:05 Monday", "11:00 Monday", "2"),
        ("10:00 Monday", "10:00 Tuesday", "1 under the current inclusive cutoff logic"),
    ], [2.35, 2.35, 2.3])
    add_text(document, "The final row illustrates why boundary behavior should be deliberate and documented. If a strict open-left window is intended, the removal comparison would need to change from `< cutoff` to `<= cutoff`.")

    add_heading(document, "9. Create an explainable rules score", 1)
    add_lesson(document,
        "Rules turn selected signals into an auditable score and a list of reasons. They are a useful first baseline because a reviewer can see exactly why an event received points.",
        "Read `src/rules/score_rules.py` and compare rule inputs with `FEATURE_COLUMNS`.",
        [
            "Start with a zero-valued integer Series indexed to the scored table.",
            "For each rule, create a Boolean mask that is True for events matching the condition.",
            "Add the configured points to matching rows and append a reason label for each matched rule.",
            "Cap the score at 100 and join the reason labels into one readable string.",
            "Open sample events with high scores and read the reasons alongside the actual feature values.",
        ],
        ["A Boolean mask has one True/False value per table row.", "`score.loc[mask] += points` updates only selected rows.", "`nonlocal score` lets the nested helper update the score object in its enclosing function.", "A single event can meet multiple rules, so its score accumulates points.", "Thresholds and points are human-set assumptions; they are not probabilities unless separately calibrated."],
        ["The event with amount ratio 4 should receive the amount-vs-profile signal but not the >=6 extreme signal.", "A low-value event can get a special testing-velocity reason when its amount is at most $5 and prior-24-hour velocity is at least two.", "`Rule_Reasons` should never be used as an independent fraud label."],
        "The rule score is useful for triage because it provides reason codes to an investigator. It also creates a baseline for asking whether a statistical model improves ranking and, more importantly, business outcomes.",
    )
    add_table(document, ["Example rule", "Points", "What the rule says"], [
        ("Amount is at least 3x typical spend", "30", "Large relative to the customer's modeled baseline."),
        ("Amount is at least 6x typical spend", "25 additional", "An even more extreme deviation earns extra points."),
        ("At least five prior events in 24 hours", "25", "The customer is transacting unusually frequently."),
        ("New customer-terminal pair", "15", "The endpoint has not previously appeared for that customer."),
        ("At least eight distinct prior customers at terminal", "18", "The endpoint is already widely shared."),
        ("Nighttime activity", "8", "Time is contextual evidence and a weak signal by itself."),
    ], [2.7, 1.2, 3.1])
    add_text(document, "Because scores add, two individually weak signals can become an alert together. But redundant rules can also over-count related evidence. A proper next step is to inspect overlap, test points and cutoffs under sensitivity scenarios, and monitor false declines and review volumes.")

    add_heading(document, "10. Fit a time aware logistic baseline", 1)
    add_lesson(document,
        "The logistic baseline learns a relationship between the allowed features and planted training labels, then estimates a score between zero and one. It is included to compare a simple learned score with transparent rules; it is not a production-ready model.",
        "Read `src/models/logistic_baseline.py` and the temporal split in `src/run_project.py`.",
        [
            "Create the temporary offline label by checking whether the transaction ID occurs in the restricted truth ID set. Do this only after feature construction.",
            "Sort distinct event dates and choose a date boundary at roughly 70 percent of dates. Earlier events form training history; later events form the holdout.",
            "Fit the model using training rows. The model extracts only the named `FEATURE_COLUMNS` and the temporary `Fraud_Label` outcome.",
            "Inspect training-only means and standard deviations, then follow the standardization and gradient updates in `fit()`.",
            "Predict scores for the full frame using coefficients learned from training rows. Evaluate model ranking and actions on the later holdout.",
            "Compare logistic, rule, and hybrid scores. Keep threshold selection on training data and final outcome evaluation on the future period.",
        ],
        ["Logistic regression maps a weighted sum through the sigmoid function `1 / (1 + exp(-x))`, returning a value between zero and one.", "Standardization subtracts each training feature's mean and divides by its standard deviation, so features with different units can be optimized together.", "A zero standard deviation is changed to one to avoid division by zero.", "Gradient descent repeatedly moves coefficients in the direction that lowers weighted logistic loss; the L2 term discourages very large weights.", "The positive-class weight compensates for rare planted fraud, capped at 12 to avoid letting a few examples dominate.", "PR-AUC (average precision here) summarizes ranking precision as recall increases and is more informative than accuracy when positive cases are rare."],
        ["Training dates precede the holdout dates; the holdout begins 2026-02-12 in the published case study.", "The default seed's held-out period has 74,237 transactions and 350 planted fraud events.", "The selected threshold set is chosen by training-period economic cost, not by searching the holdout for the best answer.", "The list of features excludes fraud labels, typology names, event IDs, and KYC band."],
        "The time split is closer to the real operating problem: build a strategy using past events and ask how it behaves on future events. That makes the holdout a more useful stress test than randomly mixing past and future rows.",
    )
    add_heading(document, "Follow the sigmoid calculation", 2)
    add_code(document, """
linear = np.clip(z @ self.weights_ + self.intercept_, -30, 30)
probability = 1.0 / (1.0 + np.exp(-linear))
error = (probability - y) * sample_weight
self.weights_ -= self.learning_rate * (
    (z.T @ error) / len(y) + self.l2 * self.weights_
)
""")
    add_text(document, "`z @ weights` is a matrix-vector multiplication that adds each feature's weighted contribution. The intercept shifts all scores. Clipping keeps the exponential calculation numerically stable. The sigmoid converts the linear value to a probability-like score. The weighted error compares prediction with label; the update moves coefficients in a direction intended to reduce loss, while L2 shrinks weights. This compact implementation is instructional and should be validated before any non-synthetic use.")
    add_heading(document, "What the NumPy implementation is teaching", 2)
    add_text(document, "The class shows the mechanics of a binary classifier without hiding the algorithm behind a library call. `self.mean_`, `self.scale_`, `self.weights_`, and `self.intercept_` are learned state. `fit()` estimates them; `predict_proba()` reuses them unchanged. When features are added, both fitting and prediction use the same explicit feature allow-list. Production modeling would add robust optimization, calibration, model versioning, stability checks, and a mature ML library only after the baseline is understood.")

    add_heading(document, "11. Turn scores into actions under capacity", 1)
    add_lesson(document,
        "The policy layer turns continuous scores into discrete actions and respects a daily manual-review limit. This stage makes the model relevant to actual operating work.",
        "Read `THRESHOLD_CANDIDATES`, `apply_policy()`, `choose_thresholds()`, and `policy_costs()` in `src/decisions/policies.py` and `src/run_project.py`.",
        [
            "Read each threshold triplet in order: challenge, review, decline.",
            "Apply the cutoffs in ascending order. Later assignments overwrite earlier ones, so a very high score ends as DECLINE.",
            "Group review decisions by calendar day, sort each day's candidates by score, and keep only the highest-risk cases up to the daily capacity.",
            "Route the remaining review candidates to CHALLENGE and set `Capacity_Overflow=1` for those cases.",
            "For each score type, apply each candidate threshold set to training data, calculate net modeled cost, and keep the lowest-cost set.",
            "Use the selected thresholds on the later holdout and inspect action counts and overflow.",
        ],
        ["A threshold is a policy choice that maps score bands to actions; it is not a universal definition of fraud.", "`groupby('Decision_Date')` enforces a per-day queue limit rather than a total-run limit.", "Stable descending sort makes ties deterministic when the same input and seed are used.", "Overflow routing is explicit: these candidates become CHALLENGE, which models a fallback step-up action."],
        ["At the standard capacity of 250 cases per day, the default holdout had no review overflow in the scored strategies.", "The sensitivity table varies capacity from 10 to 500 cases per day and reports any cases routed to challenge after the review queue fills.", "The selected score threshold can differ across rules and logistic scores because their scales and ranking behavior differ."],
        "An operating strategy must fit the investigator queue. If alerts exceed capacity, either cases wait too long or the business applies a fallback. Reporting overflow prevents a strategy from claiming success while silently sending more work than people can complete.",
    )
    add_heading(document, "Simplified threshold assignment and review spillover", 2)
    add_code(document, """
out["Decision"] = "APPROVE"
out.loc[score >= challenge_at, "Decision"] = "CHALLENGE"
out.loc[score >= review_at, "Decision"] = "REVIEW"
out.loc[score >= decline_at, "Decision"] = "DECLINE"

ordered = review_rows.sort_values(score_column, ascending=False)
spill = ordered.index[daily_capacity:]
out.loc[spill, "Decision"] = "CHALLENGE"
out.loc[spill, "Capacity_Overflow"] = 1
""")
    add_text(document, "The thresholds are applied from lower to higher. A score above all three ends at DECLINE because that assignment is last. Review candidates are then ranked within a date; Python slicing `[daily_capacity:]` selects every position after the allowed number. Those spillover rows become CHALLENGE, and the flag makes the operational limit measurable.")

    add_heading(document, "12. Measure business outcomes and stress assumptions", 1)
    add_heading(document, "Translate actions into assumed dollars", 2)
    add_text(document, "`policy_costs()` returns one modeled dollar cost per transaction. Approved fraud costs amount plus a chargeback fee. Challenged or reviewed fraud retains an assumed residual loss after intervention. Legitimate approved payments earn an assumed margin benefit. Challenges and reviews add operating cost. A false decline adds an assumed customer attrition share of lifetime value plus forgone margin. Declined fraud is assigned zero remaining fraud cost in this simplified model.")
    add_table(document, ["Action / outcome", "Modeled cost logic", "What to question"], [
        ("Fraud approved", "Transaction amount + chargeback fee", "Does the event amount represent the loss exposure? Are fees appropriate?"),
        ("Fraud challenged", "Residual fraud fraction + challenge cost", "How often does step-up verification actually stop fraud?"),
        ("Fraud reviewed", "Residual after review recovery + review cost", "Can the team recover funds, and what does queue delay do?"),
        ("Legitimate approved", "Negative cost equal to assumed payment margin", "Is the margin rate appropriate for the payment and context?"),
        ("Legitimate challenged/reviewed", "Unit friction/handling cost", "What are completion, abandonment, and service costs?"),
        ("Legitimate declined", "Attrition probability x lifetime value + lost margin", "How do customer loss and lifetime value vary by segment?"),
    ], [1.35, 2.7, 2.95])
    add_lesson(document,
        "Business evaluation combines fraud capture, fraud remaining, legitimate-customer friction, review demand, and modeled net cost. The best choice is conditional on the assumptions and risk appetite.",
        "Read `src/decisions/policies.py` and `src/evaluation/metrics.py`; inspect `strategy_metrics.csv`, `capacity_sensitivity.csv`, `economic_sensitivity.csv`, and `scenario_surface.csv`.",
        [
            "Check the precision-recall measure on the holdout. Interpret average precision relative to the positive class being rare.",
            "Read `Fraud_Value_Captured_Pct` as value-weighted intervention effectiveness under the action fractions in code, not as the percent of transactions caught.",
            "Read `False_Declines`, legitimate challenge/review counts, and review overflow beside fraud capture.",
            "Compare `Net_Economic_Cost` using the configured fictional values. More negative means modeled benefits exceed modeled costs under this code's sign convention.",
            "Change one assumption through `dataclasses.replace()` at a time and inspect whether the preferred strategy changes.",
        ],
        ["Precision is the share of intervened transactions that are planted fraud. Recall is the share of planted fraud transactions that receive any non-approve action.", "PR-AUC measures ranking over all possible cutoffs; cost measures a chosen set of actions under a specific set of assumptions.", "Value capture is not identical to avoided loss: the intervention fractions and residual-loss assumptions are separate.", "Sensitivity rows are what-if scenarios, not confidence intervals or probability statements."],
        ["In the default seed, Logistic has the lowest modeled holdout cost (-$73,729.50), captures 78.37% of fraud value, and has one false decline at capacity 250.", "Rules capture 73.09% with 30 false declines at -$56,248.77; Rules + logistic capture 76.26% with 30 false declines at -$58,811.13.", "The default-seed PR-AUC values are 0.5826 for Logistic, 0.2655 for Rules, and 0.2981 for Hybrid. Incumbent PR-AUC is not applicable because it has no continuous risk score.", "Across 30 seeds, Logistic had lower modeled cost than Rules in 30/30 runs; its paired median difference was -$15,501.82 (observed range -$22,482.27 to -$11,207.82)."],
        "The result illustrates the project's thesis: ranking quality and operating value are related but not interchangeable. A modestly better ranking is not automatically worth higher review costs or more customer friction. The preferred policy depends on the economic inputs, capacity, and customer impact.",
    )
    add_heading(document, "How to read the sensitivity tables", 2)
    add_text(document, "Capacity sensitivity reruns policy application at 10, 50, 150, 250, and 500 reviews per day, with overflow sent to challenge. Economic sensitivity holds the decisions fixed while changing selected intervention and attrition assumptions. The scenario surface varies both capacity and economics. If the preferred policy changes across plausible assumptions, the appropriate business takeaway is that the decision depends on uncertain inputs and requires better measurement—not that one row proves a universal winner.")
    add_heading(document, "A metric audit to learn from", 2)
    add_text(document, "The metric audit now assigns PR-AUC only to strategies that produce a continuous score. Rules, Logistic, and Hybrid have scores; Incumbent does not, so its value is missing and rendered as not applicable. This prevents a misleading model-ranking comparison while preserving the incumbent's action-based costs and customer outcomes.")

    add_heading(document, "13. Add network intelligence and monitoring", 1)
    add_heading(document, "Customer-terminal network summary", 2)
    add_text(document, "`src/network_intelligence.py` groups transactions by terminal and merchant and calculates event count, distinct customers, active days, and amount. It then derives customers per transaction and sorts endpoints by customer diversity and volume. This is a full-run investigation summary. It is not a point-in-time feature and must not be passed directly to the live-style scoring model because it contains later events.")
    add_heading(document, "Daily monitoring", 2)
    add_text(document, "`src/monitoring.py` aggregates daily count, value, average amount, soft-decline rate, and high-risk-score rate. For the last two target series, it computes a rolling mean and standard deviation using the preceding 14 days, with at least seven prior days required. `shift(1)` is the temporal safeguard: today's value is excluded from its own baseline. A three-standard-deviation signal asks a person to investigate a change; it does not prove fraud or model drift.")
    add_table(document, ["Monitoring field", "What changes it may signal", "Why it is not a verdict"], [
        ("Transaction_Count", "Volume spikes or outages.", "Seasonality and normal growth also change volume."),
        ("Soft_Decline_Rate", "Authentication failures or policy changes.", "A decline may be an issuer or customer issue rather than fraud."),
        ("High_Risk_Score_Rate", "Score distribution or behavior shifts.", "Threshold and mix changes affect the rate."),
        ("Prior_14d_ZScore", "A value far from a trailing baseline.", "Small, seasonal samples make z-scores unstable."),
        ("3Sigma_Alert", "A simple screening trigger.", "Alerts require investigation and corroborating context."),
    ], [1.45, 2.4, 3.15])
    add_heading(document, "Group diagnostics", 2)
    add_text(document, "The pipeline summarizes action rates, false declines, and synthetic fraud rates by segment, KYC band, and home region. These are descriptive checks to identify where the fictional policy may concentrate friction. They do not certify fairness: groups are small and synthetic, demographic coverage is absent, and the simulation is not representative of a real population. Investigate sample counts before comparing rates.")

    add_heading(document, "14. Produce the case study and dashboard", 1)
    add_lesson(document,
        "The reporting layer should make the analysis understandable to a reader who did not write the code. It should state the decision problem, method, holdout, findings, assumptions, limitations, and next experiments.",
        "Read `src/reporting.py`; open `reports/case_study.md` and `reports/dashboard.html` after a run.",
        [
            "Follow `write_case_study()`: it receives metrics and sensitivity tables from the current run rather than pasting headline values by hand.",
            "Follow `write_dashboard()`: it serializes precomputed metrics, daily monitoring, and capacity/economic scenarios into a self-contained HTML file.",
            "Run the project and compare a headline in the Markdown report with its row in `strategy_metrics.csv`.",
            "Open `reports/dashboard.html` in a browser. Change capacity and economics selectors; confirm the table and bars reflect the chosen precomputed scenario.",
            "Check every chart title, metric name, unit, and caveat. A dashboard should explain what a value means and where it came from.",
        ],
        ["`Path.write_text(..., encoding='utf-8')` writes a text artifact using a consistent character encoding.", "`json.dumps()` creates JSON for JavaScript to read. The dashboard has no external library dependency.", "The dropdowns filter the scenario table; they do not recompute a new model or threshold in the browser.", "The narrative selects a best row by modeled cost under the current assumptions, but the report must preserve uncertainty and limitations."],
        ["The dashboard says output is synthetic and lower modeled cost is better only under the chosen assumptions.", "The strategy economics view uses precomputed holdout outcomes; the daily trend shows observable simulated activity.", "The SQL database, case study, and dashboard all derive from one saved run, so mismatches can be traced to a specific pipeline stage."],
        "A strong portfolio artifact explains a decision and trade-off, not just the tools used. Clear reporting lets a risk leader ask whether a strategy is operationally acceptable, economically attractive, and safe for customers.",
    )

    add_heading(document, "15. Explain the current findings correctly", 1)
    add_text(document, "This section translates the generated results into business language. It deliberately separates observed project outputs, interpretation, and limitations.")
    add_table(document, ["Strategy", "Fraud value captured", "False declines", "PR-AUC", "Net modeled cost"], [
        ("Incumbent", "0.00%", "0", "N/A", "-$15,477.19"),
        ("Rules", "73.09%", "30", "0.2655", "-$56,248.77"),
        ("Logistic", "78.37%", "1", "0.5826", "-$73,729.50"),
        ("Rules + logistic", "82.27%", "30", "0.4119", "-$62,823.34"),
    ], [1.35, 1.15, 0.9, 1.55, 1.55])
    add_heading(document, "Finding 1: score quality, actions, and cost must be read together", 2)
    add_text(document, "For the default seed, Logistic has the lowest modeled cost and highest value capture among the scored strategies. The score ordering and selected thresholds create a more cost-effective action mix under this holdout and its assumptions. It does not mean the model is intrinsically superior or that the difference will persist under another population or cost model.")
    add_heading(document, "Finding 2: the policy intercepts substantial synthetic value", 2)
    add_text(document, "The selected Logistic strategy is credited with 78.37% fraud value captured in the default seed under assumed stop/recovery fractions. This is a modeled value-weighted measure, not an observed recovery rate. A decline receives full capture in the code, challenge 80%, review 90%, and approve zero. Real effectiveness would require measured outcomes and would vary by channel, customer, case delay, and intervention execution.")
    add_heading(document, "Finding 3: interventions create customer and staff work", 2)
    add_text(document, "In the default seed, Rules produce 30 false declines, 5,305 good-payment challenges, and 140 good-payment reviews. Logistic produces one false decline, 740 challenges, and 21 reviews. Across 30 seeds, Logistic has a median of 4,463.5 fewer good-payment challenges and 108 fewer reviews than Rules. The full observed ranges belong beside these medians; the dashboard and case study provide them.")
    add_heading(document, "Finding 4: operations and economics are assumption-sensitive", 2)
    add_text(document, "Lower review capacity increases overflow. Lower challenge effectiveness or review recovery changes modeled losses. Higher assumed attrition makes false declines more expensive. The comparison therefore supports conditional planning: identify which assumptions matter, measure them in a real setting, and revisit thresholds when operating constraints or risk appetite change.")
    add_heading(document, "Finding 5: the simulation is designed for method learning", 2)
    add_text(document, "Each seed has 246,314 synthetic transactions and 700 injected fraud events; its 74,000-event holdout contains 350 planted fraud events. This larger design reduces small-count instability inside the simulator, but does not make the population representative or prove real-world performance. The ten-seed ranges are observed simulator variation, not confidence intervals or statistical significance tests.")
    add_heading(document, "Executive explanation in one paragraph", 2)
    add_text(document, "TrustHold simulates a payments business and compares a rules score with a logistic baseline on a future holdout. Across 30 seeds, Logistic captures 77.51% of simulated fraud value on average versus 73.73% for Rules and has lower modeled cost in all 30 runs. It challenges fewer legitimate payments and also sends fewer to human review in this simulation. Those are scenario outputs under fictional economics, not real savings or a performance guarantee. The median paired cost difference is −$15,501.82, with an observed range from −$22,482.27 to −$11,207.82; these ranges are not confidence intervals.")

    add_heading(document, "16. Package, verify, and extend the project", 1)
    add_heading(document, "Reproducible public data snapshot", 2)
    add_text(document, "`scripts/package_dataset.py` splits generated CSVs into GitHub-friendly parts and writes a manifest with row counts and SHA-256 checksums. `scripts/assemble_dataset.py` restores the parts and verifies them against the manifest. It places truth labels in a clearly separated restricted folder. The complete synthetic snapshot lets a reviewer inspect artifacts without first executing the full project.")
    add_code(document, """
python -m scripts.assemble_dataset
python -m sql.run_investigation
python -m src.run_project --customers 200 --days 60
""")
    add_heading(document, "Final project verification", 2)
    for item in [
        "Rebuild from a clean environment using `requirements.txt` and the documented command.",
        "Check manifest checksums after dataset assembly; do not manually edit a published part.",
        "Confirm the truth table is separate and excluded from public model inputs and SQLite tables.",
        "Check that all generated outputs come from the current run and not from stale earlier CSV files.",
        "Reconcile one strategy metric across `strategy_metrics.csv`, `case_study.md`, and the dashboard payload.",
        "Inspect SQL results, daily monitoring, group diagnostics, typology measures, and scenario sensitivities.",
        "Review every assumption and label synthetic results clearly before using the case study in a portfolio.",
    ]:
        add_bullet(document, item)
    add_heading(document, "Suggested next build experiments", 2)
    add_table(document, ["Experiment", "Change one thing", "Business question"], [
        ("Prevalence stress test", "Change fraud frequency and keep the split protocol.", "Does alert precision and review workload remain usable?"),
        ("Typology-specific analysis", "Compare capture by planted scenario.", "Which attack pattern is currently weakly detected?"),
        ("Feature ablation", "Remove one feature family at a time.", "Does a signal add useful information or duplicate another?"),
        ("Model comparison", "Add a tree baseline after the logistic model is understood.", "Does additional complexity improve holdout economics and stability?"),
        ("Entity extension", "Add devices, IPs, login, and account-recovery events.", "Can identity networks clarify account takeover risk?"),
        ("Storage benchmark", "Compare SQLite with DuckDB/Parquet on identical data and queries.", "Is migration justified by measured speed, size, or workflow?"),
    ], [1.55, 2.65, 2.8])
    add_text(document, "Make one controlled change at a time, use a separate output directory, record the expected effect, then compare to the unchanged baseline. A new model is useful only if it improves an operating outcome enough to justify added complexity.")
    add_heading(document, "Version control and GitHub", 2)
    add_text(document, "Git records reviewed project changes as commits; GitHub hosts a remote copy. Inspect the current state before staging anything. This checkout showed the project files as untracked when the tutorial was prepared, so do not assume they have already been committed or pushed.")
    add_code(document, """
git status --short
git branch --show-current
git remote -v
""")
    add_text(document, "`git status` tells you which files are untracked, modified, or staged. `git branch --show-current` reports the branch name. `git remote -v` displays configured remote destinations. Review those outputs before deciding what belongs in a commit.")
    add_text(document, "Before publishing, confirm `.gitignore` excludes the local SQLite database and restricted local truth file, and inspect the published snapshot's README and manifest. Stage only the intended project files, review the staged diff, commit with a message that summarizes the change, and push only to the expected repository and branch. The remote repository named in the project README is `YvonneTsa/The-Cost-of-Trust`; verify the remote URL locally before any push.")

    add_heading(document, "Appendix A. Code reading map", 1)
    add_table(document, ["File", "Read it to learn", "Questions to ask"], [
        ("`src/config.py`", "Central settings and fictional unit economics.", "Which values are assumptions? Which are run controls?"),
        ("`src/simulation/generate_customers.py`", "Seeded customer profiles, categories, distributions.", "What is one row? Which quantities are medians and which are rates?"),
        ("`src/simulation/generate_world.py`", "Linked entities and baseline events.", "How is the terminal mapped to its merchant? How is time generated?"),
        ("`src/simulation/inject_fraud.py`", "Scenario event injection and isolated truth.", "Can any answer-key field reach feature creation?"),
        ("`src/features/build_features.py`", "Chronological, lagged behavior signals.", "Does the current event enter its own history?"),
        ("`src/rules/score_rules.py`", "Readable thresholds and reason strings.", "Do overlapping rules double-count related evidence?"),
        ("`src/models/logistic_baseline.py`", "Training-only scaling and NumPy optimization.", "Which columns are allowed? Is fit separate from prediction?"),
        ("`src/decisions/policies.py`", "Thresholds, queue overflow, and cost formulas.", "What does capacity force the system to do?"),
        ("`src/run_project.py`", "Order of operations and all outputs.", "When does the temporal split happen? When are labels joined?"),
        ("`src/storage.py`", "CSV plus SQLite writes.", "Which table is public? Which fields are excluded?"),
        ("`src/monitoring.py`", "Trailing, label-free indicators.", "Does the day's observation enter its own baseline?"),
        ("`src/reporting.py`", "Generated case study and dashboard.", "Are displayed results derived from this run?"),
    ], [2.35, 2.2, 2.45])

    add_heading(document, "Appendix B. Project table and output guide", 1)
    add_table(document, ["Table/file", "Grain", "Use it for"], [
        ("customers", "One row per customer", "Segment, profile amount/rate, home region, KYC band."),
        ("accounts", "One row per account", "Customer-account relationship."),
        ("merchants", "One row per merchant", "Merchant category, region, assumed profile."),
        ("terminals", "One row per endpoint", "Terminal ownership and type."),
        ("transactions", "One row per event", "Raw event context and incumbent action."),
        ("behavior_features", "One row per event", "Observable point-in-time behavior and rule outputs."),
        ("test_decisions", "One event per strategy", "Holdout actions without fraud labels."),
        ("strategy_metrics", "One row per strategy", "Holdout capture, friction, PR-AUC, and modeled cost."),
        ("capacity_sensitivity", "One strategy-capacity pair", "Review limit effects."),
        ("economic_sensitivity", "One strategy-economic scenario pair", "Effect of assumed costs and intervention rates."),
        ("scenario_surface", "One strategy-capacity-economics combination", "Combined stress-test surface used by dashboard."),
        ("daily_monitoring", "One row per date", "Observable volume and score-rate checks."),
        ("terminal_network_summary", "One row per terminal and merchant", "Offline endpoint concentration."),
        ("impact_by_customer_group", "One strategy-group summary", "Descriptive rates by segment, KYC band, and region."),
        ("typology_metrics", "One strategy and fraud typology", "Post-decision capture by planted scenario."),
        ("model_coefficients", "One row per feature", "Direction and magnitude of standardized model weights."),
        ("action_counts", "One strategy-action summary", "Approve/challenge/review/decline volumes."),
        ("restricted/fraud_ground_truth.csv", "One row per injected event", "Offline label and typology evaluation only."),
    ], [2.3, 1.75, 2.95])
    add_text(document, "The SQLite database contains observable and derived public tables but does not contain `fraud_ground_truth`. For model training and offline reporting, the runner joins planted labels in memory only after constructing features and decisions.")

    add_heading(document, "Appendix C. Glossary, checkpoints, and practice exercises", 1)
    add_table(document, ["Term", "Plain-language meaning"], [
        ("Grain", "What one row represents, such as one transaction or one customer."),
        ("Synthetic", "Fictional generated data, not a record of a real person or company."),
        ("Ground truth", "The simulator's private answer key for which events it planted as fraud."),
        ("Feature leakage", "Using information that would not have been known at the decision time."),
        ("Point in time", "Calculated using only facts available as of a defined event timestamp."),
        ("Temporal holdout", "A later block of dates set aside to mimic future evaluation."),
        ("Precision", "Among events acted on, what share were planted fraud?"),
        ("Recall", "Among planted fraud events, what share received a non-approve action?"),
        ("PR-AUC / average precision", "A ranking summary focused on precision as recall increases."),
        ("False decline", "A legitimate transaction that the policy declines."),
        ("Review overflow", "Review candidates above the configured daily capacity, routed to challenge."),
        ("Calibration", "Whether predicted risk probabilities match observed event rates."),
        ("Drift", "A change over time in data, behavior, score distribution, or model performance."),
        ("Risk appetite", "The level and type of financial/customer harm the business accepts."),
    ], [2.1, 4.9])
    add_heading(document, "Checkpoints before moving on", 2)
    for item in [
        "Can you explain the difference between a profile rate and an observed daily count?",
        "Can you prove that the current event is excluded from rolling history?",
        "Can you find the exact line where truth labels are joined after features are built?",
        "Can you explain why the model is trained on earlier dates and evaluated on later dates?",
        "Can you describe how review capacity changes the final action?",
        "Can you explain why negative net cost is a modeled benefit rather than verified profit?",
        "Can you tell a reviewer which claims are synthetic findings and which are assumptions?",
    ]:
        add_bullet(document, item)
    add_heading(document, "Practice exercises", 2)
    add_table(document, ["Exercise", "Your task", "What a sound answer includes"], [
        ("1. Change spend variability", "Raise `SPEND_LOG_SIGMA` and compare customer profiles.", "A reasoned expectation, before/after summary, and statement that it is an assumption."),
        ("2. Hand-check a feature", "Select a customer and endpoint sequence and calculate prior counts manually.", "A timestamp-ordered ledger that excludes the current event."),
        ("3. Explain one rule alert", "Choose a high-score event and trace each reason to its source field.", "A signal explanation, not a claim of fraud certainty."),
        ("4. Reduce capacity", "Compare capacity 250 with capacity 50.", "Overflow, changed challenge count, capture, and modeled cost."),
        ("5. Change economics", "Lower challenge stop probability and see whether strategy ranking changes.", "The assumption changed, actions remained fixed, interpretation is conditional."),
        ("6. Audit a query", "Rewrite an endpoint query to sort by distinct customers.", "Different concentration definition and a context caveat."),
        ("7. Audit PR-AUC applicability", "Check which strategies have a continuous score.", "Incumbent ranking is not applicable without a continuous score."),
        ("8. Plan one extension", "Design a device or IP relationship table.", "Entity grain, privacy/security concerns, temporal availability, and value hypothesis."),
    ], [1.55, 2.55, 2.9])

    add_deep_course(document)
    add_heading(document, "Final working principle", 1)
    add_text(document, "Keep the architecture ambitious and the explanations concrete. Every variable, rule, model, action, and business cost should have a clear definition and an inspectable output. Treat the simulated result as evidence that the code behaved under stated assumptions; treat real-world performance as a separate question that requires representative data, measured economics, governance, and controlled validation.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(suffix=".docx", dir=OUTPUT.parent, delete=False) as handle:
        generated = Path(handle.name)
    try:
        document.save(generated)
        replace_package_parts(generated, OUTPUT)
    finally:
        generated.unlink(missing_ok=True)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    build()
