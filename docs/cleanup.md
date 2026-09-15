# Project cleanup and incoming-file integration

The sections below record the cleanup performed on 14 September 2026.
For the current structure and verification, see the September 15 update at the end.

The working branch now includes all three downloaded commits through `47cba0f`.
Local prototype changes were reconciled with the incoming files. Git has no
unresolved merge entries; the combined source edits are left uncommitted.

## Kept

- All four original checkpoints: `best.pt`, `pothole.pt`, `yolo11n.pt`,
  and the new `emergency.pt`.
- Both recordings: `road_test.mp4` and `ambulance_test.mp4`.
- The incoming command-center theme, navigation, map workspace, fleet panel and
  emergency panel, connected to the working backend rather than fixed demo totals.
- The Python video dashboard, durable delivery queue, operator authentication,
  resolution notes, status history, and geographic query optimization.
- Existing data: the two saved resolved issues and their 12 observations were
  unchanged during this cleanup.
- Incoming emergency and traffic rule modules, formatted as standalone prototype
  helpers. Their capabilities are described in the edge README.

## Consolidated

- One connected edge runner: `01_ai_edge/scripts/main.py`. The duplicate root
  runner was removed after preserving the incoming version.
- One inspection player: `01_ai_edge/scripts/preview.py`, including the new
  checkpoint/ambulance recording option. The incoming `test_emergency.py`
  graphical script was consolidated here.
- One frontend: `04_dashboard_frontend`. Its `main.jsx` only mounts the app;
  pages, API access and operator controls live in their own modules.
- The incoming CSS theme is formatted in `styles.css`; shared connected-page
  controls are in `connected.css`. Older shell styling was removed.
- The previously removed duplicate root scripts, old debug players and empty
  placeholder files remain removed. Environments, installed dependencies,
  models, videos and runtime data were not cleared.

## Recovery and verification

`docs/before-new-files-cleanup.zip` contains the pre-integration working source,
the original incoming source under `incoming-47cba0f/`, and a pre-cleanup asset
checksum list. It excludes credentials, dependencies, datasets, databases and
binary model/video assets. Those assets remain in their original locations.
The earlier `docs/project-before-cleanup.zip` is also retained. Both are ignored
local recovery archives, not application inputs.

All six model/video assets match their Git blobs. All pre-existing asset SHA-256
checksums match the recovery record. `tools/check_models.py` verifies the four
model files against `01_ai_edge/models/manifest.json`.

After integration: 55 Python tests, six frontend service tests, the Vite build,
Python syntax checks and standalone rule checks passed. The new model preview
processed two ambulance-video frames and returned eight general-object boxes.
Backend health, dashboard and proxied statistics requests returned HTTP 200.
The browser runtime reported no available browser, so browser visual/interaction
QA is still pending.

## Model finding

The newly supplied `emergency.pt` has 80 general-object labels and no ambulance
class. `best.pt` still has one unnamed class. Neither file was renamed, removed,
retrained or represented as an evaluated emergency/RAD detector. The supplied
pothole checkpoint remains the connected detector. See the model-folder README
and [testing record](testing.md) for the exact prototype scope.

## September 15 repository handoff

The repository now includes upstream changes through `3c42b44`, five original
checkpoints and both recordings. The root README documents the runnable project;
each of the six module folders has a README, and docs/README.md indexes the guides.
The pending cleanup removes duplicate root scripts, obsolete debug players and
empty placeholders from the Git tree. Source modules, tests, fixtures, lockfiles,
configuration examples and model metadata are included in the handoff.

Root ignore rules protect local passwords, environment overrides, databases,
installed dependencies, generated output, review frames, backups and editor/agent
settings. Curated checkpoints under 01_ai_edge/models remain tracked. The latest
verified result is 68 Python tests, 11 frontend tests and a production build; all
five model hashes match the inventory. See pull-20260915.md for conflict decisions.
