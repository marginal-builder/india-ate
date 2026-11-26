"""Pluggable ingestion adapter contract for india-ate."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class BaseSourceAdapter(ABC):
    """Abstract base contract for deterministic regulatory and science adapters."""

    source_name: str
    jurisdiction_iso: str

    @abstractmethod
    def fetch(self) -> bytes:
        """Fetch raw source bytes from an official or local fixture source."""

    @abstractmethod
    def parse(self, raw: bytes) -> list[dict[str, Any]]:
        """Parse raw bytes into structured candidate dictionaries."""

    @abstractmethod
    def validate_and_emit(self, records: list[dict[str, Any]]) -> list[BaseModel]:
        """Validate strictly and quarantine ambiguous records rather than guessing."""
