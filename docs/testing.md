# Testing and readiness

## Completed checks

- 64 Python tests passed: observation retry/conflict behavior, concurrent writes,
  transaction rollback, nearby/distant/source-specific matching, distinct-bus priority,
  authorized resolution, India-day aggregates, heartbeat expiry/order, restart
  persistence, legacy preservation, tracking, outbox recovery, malformed delivery
  acknowledgements, dataset helpers, preview playback/pause timing and automatic
  connected playback without duplicate reports on replay, and Python operator
  sign-in/resolution against the shared backend. Added checks cover status notes and
  history, bounded runtime metrics, geographic filtering and dateline/pole bounds.
- Ten frontend service tests passed: server filters/pagination, failed and successful
  resolution requests with notes, network-error messaging and invalid-response handling.
- The React/Vite production build passed. Python syntax and dependency consistency
  are checked as part of handoff.
- A real local backend scenario accepted two nearby simulated reports, a duplicate
  retry, a distant report and heartbeats with expected grouping/counts.
- Live requests through the Vite API proxy verified cookie sign-in, authorized
  resolution, observation preservation, sign-out and rejection of unauthenticated
  status changes.
- The actual pothole model processed 12 video frames starting at frame 560, using four
  inferences at a deliberately reduced 0.25 threshold. Four validated observations
  entered the outbox. A later flush acknowledged all four, and the backend retrieved
  them as model-generated observations with unknown issue severity.
- The interactive recording preview detected one pothole at frame 560 with a 0.70
  threshold in a headless check. The desktop preview was launched with pause/replay
  controls; actual user interaction with those controls is not an automated test.
- The connected desktop player autoplayed the bundled clip at a 0.70 threshold.
  Three model observations were acknowledged by the live backend and grouped into
  one open issue, with simulated coordinates and current timestamps. The measured
  interval from processing timestamp to backend receipt was approximately 0.28–0.52
  seconds for those three events; dashboard polling is every two seconds. This is
  local execution evidence, not a hardware performance or model accuracy guarantee.
- The Python Dashboard/Alerts controls were tested against an isolated backend:
  polling, issue selection, an expired-session rejection, successful sign-in,
  confirmation, shared status/count updates and observation preservation passed.
  The confirmation controls fit inside a 1100×650 window in the desktop layout test.
  The running desktop window was inspected; real browser interaction remains a
  separate pending check.

The inference run is an execution check, not model accuracy evidence. All API tests
use isolated databases; the legacy migration test checks that source bytes do not
change. The real process check used a separate `browser-check.db`, not demonstration
or legacy data.

## Checks and extensions still pending

| Check | Owner | Status / reason |
| --- | --- | --- |
| Browser navigation, map popups, filtering/pagination and responsive layout | 4, 6 | Pending; browser runtime reported no available browser |
| Browser operator sign-in, resolution confirmation and failed-update behavior | 3, 4, 6 | API/service tests passed; actual UI interaction still pending |
| Browser stale/empty state while stopping/restarting the backend | 4, 6 | Implemented; interactive verification pending |
| Webcam and graphical video window shutdown | 1, 6 | Not exercised; headless recorded-video inference passed |
| Labeled dataset provenance, source isolation and holdout review | 2 | Dataset not supplied |
| Custom training, precision/recall/mAP, false positives and unseen clips | 1, 2 | Pending data and evaluation; no results invented |
| Team integration branch and known-good release tag | 6 | Procedure documented; final release awaits the above gates |

## Known prototype limits to retain in the demo

Box-overlap tracking can split identity after occlusion. Radius-only GPS matching can
merge distinct nearby potholes; one test deliberately demonstrates that limitation.
GPS is the simulated bus observation position. Priority is a distinct-bus demo rule,
and severity is unknown. The default route stops moving after 120 seconds. Map coverage
is capped and labeled at 500 filtered issues. Invalid outbox events require review.

For any new bug, record reproduction steps, expected/actual behavior, owner, demo
impact, fix and retest result here. Passing a build or obtaining predictions alone
does not satisfy the pending browser/model gates.

## Incoming-file integration, 14 September 2026

After incorporating commits through `47cba0f`, all 55 Python tests and six frontend
service tests passed again, and the updated command-center frontend built successfully.
All four model files and both videos match their original Git blobs. The new preview
processed two ambulance-video frames and returned eight general-object predictions.
The supplied emergency checkpoint has no emergency-vehicle class; no emergency
recognition or signal control is claimed. Standalone incoming rule helpers passed
synthetic checks. Existing two issues and 12 observations were preserved.

A real offline pothole run processed 12 frames with four inferences using two CPU
threads and verified the metrics JSON. Its temporary outbox was isolated from demo
data. Browser visual and interaction checks remain pending: the runtime reported
no available browser. See [cleanup](cleanup.md) and [reviewer roadmap](reviewer-roadmap.md).

## Backend review upgrade, 14 September 2026

- 64 Python tests and 10 frontend service tests passed. The frontend production
  build passed with evidence, review and export controls.
- New tests cover invalid/oversized JPEGs, missing evidence, atomic rollback,
  backend restart, outbox restart after lost acknowledgement, pre-evidence event
  fingerprints, dismissal reasons/counts, reopening and conflicting decisions.
- Invalid date extremes/reversed ranges and non-ASCII wrong passwords return
  validation/authentication errors instead of crashing. Heartbeat failure no longer
  blocks otherwise successful alert delivery.
- The native window loaded saved evidence, rejected an expired session, resolved,
  reopened, required a dismissal reason and saved that decision against an isolated
  backend. Existing resolution confirmation layout checks passed.
- The existing demo database was backed up before restart. Its original two resolved
  issues and 12 observations were verified unchanged. A previously stored event
  retried against the updated backend and returned 200/duplicate without adding rows.
- A real run with --start-frame 560 --max-frames 12 --cpu-threads 2 --save-evidence
  processed 12 frames and four inferences. Two model observations at threshold 0.70
  produced one new open issue with two JPEG crops (2,080 and 934 bytes). The short
  run ended with two pending events; --flush-only delivered both, leaving zero
  pending/invalid events. Original records remained unchanged.
- The new images decoded successfully through the Vite API proxy; filtered CSV
  returned the same open issue as the list. Status transitions were tested on
  isolated fixtures, not automatically applied to the user's real demo issue.

This is execution evidence, not evaluated detection accuracy. Browser visual and
interaction QA remains pending; the browser runtime has no available browser.
