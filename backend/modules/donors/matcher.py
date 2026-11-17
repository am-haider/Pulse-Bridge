import urllib.parse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from backend.modules.donors.compatibility import get_compatible_donor_groups, get_compatibility_description
from backend.models.schemas import MatchedDonor, BloodMatchRequest, BloodMatchResponse


def normalize_pakistan_phone(raw_phone: str) -> str:
    """
    Normalizes a Pakistani phone number to standard E.164 format (+92...).
    E.g., 3992443540 -> +923992443540, 03001234567 -> +923001234567
    """
    cleaned = "".join(filter(str.isdigit, str(raw_phone)))
    if cleaned.startswith("92") and len(cleaned) == 12:
        return f"+{cleaned}"
    if cleaned.startswith("0") and len(cleaned) == 11:
        return f"+92{cleaned[1:]}"
    if len(cleaned) == 10:
        return f"+92{cleaned}"
    return f"+92{cleaned}" if not cleaned.startswith("+") else cleaned


def mask_phone_number(normalized_phone: str) -> str:
    """
    Masks middle digits of a phone number for donor privacy.
    E.g., +923992443540 -> +92 399 ••••• 40
    """
    if len(normalized_phone) >= 12:
        prefix = normalized_phone[:6]
        suffix = normalized_phone[-2:]
        return f"{prefix} ••••• {suffix}"
    return "+92 ••• •••••••"


def generate_emergency_whatsapp_link(phone: str, recipient_group: str, city: str, hospital: Optional[str] = None) -> str:
    """
    Generates a pre-filled direct WhatsApp click-to-connect URL.
    """
    digits_only = "".join(filter(str.isdigit, phone))
    hospital_str = f" at {hospital}" if hospital else ""
    message = (
        f"🚨 EMERGENCY BLOOD REQUEST — PULSE BRIDGE\n"
        f"Assalam-o-Alaikum, an urgent requirement for blood group *{recipient_group}* has arisen in {city}{hospital_str}. "
        f"As a registered voluntary donor on Pulse Bridge, are you currently available to donate? "
        f"Your prompt response can save a life. JazakAllah Khair."
    )
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{digits_only}?text={encoded}"


def is_eligible_to_donate(last_donation_date_str: Optional[str]) -> bool:
    """
    Verifies that at least 90 days have elapsed since the donor's last whole blood donation.
    """
    if not last_donation_date_str:
        return True
    try:
        dt = datetime.strptime(str(last_donation_date_str).strip(), "%Y-%m-%d")
        return (datetime.now() - dt).days >= 90
    except Exception:
        return True


def rank_and_format_donors(
    donor_records: List[Dict[str, Any]],
    request: BloodMatchRequest
) -> BloodMatchResponse:
    """
    Applies compatibility filtering, availability status checks,
    and hierarchical location ranking (City + Area > City > Other).
    Supports both old CSV columns and new Excel columns.
    """
    req_group = request.recipient_blood_group.strip().upper()
    target_city = request.city.strip().lower()
    target_area = (request.area or "").strip().lower()
    compatible_groups = get_compatible_donor_groups(req_group)

    matched_list: List[MatchedDonor] = []

    for d in donor_records:
        # Handle both old and new column names
        d_group = str(d.get("blood_group", d.get("Blood Group", ""))).strip().upper()
        if d_group not in compatible_groups:
            continue

        raw_availability = str(
            d.get("availability_status", d.get("Available for Emergency", "Available"))
        ).strip().lower()
        availability = "Available" if raw_availability in {"available", "yes", "true", "1"} else "Unavailable"
        if request.only_available and availability != "Available":
            continue

        d_city = str(d.get("city", d.get("City", ""))).strip()
        d_area = str(d.get("area", d.get("Area/Neighborhood", ""))).strip()
        d_address = str(d.get("full_address", d.get("Address", ""))).strip()
        last_date = str(d.get("last_donation_date", d.get("Last Donation Date", ""))).strip() or None
        eligible = is_eligible_to_donate(last_date)

        # Proximity ranking
        if target_city == d_city.lower():
            if target_area and (target_area in d_area.lower() or target_area in d_address.lower()):
                rank = 1  # Exact city and area
            else:
                rank = 2  # Same city
        else:
            rank = 3  # Other city

        norm_phone = normalize_pakistan_phone(str(d.get("contact_number", d.get("Phone Number", ""))))
        masked = mask_phone_number(norm_phone)
        wa_link = generate_emergency_whatsapp_link(norm_phone, req_group, request.city)
        reason = get_compatibility_description(d_group, req_group)

        matched_donor = MatchedDonor(
            donor_code=str(d.get("donor_code", d.get("Donor ID", "DON-0000"))),
            full_name=str(d.get("full_name", d.get("Full Name", "Anonymous Donor"))),
            blood_group=d_group,
            compatibility_reason=reason,
            city=d_city,
            area=d_area or "General City Area",
            full_address=d_address,
            masked_contact=masked,
            raw_contact=norm_phone,
            whatsapp_link=wa_link,
            availability_status=availability,
            last_donation_date=last_date,
            eligible_now=eligible,
            distance_rank=rank
        )
        matched_list.append(matched_donor)

    # Sort: rank 1 first, then eligible donors first, then by donor name
    matched_list.sort(key=lambda x: (x.distance_rank, not x.eligible_now, x.full_name))

    return BloodMatchResponse(
        recipient_group=req_group,
        compatible_donor_groups=compatible_groups,
        total_matches=len(matched_list),
        donors=matched_list
    )
