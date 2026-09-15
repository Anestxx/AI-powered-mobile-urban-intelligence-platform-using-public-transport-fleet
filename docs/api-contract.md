# CODYSSEY API contract v2

This implementation uses the pothole prototype scope from the team plan. Recorded video, simulated bus GPS, and the bundled provisional pothole model are explicitly identified. Severity is `unknown`; review priority is a demo rule, not a physical damage assessment.

## Observations and issues

`POST /api/alerts` accepts one observation. Required fields: `event_id` (UUID created once at the edge), `event_type` (`pothole`), `bus_id`, `confidence` (0–1), latitude/longitude, `timestamp`, `gps_timestamp`, and `location_source` (`simulated` or `gps`). Timestamps must include a timezone and are normalized to UTC. GPS time must be within 5 seconds of detection time, including observations delivered later. Optional `bbox` is `[x1,y1,x2,y2]` with nonnegative ordered coordinates; `model_version` is optional. Unknown fields are rejected.

New observations return HTTP 201 with `{event_id, issue_id, duplicate: false}`. Identical retries return 200 with the same IDs and `duplicate: true`. Reusing an event ID with changed content returns 409. Invalid data returns 422.

Writes are serialized in a SQLite transaction. An indexed geographic bounding query limits candidates before exact distance matching. Matching chooses the nearest open issue of the same type and location source within 25 metres; ties use issue ID. An issue keeps its first observation's location. Distance-only matching may merge distinct nearby potholes. Reports near resolved issues create a new issue. Simulated and actual GPS reports never merge.

`report_count` counts distinct accepted events; `distinct_bus_count` counts distinct reporting buses. One bus gives low review priority, two medium, and three or more high, with `priority_reason` and `priority_rule_version: demo_v1`. Confidence remains on individual observations. Severity always remains unknown.

## Optional saved evidence

An observation may include `evidence` with `jpeg_base64`, `source_name` (filename or
label, never a local path), `frame_id` (0-2147483647) and `video_time` (seconds,
0-1000000000). The JPEG must decode, be at most 192 KiB and no larger than 640 by
640 pixels. Evidence and observation commit in one transaction.

The edge saves an annotated road crop per confirmed observation by default, at
most 480 pixels on the longest side, at JPEG quality 75. The image includes the
detected box and surrounding road context. Use `--no-save-evidence` for metadata only. The durable outbox owns the image bytes; the
text alert log includes only image metadata.

Changing evidence under an existing event ID returns 409. Missing/null evidence
preserves earlier observation fingerprints, including retries from old outboxes.
Issue details return evidence metadata and a URL, never the encoded image itself.
Earlier observations have `evidence: null`; their images are not reconstructed.

## Read and operator APIs

`GET /api/evidence` returns every saved observation image as metadata, with the
current issue status, priority, confidence, bus, source frame/time and coordinates.
It supports the same filters as `/api/alerts`, plus `page` and `page_size` (default
12, maximum 100). Date filters refer to the issue's last-seen date, as in the issue
list. Images are ordered by observation timestamp and event ID, newest first.
JPEGs are fetched separately through each image URL; list polling does not read
image blobs. One issue can contribute multiple gallery images.

Issue lists and details also include `evidence_count` and `latest_evidence`.
The latter describes the latest observation with a saved image, or is null.
Reports without images never hide earlier saved evidence. These fields let map
popups show images without requesting every issue's full history.

| Endpoint | Response/behavior |
| --- | --- |
| `GET /api/alerts` | `{items,total,page,page_size}` containing combined issues. Filters: `status`, `priority`, `event_type`, `date_from`, `date_to`. Pages start at 1; page size 1–100. Sort by last-seen descending, then ID |
| `GET /api/alerts/{issue_id}` | Issue fields plus `observations` (including optional evidence metadata/URL) and newest-first `activity` status history |
| `PATCH /api/alerts/{issue_id}/status` | Operator session required; JSON `{status: open\|resolved\|dismissed, note?: string, expected_status?: string}`; note maximum 500 characters; returns saved issue |
| `GET /api/observations/{event_id}/evidence` | JPEG with hash ETag; 404 if absent |
| `GET /api/reports/issues.csv` | Filtered CSV using the same status/priority/type/date filters; exports over 10,000 rows return 422 |
| `GET /api/statistics` | `open_issues`, `dismissed_issues`, `total_issues`, `new_issues_today`, `open_high_priority_issues`, `resolved_issues`, `active_buses`, `open_by_priority` |
| `GET /api/analytics` | `new_issues_by_day`, `open_by_priority`, `observations_by_bus`, `date_from`, `date_to`, `timezone` |
| `GET /api/buses` | `{items,total}`; latest telemetry and computed `online` flag |
| `POST /api/buses/{bus_id}/heartbeat` | Timezone-aware `timestamp`, `camera_status`/`ai_status` (`online`, `offline`, `error`), optional coordinate pair and location source; returns latest bus |
| `GET /api/health` | Service/database health and contract version. `/health` remains an alias |
| `POST /api/auth/login` | `{password}` creates an HttpOnly, SameSite session cookie for 8 hours |
| `GET /api/auth/session` | `{authenticated}` |
| `POST /api/auth/logout` | Invalidates the session |

`dismissed` means the operator judged this issue to be a false detection; a nonblank
reason is required. It is counted separately from resolved issues and excluded
from the open queue. Reports, evidence and history remain preserved. Reopening is
supported. New detections only match open issues.

Clients can send `expected_status` to prevent overwriting another operator's
changed decision; conflicts return 409. Repeating the already-saved target status
returns success without duplicating history or replacing its original note.

Date filters accept 1900-01-01 through 9998-12-31; invalid/reversed ranges return
422 instead of overflowing the calendar. CSV fields use UTC timestamps and contain
issue metadata, not images or operator credentials.

Issue date filters apply to `last_seen`. Analytics daily counts apply to `first_seen`; observations-by-bus uses detection time. Date bounds are inclusive calendar dates in Asia/Kolkata; storage is UTC. Analytics defaults to the last 7 days and allows at most 366 days. Open-priority breakdown is the current all-time open issue state.

Heartbeats are normally sent every 10 seconds. Activity expires after 30 seconds of server receipt time; an old delayed heartbeat (over 30 seconds old) cannot make a bus online. Future heartbeats over 5 seconds ahead are rejected. Out-of-order timestamps do not replace newer telemetry. Detection submissions alone do not mark buses online.

The local operator password is configured through `CODYSSEY_OPERATOR_PASSWORD` or generated once at first startup in the ignored database directory. It is never embedded in frontend code. Session state is in memory, so restarting the backend requires signing in again. Run behind HTTPS with a suitable identity provider before deploying beyond a trusted local prototype.

## Storage transition

Actual status changes create an activity record with previous/new status, trimmed
optional note, UTC timestamp and actor `local_operator`, in the same transaction.
The local shared credential does not identify a named person. Same-status retries
do not create another history entry. Existing issues have no invented past history;
startup adds the activity/evidence tables and location index without deleting saved records.

The new default database is `03_backend_database/database/codyssey_v2.db`. The original `urban_sensing.db` is preserved. A separate migration command previews legacy rows and requires explicit source/timezone assumptions before importing eligible observations. Invalid or unsupported rows remain in the original database; there is no automatic relabeling, deletion, or regrouping of that source.
