from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    event_type: str = "pothole"

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    severity: str = "medium"

    priority_score: float = 0.0

    bus_id: Optional[str] = None

    timestamp: Optional[datetime] = None

    bbox: Optional[str] = None


class AlertResponse(AlertCreate):
    id: int
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True