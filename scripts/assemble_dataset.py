"""Reassemble the versioned CSV parts published with TrustHold."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "synthetic" / "published_run"
DEFAULT_DESTINATION = ROOT / "data" / "synthetic" / "run"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def assemble(source: Path, destination: Path) -> list[Path]:
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    destination.mkdir(parents=True, exist_ok=True)
    restored = []
    for table_name, table in manifest["tables"].items():
        output = destination / f"{table_name}.csv"
        with output.open("wb") as target:
            for part_name in table["parts"]:
                part = source / part_name
                if not part.is_file():
                    raise FileNotFoundError(f"Dataset part missing: {part}")
                with part.open("rb") as stream:
                    header = stream.readline()
                    if target.tell() == 0:
                        target.write(header)
                    else:
                        # Every part has a header; retain only the first one.
                        pass
                    shutil.copyfileobj(stream, target)
        expected_hash = table["sha256"]
        actual_hash = sha256(output)
        if actual_hash != expected_hash:
            output.unlink(missing_ok=True)
            raise ValueError(
                f"Checksum mismatch for {output.name}: expected {expected_hash}, got {actual_hash}"
            )
        if table_name == "fraud_ground_truth":
            restricted = destination / "restricted"
            restricted.mkdir(parents=True, exist_ok=True)
            target = restricted / output.name
            output.replace(target)
            output = target
        restored.append(output)
    return restored


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    outputs = assemble(args.source, args.destination)
    print(f"Restored and checksum-verified {len(outputs)} tables into {args.destination}")


if __name__ == "__main__":
    main()

