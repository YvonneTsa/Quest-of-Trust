"""Run each SELECT in this folder against the generated SQLite database."""

import argparse
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "synthetic" / "run" / "trusthold.sqlite"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DB_PATH)
    database_path = parser.parse_args().database
    if not database_path.exists():
        raise SystemExit("Run `python -m src.run_project` before the SQL investigation.")
    with sqlite3.connect(database_path) as connection:
        for query_path in sorted(Path(__file__).parent.glob("*.sql")):
            query = query_path.read_text(encoding="utf-8")
            cursor = connection.execute(query)
            names = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            print(f"\n## {query_path.name}")
            print(" | ".join(names))
            for row in rows[:12]:
                print(" | ".join(str(value) for value in row))
            print(f"(showing {min(12, len(rows))} of {len(rows)} rows)")


if __name__ == "__main__":
    main()
