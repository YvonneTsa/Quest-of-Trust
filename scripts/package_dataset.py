"""Split a generated TrustHold run into GitHub-friendly CSV parts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "synthetic" / "run"
DEFAULT_DESTINATION = ROOT / "data" / "synthetic" / "published_run"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def package(source: Path, destination: Path, max_bytes: int) -> dict:
    if max_bytes < 1024:
        raise ValueError("--max-bytes must be at least 1024")
    if not source.is_dir():
        raise FileNotFoundError(f"Generated run directory not found: {source}")

    destination.mkdir(parents=True, exist_ok=True)
    for old_part in destination.glob("*.part*.csv"):
        old_part.unlink()

    manifest = {"format": 1, "source": "synthetic only", "tables": {}}
    csv_files = sorted(source.glob("*.csv"))
    hidden_truth = source / "restricted" / "fraud_ground_truth.csv"
    if hidden_truth.exists():
        csv_files.append(hidden_truth)
    if not csv_files:
        raise FileNotFoundError(f"No generated CSV outputs found in {source}")

    for path in csv_files:
        table_name = "fraud_ground_truth" if path == hidden_truth else path.stem
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream)
            header = next(reader, None)
            if header is None:
                continue
            header_bytes = (csv_line(header)).encode("utf-8")
            part_paths: list[Path] = []
            index = 1
            output = None
            output_bytes = 0
            rows = 0
            try:
                for row in reader:
                    line = (csv_line(row)).encode("utf-8")
                    if output is None or (output_bytes + len(line) > max_bytes and rows > 0):
                        if output is not None:
                            output.close()
                        part = destination / f"{table_name}.part{index:03}.csv"
                        index += 1
                        output = part.open("wb")
                        output.write(header_bytes)
                        output_bytes = len(header_bytes)
                        part_paths.append(part)
                        rows = 0
                    output.write(line)
                    output_bytes += len(line)
                    rows += 1
            finally:
                if output is not None:
                    output.close()

        manifest["tables"][table_name] = {
            "parts": [part.name for part in part_paths],
            "rows": sum(count_rows(part) for part in part_paths),
            "sha256": sha256(path),
            "ground_truth": table_name == "fraud_ground_truth",
        }

    manifest_path = destination / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def csv_line(row: list[str]) -> str:
    import io

    buffer = io.StringIO(newline="")
    csv.writer(buffer, lineterminator="\r\n").writerow(row)
    return buffer.getvalue()


def count_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return max(0, sum(1 for _ in csv.reader(stream)) - 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument("--max-bytes", type=int, default=300_000)
    args = parser.parse_args()
    manifest = package(args.source, args.destination, args.max_bytes)
    parts = sum(len(table["parts"]) for table in manifest["tables"].values())
    rows = sum(table["rows"] for table in manifest["tables"].values())
    print(f"Packaged {len(manifest['tables'])} tables, {rows:,} rows into {parts} parts.")
    print(f"Manifest: {args.destination / 'manifest.json'}")


if __name__ == "__main__":
    main()
