# Architecture

```mermaid
flowchart LR
  Camera[Recorded video or webcam] --> Edge[Edge detector and track validation]
  GPS[Video-time simulated GPS] --> Edge
  Edge --> Queue[Durable local outbox]
  Queue --> API[FastAPI observation endpoint]
  Edge --> Heartbeat[Heartbeat worker]
  Heartbeat --> API
  API --> Match[Pure location matching and priority]
  API --> DB[(SQLite: observations, evidence, issues, history, buses)]
  DB --> API
  API --> UI[React and Leaflet dashboard]
  UI --> Operator[Operator sign-in and resolution]
  Operator --> API
  Training[Dataset and evaluated model handoff] -.-> Edge
```

The edge owns frame tracking and stable event IDs. The backend owns retry
deduplication, transactions, persistence and issue counts. The location package
accepts candidate records and never accesses the database. The frontend displays
backend aggregates and never derives city totals from one page of results.

Full camera frames and video are not sent to the backend. Optional `--save-evidence`
attaches a compact pothole crop to an observation and the durable retry payload. Metadata includes approximate bus
coordinates with explicit source, UTC time, confidence and optional box. Physical
severity is unknown. Source-specific matching prevents simulated reports from being
combined with real GPS observations.
