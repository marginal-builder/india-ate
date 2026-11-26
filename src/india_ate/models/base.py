"""Base models for provenance and polymorphic regulatory identifiers."""

from datetime import datetime
from typing import Any, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    HttpUrl,
    ModelWrapValidatorHandler,
    ValidationInfo,
    model_validator,
)

VerificationTier = Literal[
    "official_registry",
    "peer_reviewed_science",
    "user_verified_snapshot",
]


class EvidenceProvenance(BaseModel):
    """Cryptographically anchored provenance for every graph claim."""

    model_config = ConfigDict(strict=True, frozen=True)

    source_name: str
    source_url: HttpUrl
    retrieved_at: datetime
    content_sha256: str
    verification_tier: VerificationTier


class RegulatoryIdentifier(BaseModel):
    """Base polymorphic identifier enabling multi-country expansion."""

    model_config = ConfigDict(strict=True, frozen=True)

    jurisdiction_iso: str
    scheme: str
    raw_value: str

    @model_validator(mode="wrap")
    @classmethod
    def _dispatch_subclass_from_json(
        cls,
        value: object,
        handler: ModelWrapValidatorHandler[Self],
        info: ValidationInfo,
    ) -> Self:
        """Reconstruct concrete identifier subclasses during JSON deserialization."""
        if (
            cls is RegulatoryIdentifier
            and info.mode == "json"
            and isinstance(value, dict)
        ):
            scheme = value.get("scheme")
            for sub in cls.__subclasses__():
                scheme_field = sub.model_fields.get("scheme")
                if scheme_field is not None and scheme_field.default == scheme:
                    return sub.model_validate(value)
        return handler(value)

    def decode_offline(self) -> dict[str, Any]:
        """Decode identifier components offline without network access."""
        raise NotImplementedError
