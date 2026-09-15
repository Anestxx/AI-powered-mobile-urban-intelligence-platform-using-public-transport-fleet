# Edge AI

The runner uses `video_reader.py`, `detector.py`, `alert_manager.py`, `api_client.py`,
`outbox.py` and `config.py`. Run `scripts/main.py --help` with the project environment
for all options. Defaults: labeled `pothole.pt`, image size 640, confidence 0.70,
every third frame, three consecutive observations per track.

Boxes are associated by overlap. Each continuously tracked pothole emits one UUID
event; distinct tracks can emit separately. A short spatial cooldown limits noisy
reappearance. Fast camera motion or occlusion can break track identity; these rules
are prototype validation rather than an evaluated multi-object tracker.

Simulated locations follow video time. Missing/invalid GPS is retained in the local
alert log with a delivery error and is not sent with fabricated coordinates. Valid
events enter an SQLite outbox before HTTP submission. A background worker sends
heartbeats and retries, so backend latency does not block the video loop. Successful
receipts acknowledge an event before marking it sent; 4xx validation/conflict failures
remain available as invalid records. `--flush-only` retries pending records immediately.

`preview.py --model pothole --start-frame 560 --headless --max-frames 1` checks one
model independently. `preview.py --model general` exercises the bundled general model;
the legacy `--model rad` preview only inspects the unnamed `best.pt` checkpoint and
does not establish RAD capability. `extract_frames.py` saves samples only when called
explicitly. Each confirmed observation saves an annotated road image by default; `--no-save-evidence` disables image capture.

## Connected video with location alerts

Start the backend and dashboard, then run from the project root:

```powershell
.\.venv\Scripts\python.exe 01_ai_edge/scripts/main.py --start-frame 450 --loop --cpu-threads 2 --save-evidence
```

This player starts automatically. It shows the moving video, predicted pothole
boxes, current simulated route coordinates and the latest alert's coordinates.
Three consecutive detections confirm an observation; it enters the durable outbox
and the worker submits it to the backend. The player says **SENT** only after an
acknowledgement for that event, and counts only alerts from the current run.
The dashboard polls every two seconds. Its map groups nearby open observations
into an issue, so several reports can produce one marker.

The Python window includes a **Dashboard** with shared counts and an **Alerts** tab
with status filters, pages, issue coordinates and individual observations. Select
an open issue, sign in with your existing operator password, choose **Mark selected
issue resolved**, optionally add a note, then confirm. The Status history tab shows
saved status changes and notes. This uses the same authenticated backend status
endpoint as the web dashboard; it does not maintain a separate list or change the
database directly. Failed/expired sign-ins and rejected updates leave the issue's
saved status unchanged. Backend polling and resolution run in a background thread.

**Pause video** / **Resume video** controls playback; **Close player** quits.
The tabs remain usable while paused and after a non-looped recording ends.
`--video-only` selects the compact OpenCV player with Space/Q keyboard controls;
offline mode also uses that compact player. Tkinter and Pillow support the full
desktop window in the verified Windows environment.

`--loop` replays the recording for viewing
without creating additional alerts after its first pass. Restarting the command
begins a new run and can create new observations. Remove `--loop` for a single pass.
The connected player retains sampled frames for temporal validation; playback can
be slower than the source video when CPU inference is slow. Network delivery runs
separately and does not wait for the clip to finish.

Locations come from an example bus route, not the image. Detection and simulated
GPS timestamps use the current processing time; route positions follow video time.
For a real fixed CCTV installation, configure the camera's surveyed coordinates;
for a moving camera, connect its timestamped GPS feed. Neither is supplied by this
bundled clip. Those real-location sources are not connected by this example.

Use `--cpu-threads 2` to try the measured setting for the current laptop. The default
keeps the framework's CPU setting; results vary by machine. The player displays
measured inference time and processed frames per second. `--metrics-file` saves
recent-window performance counters when the run stops. These are speed measurements,
not model accuracy estimates, and playback can be slower than the source recording.

## Optional inspection-only preview

Run this from the project root for a visible example starting near the potholes in
the bundled recording:

```powershell
.\.venv\Scripts\python.exe 01_ai_edge/scripts/preview.py --model pothole --confidence 0.70 --start-frame 560 --loop --paused
```

The window opens on a model-annotated frame. Press **Space** to play/pause, **R** to
replay from the selected start frame, and **Q** or the window close button to exit.
Colored boxes and percentages are actual model predictions. The header reports
video time, box count and inference time. Playback skips overdue frames when the
CPU cannot evaluate every source frame, so a moving picture does not imply that
every frame was analyzed. This is a recording replay with inference during playback;
it is not a live CCTV connection or evidence of model accuracy.

For your own CCTV recording, replace the source with `--video "C:/path/footage.mp4"`
and omit `--start-frame 560`. This preview does not publish alerts, so repeatedly
watching the same footage does not add reports. Use `scripts/main.py --source
"C:/path/footage.mp4"` for the connected detection, temporal validation and dashboard
delivery flow. Live network CCTV streams are not connected by this example.

## Newly supplied assets

`preview.py --model emergency` selects the preserved `emergency.pt` and
`ambulance_test.mp4`; `--video` can override the recording. This checkpoint has
general-object labels, not emergency-vehicle labels, and the preview does not send
alerts. All four checkpoints remain in `models/`; its README and manifest explain
their actual labels and checksums.

The incoming `emergency_intelligence.py` and `traffic_intelligence.py` are retained
standalone rule modules. Their synthetic-rule checks pass, but they are not wired
to the pothole observation contract or real traffic signals. The duplicate incoming
`test_emergency.py` graphical runner was consolidated into `preview.py`.

## Evidence and review

The runner stores one annotated road crop with each confirmed observation by default. The JPEG
is at most 480 pixels on its longest side, at quality 75, with a 192 KiB hard limit.
The outbox retains its bytes until delivery and across restarts. Use
`--no-save-evidence` for metadata-only alerts. The text log excludes encoded image bytes.
The backend stores the crop, source filename, frame number and video time.

Inside the Python Alerts tab, select a report and open Saved evidence. The action
selector supports Resolve, False detection (reason required), and Reopen. These
use the same operator session, history and conflict protection as the web dashboard.

Heartbeat failures no longer prevent queued observations from being submitted.
A short headless run may finish with pending events; use `--flush-only` to drain
that queue, or leave the connected player running for background delivery.
