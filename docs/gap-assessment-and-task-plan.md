# CODYSSEY: gap assessment and team task plan

Assessment date: 13 September 2026. Scope: compare the current project with the supplied six-member assignment and plan the work. Application code was not changed for this assessment.

**The project has runnable components, but the complete six-member workflow is not implemented.** The largest gaps are the observation/issue data model, live dashboard integration, video-linked GPS, and agreement on the pothole model contract. The earlier cleanup repaired execution problems; it did not implement these new requirements.

The supplied text repeats Members 1 and 2, and the Member 3 section ends mid-sentence. This assessment treats the repeated sections once and uses the explicit API and integration requirements in Members 4–6 to assess the backend. Proposed decisions below are planning recommendations, not an already agreed contract.

## 1. Current readiness

| Owner | Existing work to reuse | Main gap | Readiness against assignment |
| --- | --- | --- | --- |
| Member 1: Edge AI | Video runner, real pothole inference, boxes, confidence thresholds, temporal checks, cooldown, local JSON logging, HTTP submission | Per-object duplicate handling, stable submitted event IDs, modular sender/video configuration, GPS integration, heartbeat, optional durable retries | Partial; a local inference demonstration runs |
| Member 2: Dataset/model | Frame extraction, dataset preparation/import/validation, CPU/CUDA training and evaluation scripts | No training dataset or evaluation evidence; current training configuration is six-class RAD instead of one-class pothole | Tooling exists; custom model deliverable is unverified |
| Member 3: Backend | FastAPI, SQLite, alert create/list/detail/delete, statistics, health, input range checks | Separate issues/observations/buses, retry deduplication, matching, filters/pagination, status updates, telemetry, new statistics | Partial; current API contract differs substantially |
| Member 4: Frontend | React/Vite, Leaflet, styled dashboard, mock events, selection/filter controls | API service layer, actual pages, persisted resolution, buses/analytics, loading/error/stale states | Visual prototype; disconnected from backend |
| Member 5: Location | Coordinate simulator, Haversine distance, temporary multi-bus corroboration, priority helper | Importable package, video-time GPS, freshness validation, matching against persisted open issues, explainable priority, unknown severity | Standalone helpers; not integrated |
| Member 6: Integration | Root setup guide, dependencies, backend launcher, ignore rules, 14 regression tests | Shared contract/fixtures, simulator, end-to-end tests, migration/setup decisions, demo/readiness documentation | Cleanup baseline exists; integration work remains |

Keep the current numbered folders as ownership boundaries. Creating another `edge-ai/`, `backend/`, or `frontend/` tree would duplicate the project. Add the requested internal structure within the existing folders, and place shared contracts/tools at the root.

## 2. Evidence and verification limits

These results were established during the preceding cleanup and recorded in [cleanup.md](cleanup.md):

- 14 automated tests passed, covering existing alert behavior, the current API, dataset validation, location helpers, and handling of unknown model labels.
- Backend startup from another working directory returned HTTP 200 for health and OpenAPI.
- The frontend production build passed.
- The edge gateway processed six video frames and two CPU inferences. A separate pothole preview returned five predictions at frame 560.
- Dependency consistency, Python syntax, backup integrity, and basic dataset import safeguards passed.

This assessment re-inspected the source; it did not rerun or expand those checks. Existing tests do not establish model accuracy, unseen-video performance, GUI behavior, persistence across backend restarts, or the requested complete workflow. In particular, the current API round-trip test submits a prepared observation payload; it is not a camera-to-dashboard test.

| Evidence | What it establishes |
| --- | --- |
| [Edge runner](../01_ai_edge/scripts/main.py), [detector](../01_ai_edge/scripts/detector.py), [alert manager](../01_ai_edge/scripts/alert_manager.py) | Current inference, payload, timing, duplicate and severity behavior |
| [Training configuration](../02_dataset_model_training/training/data.yaml), [training script](../02_dataset_model_training/training/train.py), [evaluation script](../02_dataset_model_training/training/validate_model.py) | Current six-class target and available tooling |
| [Database models](../03_backend_database/app/models.py), [schemas](../03_backend_database/app/schemas.py), [routes](../03_backend_database/app/routes.py) | Single alert table and existing request/response contract |
| [Frontend entry point](../04_dashboard_frontend/src/main.jsx) | Hardcoded events, buses and totals; no backend requests |
| `project-before-cleanup.zip` (local recovery archive, excluded from Git) | Standalone behavior at assessment time; subsequently replaced by `location_intelligence` |
| [Regression tests](../06_integration_testing_demo/test_backend.py) | The assessment began with 14 checks and an isolated in-memory API database; the linked suite has since been expanded |

## 3. Decisions that come first

Member 6 owns recording these decisions in a future `docs/api-contract.md`, with the listed owners reviewing their interfaces. No team approvals or implementation are implied by this plan.

| Decision | Current conflict | Proposed agreement | Owners |
| --- | --- | --- | --- |
| Prototype target | Code supports RAD categories; assignment starts with potholes | Make `pothole` the initial shared event type. Keep RAD work as a separate future capability | 1, 2, 3, 6 |
| Model identity | `best.pt` exposes `{0: '0'}`; `pothole.pt` exposes `{0: 'pothole'}` | Use the labeled pothole model as a provisional integration artifact. Validate any replacement's class names, provenance and performance; renaming a file does not establish compatibility | 1, 2 |
| IDs and retries | Local `alert_id` is omitted from HTTP payload; backend assigns an unrelated integer | Edge generates `event_id` once per observation and retains it across retries. Backend generates a separate `issue_id` | 1, 3, 6 |
| Required location/time | Coordinates, bus and timestamp are optional in the API; timezone is not enforced | Require event ID, bus ID, type, confidence, coordinates, timezone-aware timestamp and `location_source`. Propose required `gps_timestamp` so freshness can be checked against detection time | 1, 3, 5, 6 |
| Optional evidence | Bounding box is currently a JSON string | Agree on an optional numeric `[x1, y1, x2, y2]` array. Do not add image delivery without an evidence API | 1, 3, 4 |
| Severity and priority | Potholes are automatically high severity; priority uses confidence | Keep severity `unknown`. Derive review priority on the backend using Member 5's rule: one distinct bus low, two medium, three or more high; return reason and rule version | 3, 5, 6 |
| Counting | Current totals count alert rows | `report_count` counts unique accepted observations. Maintain a separate distinct-bus count for priority. Retries increase neither | 3, 4, 5, 6 |
| Issue matching | In-memory nearby observations expire after 300 seconds; no issue identity exists | Match nearest eligible open issue of the same type within a configurable demo radius. Specify tie-breaking and document false merges; resolved issues are not silently reopened | 3, 5, 6 |
| Time semantics | Edge uses processing time and constant coordinates | Use a session start plus video time for recorded detection/GPS timestamps. Compare GPS freshness with detection time, including delayed delivery. Store UTC; calculate dashboard “today” in Asia/Kolkata | 1, 3, 5, 6 |
| Heartbeats | No heartbeat contract or bus table | Agree on interval, inactivity timeout, server receipt time, camera/AI states, optional coordinates, and rejection/handling of out-of-order telemetry | 1, 3, 4, 6 |
| API transition | Alert array, integer IDs and delete action differ from new issue API | Change edge, API, frontend fixtures and tests together; document migration of existing SQLite records before changing storage | 1, 3, 4, 6 |
| Resolution authorization | Existing API has no authentication | Define the operator/session mechanism and enforce permission at the backend. A UI confirmation alone does not meet the assignment's authorized-user requirement | 3, 4, 6 |
| Offline scope | Local logging exists without replay | Recommend durable retry delivery for the requested recovery demo. If deferred, explicitly remove offline recovery from demo acceptance | 1, 6 |

The example confidence threshold of `0.70` is a starting proposal, not validated performance evidence. Member 2 should measure the precision/recall tradeoff and provide the selected threshold to Member 1. GPS freshness tolerance, matching radius, heartbeat timeout and model acceptance targets still need measured or explicitly documented demo values.

### API differences to resolve

| Endpoint | Current implementation | Required target |
| --- | --- | --- |
| `POST /api/alerts` | Creates one alert row on every accepted submission | Accept observation; transactionally deduplicate, match/create issue, link observation and update totals. Define retry response and conflicting-ID behavior |
| `GET /api/alerts` | Plain array; `limit` only | `{items, total, page, page_size}` of issues; status, priority, event type and date-range filters |
| `GET /api/alerts/{issue_id}` | Integer alert details | Combined issue and linked observations, preserving observation confidence |
| `PATCH /api/alerts/{issue_id}/status` | Missing; delete is available | Authorized `open`/`resolved` transition; preserve reports and refresh totals |
| `GET /api/statistics` | Alert/category/severity counts | Issue totals, new issues today, open high-priority issues, resolved issues, active buses |
| `GET /api/buses` | Missing | Latest telemetry and heartbeat-derived activity |
| `POST /api/buses/{bus_id}/heartbeat` | Missing | Telemetry independent of detections |
| `GET /api/health` | Health exists at `/health` | Agree on `/api/health`; keep an alias if existing tooling needs it |
| Analytics | Missing | Propose `GET /api/analytics`: new issues by day, open issues by priority, observations by bus; define date range/timezone |

Recommended submission behavior: HTTP 201 for a new observation, HTTP 200 for an identical retry with the same IDs, and HTTP 409 if an existing event ID is reused for different content. Member 6 should record the exact response bodies and unknown-field policy before clients depend on them.

## 4. Tasks by member

Priority definitions: **P0** = settle before dependent implementation; **P1** = needed for the requested integrated prototype; **P2** = follow-up capability that can be scheduled after the core recorded-video demo.

### Member 1 — Edge AI

Current detail: thresholds are configurable through CLI arguments, but video reading and sending remain inside `main.py`. Temporal validation groups observations by `event_type:class_name`, not by tracked pothole. It prevents multiple boxes in one frame from counting as separate temporal evidence, but can suppress a second pothole during the shared cooldown or re-alert on a continuously visible pothole after cooldown. The log does not record delivery acknowledgements or retry work.

| ID | Priority | Task and deliverable | Depends on | Acceptance |
| --- | --- | --- | --- | --- |
| E1 | P1 | Extract `video_reader.py`, `config.py`, and `api_client.py` within `01_ai_edge/scripts/`; preserve a single runner and current CLI usability | C1 | Recorded video starts, ends and releases resources; settings have one source; sender can be tested without YOLO |
| E2 | P1 | Add per-object association/tracking and frame/video-time validation; generate one stable `event_id` per validated track | E1, agreed model interface | A brief detection creates no alert; one persistent pothole creates one alert; two separate potholes can create two alerts; low confidence is rejected |
| E3 | P1 | Attach Member 5's timestamped simulated location, send contract payloads and regular heartbeats, and remove unassessed severity/priority calculations from edge output | C1, L1, B1, B3 | API accepts generated observations; slow/fast processing gives the same location at the same video time; no-detection video still sends heartbeats |
| E4 | P1 if offline scope retained | Persist pending events, acknowledgement state and retry schedule; retain event ID across restart and retry; distinguish transient failures from invalid requests | E2, B2 | Backend outage preserves pending events; restart/retry accepts each event once without blocking video on every request |
| E5 | P2 | Add webcam/live-camera input through the same reader interface | E1 | Camera selection, read failures and clean shutdown work; recorded-video behavior remains covered |

Shadow/puddle/normal-road behavior needs labeled clips and model evaluation from Member 2. Unit tests of the alert manager cannot establish visual detection accuracy.

### Member 2 — Dataset and model training

Current detail: `training/data.yaml` names HMV, LMV, Pedestrian, RoadDamages, SpeedBump and UnsurfacedRoad. That differs from the supplied assignment's `0: pothole`. The current `best.pt` has an unnamed class; its filename is not evidence that it satisfies either contract. `pothole.pt` runs, but no dataset provenance, holdout evaluation or model report was found. Training data is absent.

| ID | Priority | Task and deliverable | Depends on | Acceptance |
| --- | --- | --- | --- | --- |
| M1 | P0 | Agree on pothole class/model interface and document the provisional model's identity; choose one configurable model path for the pothole demo | C1 with Members 1/2 | `0: pothole`, input size, YOLO compatibility and configurable threshold are explicit; unknown labels are rejected or clearly flagged |
| M2 | P1 | Obtain and label a representative pothole dataset; keep provenance, negative examples, quality checks and train/val/test split manifest | Dataset availability | Images/labels validate; near-duplicate frames from one source do not leak into holdout splits; normal roads, shadows, patches and water cases are represented |
| M3 | P1 | Align training/validation with a one-class pothole configuration; add reproducible split/cleaning workflow and reuse frame extraction | M1, M2 | Fresh setup resolves all paths; split/class validation passes; training and evaluation select the intended data and weights |
| M4 | P1 | Train, evaluate and hand off versioned weights plus `model-report.md` | M3 and compute availability | Actual precision/recall/mAP and speed are recorded; unseen clips are tested; confidence setting, known errors, dataset version and weight checksum accompany the model |

Model training time and accuracy cannot be estimated reliably until data volume, labels and hardware are known. Use the existing labeled model to unblock plumbing tests while Member 2 develops the final model; label that substitution in demonstrations.

### Member 3 — Backend and database

Current detail: only the `Alert` table exists. The API accepts any nonempty event type, optional bus/location/time and timezone-naive timestamps. Repeated requests create more rows. Status defaults to `new`; deletion is not issue resolution. SQLite persistence is present, but there is no issue migration, grouping, bus telemetry or requested aggregate API.

| ID | Priority | Task and deliverable | Depends on | Acceptance |
| --- | --- | --- | --- | --- |
| B1 | P1 | Implement observation/issue/bus models and schemas; configurable test/runtime databases; a documented migration preserving existing records | C1, C2 | Required fields/enums/timezones validate; tables relate correctly; migration works on a copied database without clearing original data |
| B2 | P1 | Add transactional event deduplication, Member 5 matching and issue/count updates | B1, L2 | Identical retries do not add reports; conflicting payloads follow contract; two nearby buses give one issue/two reports; a distant report gives another issue; concurrent retries cannot duplicate event rows |
| B3 | P1 | Implement filtered/paginated issue APIs, linked details, authorized status updates, buses, heartbeats and health contract | B1, B2 | Unknown IDs return 404; invalid filters/status fail clearly; resolving preserves observations; buses can be active without alerts |
| B4 | P1 | Implement issue statistics and agreed analytics aggregates | B2, B3, L3 | Totals come from stored records; India-date boundaries and heartbeat expiry are tested; charts do not depend on the current alerts page |

Preserve the original SQLite file during development. Decide how legacy rows receive observation IDs and whether/how they are grouped; do not silently assign historical reports to invented issues or delete demo data to simplify migration.

### Member 4 — Frontend

Current detail: `src/main.jsx` contains hardcoded `EVENTS`, `BUSES`, totals and “live” labels. Sidebar selection changes a label rather than routing to the assigned pages. Some controls are placeholders. The Leaflet map and styling are reusable, but a successful build does not demonstrate backend integration or working resolution.

| ID | Priority | Task and deliverable | Depends on | Acceptance |
| --- | --- | --- | --- | --- |
| F1 | P1 | Extract `App.jsx`, shared components and page navigation; add `services/api.js`, `VITE_API_BASE_URL`, shared-fixture mock adapter and explicit mock mode | C1, C2 | Dashboard/Map/Alerts/Details/Buses/Analytics navigation works; mock and HTTP services use identical response shapes |
| F2 | P1 | Connect dashboard, map and server-filtered/paginated issue list | F1, B3, B4 | One marker per returned issue; totals use statistics; filters fetch new results; list/map coverage limits are explicit and no coordinates are invented |
| F3 | P1 | Implement issue details and confirmed, authorized resolution with saving/error states | F1, B3 | Observations show their own confidence; failed saves leave status unchanged; success refreshes affected lists/maps/totals; severity displays Unknown |
| F4 | P1 | Connect heartbeat-based bus status and agreed analytics; add loading/empty/error/retry/stale states and responsive checks | F2, B4 | Offline backend is visible; last successful refresh is shown; missing bus location is explicit; no mock “live” claim appears in real mode |

Remove or defer emergency/signal-priority controls and other placeholder features from the initial pothole workflow unless the team separately scopes and implements them. Decide how a full city map obtains all relevant issues without accidentally showing only page one.

### Member 5 — Location intelligence

Current detail: `GPSSimulator.move()` increments coordinates per call, and the runner uses fixed CLI coordinates instead. `MultiBusValidator` compares temporary observations by distance and wall-clock age; it does not return a persisted `issue_id`. `PriorityEngine` uses confidence and derives severity from its score, which conflicts with the new assignment.

| ID | Priority | Task and deliverable | Depends on | Acceptance |
| --- | --- | --- | --- | --- |
| L1 | P1 | Create importable `location_intelligence` package, deterministic route fixtures, `get_location(video_time_seconds)` and coordinate/time validator | C1 | Same video time gives same route position; timestamps/source are explicit; invalid, missing and stale GPS are flagged |
| L2 | P1 | Extract validated metre-distance function and pure `match_issue(observation, candidates, config)` | C1, L1 | Nearest eligible open issue is selected deterministically; different type/far/resolved cases do not match; invalid coordinates fail; ambiguous nearby potholes are documented/tested |
| L3 | P1 | Implement proposed distinct-bus priority with reason/version and severity `unknown` | C1; review by Members 3/6 | One/two/three distinct buses yield agreed levels; repeated reports by one bus do not raise independent-bus count; confidence/box size do not determine severity |
| L4 | P1 | Publish package installation/import instructions and fixtures; integrate through the edge and backend adapters | L1–L3, E3, B2 | Edge/backend use the same functions/configuration; location package never opens or changes the database |

Treat bus coordinates as an approximate observation position. Distance-only matching cannot prove two reports refer to the same pothole; the demo must retain this limitation.

### Member 6 — Integration, setup and testing

Current detail: the existing tests are a useful regression base, including an in-memory API database. They currently assert the old payload/response shapes and priority behavior. No shared contract, fixtures, event simulator, live dashboard integration suite or documented demo release process was found in the inspected project files.

| ID | Priority | Task and deliverable | Depends on | Acceptance |
| --- | --- | --- | --- | --- |
| C1 | P0 | Record reviewed fields, responses, error semantics, model interface, matching/priority/time/heartbeat rules and resolution authorization in `docs/api-contract.md` | Members 1–5 input | No conflicting ID/count/status meanings; all endpoints have examples; proposals and accepted decisions are distinguished |
| C2 | P0 | Create `contracts/fixtures/` for valid/invalid/retry/nearby/distant/resolved/empty/paginated/offline-bus scenarios | C1 | Backend tests and frontend mock adapter consume the same fixtures |
| C3 | P1 | Build `tools/simulate_events.py` using the agreed contract and explicitly simulated coordinates | C2, B2, B3 | Configurable API address; sends observations/heartbeats and verifies retry and grouping results; failures cause a clear nonzero exit |
| C4 | P1 | Expand integration tests and maintain `docs/testing.md`; retain relevant cleanup regressions while replacing old-contract assertions | B1–B4, E2–E4, F2–F4, L1–L4 | Required acceptance scenarios below pass using isolated databases and fixtures |
| C5 | P1 | Complete root setup, module `.env.example` files, reproducible dependency/model instructions, architecture/integration docs and demo flow | C1, module handoffs | A teammate can set up and run the demo from instructions; known limits and fallback are accurate |
| C6 | P1 | Document module branches, integration checks and a known-good demo version; agree on model/video distribution | C4, C5 | Reviewed passing changes reach the integration branch; release evidence identifies code, data/model versions and test results |

Branch pushes, merges, deployment and training runs are future team actions, not actions performed by this assessment. Module owners implement their code; Member 6 coordinates interfaces and verifies the combined behavior.

## 5. Execution order and handoff gates

No deadline or team availability was supplied, so this plan uses completion gates rather than unsupported calendar estimates.

| Stage | Work that can proceed together | Required result before advancing |
| --- | --- | --- |
| 0. Contract | Member 6 coordinates C1/C2; Members 1/2 agree M1; Member 5 proposes location/priority rules | One documented contract and shared fixtures accepted by affected owners |
| 1. Independent implementation | Member 1 E1/E2; Member 2 data work; Member 3 B1; Member 4 F1; Member 5 L1–L3 | Each module runs against shared fixtures; no dependency on final training to test APIs/UI |
| 2. Stored issue workflow | Members 3/5 connect B2; Member 3 B3/B4; Member 4 F2/F3; Member 6 C3 | Simulator → persisted/grouped issues → dashboard details → resolution → updated totals |
| 3. Actual edge integration | Members 1/5 connect E3; Member 1 E4 if included; Member 4 F4; Member 6 recovery tests | Video → validated event → labeled GPS → backend → dashboard, plus heartbeat and retry behavior |
| 4. Model handoff | Member 2 M4; Member 1 compatibility and unseen-video checks | Versioned assessed pothole model and honest accuracy/speed report; threshold selected from evidence |
| 5. Demo readiness | Member 6 C4–C6 with all owners | Complete demo and recovery checks pass; no unresolved critical integration defects |

The software integration path is **contract → issue/observation backend with location matching → live frontend → edge integration → end-to-end verification**. Model/data work runs alongside that path; custom-model acceptance additionally depends on Member 2's dataset and evaluation.

## 6. Acceptance checklist for the completed prototype

These are planned checks, not claims about current functionality.

| Scenario | Passing result | Primary owners |
| --- | --- | --- |
| Persistent pothole and a separate second pothole | First track alerts once; second track can alert independently | 1, 2 |
| Normal road, shadow, puddle, patch and unseen pothole clips | Results compared with labels and recorded in model report; no invented accuracy claims | 1, 2 |
| Identical event retried | Same observation/issue IDs; report count unchanged | 1, 3, 6 |
| Event ID reused with different content | Documented conflict response; original observation preserved | 3, 6 |
| Two nearby buses and one distant bus | Nearby observations combine; distant report creates another issue | 3, 5, 6 |
| More observations from only one bus | Report count grows for new events; distinct-bus priority does not grow | 3, 5 |
| Two nearby but physically distinct potholes | Matching ambiguity is measured/documented; scenario is not falsely presented as proven identity | 2, 5, 6 |
| Missing/stale GPS | Detection retained locally with a clear reason; no fabricated coordinates submitted | 1, 5 |
| Slow versus fast playback processing | GPS corresponds to the same video time | 1, 5 |
| Resolve and refresh; report near resolved issue | Resolution persists without deleting observations; new report follows explicit resolved-issue policy | 3, 4, 5 |
| No detections but regular heartbeat; then heartbeat stops | Bus remains online during heartbeats and becomes inactive after agreed timeout | 1, 3, 4 |
| Backend restart | Stored issues, observations and status remain in a separate persistence-test database | 3, 6 |
| Backend down and restored | UI reports unavailable/stale data; retry queue recovers without duplication if offline scope is included | 1, 3, 4, 6 |
| Empty results, filters, pagination, responsive layout | Correct requests, clear states and usable navigation; no city totals computed from one page | 4, 6 |
| Analytics/date boundaries | Aggregates agree with storage and the defined India-day/UTC rules | 3, 4, 6 |
| Unauthorized resolution | Backend rejects the update under the agreed operator-access design | 3, 4, 6 |
| Full demonstration | Recorded video → actual inference → simulated GPS → one issue → second-bus corroboration → inspect → resolve → refreshed totals | All; coordinated by 6 |

## 7. Immediate assignments

1. **Member 6:** draft the shared contract and fixtures, starting with observation versus issue identity and counting.
2. **Members 1 and 2:** agree on the one-class pothole model contract and document the provisional `pothole.pt` handoff.
3. **Member 3:** design the three-table schema and a safe migration from the current alert table.
4. **Member 5:** define the pure location/matching interfaces and proposed priority rules, with fixtures for repeated and distinct buses.
5. **Member 4:** map the existing UI into the assigned pages and design the service adapter against the agreed fixtures.

Completion should be judged by the acceptance checks above. Counting files, passing a build, or obtaining a YOLO prediction alone does not establish that the six-module application is complete.
