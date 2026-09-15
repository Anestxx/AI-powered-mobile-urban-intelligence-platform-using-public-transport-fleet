# Integration tests and reviewer demo

These tests cover the shared contract, persistence, idempotent alert delivery,
geographic matching, operator review, evidence storage and pagination, playback,
dataset checks and desktop operator controls. Tests use isolated temporary data.

From the project root, after installing [the dependencies](../README.md):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s 06_integration_testing_demo -v
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe tools/check_models.py
cd 04_dashboard_frontend
npm test
npm run build
```

The current verified result is 68 Python tests, 11 frontend service tests and a
successful frontend production build. Desktop tests require Python's Tk support.
These results verify software behavior; they do not measure model accuracy.
Browser interaction and physical camera checks remain pending.

For a presentation, follow [the demo walkthrough](../docs/demo-flow.md). The shared
[fixture](../contracts/fixtures/demo.json) supplies explicitly simulated events.
`tools/simulate_events.py` sends that scenario to a running backend. The connected
video runner performs actual inference on the bundled recording and saves images
by default. Runtime data and operator credentials remain local to each clone.
