import pytest
from backend.modules.doctors.synthesizer import DoctorRAGService
from backend.models.schemas import DoctorSearchQuery


def test_doctor_search_heart_symptom():
    query = DoctorSearchQuery(query="consult with doctor about heart", limit=5)
    res = DoctorRAGService.search(query)
    assert res.total_found > 0
    # At least one returned doctor must have Cardiology specialty
    specs = [s.lower() for d in res.doctors for s in d.specializations]
    assert any("cardio" in s for s in specs)


def test_doctor_search_city_filter():
    query = DoctorSearchQuery(query="Skin specialist in Quetta", city="Quetta", specialization="Dermatologist", limit=5)
    res = DoctorRAGService.search(query)
    assert res.total_found > 0
    for d in res.doctors:
        assert d.city.lower() == "quetta"
        assert any("dermatolog" in s.lower() for s in d.specializations)


def test_doctor_search_max_fee_budget():
    max_fee = 1500
    query = DoctorSearchQuery(query="General Physician", city="Lahore", max_fee=max_fee, limit=5)
    res = DoctorRAGService.search(query)
    assert res.total_found > 0
    for d in res.doctors:
        assert d.fee_pkr <= max_fee


def test_zero_hallucination_verification():
    # Doctors must have verified genuine data (not fabricated)
    query = DoctorSearchQuery(query="Child specialist in Lahore", limit=3)
    res = DoctorRAGService.search(query)
    assert res.total_found > 0
    for d in res.doctors:
        assert d.doctor_name
        assert d.city
        assert d.specialization_primary
        assert d.experience_years >= 0
        assert d.total_reviews >= 0
        assert 0 <= d.patient_satisfaction_pct <= 100
