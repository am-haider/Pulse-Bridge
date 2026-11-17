import pandas as pd
import pytest

from backend.models.schemas import BloodMatchRequest, DonorRegistrationRequest
from backend.modules.donors import service as donor_service_module
from backend.modules.donors.compatibility import get_compatible_donor_groups, is_compatible
from backend.modules.donors.service import BloodDonorService


def test_compatibility_rules():
    # O- is universal donor
    assert is_compatible("O-", "A+")
    assert is_compatible("O-", "B+")
    assert is_compatible("O-", "AB+")
    assert is_compatible("O-", "O-")

    # AB+ is universal recipient
    assert set(get_compatible_donor_groups("AB+")) == {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}

    # B+ recipient can only receive B+, B-, O+, O-
    assert set(get_compatible_donor_groups("B+")) == {"B+", "B-", "O+", "O-"}
    assert not is_compatible("A+", "B+")
    assert not is_compatible("AB+", "B+")


def test_donor_search_and_privacy_masking(tmp_path, monkeypatch):
    registry_path = tmp_path / "donor_registry.xlsx"
    pd.DataFrame([{
        "Donor ID": "DON-TEST",
        "Full Name": "Test Donor",
        "Blood Group": "A+",
        "City": "Lahore",
        "Area/Neighborhood": "Gulberg",
        "Phone Number": "03000000000",
        "Last Donation Date": "2024-01-01",
        "Available for Emergency": "Yes",
        "Status": "Active",
    }]).to_excel(registry_path, index=False)
    monkeypatch.setattr(donor_service_module, "DONOR_REGISTRY_XLSX_PATH", registry_path)

    req = BloodMatchRequest(recipient_blood_group="A+", city="Lahore", urgency="Emergency")
    res = BloodDonorService.match_donors(req)
    assert res.total_matches > 0
    for donor in res.donors:
        # Check donor blood group is safe
        assert donor.blood_group in ["A+", "A-", "O+", "O-"]
        # Check contact masking format
        assert "•••••" in donor.masked_contact or "•••" in donor.masked_contact
        # Check WhatsApp link is generated
        assert donor.whatsapp_link.startswith("https://wa.me/")


def test_donor_registration_creates_local_registry_backup(tmp_path, monkeypatch):
    xlsx_path = tmp_path / "donor_registrations.xlsx"
    monkeypatch.setattr(donor_service_module, "DONOR_REGISTRY_XLSX_PATH", xlsx_path)

    data = DonorRegistrationRequest(
        full_name="Ali Khan",
        age=30,
        gender="Male",
        blood_group="O-",
        city="Lahore",
        area="Gulberg",
        address="12 Main Street",
        contact_number="923001234567",
        availability="Available",
    )

    saved = BloodDonorService.register_donor(data)

    assert saved["Full Name"] == "Ali Khan"
    assert xlsx_path.exists()

    xlsx_df = pd.read_excel(xlsx_path)
    assert xlsx_df.iloc[-1]["Full Name"] == "Ali Khan"
    assert xlsx_df.iloc[-1]["Blood Group"] == "O-"
