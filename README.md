# CODYSSEY ? Mobile Urban Intelligence

A reviewer prototype that turns recorded road footage into pothole observations,
groups nearby reports, and lets operators inspect images and resolve issues from
a Python video player or a React dashboard.

**Current scope:** actual pothole inference on bundled footage, simulated bus GPS,
and local operator review. Five model checkpoints and two recordings are included.
The new ambulance checkpoint is preserved; ambulance alert integration, accident
detection and measured model accuracy remain pending.

[Demo walkthrough](docs/demo-flow.md) ? [Architecture](docs/architecture.md) ?
[API contract](docs/api-contract.md) ? [Project status](docs/implementation-status.md) ?
[Documentation](docs/README.md)

## What works

- Moving road video with detection boxes, confidence and approximate simulated location.
- Durable alert delivery with retries, duplicate protection and saved detection images.
- Command Center, incident photo gallery, image previews on the map, fleet and analytics.
- Shared issue review: resolve, dismiss an incorrect detection with a reason, or reopen.
- Preserved observations, review history and filtered CSV export.
- Dataset preparation, source-based splitting, validation, training and evaluation tools.

## Install on Windows

The tested environment uses Python 3.10 and Node.js 25. From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
cd 04_dashboard_frontend
npm ci
cd ..
```

`requirements.txt` contains the direct dependencies; `requirements-lock.txt`
records the tested versions. Both install the local location-intelligence package.
Virtual-environment activation is optional when using the commands shown here.

## Run the project

Start the backend in terminal 1:

```powershell
.\.venv\Scripts\python.exe run_backend.py
```

Start the dashboard in terminal 2:

```powershell
cd 04_dashboard_frontend
npm run dev
```

Open **http://127.0.0.1:5173**. API documentation is at
http://127.0.0.1:8000/docs. A fresh clone starts with an empty database; run the
video player to create real model observations from the bundled recording.

Start the connected video player in terminal 3:

```powershell
.\.venv\Scripts\python.exe 01_ai_edge/scripts/main.py --start-frame 450 --loop --cpu-threads 2
```

The video starts near the pothole segment. Use **Pause video**, **Resume video**
or **Close player**. The recording loops for viewing; only the first pass submits
alerts. Saved images include a detection box and surrounding road context.

The web dashboard refreshes every two seconds. Open **Incidents ? Photo gallery**
to see all saved images, select **Review** to inspect an issue, or use **Open image**
to view a JPEG. **Issue list** also includes older records without images.
The Python player has shared **Dashboard**, **Alerts** and **Saved evidence** views.

### Review and resolve

Click **Operator sign in** and use the password generated on first backend startup
in `03_backend_database/database/operator-password.txt`. Choose a review action,
add a note and confirm. Marking a false detection requires a reason. Both
interfaces show the saved status and retain the original evidence and history.

**Incidents ? Download issues CSV** exports the filtered issue list, including
records beyond the displayed page. Closing or pausing the video does not remove
saved issues. Local authentication is intended for this loopback-hosted prototype.

### Other inputs and delivery recovery

```powershell
# Another recording, or use --source 0 for a webcam
.\.venv\Scripts\python.exe 01_ai_edge/scripts/main.py --source "D:/videos/road.mp4"

# Short run without opening the player
.\.venv\Scripts\python.exe 01_ai_edge/scripts/main.py --headless --start-frame 560 --max-frames 12

# Retry queued observations after a connection outage
.\.venv\Scripts\python.exe 01_ai_edge/scripts/main.py --flush-only
```

`--offline` queues observations locally. `--no-save-evidence` disables image
capture; images are saved by default. `--video-only` selects the compact OpenCV
player. See the [edge guide](01_ai_edge/README.md) for all options.

For a repeatable metadata-only scenario, run `tools/simulate_events.py` after
starting the backend. It sends explicitly simulated reports and heartbeats,
checks grouping and retries, and preserves existing data.

## Repository structure

| Folder or file | Purpose |
| --- | --- |
| [01_ai_edge](01_ai_edge/README.md) | Video inference, tracking, delivery queue, operator window, checkpoints and recordings |
| [02_dataset_model_training](02_dataset_model_training/README.md) | Dataset audit, labeling preparation, splitting, training and evaluation |
| [03_backend_database](03_backend_database/README.md) | FastAPI, SQLite observations/issues, evidence and operator sessions |
| [04_dashboard_frontend](04_dashboard_frontend/README.md) | React command center, map, gallery, fleet and review controls |
| [05_gps_gis_prioritization](05_gps_gis_prioritization/README.md) | Shared GPS validation, distance, matching and review priority |
| [06_integration_testing_demo](06_integration_testing_demo/README.md) | Integration tests and reviewer demonstration checks |
| [contracts/fixtures](contracts/fixtures/README.md) | Shared, explicitly simulated contract examples |
| [docs](docs/README.md) | Architecture, API, demo, verification and project status |
| `tools/` | Model checks, event simulation, benchmarking and legacy migration |
| `run_backend.py` | Backend entry point from the repository root |

The connected application has one edge runner, one backend and one frontend.
Old duplicate root scripts, debug players and empty placeholders have been
consolidated. Models and recordings retain their original paths and bytes.

## Models and training

| Checkpoint | Current role |
| --- | --- |
| `pothole.pt` | Active detector; one named pothole class |
| `ambulance.pt` | One named ambulance class; evaluation and alert integration pending |
| `emergency.pt` | General-object checkpoint; does not expose emergency-vehicle classes |
| `yolo11n.pt` | General-object preview and local training initialization |
| `best.pt` | Preserved checkpoint with unnamed class `0`; meaning needs confirmation |

[Model metadata](01_ai_edge/models/README.md) records class names and checksums.
No checkpoint was retrained or replaced during repository cleanup. No labeled
training/validation/test dataset has been supplied. The training guide explains
how to prepare frames for human annotation and evaluate versioned replacement
weights. Model proposals are never treated as verified training labels.

## Configuration and local data

Copy the relevant `.env.example` to `.env` in the edge, backend or frontend folder
to override defaults. The dashboard uses Vite's `/api` proxy to port 8000.
`VITE_USE_MOCKS=true` enables clearly labeled fixture data for frontend development.

The backend creates `03_backend_database/database/codyssey_v2.db` and its operator
password locally. The edge creates its alert log and durable outbox under
`01_ai_edge/alerts/`. Runtime data, credentials, generated training frames, local
backups, editor settings and installed dependencies are excluded from Git.
Curated checkpoints in `01_ai_edge/models/` and both demo videos are tracked.

For an existing legacy database, see the [migration guide](docs/integration.md).
The migration tool preserves the source and requires explicit location/timezone
assumptions.

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s 06_integration_testing_demo -v
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe tools/check_models.py
cd 04_dashboard_frontend
npm test
npm run build
```

Verified: **68 Python tests**, **11 frontend service tests**, production build,
model checksums and actual recorded-video alert/image delivery. Browser interaction
and physical camera testing remain pending. See the [testing record](docs/testing.md).

## Prototype limits

- GPS follows a simulated route and represents approximate bus position.
- Matching within 25 metres can merge distinct nearby potholes. Simulated and real
  GPS reports are kept separate.
- Priority reflects distinct reporting buses; physical damage severity is unknown.
- The confidence threshold is provisional. Labeled holdout accuracy, accident
  detection and ambulance alert integration have not been established.
- Map tiles and optional web fonts need internet. CPU inference speed depends on
  the device; `--cpu-threads 2` improved the measured run on the development laptop.

See the [reviewer roadmap](docs/reviewer-roadmap.md) for the next development tasks.
