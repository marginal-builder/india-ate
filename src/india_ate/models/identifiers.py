"""Deterministic offline decoder for Indian 14-digit FSSAI identifiers."""

from typing import Any, Literal

from india_ate.models.base import RegulatoryIdentifier

FSSAI_LENGTH = 14
TIER_LICENSE_DIGIT = "1"
TIER_BASIC_REG_DIGIT = "2"
CENTRAL_STATE_CODE = "00"
YEAR_CENTURY_BASE = 2000

_TIER_INDEX = 0
_STATE_SLICE = slice(1, 3)
_YEAR_SLICE = slice(3, 5)
_OFFICER_SLICE = slice(5, 8)
_SERIAL_SLICE = slice(8, 14)

_TIER_LABELS: dict[str, str] = {
    TIER_LICENSE_DIGIT: "license",
    TIER_BASIC_REG_DIGIT: "basic_registration",
}

STATE_UT_CODES: dict[str, str] = {
    "00": "Central",
    "01": "Andhra Pradesh",
    "02": "Arunachal Pradesh",
    "03": "Assam",
    "04": "Bihar",
    "05": "Chhattisgarh",
    "06": "Goa",
    "07": "Gujarat",
    "08": "Haryana",
    "09": "Himachal Pradesh",
    "10": "Jammu & Kashmir",
    "11": "Jharkhand",
    "12": "Karnataka",
    "13": "Kerala",
    "14": "Madhya Pradesh",
    "15": "Maharashtra",
    "16": "Manipur",
    "17": "Meghalaya",
    "18": "Mizoram",
    "19": "Nagaland",
    "20": "Odisha",
    "21": "Punjab",
    "22": "Rajasthan",
    "23": "Sikkim",
    "24": "Tamil Nadu",
    "25": "Tripura",
    "26": "Uttarakhand",
    "27": "Uttar Pradesh",
    "28": "West Bengal",
    "29": "Andaman & Nicobar Islands",
    "30": "Chandigarh",
    "31": "Dadra & Nagar Haveli",
    "32": "Daman & Diu",
    "33": "Delhi",
    "34": "Lakshadweep",
    "35": "Puducherry",
    "36": "Telangana",
    "37": "Ladakh",
}

CENTRAL_RO_DO_CODES: dict[str, tuple[str, str]] = {
    "021": ("RO Mumbai", "Gujarat"),
    "022": ("RO Mumbai", "Maharashtra"),
    "023": ("RO Mumbai", "Dadra & Nagar Haveli"),
    "024": ("RO Mumbai", "Daman & Diu"),
    "025": ("RO Mumbai", "Goa"),
    "026": ("RO Mumbai", "Madhya Pradesh"),
    "031": ("RO Kolkata", "West Bengal"),
    "032": ("RO Kolkata", "Odisha"),
    "033": ("RO Kolkata", "Bihar"),
    "034": ("RO Kolkata", "Jharkhand"),
    "035": ("RO Kolkata", "Sikkim"),
    "036": ("RO Kolkata", "Andaman & Nicobar Islands"),
    "037": ("RO Kolkata", "Chhattisgarh"),
    "041": ("RO Chennai", "Kerala"),
    "042": ("RO Chennai", "Tamil Nadu"),
    "043": ("RO Chennai", "Karnataka"),
    "044": ("RO Chennai", "Andhra Pradesh"),
    "045": ("RO Chennai", "Puducherry"),
    "046": ("RO Chennai", "Lakshadweep"),
    "071": ("RO Guwahati", "Assam"),
    "072": ("RO Guwahati", "Arunachal Pradesh"),
    "073": ("RO Guwahati", "Tripura"),
    "074": ("RO Guwahati", "Manipur"),
    "075": ("RO Guwahati", "Mizoram"),
    "076": ("RO Guwahati", "Meghalaya"),
    "077": ("RO Guwahati", "Nagaland"),
}


def _normalize_and_validate(raw_value: str) -> str:
    """Trim whitespace and verify 14-digit ASCII numeric FSSAI format."""
    cleaned = raw_value.strip()
    if len(cleaned) != FSSAI_LENGTH or not cleaned.isascii() or not cleaned.isdigit():
        raise ValueError("FSSAI ID must be a 14-digit numeric string")
    tier_digit = cleaned[_TIER_INDEX]
    if tier_digit not in _TIER_LABELS:
        raise ValueError(f"Invalid FSSAI license tier digit: {tier_digit!r}")
    state_code = cleaned[_STATE_SLICE]
    if state_code not in STATE_UT_CODES:
        raise ValueError(f"Unknown FSSAI state or UT code: {state_code!r}")
    return cleaned


def _resolve_central_ro(
    state_code: str, officer_code: str
) -> tuple[str | None, str | None]:
    if state_code != CENTRAL_STATE_CODE:
        return None, None
    return CENTRAL_RO_DO_CODES.get(officer_code, (None, None))


def _authority_scope(state_code: str) -> str:
    return "central" if state_code == CENTRAL_STATE_CODE else "state_or_ut"


class IndiaFSSAI14(RegulatoryIdentifier):
    """Deterministic offline decoder per FSSAI Circular 5a968698b3ceb13.pdf."""

    jurisdiction_iso: Literal["IN"] = "IN"
    scheme: Literal["IN_FSSAI_14"] = "IN_FSSAI_14"

    def decode_offline(self) -> dict[str, Any]:
        """Decode the 14-digit FSSAI identifier into structured metadata."""
        cleaned = _normalize_and_validate(self.raw_value)
        tier_digit = cleaned[_TIER_INDEX]
        state_code = cleaned[_STATE_SLICE]
        officer_code = cleaned[_OFFICER_SLICE]
        central_ro, ro_state = _resolve_central_ro(state_code, officer_code)
        return {
            "tier": _TIER_LABELS[tier_digit],
            "pre_inspection_exempt_post_apr2026": tier_digit == TIER_BASIC_REG_DIGIT,
            "authority_scope": _authority_scope(state_code),
            "state_code": state_code,
            "state_name": STATE_UT_CODES[state_code],
            "registration_year": YEAR_CENTURY_BASE + int(cleaned[_YEAR_SLICE]),
            "officer_code": officer_code,
            "central_regional_office": central_ro,
            "officer_jurisdiction_state": ro_state,
            "serial": cleaned[_SERIAL_SLICE],
        }
