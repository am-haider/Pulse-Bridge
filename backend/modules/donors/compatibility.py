from typing import List, Dict

# Complete Red Blood Cell & Whole Blood Compatibility Matrix
BLOOD_COMPATIBILITY_MAP: Dict[str, List[str]] = {
    "A+": ["A+", "A-", "O+", "O-"],
    "A-": ["A-", "O-"],
    "B+": ["B+", "B-", "O+", "O-"],
    "B-": ["B-", "O-"],
    "AB+": ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"],  # Universal Recipient
    "AB-": ["AB-", "A-", "B-", "O-"],
    "O+": ["O+", "O-"],
    "O-": ["O-"],  # Universal Donor
}


def get_compatible_donor_groups(recipient_blood_group: str) -> List[str]:
    """
    Returns the list of medically compatible donor blood groups for a given recipient.
    """
    clean_group = recipient_blood_group.strip().upper()
    return BLOOD_COMPATIBILITY_MAP.get(clean_group, [clean_group])


def is_compatible(donor_group: str, recipient_group: str) -> bool:
    """
    Returns True if the donor's blood group can be safely transfused to the recipient.
    """
    compatible_list = get_compatible_donor_groups(recipient_group)
    return donor_group.strip().upper() in compatible_list


def get_compatibility_description(donor_group: str, recipient_group: str) -> str:
    """
    Generates human-readable clinical rationale for the match.
    """
    d = donor_group.strip().upper()
    r = recipient_group.strip().upper()

    if d == r:
        return f"Exact identical match ({d})"
    if d == "O-":
        return f"Universal donor (O-) safely compatible with recipient {r}"
    if d == "O+" and "+" in r:
        return f"Rh-compatible group (O+) for Rh-positive recipient {r}"
    if r == "AB+":
        return f"Compatible with universal recipient AB+"
    return f"Compatible donor group ({d}) for recipient ({r})"
