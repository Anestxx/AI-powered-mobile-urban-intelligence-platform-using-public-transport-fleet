from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)

    event_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    severity = Column(String, default="medium")
    priority_score = Column(Float, default=0.0)

    bus_id = Column(String, nullable=True)

    timestamp = Column(
        DateTime,
        default=datetime.utcnow
    )

    bbox = Column(String, nullable=True)

    status = Column(
        String,
        default="new"
    )