"""ICMR-NIN IFCT 2017 nutrition composition adapter."""

import csv
import hashlib
import io
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from india_ate.adapters import BaseSourceAdapter
from india_ate.adapters._common import (
    build_provenance,
    make_quarantined,
    require_non_empty,
)
from india_ate.models import (
    EvidenceProvenance,
    FoodItem,
    IngestionBatch,
    QuarantinedRecord,
    ScientificStandard,
    Substance,
)

IFCT_SOURCE_URL = "https://github.com/ifct2017/ifct2017"
IFCT_EFFECTIVE_DATE = date(2017, 1, 1)

NUTRIENT_COLUMNS: dict[str, tuple[str, str]] = {
    "enerc": ("Energy", "kJ/100g"),
    "protcnt": ("Protein", "g/100g"),
    "fatce": ("Total Fat", "g/100g"),
    "fibtg": ("Dietary Fiber", "g/100g"),
    "choavldf": ("Carbohydrate", "g/100g"),
    "ca": ("Calcium", "mg/100g"),
    "fe": ("Iron", "mg/100g"),
    "zn": ("Zinc", "mg/100g"),
    "vitc": ("Ascorbic Acid (Vitamin C)", "mg/100g"),
}


class IFCTNutritionAdapter(BaseSourceAdapter):
    """Adapter for ICMR-NIN IFCT 2017 measured Indian food compositions."""

    source_name = "ICMR-NIN IFCT 2017"
    jurisdiction_iso = "IN"

    def __init__(self, csv_path: Path | None = None) -> None:
        self._csv_path = csv_path
        self._content_sha256 = hashlib.sha256(b"").hexdigest()
        self._retrieved_at = datetime.now(UTC)

    def fetch(self) -> bytes:
        """Read raw IFCT CSV bytes from the configured local corpus path."""
        if self._csv_path is None:
            raise ValueError("csv_path is required for IFCTNutritionAdapter.fetch()")
        raw = self._csv_path.read_bytes()
        self._content_sha256 = hashlib.sha256(raw).hexdigest()
        self._retrieved_at = datetime.now(UTC)
        return raw

    def parse(self, raw: bytes) -> list[dict[str, Any]]:
        """Parse UTF-8 IFCT CSV bytes into candidate row dictionaries."""
        self._content_sha256 = hashlib.sha256(raw).hexdigest()
        self._retrieved_at = datetime.now(UTC)
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8")))
        return [dict(row) for row in reader]

    def _build_standard(
        self,
        code: str,
        col: str,
        raw_val: object,
        item_id: str,
        unit: str,
        prov: EvidenceProvenance,
    ) -> ScientificStandard:
        try:
            value = float(str(raw_val))
        except ValueError as exc:
            raise ValueError(f"Non-numeric IFCT value for {col}: {raw_val}") from exc
        return ScientificStandard(
            standard_id=f"std:in:ifct:{code}:{col}",
            standard_type="nutrient_composition",
            jurisdiction_iso=self.jurisdiction_iso,
            substance_id=f"sub:ifct:{col}",
            food_item_id=item_id,
            value=value,
            unit=unit,
            effective_date=IFCT_EFFECTIVE_DATE,
            provenance=prov,
        )

    def _parse_nutrients(
        self,
        record: dict[str, Any],
        item_id: str,
        code: str,
        prov: EvidenceProvenance,
    ) -> list[ScientificStandard]:
        standards: list[ScientificStandard] = []
        for col, (_, unit) in NUTRIENT_COLUMNS.items():
            raw_val = record.get(col)
            if raw_val not in (None, ""):
                standards.append(
                    self._build_standard(code, col, raw_val, item_id, unit, prov)
                )
        return standards

    def _emit_row(
        self, record: dict[str, Any], prov: EvidenceProvenance
    ) -> tuple[FoodItem, list[ScientificStandard]]:
        code = require_non_empty(record, "code", "code")
        name = require_non_empty(record, "name", "name")
        item = FoodItem(
            item_id=f"item:in:ifct:{code}",
            canonical_name=name,
            item_kind="raw_staple",
            ifct_code=code,
        )
        standards = self._parse_nutrients(record, item.item_id, code, prov)
        return item, standards

    def _nutrient_substances(self) -> list[BaseModel]:
        return [
            Substance(
                substance_id=f"sub:ifct:{col}",
                canonical_name=label,
                substance_class="nutrient",
            )
            for col, (label, _) in NUTRIENT_COLUMNS.items()
        ]

    def validate_and_emit_batch(self, records: list[dict[str, Any]]) -> IngestionBatch:
        """Validate IFCT rows strictly and quarantine malformed rows."""
        prov = build_provenance(
            self.source_name,
            IFCT_SOURCE_URL,
            self._retrieved_at,
            self._content_sha256,
            tier="peer_reviewed_science",
        )
        entities: list[BaseModel] = self._nutrient_substances()
        quarantined: list[QuarantinedRecord] = []
        for record in records:
            try:
                item, standards = self._emit_row(record, prov)
            except ValueError as exc:
                quarantined.append(
                    make_quarantined(
                        self.source_name, record, str(exc), self._retrieved_at
                    )
                )
                continue
            entities.append(item)
            entities.extend(standards)
        return IngestionBatch(entities=entities, quarantined=quarantined)

    def validate_and_emit(self, records: list[dict[str, Any]]) -> list[BaseModel]:
        """Return only validated entities, routing invalid rows to quarantine."""
        return self.validate_and_emit_batch(records).entities
