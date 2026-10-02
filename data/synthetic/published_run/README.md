# Complete synthetic run snapshot

This folder contains the generated TrustHold snapshot as 29 CSV tables split into 480 GitHub-friendly parts: 28 public analytical tables (1,093,694 rows total) and 700 separate synthetic fraud labels. The base seed contains 246,314 events. Its later-date test period contains 350 simulated fraud cases; the nested campaign-identity check contains 175 cases in this default seed. Primary stability outputs summarize 30 deterministic later-date runs. All data and outcomes are synthetic. `fraud_ground_truth` supports transparent offline evaluation and must remain separate from model inputs and observable SQL investigations.

Restore all original CSV tables, joining each table's parts and verifying SHA-256 checksums:

```powershell
python -m scripts.assemble_dataset
```

The restored observable CSV tables and `fraud_ground_truth.csv` will be placed under `data/synthetic/run/`; labels go under `data/synthetic/run/restricted/`. The SQLite database can be rebuilt, with the current schema and public-table separation, by running:

```powershell
python -m src.run_project
```

`manifest.json` lists every part, row count, ground-truth status, and original-file checksum.
