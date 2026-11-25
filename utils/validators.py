import re
from datetime import date

BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
COMPONENT_TYPES = {"Whole Blood", "Red Blood Cells", "Platelets", "Plasma"}
SOURCES = {
    "Direct Blood Donation", "Blood Donation Camp", "Hospital",
    "Blood Bank Transfer", "Other",
}


def parse_date(value, field):
    try:
        parsed = date.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be a valid date")
    return parsed


def validate_inventory(payload, require_all=True):
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object")

    required = [
        "blood_group", "component_type", "units_collected", "donor_name",
        "donor_phone", "city", "source", "donation_date", "collection_date",
        "expiry_date",
    ]
    if require_all:
        missing = [field for field in required if payload.get(field) in (None, "")]
        if missing:
            raise ValueError("Missing required fields: " + ", ".join(missing))

    if payload.get("blood_group") not in BLOOD_GROUPS:
        raise ValueError("Invalid blood group")
    if payload.get("component_type") not in COMPONENT_TYPES:
        raise ValueError("Invalid component type")
    if payload.get("source") not in SOURCES:
        raise ValueError("Invalid donation source")

    phone = str(payload.get("donor_phone", "")).strip()
    if not re.fullmatch(r"\+?[0-9][0-9\- ]{7,14}[0-9]", phone):
        raise ValueError("Invalid donor phone number")

    try:
        units = int(payload["units_collected"])
    except (TypeError, ValueError, KeyError):
        raise ValueError("Units collected must be a positive integer")
    if units < 1:
        raise ValueError("Units collected must be a positive integer")

    donation = parse_date(payload["donation_date"], "Donation date")
    collection = parse_date(payload["collection_date"], "Collection date")
    expiry = parse_date(payload["expiry_date"], "Expiry date")
    if donation > collection:
        raise ValueError("Donation date cannot be after collection date")
    if expiry <= collection:
        raise ValueError("Expiry date must be after collection date")

    if not str(payload.get("donor_name", "")).strip():
        raise ValueError("Donor name is required")
    if not str(payload.get("city", "")).strip():
        raise ValueError("City is required")

    return {
        "blood_group": payload["blood_group"].strip(),
        "component_type": payload["component_type"].strip(),
        "units_collected": units,
        "donor_name": str(payload["donor_name"]).strip(),
        "donor_phone": phone,
        "city": str(payload["city"]).strip(),
        "source": payload["source"].strip(),
        "donation_date": donation,
        "collection_date": collection,
        "expiry_date": expiry,
        "remarks": str(payload.get("remarks", "")).strip(),
    }
