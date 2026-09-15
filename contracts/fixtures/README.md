# Shared fixtures

`demo.json` is shared by frontend mock mode and API tests. The second observation is near the first; the third is distant. Reuse the first object unchanged to test a duplicate retry. The example issue list represents the state after resolving the distant issue. Empty, invalid, out-of-range-page and offline-bus examples are included.

These are explicitly simulated historical fixtures. The event simulator substitutes current detection/heartbeat times and fresh event IDs for each new scenario; within a scenario it reuses the same event ID for retries.
