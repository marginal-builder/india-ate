"""Unit tests for QuarantinedRecord and IngestionBatch models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from india_ate.models import IngestionBatch, QuarantinedRecord


def test_quarantined_record_valid_and_frozen() -> None:
    record = QuarantinedRecord(
        source_name="FSSAI Hygiene Rating Portal",
        raw_record={"fssai_id": "12345"},
        reason="Invalid 14-digit FSSAI ID",
        quarantined_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
    )
    assert record.source_name == "FSSAI Hygiene Rating Portal"
    assert record.raw_record == {"fssai_id": "12345"}
    with pytest.raises(ValidationError):
        record.reason = "mutated"  # type: ignore[misc]


def test_quarantined_record_strict_types() -> None:
    with pytest.raises(ValidationError):
        QuarantinedRecord(
            source_name=123,  # type: ignore[arg-type]
            raw_record={"fssai_id": "12345"},
            reason="Invalid",
            quarantined_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
        )


def test_ingestion_batch_defaults_and_frozen() -> None:
    batch = IngestionBatch()
    assert batch.entities == []
    assert batch.quarantined == []
    with pytest.raises(ValidationError):
        batch.entities = []  # type: ignore[misc]
