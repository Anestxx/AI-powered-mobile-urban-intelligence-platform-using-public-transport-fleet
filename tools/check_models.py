"""Verify that every preserved checkpoint still matches its recorded SHA-256."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / "01_ai_edge/models/manifest.json").read_text(encoding="utf-8"))
    failures = []
    for entry in manifest["models"]:
        path = ROOT / entry["path"]
        if not path.is_file():
            failures.append(f"Missing: {entry['path']}")
            continue
        checksum = hashlib.sha256()
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                checksum.update(block)
        if path.stat().st_size != entry["bytes"] or checksum.hexdigest() != entry["sha256"]:
            failures.append(f"Changed: {entry['path']}")
        else:
            print(f"OK: {path.name} ({len(entry['classes'])} recorded classes)")
    if failures:
        print("\n".join(failures))
        return 1
    print("All preserved model checksums match. This verifies files, not model accuracy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
