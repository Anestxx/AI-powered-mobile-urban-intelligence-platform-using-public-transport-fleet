from sqlalchemy import Column, Float, ForeignKey, Index, Integer, LargeBinary, String, Text
from .database import Base


class Issue(Base):
    __tablename__ = "issues"
    issue_id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_source = Column(String, nullable=False)
    severity = Column(String, nullable=False, default="unknown")
    priority = Column(String, nullable=False, default="low", index=True)
    priority_reason = Column(String, nullable=False)
    priority_rule_version = Column(String, nullable=False, default="demo_v1")
    report_count = Column(Integer, nullable=False, default=0)
    distinct_bus_count = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="open", index=True)
    first_seen = Column(String, nullable=False)
    last_seen = Column(String, nullable=False, index=True)


ISSUE_LOCATION_INDEX = Index("ix_issues_location_match", Issue.status, Issue.event_type, Issue.location_source, Issue.latitude, Issue.longitude)


class IssueActivity(Base):
    __tablename__ = "issue_activity"
    activity_id = Column(String, primary_key=True)
    issue_id = Column(String, ForeignKey("issues.issue_id"), nullable=False, index=True)
    previous_status = Column(String, nullable=False)
    status = Column(String, nullable=False)
    note = Column(String, nullable=False, default="")
    actor = Column(String, nullable=False, default="local_operator")
    timestamp = Column(String, nullable=False)


class Observation(Base):
    __tablename__ = "observations"
    event_id = Column(String, primary_key=True)
    issue_id = Column(String, ForeignKey("issues.issue_id"), nullable=False, index=True)
    bus_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_source = Column(String, nullable=False)
    timestamp = Column(String, nullable=False, index=True)
    gps_timestamp = Column(String, nullable=False)
    received_at = Column(String, nullable=False)
    bbox = Column(Text, nullable=True)
    model_version = Column(String, nullable=True)
    fingerprint = Column(String, nullable=False)


class Bus(Base):
    __tablename__ = "buses"
    bus_id = Column(String, primary_key=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_source = Column(String, nullable=True)
    timestamp = Column(String, nullable=False)
    last_seen = Column(String, nullable=False, index=True)
    camera_status = Column(String, nullable=False)
    ai_status = Column(String, nullable=False)


class ObservationEvidence(Base):
    __tablename__ = "observation_evidence"
    event_id = Column(String, ForeignKey("observations.event_id"), primary_key=True)
    jpeg = Column(LargeBinary, nullable=False)
    sha256 = Column(String, nullable=False)
    byte_count = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    source_name = Column(String, nullable=False)
    frame_id = Column(Integer, nullable=False)
    video_time = Column(Float, nullable=False)
