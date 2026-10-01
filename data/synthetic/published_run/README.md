# Complete synthetic run snapshot

This folder contains the generated TrustHold snapshot as 21 CSV tables split into GitHub-friendly parts: 20 public analytical tables (797,106 rows total) and 700 separate planted-fraud labels. The underlying seed contains 246,314 events, including 700 planted fraud events, with 350 planted fraud events in each later-period holdout. The data are fully synthetic. `fraud_ground_truth` is provided for transparent offline evaluation and must remain separate from model inputs and observable SQL investigations.

Restore all original CSV tables, joining each table's parts and verifying SHA-256 checksums:

```powershell
python -m scripts.assemble_dataset
```

The restored observable CSV tables and `fraud_ground_truth.csv` will be placed under `data/synthetic/run/`; labels go under `data/synthetic/run/restricted/`. The SQLite database can be rebuilt, with the current schema and public-table separation, by running:

```powershell
python -m src.run_project
```

`manifest.json` lists every part, row count, ground-truth status, and original-file checksum.
