"""Open-data UTF-8 JSONL dataset export and import round-trip."""

import json
from collections.abc import Sequence
from pathlib import Path

from india_ate.models import (
    AuthoritativeEvent,
    BrandListing,
    FoodActor,
    FoodItem,
    FoodPremises,
    ScientificStandard,
    Substance,
)

EntityModel = (
    FoodActor
    | FoodPremises
    | BrandListing
    | FoodItem
    | Substance
    | ScientificStandard
    | AuthoritativeEvent
)

ENTITY_REGISTRY: dict[str, type[EntityModel]] = {
    "FoodActor": FoodActor,
    "FoodPremises": FoodPremises,
    "BrandListing": BrandListing,
    "FoodItem": FoodItem,
    "Substance": Substance,
    "ScientificStandard": ScientificStandard,
    "AuthoritativeEvent": AuthoritativeEvent,
}


def export_jsonl(entities: Sequence[EntityModel], path: Path) -> int:
    """Export entity models to a UTF-8 JSONL file and return record count."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(
            {
                "entity_type": type(entity).__name__,
                "payload": json.loads(entity.model_dump_json()),
            },
            ensure_ascii=False,
        )
        for entity in entities
    ]
    content = "\n".join(lines) + ("\n" if lines else "")
    path.write_text(content, encoding="utf-8")
    return len(lines)


def _decode_jsonl_line(line: str) -> EntityModel:
    """Parse one JSONL line into its validated Pydantic entity model."""
    record = json.loads(line)
    if not isinstance(record, dict):
        raise ValueError("JSONL line must decode to a JSON object")
    entity_type = record.get("entity_type")
    if not isinstance(entity_type, str) or entity_type not in ENTITY_REGISTRY:
        raise ValueError(f"Unknown or missing entity_type: {entity_type!r}")
    if "payload" not in record:
        raise ValueError("JSONL record missing 'payload' field")
    model_cls = ENTITY_REGISTRY[entity_type]
    return model_cls.model_validate_json(json.dumps(record["payload"]))


def import_jsonl(path: Path) -> list[EntityModel]:
    """Import entity models from a UTF-8 JSONL file with strict validation."""
    raw = path.read_text(encoding="utf-8")
    if not raw:
        return []
    return [_decode_jsonl_line(line) for line in raw.splitlines()]
