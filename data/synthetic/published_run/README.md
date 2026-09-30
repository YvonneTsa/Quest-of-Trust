# Complete synthetic run snapshot

This folder contains every CSV table from the generated TrustHold run, split into GitHub-friendly parts. The data are fully synthetic. `fraud_ground_truth` is provided for transparent offline evaluation and must remain separate from model inputs and observable SQL investigations.

Restore all original CSV tables, joining each table's parts and verifying SHA-256 checksums:

```powershell
python -m scripts.assemble_dataset
```

The restored observable CSV tables and `fraud_ground_truth.csv` will be placed under `data/synthetic/run/`; labels go under `data/synthetic/run/restricted/`. The SQLite database can be rebuilt, with the current schema and public-table separation, by running:

```powershell
python -m src.run_project
```

`manifest.json` lists every part, row count, ground-truth status, and original-file checksum.

