from datetime import date, datetime, time, timedelta, timezone
import hashlib
import json
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import func, or_, select, text
from location_intelligence import match_issue, review_priority, search_bounds
from .models import Bus, Issue, Observation, ObservationEvidence
from .evidence import decode_jpeg

INDIA = ZoneInfo("Asia/Kolkata")


def utc_now():
    return datetime.now(timezone.utc)


def iso(value):
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def record_dict(record):
    result = {column.name: getattr(record, column.name) for column in record.__table__.columns}
    result.pop("fingerprint", None)
    if "bbox" in result and result["bbox"]:
        result["bbox"] = json.loads(result["bbox"])
    return result


def evidence_columns():
    """Select gallery metadata without reading JPEG blobs during polling."""
    return (ObservationEvidence.event_id, ObservationEvidence.source_name, ObservationEvidence.frame_id,
            ObservationEvidence.video_time, ObservationEvidence.width, ObservationEvidence.height,
            ObservationEvidence.byte_count)


def evidence_dict(row):
    result = {column.key: getattr(row, column.key) for column in evidence_columns()}
    result["url"] = f"/api/observations/{row.event_id}/evidence"
    return result


def issue_summaries(db, records):
    """Attach one latest saved image per issue in a single bounded query."""
    results = {record.issue_id: dict(record_dict(record), evidence_count=0, latest_evidence=None) for record in records}
    if not results:
        return []
    ranked = select(*evidence_columns(), Observation.issue_id, Observation.bus_id, Observation.confidence,
                    Observation.timestamp, func.count().over(partition_by=Observation.issue_id).label("image_count"),
                    func.row_number().over(partition_by=Observation.issue_id,
                                           order_by=(Observation.timestamp.desc(), Observation.event_id.desc())).label("rank"))
    ranked = ranked.join(Observation).where(Observation.issue_id.in_(results)).subquery()
    for row in db.execute(select(ranked).where(ranked.c.rank == 1)):
        results[row.issue_id]["evidence_count"] = row.image_count
        results[row.issue_id]["latest_evidence"] = dict(evidence_dict(row), bus_id=row.bus_id,
                                                      confidence=row.confidence, timestamp=row.timestamp)
    return list(results.values())


def nearby_issue_query(payload, radius_m):
    lower, upper, longitudes = search_bounds(payload["latitude"], payload["longitude"], radius_m)
    return select(Issue).where(Issue.status == "open", Issue.event_type == payload["event_type"],
                              Issue.location_source == payload["location_source"], Issue.latitude.between(lower, upper),
                              or_(*(Issue.longitude.between(start, end) for start, end in longitudes)))


def accept_observation(db, observation, settings):
    payload = observation.model_dump(mode="json")
    payload["timestamp"] = iso(observation.timestamp)
    payload["gps_timestamp"] = iso(observation.gps_timestamp)
    # Keep pre-evidence fingerprints stable when an old outbox is retried.
    if payload.get("evidence") is None:
        payload.pop("evidence", None)
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    # Lock before reading existing IDs/candidates, including across worker processes.
    db.execute(text("BEGIN IMMEDIATE"))
    existing = db.get(Observation, payload["event_id"])
    if existing:
        if existing.fingerprint != fingerprint:
            db.rollback()
            raise HTTPException(409, "event_id already exists with different observation data")
        db.commit()
        return {"event_id": existing.event_id, "issue_id": existing.issue_id, "duplicate": True}
    candidates = db.scalars(nearby_issue_query(payload, settings.match_radius_m)).all()
    match = match_issue(payload, [record_dict(issue) for issue in candidates], settings.match_radius_m)
    issue = db.get(Issue, match["matched_issue_id"]) if match["matched_issue_id"] else None
    if issue is None:
        issue = Issue(issue_id=f"ISSUE_{uuid4().hex}", event_type=payload["event_type"], latitude=payload["latitude"], longitude=payload["longitude"],
                      location_source=payload["location_source"], first_seen=payload["timestamp"], last_seen=payload["timestamp"], priority_reason="First observation")
        db.add(issue)
        db.flush()
    stored = dict(payload, issue_id=issue.issue_id, received_at=iso(utc_now()), fingerprint=fingerprint)
    evidence = stored.pop("evidence", None)
    stored["bbox"] = json.dumps(payload["bbox"]) if payload["bbox"] is not None else None
    db.add(Observation(**stored))
    db.flush()
    if evidence:
        content, width, height = decode_jpeg(evidence["jpeg_base64"])
        db.add(ObservationEvidence(event_id=payload["event_id"], jpeg=content, sha256=hashlib.sha256(content).hexdigest(),
                                   byte_count=len(content), width=width, height=height, source_name=evidence["source_name"],
                                   frame_id=evidence["frame_id"], video_time=evidence["video_time"]))
    bus_ids = db.scalars(select(Observation.bus_id).where(Observation.issue_id == issue.issue_id).distinct()).all()
    issue.report_count = db.scalar(select(func.count()).select_from(Observation).where(Observation.issue_id == issue.issue_id))
    for key, value in review_priority(bus_ids).items():
        setattr(issue, key, value)
    issue.first_seen = min(issue.first_seen, payload["timestamp"])
    issue.last_seen = max(issue.last_seen, payload["timestamp"])
    db.commit()
    return {"event_id": payload["event_id"], "issue_id": issue.issue_id, "duplicate": False}


def date_bounds(date_from, date_to):
    if any(value and not date(1900, 1, 1) <= value <= date(9998, 12, 31) for value in (date_from, date_to)):
        raise HTTPException(422, "Dates must be between 1900-01-01 and 9998-12-31")
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "date_from must not be later than date_to")
    lower = iso(datetime.combine(date_from, time.min, INDIA)) if date_from else None
    upper = iso(datetime.combine(date_to + timedelta(days=1), time.min, INDIA)) if date_to else None
    return lower, upper


def filter_issues(query, status=None, priority=None, event_type=None, date_from=None, date_to=None):
    for field, value in ((Issue.status, status), (Issue.priority, priority), (Issue.event_type, event_type)):
        if value:
            query = query.where(field == value)
    lower, upper = date_bounds(date_from, date_to)
    if lower:
        query = query.where(Issue.last_seen >= lower)
    if upper:
        query = query.where(Issue.last_seen < upper)
    return query


def bus_dict(bus, timeout, now=None):
    result = record_dict(bus)
    now = now or utc_now()
    result["online"] = (now - datetime.fromisoformat(bus.last_seen.replace("Z", "+00:00"))).total_seconds() <= timeout
    return result


def save_heartbeat(db, bus_id, data, settings):
    now = utc_now()
    age = (now - data.timestamp).total_seconds()
    if age < -5:
        raise HTTPException(422, "Heartbeat timestamp is in the future")
    if age > settings.heartbeat_timeout:
        raise HTTPException(422, "Heartbeat is too old; send current telemetry")
    db.execute(text("BEGIN IMMEDIATE"))
    bus = db.get(Bus, bus_id)
    timestamp = iso(data.timestamp)
    if bus and bus.timestamp >= timestamp:
        db.commit()
        return bus_dict(bus, settings.heartbeat_timeout, now)
    if not bus:
        bus = Bus(bus_id=bus_id)
        db.add(bus)
    for key, value in data.model_dump().items():
        setattr(bus, key, timestamp if key == "timestamp" else value)
    bus.last_seen = iso(now)
    db.commit()
    return bus_dict(bus, settings.heartbeat_timeout, now)


def open_priorities(db):
    counts = dict(db.execute(select(Issue.priority, func.count()).where(Issue.status == "open").group_by(Issue.priority)).all())
    return {priority: counts.get(priority, 0) for priority in ("low", "medium", "high")}


def statistics(db, settings):
    today = utc_now().astimezone(INDIA).date()
    lower, upper = date_bounds(today, today)
    count = lambda *conditions: db.scalar(select(func.count()).select_from(Issue).where(*conditions))
    priorities = open_priorities(db)
    cutoff = iso(utc_now() - timedelta(seconds=settings.heartbeat_timeout))
    return {"total_issues": count(), "new_issues_today": count(Issue.first_seen >= lower, Issue.first_seen < upper),
            "open_high_priority_issues": priorities["high"], "resolved_issues": count(Issue.status == "resolved"),
            "open_issues": sum(priorities.values()), "dismissed_issues": count(Issue.status == "dismissed"),
            "active_buses": db.scalar(select(func.count()).select_from(Bus).where(Bus.last_seen >= cutoff)), "open_by_priority": priorities}


def analytics(db, date_from=None, date_to=None):
    date_to = date_to or utc_now().astimezone(INDIA).date()
    date_bounds(date_from, date_to)
    date_from = date_from or date_to - timedelta(days=6)
    if (date_to - date_from).days > 365:
        raise HTTPException(422, "Analytics date range cannot exceed 366 days")
    lower, upper = date_bounds(date_from, date_to)
    days = {(date_from + timedelta(days=offset)).isoformat(): 0 for offset in range((date_to - date_from).days + 1)}
    for value in db.scalars(select(Issue.first_seen).where(Issue.first_seen >= lower, Issue.first_seen < upper)):
        day = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(INDIA).date().isoformat()
        days[day] += 1
    buses = db.execute(select(Observation.bus_id, func.count()).where(Observation.timestamp >= lower, Observation.timestamp < upper).group_by(Observation.bus_id).order_by(Observation.bus_id)).all()
    return {"date_from": date_from.isoformat(), "date_to": date_to.isoformat(), "timezone": "Asia/Kolkata",
            "new_issues_by_day": [{"date": day, "count": count} for day, count in days.items()], "open_by_priority": open_priorities(db),
            "observations_by_bus": [{"bus_id": bus, "count": count} for bus, count in buses]}
