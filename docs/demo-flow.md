# Local demonstration

1. Start the backend and dashboard using the root README. Show that an empty database
   produces an empty state, or explain any previously stored simulated reports.
2. Run the edge runner with the recorded road video and `--save-evidence`. Identify the footage as recorded,
   the detections as actual model inference, and GPS as simulated approximate bus location.
3. Show a validated observation in the console and its delivery state. Threshold 0.70
   is provisional; a lower threshold used for a technical check is not an accuracy claim.
4. Open Incidents to show the saved-image gallery, then select Review on a photo.
   Show the map image preview and the resulting issue, event IDs, per-observation
   confidence, report count and source labels. Severity remains Unknown.
5. Use `tools/simulate_events.py` to demonstrate nearby reports from two buses, an
   unchanged-ID retry and a distant report. Explain that this step uses generated
   metadata and is independent of the detector.
6. Show the combined issue and distinct-bus review priority. Explain that distance-only
   matching can merge nearby separate potholes.
7. Open a new issue and show its saved crop plus recording/frame/time. Sign in as
   the operator, add a note, confirm resolution and verify refreshed status/totals.
   Explain False detection (reason required) and Reopen. Export the filtered Incidents
   list using Download issues CSV. Do review demonstrations on designated demo issues.
8. Show Buses. Heartbeats can keep a bus online even without detections; stop the runner
   and wait more than 30 seconds to demonstrate inactivity.
9. For recovery: run the edge offline, start the backend, then run `main.py --flush-only`.
   Verify that pending events are acknowledged once. Do this against a designated demo
   database so demonstration counts are understood.

Fallback: the event simulator demonstrates the backend/dashboard if inference is
unavailable. Label it as a metadata simulation. Do not claim a live bus feed, exact
pothole GPS, assessed physical severity, or evaluated model accuracy.
