"""
Blood Donor Service using Excel file for registry.
No Supabase required - works entirely from local Excel file.
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

from backend.models.schemas import (
    BloodMatchRequest,
    BloodMatchResponse,
    DonorRegistrationRequest,
    BloodRequestCreate,
    BloodRequestResponse,
)
from backend.modules.donors.matcher import rank_and_format_donors, normalize_pakistan_phone

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
DONOR_REGISTRY_XLSX_PATH = DATA_DIR / "blood_donors.xlsx"
SEED_CSV_PATH = DATA_DIR / "blood_donors.csv"

DONOR_REGISTRY_COLUMNS = [
    "Donor ID",
    "Full Name",
    "Blood Group",
    "City",
    "Area/Neighborhood",
    "Phone Number",
    "Email",
    "Last Donation Date",
    "Available for Emergency",
    "Medical Conditions",
    "Weight (kg)",
    "Age",
    "Gender",
    "Registration Date",
    "Status",
    "Notes"
]


def load_donors_from_excel() -> List[Dict[str, Any]]:
    """Load donors from the Excel registry."""
    if DONOR_REGISTRY_XLSX_PATH.exists():
        try:
            df = pd.read_excel(DONOR_REGISTRY_XLSX_PATH, engine='openpyxl')
        except Exception as exc:
            raise RuntimeError("Unable to load the Excel donor registry") from exc

        if not df.empty:
            for col in DONOR_REGISTRY_COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            active = df["Status"].fillna("").astype(str).str.strip().str.casefold() == "active"
            return df.loc[active].to_dict(orient="records")

    if not SEED_CSV_PATH.exists():
        return []

    df = pd.read_csv(SEED_CSV_PATH)
    donors = []
    for _, row in df.iterrows():
        address = str(row.get("Address", "") or "")
        address_parts = [part.strip() for part in address.split(",")]
        donors.append({
            "Donor ID": str(row["Donor_ID"]),
            "Full Name": str(row["Full_Name"]),
            "Blood Group": str(row["Blood_Group"]),
            "City": str(row["City"]),
            "Area/Neighborhood": address_parts[2] if len(address_parts) > 2 else "Central",
            "Phone Number": str(row["Contact_Number"]),
            "Email": "",
            "Last Donation Date": str(row["Last_Donation_Date"]),
            "Available for Emergency": str(row["Availability"]),
            "Medical Conditions": "None",
            "Weight (kg)": 70,
            "Age": int(row["Age"]),
            "Gender": str(row["Gender"]),
            "Registration Date": datetime.now().strftime("%Y-%m-%d"),
            "Status": "Active",
            "Notes": ""
        })
    return donors


def save_donors_to_excel(donors: List[Dict[str, Any]]) -> None:
    """Save donors to the Excel registry."""
    df = pd.DataFrame(donors)
    # Ensure column order
    for col in DONOR_REGISTRY_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[DONOR_REGISTRY_COLUMNS]
    df.to_excel(DONOR_REGISTRY_XLSX_PATH, index=False, engine='openpyxl')


class BloodDonorService:
    @staticmethod
    def match_donors(request: BloodMatchRequest) -> BloodMatchResponse:
        """
        Retrieves donors from Excel registry.
        Applies blood compatibility rules and proximity hierarchy.
        """
        records = load_donors_from_excel()

        if not records:
            return BloodMatchResponse(
                request_code=request.request_code or f"REQ-{uuid.uuid4().hex[:6].upper()}",
                blood_group_needed=request.blood_group_needed.upper(),
                city=request.city.title(),
                total_matches=0,
                matches=[],
                message="No donors registered yet."
            )

        return rank_and_format_donors(records, request)

    @staticmethod
    def register_donor(data: DonorRegistrationRequest, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Registers a new voluntary donor in the Excel registry.
        """
        normalized_phone = normalize_pakistan_phone(data.contact_number)
        donor_code = f"DON-{uuid.uuid4().hex[:6].upper()}"

        record = {
            "Donor ID": donor_code,
            "Full Name": data.full_name,
            "Blood Group": data.blood_group.upper(),
            "City": data.city.title(),
            "Area/Neighborhood": data.area or "General City Area",
            "Phone Number": normalized_phone,
            "Email": data.email or "",
            "Last Donation Date": data.last_donation_date or "",
            "Available for Emergency": data.availability,
            "Medical Conditions": data.medical_conditions or "None",
            "Weight (kg)": data.weight_kg or 70,
            "Age": data.age,
            "Gender": data.gender,
            "Registration Date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "Status": "Active",
            "Notes": data.notes or ""
        }

        donors = load_donors_from_excel()
        donors.append(record)
        save_donors_to_excel(donors)

        return record

    @staticmethod
    def create_blood_request(data: BloodRequestCreate, requester_id: Optional[str] = None) -> BloodRequestResponse:
        """
        Broadcasts an emergency blood request.
        """
        req_id = str(uuid.uuid4())
        req_code = f"REQ-{uuid.uuid4().hex[:6].upper()}"

        record = BloodRequestResponse(
            id=req_id,
            request_code=req_code,
            patient_name=data.patient_name,
            blood_group_needed=data.blood_group_needed.upper(),
            units_required=data.units_required,
            city=data.city.title(),
            hospital_name=data.hospital_name,
            urgency_level=data.urgency_level,
            contact_person=data.contact_person,
            contact_phone=normalize_pakistan_phone(data.contact_phone),
            request_status="Open",
            requester_id=requester_id,
            created_at=datetime.now(timezone.utc).isoformat()
        )

        # In a real app, you'd save this to a requests Excel file too
        return record

    @staticmethod
    def list_blood_requests(limit: int = 20) -> List[BloodRequestResponse]:
        """
        Lists all open emergency blood requests.
        For now returns empty list - would need a requests Excel file.
        """
        return []


# Backward compatibility
def load_seed_donors_from_csv() -> List[Dict[str, Any]]:
    """Legacy function for backward compatibility."""
    return load_donors_from_excel()