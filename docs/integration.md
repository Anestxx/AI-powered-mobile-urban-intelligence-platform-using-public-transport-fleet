# Integration and configuration

Use the root README's Windows commands. The Python lock and npm lock record the
tested dependency set. Keep the numbered module directories; the location package
is installed editable through the root requirements files.

The software handoff is contract → shared fixtures → backend/location transactions
→ API-connected UI → edge outbox/heartbeat → model evaluation. The event simulator
allows integration to proceed without a final trained model. The normal application
uses live backend records; fixture mode must be explicitly enabled.

## Migrating earlier data

`tools/migrate_legacy.py` previews `urban_sensing.db` by default. It opens the source
read-only and does not alter it. The target must be a different database. If legacy
timestamps and GPS source are known, an explicit import can be performed:

```powershell
.\.venv\Scripts\python.exe tools/migrate_legacy.py --apply --location-source simulated --legacy-timezone UTC --assume-gps-at-detection
```

Those flags assert knowledge; do not use them if the original source/timezone is
unknown. Legacy records have no independent GPS timestamp, hence the additional
assumption must be acknowledged. Supported, valid pothole rows receive deterministic
event IDs under a stable `--source-id` namespace. Repeating import is idempotent.
Invalid/unsupported rows are reported and remain in the old database. Their original
severity is preserved there; the new issue severity is unknown. Distinct legacy
databases should have distinct source IDs.

## Team integration process

Each member develops within their module branch. Changes to shared fields, fixtures
or priority/matching rules require an accompanying contract update. Integrate reviewed
changes with passing tests; a push alone does not mean a merge. Use a dedicated
integration branch and identify a release only after the readiness gates pass.

A reproducible model/demo handoff includes code revision, dependency locks, model
checksum, dataset/split manifest, measured model report and test evidence. Keep large
models/videos in agreed release storage with checksums. No repository pushes, merges
or release tags were performed by this implementation task.
