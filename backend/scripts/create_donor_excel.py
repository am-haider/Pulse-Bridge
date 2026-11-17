#!/usr/bin/env python
"""
Create an Excel file for blood donor registration.
Run this once to create the donor registry file.
"""
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
EXCEL_PATH = DATA_DIR / "blood_donors.xlsx"


def create_donor_excel():
    """Create the donor registry Excel file with proper columns."""
    columns = [
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
        "Status",  # Active, Inactive, Deferred
        "Notes"
    ]

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if EXCEL_PATH.exists():
        raise FileExistsError(f"Refusing to overwrite existing donor registry: {EXCEL_PATH}")

    df = pd.DataFrame(columns=columns)

    df.to_excel(EXCEL_PATH, index=False, engine='openpyxl')
    print(f"[OK] Created empty donor registry at {EXCEL_PATH}")


if __name__ == "__main__":
    create_donor_excel()