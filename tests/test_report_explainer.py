import pytest
from backend.modules.report.explainer import ReportExplainerService
from backend.core.guardrails import validate_and_sanitize_medical_text, MANDATORY_DISCLAIMER_EN, MANDATORY_DISCLAIMER_UR


def test_guardrails_prevent_unauthorized_diagnoses():
    violating_text = "Based on your test, you have leukemia and must take 500mg amoxicillin."
    sanitized, warnings = validate_and_sanitize_medical_text(violating_text, language="en")
    # Must have caught both diagnostic and prescriptive violations
    assert len(warnings) >= 2
    # The explicit diagnosis must be sanitized
    assert "you have leukemia" not in sanitized.lower()
    # Disclaimer must be attached
    assert MANDATORY_DISCLAIMER_EN in sanitized


def test_report_pipeline_extraction_and_disclaimer():
    sample_text = """
    LABORATORY TEST REPORT
    Hemoglobin: 9.5 g/dL (Reference: 12.0 - 15.5 g/dL)
    WBC Count: 7,200 /uL (Reference: 4,000 - 11,000 /uL)
    """
    res = ReportExplainerService.process_and_explain(
        file_bytes=sample_text.encode("utf-8"),
        filename="cbc_test.txt",
        language="en"
    )
    assert len(res.biomarkers) >= 2
    # Hemoglobin should be flagged as LOW
    hb = next((b for b in res.biomarkers if "hemoglobin" in b.name.lower()), None)
    assert hb is not None
    assert hb.status == "LOW"
    # Mandatory disclaimer must be present
    assert bool(res.mandatory_disclaimer)
    assert MANDATORY_DISCLAIMER_EN in res.mandatory_disclaimer
