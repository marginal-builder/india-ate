"""Quarantine and ingestion batch models for deterministic adapter output."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QuarantinedRecord(BaseModel):
    """Ambiguous or invalid source record quarantined instead of guessed."""

    model_config = ConfigDict(strict=True, frozen=True)

    source_name: str
    raw_record: dict[str, object]
    reason: str
    quarantined_at: datetime


class IngestionBatch(BaseModel):
    """Deterministic output of adapter validation with entities and quarantine."""

    model_config = ConfigDict(strict=True, frozen=True)

    entities: list[BaseModel] = Field(default_factory=list)
    quarantined: list[QuarantinedRecord] = Field(default_factory=list)
