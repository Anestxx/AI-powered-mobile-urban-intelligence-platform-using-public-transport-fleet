from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Alert
from schemas import AlertCreate


router = APIRouter(prefix="/api")


@router.post("/alerts")
def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db)
):
    alert = Alert(
        event_type=alert_data.event_type,
        confidence=alert_data.confidence,
        latitude=alert_data.latitude,
        longitude=alert_data.longitude,
        severity=alert_data.severity,
        priority_score=alert_data.priority_score,
        bus_id=alert_data.bus_id,
        timestamp=alert_data.timestamp or datetime.utcnow(),
        bbox=alert_data.bbox
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return {
        "success": True,
        "alert_id": alert.id,
        "message": "Alert stored successfully"
    }


@router.get("/alerts")
def get_alerts(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, le=500)
):
    return (
        db.query(Alert)
        .order_by(Alert.timestamp.desc())
        .limit(limit)
        .all()
    )


@router.get("/alerts/{alert_id}")
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id)
        .first()
    )

    if not alert:
        return {
            "success": False,
            "message": "Alert not found"
        }

    return alert


@router.get("/statistics")
def get_statistics(
    db: Session = Depends(get_db)
):
    alerts = db.query(Alert).all()

    return {
        "total_alerts": len(alerts),

        "potholes": sum(
            a.event_type == "pothole"
            for a in alerts
        ),

        "traffic_events": sum(
            a.event_type == "traffic"
            for a in alerts
        ),

        "infrastructure_events": sum(
            a.event_type == "infrastructure"
            for a in alerts
        ),

        "unsafe_events": sum(
            a.event_type == "unsafe_behaviour"
            for a in alerts
        ),

        "emergency_events": sum(
            a.event_type == "emergency"
            for a in alerts
        ),

        "high_severity": sum(
            a.severity == "high"
            for a in alerts
        ),

        "medium_severity": sum(
            a.severity == "medium"
            for a in alerts
        ),

        "low_severity": sum(
            a.severity == "low"
            for a in alerts
        )
    }


@router.delete("/alerts/{alert_id}")
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id)
        .first()
    )

    if not alert:
        return {
            "success": False,
            "message": "Alert not found"
        }

    db.delete(alert)
    db.commit()

    return {
        "success": True,
        "message": "Alert deleted"
    }