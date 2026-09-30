# End-to-end implementation walkthrough

This document explains the job of each module, the important syntax, why the design is used, and when to inspect it. The runnable code is under `src/`; PowerShell commands are entered in the terminal, while Python code belongs in the named `.py` files. Begin with `python -m src.run_project`, then inspect one generated table at a time.

## 1. Settings and repeatability — `src/config.py`

`SEED` is the repeatable starting point for pseudo-random generation. Each layer creates a `numpy.random.default_rng` with a small seed offset so its draws do not depend on how many random values another module happened to consume. Re-running with the same code and settings therefore creates the same fictional world.

`N_CUSTOMERS`, `N_MERCHANTS`, `N_TERMINALS`, `SIMULATION_DAYS`, and `START_DATE` describe the default learning world. These are explicit assumptions, not estimates. The command-line options in `run_project.py` can change row counts and review capacity without editing source.

`Economics` is a frozen dataclass. A dataclass groups related settings under named fields; `frozen=True` prevents accidental changes while the pipeline is running. `replace(ECONOMICS, ...)` creates deliberate stress scenarios without mutating the base assumptions.

## 2. Customers and linked entities — `src/simulation/generate_customers.py` and `generate_world.py`

The customer generator returns one pandas row per customer. A list comprehension such as `[f"C{i:06d}" for i in range(...)]` applies a simple ID format to each integer. The `:06d` f-string field pads it to six digits so IDs sort predictably as text.

`rng.choice(values, size=n, p=probabilities)` samples categories using the probabilities in matching order. The probabilities describe the fictional population mix; a small sample is not forced to match those exact percentages.

The segment dictionaries map a category to a configured median. The list comprehensions look up the median in customer order. `rng.lognormal(mean=np.log(medians), sigma=...)` draws positive, right-skewed values. Since the parameter is in log space, logging a chosen median makes that value the distribution median. A configured transaction rate is a latent decimal rate, not a daily event count.

`generate_entities` makes a customer table, a one-account-per-customer table, merchants, and terminals. IDs are generated once at each entity's grain. A terminal stores its owning merchant ID, so a later transaction can link to both the business and the endpoint without inconsistent relationships.

Each customer receives a small set of familiar terminals in their home region. Most baseline events use that set; a small share uses any endpoint to retain ordinary travel. This creates observable baselines against which later endpoint changes can be compared.

### Tiny distribution example

If a fictional segment's configured median spend is $50 and log-space sigma is 0.40, a customer draw is positive and may fall above or below $50. It is not a claim that every customer spends $50, or that $50 is an empirical average.

## 3. Legitimate activity — `generate_legitimate_transactions`

For each customer and day, `rng.poisson(customer.Typical_Transactions_Per_Day)` draws a whole-number transaction count. Poisson is used because event counts are nonnegative integers, while the customer profile is a decimal expected rate. It is appropriate here as a first simple count process; burstier real activity may require another model.

`rng.integers(0, 86400, size=event_count)` chooses seconds in the day. `np.sort` puts those events in time order. A Python `for` loop then creates one dictionary per transaction; the dictionaries are collected into a DataFrame at the end. The terminal-to-merchant mapping is a dictionary so each lookup is direct and consistent.

Amounts use a log-normal draw around customer typical spend. Channel, authentication type, and authentication result are random from the named fictional mix. The incumbent decision is a deliberately simple comparator: approve approved authentication; challenge a soft decline.

## 4. Fraud injection and truth boundary — `src/simulation/inject_fraud.py`

Fraud events are created after baseline events, in two phases. Each typology appears in both the training era and later evaluation era. A nested `add_event` function shares the transaction counter and event counter with its parent function; `nonlocal` means assignments update those parent-scope variables. It creates a raw transaction row and a separate truth row with an event ID and typology.

The returned `transactions` table contains no fraud field. The separate truth table contains injected transaction IDs and scenario metadata. `run_project.py` builds features first, then uses transaction IDs to construct an in-memory label for training and evaluation. This order keeps a future answer key out of the investigative feature process.

## 5. Point-in-time behavior — `src/features/build_features.py`

`sort_values(..., kind="stable")` processes transactions in timestamp order while retaining a predictable order for ties. `map` joins each customer's typical spend onto the event. `Amount_To_Typical_Spend` is current amount divided by that earlier-defined profile.

The rolling transaction count uses a `deque`, a double-ended queue. Before each event is scored, timestamps older than the prior 24-hour window are removed. The current event's features are then calculated from the remaining history; only afterward is the current timestamp appended. That order is the key point-in-time safeguard.

Terminal transaction count, distinct customers previously seen at a terminal, and prior customer-terminal pair count are held in dictionaries. These values are read before they are incremented, so none includes the current event. Time, channel, authentication, and region flags encode current context into numeric columns.

### Tiny timing example

Suppose the same customer's earlier event occurred at 1:05 p.m. and the current event is at 1:10 p.m. `Tx_Count_Prior_24h` includes the 1:05 event but not the 1:10 event. If the current amount is $120 and typical spend is $40, the amount multiple is 3.0; this is unusual context, not proof of fraud.

## 6. Explainable rules — `src/rules/score_rules.py`

Each `add(mask, points, label)` call checks a boolean condition for every row. Rows meeting it receive the named points and a reason string. Several weak signals can accumulate; extreme amount, repeated low-value activity, endpoint network burst, nighttime activity, authentication soft decline, and home-region mismatch are separately visible.

The score is capped at 100 so an unusual event with many signals remains on a familiar 0–100 scale. The reason list supports review and learning. The point values are policy assumptions; they need sensitivity checks, not claims of statistical truth.

## 7. Logistic baseline — `src/models/logistic_baseline.py`

`FEATURE_COLUMNS` is the allow-list of model inputs. Fraud labels, event IDs, typology names, and KYC band are not in it. The training matrix is converted to floating-point NumPy values. The model calculates means and standard deviations on training rows only, then standardizes each input; a zero standard deviation is changed to 1 to avoid division by zero.

The logistic model calculates `1 / (1 + exp(-linear_score))` to return a number between 0 and 1. Full-batch gradient descent repeatedly adjusts coefficients to reduce weighted logistic error. Positive-class weights are capped because fraud is rare. L2 regularization discourages extreme coefficients. This compact NumPy implementation is a teaching baseline, not a library-grade production learner.

The latest 30% of dates are held out. Earlier rows fit the coefficients and choose a threshold band; later rows are evaluated. This approximates the operational question: how does a strategy behave on events that occur after its model-building history?

## 8. Actions, review capacity, and costs — `src/decisions/policies.py`

Scores below the challenge threshold are approved; progressively higher scores are challenged, reviewed, or declined. The threshold grid is short and visible. Each candidate is applied to training labels and ranked by the configured training net cost; the selected band is then applied to the holdout.

Review candidates are sorted by score within each day. Only the top `capacity` remain in REVIEW. Overflow candidates become CHALLENGE, which models a practical fallback when investigator capacity is full.

`policy_costs` calculates one dollar-cost row at a time from the action, amount, fraud label (offline only), and `Economics`. Approved fraud costs amount plus chargeback. Challenged/reviewed fraud has residual expected loss after the assumed intervention effect. Legitimate approvals earn an assumed margin; challenges and reviews incur unit cost; a false decline incurs an assumed attrition share of lifetime value and lost margin.

`evaluate_policy` reports fraud value captured, remaining fraud loss, precision/recall among interventions, good-customer challenge/review counts, false declines, review overflow, and net cost. On the rare-event data, accuracy would mostly describe the many ordinary events, so it is not treated as the project objective.

## 9. Sensitivities, groups, and typologies — `src/run_project.py`

The capacity sensitivity reapplies selected score bands at daily capacities 1, 5, 15, 25, and 50. Economic scenarios change challenge effectiveness, false-decline attrition, or review recovery while holding decisions fixed. They show how assumptions change the comparison; they are not confidence intervals.

Group diagnostics summarize challenge, review, decline, false-decline, and planted fraud rates by segment, KYC band, and home region. They are descriptive outputs over fictional groups, not fairness certification. Typology metrics join the restricted truth table only after the strategy decisions have been made.

## 10. SQL, monitoring, and deliverables

`storage.py` writes CSV files and a local SQLite database with `pandas.to_sql`. SQLite is part of Python, so there is no server setup. Hidden truth is never added to the database. The `.sql` files are read-only investigation queries; `python sql/run_investigation.py` executes and prints their first twelve rows.

`monitoring.py` groups observable transactions by day. `shift(1)` makes the rolling 14-day mean and standard deviation use earlier days only. Three-sigma flags are screening alerts; they do not prove drift or fraud.

`reporting.py` creates a case study from the actual run and a standalone HTML dashboard. The dashboard controls select precomputed holdout outcomes by review capacity and economic scenario. `notebooks/01_investigation.ipynb` provides another way to inspect generated tables without loading hidden labels.

## 11. How to change and learn safely

Change one named assumption at a time. Run the pipeline again, compare the resulting files, and record why the change was made. Start with `src/config.py` for population, horizon, and economics; use command options for row counts and capacity. Do not change fraud labels or outcome logic to make a strategy appear successful. The best strategy can change when data or business assumptions change, and that trade-off is the central point of TrustHold.

