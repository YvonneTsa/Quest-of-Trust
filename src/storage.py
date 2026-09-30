"""Persist versioned CSV artifacts and an SQLite analytical database."""

import sqlite3
from pathlib import Path

import pandas as pd


def save_run(output_dir: Path, tables: dict[str, pd.DataFrame]) -> Path:
    """Write named tables to CSV and to a local SQLite database."""
    output_dir.mkdir(parents=True, exist_ok=True)
    database_path = output_dir / "trusthold.sqlite"
    with sqlite3.connect(database_path) as connection:
        for name, frame in tables.items():
            safe = frame.copy()
            safe.to_csv(output_dir / f"{name}.csv", index=False)
            safe.to_sql(name, connection, if_exists="replace", index=False)
    return database_path
