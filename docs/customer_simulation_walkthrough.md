# Customer simulation walkthrough

This guide explains the customer generator in plain language and gives the reason for each design choice. The code lives in `src/simulation/generate_customers.py`; run it from PowerShell at the repository root with `python -m src.simulation.generate_customers`.

## 1. Imports and file locations

`Path` from Python's standard library builds file-system paths safely across Windows and other operating systems. `numpy` provides a seeded random generator and the log-normal distribution. `pandas` stores customer attributes in a table and writes a CSV file.

`Path(__file__).resolve()` finds the full path of this Python file. `.parents[2]` walks from `src/simulation/generate_customers.py` to the repository root. Building `OUTPUT_PATH` from that root means the output always lands in `data/synthetic/customers.csv`, even if PowerShell is currently in a different folder.

## 2. Reproducibility and learning sample

`SEED` is the starting state for pseudo-random draws. `np.random.default_rng(SEED)` creates a generator. Using the same seed and same settings produces the same profiles again, which makes debugging and explanation easier. The earlier saved script used 20 customers, so `N_CUSTOMERS = 20` preserves that observed state. The roadmap snapshot's earlier value of 10 is recorded as historical context, not silently substituted.

Inside `generate_customers`, a fresh generator is created for each call. This makes two calls with the same count return the same table instead of depending on whether some other code has already consumed random values. `n_customers < 1` is rejected because a zero-row or negative-size simulation would not be useful here.

## 3. Segment sampling

`SEGMENTS` lists the three fictional customer groups. `SEGMENT_PROBABILITIES` pairs each group with its sampling chance in the same order; the values add to 1. `customer_rng.choice(..., size=n_customers, p=...)` makes one random category selection for each customer. A 20-row sample can differ from exactly 70/20/10; the probabilities describe the generator, not a quota.

## 4. Customer identifiers

`range(1, n_customers + 1)` generates numbers from 1 through the requested count because Python stops before the upper bound. The f-string format `:06d` pads each number to six digits, giving IDs such as `C000001`. Stable IDs make it possible to link customer rows to future account and transaction tables.

## 5. Spend and transaction-rate profiles

The two dictionaries map each segment to a fictional median profile value. The list comprehensions look up the matching value for each sampled segment while preserving row order. `np.lognormal(mean=np.log(median_values), sigma=...)` turns each segment median into a positive, right-skewed customer value. `SPEND_LOG_SIGMA` and `TRANSACTION_RATE_LOG_SIGMA` describe spread in log space; they are assumptions, not fitted estimates.

`Typical_Transactions_Per_Day` is a decimal latent rate. It is not an observed count. Later, a count-generation process can use this profile to make integer transaction events over time.

## 6. Region and KYC attributes

The region list and its probability list define a fictional location mix. The KYC list and probabilities define fictional low/medium/high onboarding-risk bands. Separate random draws keep these fields independent of segment, spend, transaction rate, and each other in this first version. In particular, KYC risk does not label a customer as fraudulent. Fraud ground truth will be generated later through explicit scenarios.

## 7. DataFrame and rounding

The returned `pandas.DataFrame` creates one column for each customer attribute. `.round(2)` rounds displayed spend and rate values to two decimal places; it does not change the underlying distribution design. Customer ID and category columns remain text values.

## 8. Saving and inspecting output

`OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)` creates `data/synthetic/` if it is missing and does not fail if it already exists. `to_csv(..., index=False)` writes rows and headers without an extra DataFrame index column. `head(10)` shows a manageable sample. `groupby("Segment")` and `agg(...)` summarize counts and spend ranges so the simulated profile can be inspected before adding more entities.

## Why this matters to a fraud/risk analyst

The generator separates customer context from fraud labels and makes assumptions visible. It provides a controlled starting point for asking whether behavior departs from an individual's baseline. A large spend or high KYC band is context, not proof of fraud. The next milestones can link these profiles to accounts, merchants, terminals, and time-stamped legitimate transactions before any fraud is injected.
