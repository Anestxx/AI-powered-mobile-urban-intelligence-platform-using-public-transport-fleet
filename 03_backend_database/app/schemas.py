from datetime import timezone
import math
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator
from location_intelligence import validate_location


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class EvidenceCreate(ContractModel):
    jpeg_base64: str = Field(min_length=4, max_length=262144)
    source_name: str = Field(min_length=1, max_length=160)
    frame_id: int = Field(ge=0, le=2147483647, strict=True)
    video_time: float = Field(ge=0, le=1000000000)

    @field_validator("jpeg_base64")
    @classmethod
    def valid_jpeg(cls, value):
        from .evidence import decode_jpeg
        decode_jpeg(value)
        return value

    @field_validator("source_name")
    @classmethod
    def source_label(cls, value):
        if any(char in value for char in ("/", "\\", "\x00")) or not value.strip():
            raise ValueError("Use a source label or filename, not a local path")
        return value.strip()


class ObservationCreate(ContractModel):
    event_id: UUID
    event_type: Literal["pothole"]
    bus_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    confidence: float = Field(ge=0, le=1, strict=True)
    latitude: float = Field(ge=-90, le=90, strict=True)
    longitude: float = Field(ge=-180, le=180, strict=True)
    timestamp: AwareDatetime
    gps_timestamp: AwareDatetime
    location_source: Literal["simulated", "gps"]
    bbox: list[float] | None = Field(default=None, min_length=4, max_length=4)
    model_version: str | None = Field(default=None, max_length=160)
    evidence: EvidenceCreate | None = None

    @field_validator("timestamp", "gps_timestamp")
    @classmethod
    def to_utc(cls, value):
        return value.astimezone(timezone.utc)

    @field_validator("bbox", mode="before")
    @classmethod
    def valid_box(cls, value):
        if value is None:
            return value
        if not isinstance(value, list) or len(value) != 4 or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0 for x in value):
            raise ValueError("bbox must contain four finite nonnegative coordinates")
        if value[2] <= value[0] or value[3] <= value[1]:
            raise ValueError("bbox must have positive width and height")
        return value

    @model_validator(mode="after")
    def fresh_location(self):
        validate_location(self.model_dump(), self.timestamp)
        return self


class HeartbeatCreate(ContractModel):
    timestamp: AwareDatetime
    camera_status: Literal["online", "offline", "error"]
    ai_status: Literal["online", "offline", "error"]
    latitude: float | None = Field(default=None, ge=-90, le=90, strict=True)
    longitude: float | None = Field(default=None, ge=-180, le=180, strict=True)
    location_source: Literal["simulated", "gps"] | None = None

    @field_validator("timestamp")
    @classmethod
    def to_utc(cls, value):
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def location_pair(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Provide both latitude and longitude")
        if self.latitude is not None and self.location_source is None:
            raise ValueError("Provide location_source with coordinates")
        return self


class StatusUpdate(ContractModel):
    status: Literal["open", "resolved", "dismissed"]
    note: str = Field(default="", max_length=500)
    expected_status: Literal["open", "resolved", "dismissed"] | None = None

    @model_validator(mode="after")
    def dismissal_reason(self):
        if self.status == "dismissed" and not self.note.strip():
            raise ValueError("A reason is required when marking a false detection")
        return self


class Login(ContractModel):
    password: str = Field(min_length=1, max_length=512)
