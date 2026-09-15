# Implementation status — 14 September 2026

The integrated software implementation is present. Final model/data acceptance and
interactive browser/camera verification remain pending. The original assessment is
a historical baseline; this file describes the current result.

The default Python video player now includes shared **Dashboard** and **Alerts**
tabs with operator sign-in, issue observations, resolution notes, status history and confirmed resolution. Its changes
use the existing backend API and appear in the React dashboard too. The bundled
recording still uses explicitly simulated location data.

| Plan tasks | Result |
| --- | --- |
| C1–C2 | Implemented contract and shared fixtures; prototype defaults are documented |
| E1–E4 | Modular video/model pipeline, per-object validation, simulated location, durable retry delivery and background heartbeat implemented |
| E5 | Webcam input implemented; physical camera behavior not exercised |
| M1, M3 | One-class pothole model interface, audit/split/validation tools, training and measured-report generation implemented |
| M2, M4 | Pending: no labeled dataset supplied; no custom training or accuracy/holdout evaluation claimed |
| B1–B4 | Transactional observations/issues/buses, idempotency, matching, filters, status authorization, telemetry, statistics, analytics and explicit legacy migration implemented and tested |
| F1–F4 | API-connected pages, shared mock adapter, error/empty/stale states and resolution flow implemented; build and service tests pass; browser interaction QA pending |
| L1–L4 | Shared importable GPS, validation, distance, matching, review priority and unknown-severity functions implemented and connected |
| C3–C5 | Simulator, integration tests, dependency lock, configuration and setup/demo/readiness documentation implemented; browser portion of C4 pending |
| C6 | Branch/release handoff procedure documented; final release tag awaits readiness gates and team integration |

The usable bundled `pothole.pt` is provisional. The unrelated/unnamed `best.pt` and
sample video were preserved. The legacy GPS helper files were replaced by the
importable package, and the old API's data file remains separate from v2 storage.

No browser was available through the browser runtime during this implementation;
that is a verification limitation, not a passing UI test. See [testing.md](testing.md)
for exact completed checks and the remaining acceptance list.

## Latest incoming files

The working branch includes origin/main through `3c42b44`. All five checkpoints
and both recordings are preserved. The new `ambulance.pt` exposes a named
ambulance class; its evaluation and connection to shared alerts remain pending.
The older `emergency.pt` exposes general objects. Emergency/traffic rule modules
and the incoming in-memory clustering helper remain standalone examples. Active
location matching uses the shared package and persistent issue IDs.
See [cleanup](cleanup.md), [model metadata](../01_ai_edge/models/README.md), and
[the prioritized reviewer roadmap](reviewer-roadmap.md).

## Backend review workflow upgrade

Annotated road images are saved by default and travel through the outbox atomically
with observations. The API still accepts metadata-only reports. Python and web issue review show these images. Both interfaces
support resolved, false detection (reason required) and reopened states, retain
history, and guard against stale conflicting status updates. Filtered CSV export
is available from web Alerts. Old metadata-only retries remain idempotent.

Validation now includes 68 Python tests, 11 frontend service tests and a passing
production build. A real model run added two image-backed observations to one new
open demo issue while preserving all pre-existing records. GPS remains simulated;
model accuracy, route coverage and emergency recognition remain future work.

## Image gallery and training preparation

Command Center shows the latest image and a detection photo stream. Incidents
opens a paginated gallery with status, priority and date filters; the issue-list
view retains older records without images. Map popups show the latest saved image.
Each photo links to the issue review page and the original saved JPEG.

The training preparation script samples source frames and writes unverified model
proposals and recording groups for human annotation. It never creates ground-truth
labels from predictions. Training and holdout evaluation remain pending data.
