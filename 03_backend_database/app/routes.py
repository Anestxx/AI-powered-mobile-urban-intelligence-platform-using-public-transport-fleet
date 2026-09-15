from datetime import date
from typing import Literal
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from .auth import require_operator
from .database import get_db
from .models import Bus, Issue, IssueActivity, Observation, ObservationEvidence
from .schemas import HeartbeatCreate, ObservationCreate, StatusUpdate
from . import services

router = APIRouter(prefix="/api")


@router.post("/alerts")
def create_alert(data: ObservationCreate, request: Request, response: Response, db: Session = Depends(get_db)):
    result = services.accept_observation(db, data, request.app.state.settings)
    response.status_code = 200 if result["duplicate"] else 201
    return result


@router.get("/alerts")
def get_alerts(status: Literal["open", "resolved", "dismissed"] | None = None, priority: Literal["low", "medium", "high"] | None = None,
               event_type: Literal["pothole"] | None = None, date_from: date | None = None, date_to: date | None = None,
               page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    query = services.filter_issues(select(Issue), status, priority, event_type, date_from, date_to)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    records = db.scalars(query.order_by(Issue.last_seen.desc(), Issue.issue_id).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": services.issue_summaries(db, records), "total": total, "page": page, "page_size": page_size}


@router.get("/evidence")
def get_evidence_gallery(status: Literal["open", "resolved", "dismissed"] | None = None,
                         priority: Literal["low", "medium", "high"] | None = None,
                         event_type: Literal["pothole"] | None = None,
                         date_from: date | None = None, date_to: date | None = None,
                         page: int = Query(1, ge=1), page_size: int = Query(12, ge=1, le=100),
                         db: Session = Depends(get_db)):
    query = select(*services.evidence_columns(), Observation.issue_id, Observation.bus_id, Observation.event_type,
                   Observation.confidence, Observation.timestamp, Observation.latitude, Observation.longitude,
                   Observation.location_source, Issue.status, Issue.priority)
    query = query.select_from(ObservationEvidence).join(Observation).join(Issue)
    query = services.filter_issues(query, status, priority, event_type, date_from, date_to)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.execute(query.order_by(Observation.timestamp.desc(), Observation.event_id.desc())
                      .offset((page - 1) * page_size).limit(page_size))
    fields = ("event_id", "issue_id", "bus_id", "event_type", "confidence", "timestamp", "latitude", "longitude",
              "location_source", "status", "priority")
    items = [dict({key: getattr(row, key) for key in fields}, evidence=services.evidence_dict(row)) for row in rows]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/alerts/{issue_id}")
def get_alert(issue_id: str, db: Session = Depends(get_db)):
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise HTTPException(404, "Issue not found")
    result = services.issue_summaries(db, [issue])[0]
    result["observations"] = [services.record_dict(record) for record in db.scalars(select(Observation).where(Observation.issue_id == issue_id).order_by(Observation.timestamp.desc(), Observation.event_id))]
    evidence_query = select(ObservationEvidence.event_id, ObservationEvidence.source_name, ObservationEvidence.frame_id,
                            ObservationEvidence.video_time, ObservationEvidence.width, ObservationEvidence.height,
                            ObservationEvidence.byte_count).join(Observation).where(Observation.issue_id == issue_id)
    evidence = {row.event_id: dict(row._mapping) for row in db.execute(evidence_query)}
    for observation in result["observations"]:
        item = evidence.get(observation["event_id"])
        observation["evidence"] = dict(item, url=f"/api/observations/{observation['event_id']}/evidence") if item else None
    result["activity"] = [services.record_dict(record) for record in db.scalars(select(IssueActivity).where(IssueActivity.issue_id == issue_id).order_by(IssueActivity.timestamp.desc(), IssueActivity.activity_id))]
    return result


@router.patch("/alerts/{issue_id}/status", dependencies=[Depends(require_operator)])
def update_status(issue_id: str, data: StatusUpdate, db: Session = Depends(get_db)):
    db.execute(text("BEGIN IMMEDIATE"))
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise HTTPException(404, "Issue not found")
    if data.expected_status is not None and issue.status not in (data.expected_status, data.status):
        raise HTTPException(409, "Issue changed since you opened it. Refresh before updating its status.")
    if issue.status != data.status:
        db.add(IssueActivity(activity_id=str(uuid4()), issue_id=issue_id, previous_status=issue.status, status=data.status,
                             note=data.note.strip(), actor="local_operator", timestamp=services.iso(services.utc_now())))
        issue.status = data.status
    db.commit()
    return services.record_dict(issue)


@router.get("/observations/{event_id}/evidence")
def get_evidence(event_id: str, db: Session = Depends(get_db)):
    item = db.get(ObservationEvidence, event_id)
    if item is None:
        raise HTTPException(404, "No saved evidence for this observation")
    return Response(content=item.jpeg, media_type="image/jpeg", headers={"X-Content-Type-Options": "nosniff",
                    "Cache-Control": "private, max-age=3600", "ETag": f'"{item.sha256}"'})


@router.get("/reports/issues.csv")
def export_issues(status: Literal["open", "resolved", "dismissed"] | None = None,
                  priority: Literal["low", "medium", "high"] | None = None, event_type: Literal["pothole"] | None = None,
                  date_from: date | None = None, date_to: date | None = None, db: Session = Depends(get_db)):
    import csv
    from io import StringIO
    query = services.filter_issues(select(Issue), status, priority, event_type, date_from, date_to)
    records = db.scalars(query.order_by(Issue.last_seen.desc(), Issue.issue_id).limit(10001)).all()
    if len(records) > 10000:
        raise HTTPException(422, "Export exceeds 10,000 issues. Narrow the date or status filters.")
    fields = ("issue_id", "event_type", "status", "priority", "severity", "latitude", "longitude", "location_source",
              "report_count", "distinct_bus_count", "first_seen", "last_seen")
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(fields)
    for record in records:
        values = [str(getattr(record, field)) for field in fields]
        writer.writerow(["'" + value if value.lstrip().startswith(("=", "+", "-", "@")) and field not in ("latitude", "longitude") else value
                         for field, value in zip(fields, values)])
    return Response(output.getvalue(), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="codyssey-issues.csv"'})


@router.get("/statistics")
def get_statistics(request: Request, db: Session = Depends(get_db)):
    return services.statistics(db, request.app.state.settings)


@router.get("/analytics")
def get_analytics(date_from: date | None = None, date_to: date | None = None, db: Session = Depends(get_db)):
    return services.analytics(db, date_from, date_to)


@router.get("/buses")
def get_buses(request: Request, db: Session = Depends(get_db)):
    records = db.scalars(select(Bus).order_by(Bus.bus_id)).all()
    return {"items": [services.bus_dict(bus, request.app.state.settings.heartbeat_timeout) for bus in records], "total": len(records)}


@router.post("/buses/{bus_id}/heartbeat")
def heartbeat(data: HeartbeatCreate, request: Request, bus_id: str = Path(pattern=r"^[A-Za-z0-9_-]{1,80}$"), db: Session = Depends(get_db)):
    return services.save_heartbeat(db, bus_id, data, request.app.state.settings)


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "healthy", "contract_version": "2.0"}
