# CODYSSEY API v2

Run `python run_backend.py` from the project root using its environment. Alternatively,
from this folder use `python -m uvicorn app.main:app`. Configuration is read from this
folder's optional `.env`; `.env.example` documents overrides.

See [the shared contract](../docs/api-contract.md) for fields, endpoints and error
semantics. SQLite contains separate observations, issues and buses. Observation
creation runs inside a transaction that locks before deduplication and matching.
The new default `database/codyssey_v2.db` preserves the older `urban_sensing.db`.

Issue resolution requires a backend operator session. The password comes from
`CODYSSEY_OPERATOR_PASSWORD` or is generated once in `database/operator-password.txt`.
Frontend code only sends it during sign-in; the browser receives an HttpOnly session
cookie. Sessions expire after eight hours and are cleared on backend restart.
The local prototype has public read/ingestion APIs; deployment requires a suitable
identity/access design beyond this trusted loopback demonstration.

Health: `/api/health` (also `/health`). API docs: `/docs`. Tests construct apps with
isolated databases/passwords and never clear demonstration data. Migration is a
separate explicit tool; see [integration instructions](../docs/integration.md).

## Review workflow and evidence

- Statuses are open, resolved and dismissed. Dismissal means a false detection and
  requires a reason; it is not counted as a resolved issue.
- Status changes preserve observations/evidence and append operator history.
  Optional expected_status protects against a conflicting decision from another
  reviewer. The local actor is a shared operator account.
- POST /api/alerts optionally accepts a bounded JPEG crop with source/frame/time.
- GET /api/evidence lists all saved detection images with pagination and issue filters.
- Alert summaries include the latest image and saved-image count for map previews.
  SQLite stores image bytes and the observation in the same transaction. No new
  filesystem upload directory or separate database migration is required.
- GET /api/observations/{event_id}/evidence returns a JPEG or 404. Issue details
  include only its metadata/URL, keeping repeated dashboard polling small.
- GET /api/reports/issues.csv exports matching issue records across pages. It
  accepts the list filters and rejects exports above 10,000 rows.
- Statistics expose open_issues and dismissed_issues separately. Accepted reports
  use SQL counts and distinct bus IDs instead of loading all historical bus IDs.

Old observations and outbox fingerprints remain valid when evidence is absent.
Before upgrading the local demo, a SQLite backup was saved in the ignored database
folder. No historical images or review decisions are fabricated.

See ../docs/api-contract.md for limits, validation, examples and response semantics.
