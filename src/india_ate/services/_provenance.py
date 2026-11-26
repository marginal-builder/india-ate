"""Shared provenance classification for authoritative events."""

from india_ate.models import AuthoritativeEvent

OFFICIAL_VERIFICATION_TIERS: frozenset[str] = frozenset(
    {"official_registry", "peer_reviewed_science"}
)


def is_official_event(event: AuthoritativeEvent) -> bool:
    """Return True only for events backed by official or peer-reviewed sources."""
    return event.provenance.verification_tier in OFFICIAL_VERIFICATION_TIERS
