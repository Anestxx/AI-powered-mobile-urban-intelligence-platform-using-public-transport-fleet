# Location intelligence

Install from the project root: `python -m pip install -e ./05_gps_gis_prioritization --no-build-isolation`.
Public functions are exported from `location_intelligence` and used by both edge and backend.

`GPSSimulator(bus_id, start_time).get_location(video_time_seconds)` returns deterministic route coordinates with explicit simulated source and GPS time. Coordinates follow video time, not inference speed. The route holds its final position after 120 seconds; supply a longer route for a longer recording. The coordinates describe the approximate bus observation location, not the exact pothole position.

Matching is a pure function over supplied open issues, selecting nearest within 25 metres with deterministic ID tie-breaking. Simulated and GPS locations remain separate. Distinct nearby potholes may falsely merge: distance alone is not identity evidence. Priority is a versioned demo rule based on distinct buses; severity stays unknown. No function in this package accesses a database.

`spatial_cluster.py` is the standalone in-memory helper received in commit
`3c42b44`. It is preserved for team development. The connected prototype uses
`location_intelligence` and persistent backend issue IDs for grouping; the helper
is not an additional active clustering stage.
