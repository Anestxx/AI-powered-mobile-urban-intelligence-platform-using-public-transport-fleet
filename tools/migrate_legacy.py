"""Preview or explicitly import eligible legacy alerts without changing the source database."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import sqlite3
import sys
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_backend_database"))
from app.config import Settings
from app.database import Base, create_database
from app.schemas import ObservationCreate
from app.services import accept_observation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "03_backend_database/database/urban_sensing.db")
    parser.add_argument("--source-id", default="legacy", help="Stable unique namespace for this source database")
    parser.add_argument("--database-url", default=Settings().database_url)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--location-source", choices=["simulated", "gps"])
    parser.add_argument("--legacy-timezone", help="Explicit timezone for legacy timestamps, e.g. UTC or Asia/Kolkata")
    parser.add_argument("--assume-gps-at-detection", action="store_true", help="Acknowledge that legacy records contain no independent GPS timestamp")
    args = parser.parse_args()
    if not args.source.is_file():
        parser.error("Source database does not exist")
    target_path = make_url(args.database_url).database
    if target_path and target_path != ":memory:" and Path(target_path).resolve() == args.source.resolve():
        parser.error("The destination database must differ from the legacy source")
    with sqlite3.connect(args.source.resolve().as_uri() + "?mode=ro", uri=True) as source:
        source.row_factory = sqlite3.Row
        rows = [dict(row) for row in source.execute("SELECT * FROM alerts ORDER BY id")]
    print(f"Legacy source: {len(rows)} rows. Source database will remain unchanged.")
    if not args.apply:
        print(f"Pothole rows: {sum(row.get('event_type') == 'pothole' for row in rows)}")
        print("Preview only. Apply requires explicit location source, legacy timezone and GPS-time assumption. Invalid rows are skipped and reported.")
        return
    if not args.location_source or not args.legacy_timezone or not args.assume_gps_at_detection:
        parser.error("Apply requires --location-source, --legacy-timezone and --assume-gps-at-detection")
    zone = ZoneInfo(args.legacy_timezone)
    engine, factory = create_database(args.database_url)
    Base.metadata.create_all(engine)
    imported = skipped = 0
    try:
        for row in rows:
            try:
                timestamp = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=zone)
                payload = ObservationCreate(event_id=uuid5(NAMESPACE_URL, f"codyssey:{args.source_id}:{row['id']}"), event_type=row["event_type"], bus_id=row["bus_id"],
                    confidence=row["confidence"], latitude=row["latitude"], longitude=row["longitude"], timestamp=timestamp, gps_timestamp=timestamp,
                    location_source=args.location_source, bbox=json.loads(row["bbox"]) if row.get("bbox") else None, model_version=f"legacy:{args.source_id}")
                with factory() as db:
                    accept_observation(db, payload, Settings(database_url=args.database_url))
                imported += 1
            except Exception as exc:
                skipped += 1
                print(f"Skipped legacy ID {row.get('id')}: {exc}")
    finally:
        engine.dispose()
    print(f"Imported/previously accepted: {imported}; skipped: {skipped}. Old severity remains available in the unchanged source; new severity is unknown.")
    if skipped:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
