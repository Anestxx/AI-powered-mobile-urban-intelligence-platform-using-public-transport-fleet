# CODYSSEY operator dashboard

From this folder, run `npm ci`, then `npm run dev`. Open http://127.0.0.1:5173.
Start the Python backend on port 8000 in another terminal. Vite proxies `/api` to
the backend; `.env.example` documents `VITE_API_BASE_URL` and `VITE_USE_MOCKS`.

The command-center design from `47cba0f` is the active frontend. It is split into
`App.jsx`, page components and shared API services instead of one large `main.jsx`.
`styles.css` retains the incoming theme; `connected.css` styles the working review
pages and operator controls.

The application has Command Center, City Map, Alerts, Issue details, Fleet, Emergency
module status and Analytics pages. Summary cards use server totals; the original
fixed fleet/coverage figures are replaced by real counts or omitted when unmeasured.
Filters and pagination request new results.
Maps show combined issues, source labels and a legend; the city map explicitly caps
coverage at the latest 500 matching issues. Observations retain individual confidence.

Operator sign-in is required to resolve an issue. Confirmation precedes the PATCH,
and an optional note and status history are saved with each status change. The saved
status is displayed after the backend succeeds. Loading, empty, failure
and stale-update states are implemented; refresh runs every 2 seconds. Bus activity
is based on heartbeats, not detections.

For independent development set `VITE_USE_MOCKS=true` and restart Vite. The mock
adapter uses `contracts/fixtures/demo.json` and displays a visible demo banner; its
changes are held only for that browser session. Historical mock analytics are labeled
and do not claim to represent the current day.

Run `npm test` for the service-layer checks and `npm run build` for production output.
The build is static; a deployed server must proxy `/api` or use a configured backend
address. Operator passwords must never be put in `VITE_*` variables. Browser visual
and interaction QA remains listed separately in the project readiness record.

## Review and export

Command Center shows the latest capture and a photo stream. Incidents opens a
paginated photo gallery by default, with an Issue list toggle for all records,
including older reports without images. Map popups show the latest saved image.
Each photo links to its issue's location and review actions and can open the JPEG
in a separate tab. Issue details show all saved images with recording and frame/time.
Metadata-only observations have an explicit no-image state. Resolve, False detection
and Reopen are authenticated decisions. False detection requires a reason; stale
conflicting updates prompt a refresh. Dismissed issues are excluded from open counts.

The Alerts page offers Download CSV using the current filters, covering all matching
records, not just the visible page. The backend rejects exports over 10,000 issues
with a request to narrow the filters. The fixture adapter supports the same review
and export workflow, with its existing visible demo label.
