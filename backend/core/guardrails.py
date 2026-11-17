import re
from typing import Tuple, List

MANDATORY_DISCLAIMER_EN = (
    "IMPORTANT MEDICAL NOTICE: This analysis is provided for educational and health literacy purposes only. "
    "It does not constitute a medical diagnosis, clinical prognosis, or treatment plan. "
    "Always discuss your laboratory results directly with a qualified, licensed medical professional."
)

MANDATORY_DISCLAIMER_UR = (
    "اہم طبی آگاہی: یہ خلاصہ صرف معلوماتی اور طبی آگاہی کے لیے فراہم کیا گیا ہے۔ "
    "یہ کسی بھی صورت میں حتمی تشخیص یا علاج کی تجویز نہیں ہے۔ "
    "اپنی رپورٹ کے حوالے سے ہمیشہ مستند اور قابل معالج (ڈاکٹر) سے براہ راست رجوع فرمائیں۔"
)

# Prohibited diagnostic assertion patterns
DIAGNOSTIC_PATTERNS = [
    r"\byou\s+have\s+(cancer|leukemia|diabetes|tuberculosis|hepatitis|hiv|aids|cardiac arrest)\b",
    r"\bwe\s+diagnose\s+you\s+with\b",
    r"\bdiagnosis:\s*(confirmed|positive|definite)\b",
    r"\byou\s+are\s+suffering\s+from\s+[a-z\s]+disease\b",
]

# Prohibited prescriptive instruction patterns
PRESCRIPTIVE_PATTERNS = [
    r"\btake\s+\d+\s*(mg|ml|tablets?|capsules?|pills?)\b",
    r"\bprescribe\s+[a-z\s]+\b",
    r"\byou\s+must\s+take\s+[a-z\s]+\b",
    r"\bdosage:\s*\d+\b",
]


def validate_and_sanitize_medical_text(text: str, language: str = "en") -> Tuple[str, List[str]]:
    """
    Deterministic safety guardrail:
    1. Scans generated AI content for unauthorized clinical diagnosis or prescription attempts.
    2. Redacts or softens violating sentences.
    3. Guarantees presence of the mandatory bilingual disclaimer.
    """
    warnings = []
    sanitized_text = text

    # Check and sanitize diagnostic claims
    for pattern in DIAGNOSTIC_PATTERNS:
        matches = re.findall(pattern, sanitized_text, flags=re.IGNORECASE)
        if matches:
            warnings.append(f"Blocked explicit diagnostic statement matching pattern: {pattern}")
            sanitized_text = re.sub(
                pattern,
                "these laboratory findings should be evaluated by a physician for potential conditions",
                sanitized_text,
                flags=re.IGNORECASE
            )

    # Check and sanitize prescriptive assertions
    for pattern in PRESCRIPTIVE_PATTERNS:
        matches = re.findall(pattern, sanitized_text, flags=re.IGNORECASE)
        if matches:
            warnings.append(f"Blocked prescriptive drug/dosage statement matching pattern: {pattern}")
            sanitized_text = re.sub(
                pattern,
                "consult your doctor regarding whether any medication or dosage is indicated",
                sanitized_text,
                flags=re.IGNORECASE
            )

    # Ensure disclaimer attachment
    disclaimer = MANDATORY_DISCLAIMER_UR if language == "ur" else MANDATORY_DISCLAIMER_EN
    if disclaimer not in sanitized_text:
        sanitized_text = f"{sanitized_text.strip()}\n\n---\n**{disclaimer}**"

    return sanitized_text, warnings
