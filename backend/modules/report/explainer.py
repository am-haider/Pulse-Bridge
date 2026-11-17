import uuid
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types
from backend.core.config import settings
from backend.core.guardrails import validate_and_sanitize_medical_text, MANDATORY_DISCLAIMER_EN, MANDATORY_DISCLAIMER_UR
from backend.core.supabase_client import get_supabase_client
from backend.models.schemas import ReportExplanationResponse, BiomarkerItem
from backend.modules.report.parser import inspect_report_file
from backend.modules.report.extractor import extract_biomarkers_with_gemini, fallback_rule_based_extractor


EXPLANATION_PROMPT_TEMPLATE = """
You are Pulse Bridge's premium medical health literacy AI — the "VIP Concierge" for understanding lab reports.
Target Language: {language}

Here is the extracted patient biomarker data:
{biomarkers_summary}

YOUR PREMIUM CLINICAL LITERACY RESPONSIBILITIES:
1. **Structure**: Use CLEAR bullet points (•) and numbered lists. Bold key terms. Short paragraphs. Scannable format.
2. **Tone**: VIP concierge — professional, empathetic, clear. No jargon without plain-language explanation.
3. **For each abnormal marker**: Explain what it means in everyday terms, potential implications, and context.
4. **Language**: If 'ur', provide fluent, culturally respectful Urdu (Nastaliq-appropriate) for Pakistani patients.
5. **Questions for Doctor**: 3 specific, educated questions the patient should ask their physician.
6. **Wellness Considerations**: 2 general dietary/lifestyle tips (non-prescriptive, e.g., "iron-rich foods like spinach").
7. **SAFETY GUARDRAIL**: NEVER diagnose, NEVER prescribe. Always advise consulting a licensed physician.

FORMAT YOUR RESPONSE AS JSON:
{{
  "abnormal_findings_summary": "Concise bullet-point summary of out-of-range markers with plain-language meaning",
  "overall_health_insight": "Empathetic VIP overview of the patient's test panel — what it means holistically",
  "suggested_questions_for_doctor": [
    "Specific question 1 for the attending physician",
    "Specific question 2 for the attending physician",
    "Specific question 3 for the attending physician"
  ],
  "dietary_lifestyle_considerations": [
    "Practical, non-prescriptive wellness tip 1",
    "Practical, non-prescriptive wellness tip 2"
  ],
  "key_takeaways": [
    "VIP takeaway 1 — most important actionable insight",
    "VIP takeaway 2 — second most important insight",
    "VIP takeaway 3 — reassurance or next step guidance"
  ]
}}
"""


class ReportExplainerService:
    @staticmethod
    def process_and_explain(
        file_bytes: bytes,
        filename: str,
        language: str = "en",
        user_id: Optional[str] = None
    ) -> ReportExplanationResponse:
        """
        End-to-end report pipeline:
        1. Parse file bytes (PDF text / image)
        2. Extract structured biomarkers
        3. Generate patient-friendly explanation in EN or UR
        4. Pass through clinical safety guardrails
        5. Persist record to Supabase
        """
        extracted_text, mime_type = inspect_report_file(file_bytes, filename)

        # 1. Structured Biomarker Extraction
        extracted_data: Dict[str, Any] = {}
        if settings.GEMINI_API_KEY:
            try:
                extracted_data = extract_biomarkers_with_gemini(
                    text_content=extracted_text,
                    image_bytes=file_bytes if mime_type and mime_type.startswith("image/") else None,
                    mime_type=mime_type
                )
            except Exception as e:
                print(f"[ReportExplainer] Gemini extraction notice: {e}. Utilizing fallback parser.")
                extracted_data = fallback_rule_based_extractor(extracted_text or filename)
        else:
            extracted_data = fallback_rule_based_extractor(extracted_text or filename)

        biomarkers = [BiomarkerItem(**b) for b in extracted_data.get("biomarkers", [])]
        report_title = extracted_data.get("report_title", "Medical Diagnostic Report")
        category = extracted_data.get("detected_category", "Clinical Laboratory")

        # 2. Generate Bilingual Explanation
        abnormal_items = [b for b in biomarkers if b.status in ("LOW", "ELEVATED")]
        biomarkers_summary = "\n".join([
            f"- {b.name}: {b.observed_value} (Normal: {b.reference_range}) -> Status: {b.status}"
            for b in biomarkers
        ])

        if settings.GEMINI_API_KEY:
            try:
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                prompt = EXPLANATION_PROMPT_TEMPLATE.format(
                    language="Urdu (اردو)" if language == "ur" else "English",
                    biomarkers_summary=biomarkers_summary
                )
                res = client.models.generate_content(
                    model=settings.GEMINI_CHAT_MODEL,
                    contents=prompt
                )
                raw_json = res.text.strip()
                if "```json" in raw_json:
                    raw_json = raw_json.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_json:
                    raw_json = raw_json.split("```")[1].split("```")[0].strip()
                import json
                explanation_data = json.loads(raw_json)
            except Exception as e:
                print(f"[ReportExplainer] Gemini explanation notice: {e}")
                explanation_data = ReportExplainerService._generate_rule_based_explanation(abnormal_items, language)
        else:
            explanation_data = ReportExplainerService._generate_rule_based_explanation(abnormal_items, language)

        abnormal_summary = explanation_data.get("abnormal_findings_summary", "")
        health_insight = explanation_data.get("overall_health_insight", "")
        questions = explanation_data.get("suggested_questions_for_doctor", [])
        lifestyle = explanation_data.get("dietary_lifestyle_considerations", [])
        key_takeaways = explanation_data.get("key_takeaways", [])

        # 3. Clinical Safety Guardrail Pass
        sanitized_summary, _ = validate_and_sanitize_medical_text(abnormal_summary, language)
        sanitized_insight, _ = validate_and_sanitize_medical_text(health_insight, language)
        disclaimer = MANDATORY_DISCLAIMER_UR if language == "ur" else MANDATORY_DISCLAIMER_EN

        report_id = str(uuid.uuid4())

        # 4. Optional Supabase Persistence
        try:
            supabase = get_supabase_client()
            supabase.table("report_records").insert({
                "id": report_id,
                "user_id": user_id,
                "report_title": report_title,
                "detected_category": category,
                "language": language,
                "biomarkers": [b.model_dump() for b in biomarkers],
                "abnormal_findings": sanitized_summary,
                "health_insight": sanitized_insight,
                "questions_for_doctor": questions,
                "disclaimer_acknowledged": True
            }).execute()
        except Exception:
            pass

        return ReportExplanationResponse(
            id=report_id,
            report_title=report_title,
            detected_category=category,
            language=language,
            biomarkers=biomarkers,
            abnormal_findings_summary=sanitized_summary,
            overall_health_insight=sanitized_insight,
            suggested_questions_for_doctor=questions,
            dietary_lifestyle_considerations=lifestyle,
            key_takeaways=key_takeaways,
            mandatory_disclaimer=disclaimer
        )

    @staticmethod
    def _generate_rule_based_explanation(abnormal_items: List[BiomarkerItem], language: str) -> Dict[str, Any]:
        if language == "ur":
            if not abnormal_items:
                return {
                    "abnormal_findings_summary": "• تمام بنیادی ٹیسٹ عام حد میں ہیں — کوئی غیر معمولی Resultado نہیں۔",
                    "overall_health_insight": "آپ کے لیب کے نتائج مستحکم ہیں۔ روتین چیک اپ جاری رکھیں۔",
                    "suggested_questions_for_doctor": [
                        "کیا مجھے سالانہ کوئی مخصوص ویلمس مارکر چیک کرانے چاہئیں؟",
                        "کیا میری موجودہ نتائج میری لائف سٹائل کے لیے درست ہیں؟"
                    ],
                    "dietary_lifestyle_considerations": [
                        "متوازن خوراک اور پانی کا مناسب استعمال رکھیں",
                        "روزنہ ہلکی ورزش کو اپن روتین کا حصہ بنائیں"
                    ],
                    "key_takeaways": [
                        "✅ سب ٹیسٹ معمول کے دائرے میں — فکر کی بات نہیں",
                        "📅 باقاعدہ سالانہ چیک اپ جاری رکھیں",
                        "💧 پانی پینے اور صحت مند کھانے پر توجہ دیں"
                    ]
                }
            items_str = "، ".join([f"{b.name} ({b.observed_value})" for b in abnormal_items])
            return {
                "abnormal_findings_summary": f"• **{items_str}** میں تبدیلی دیکھی گئی — یہ اکثر غذائی یا عارضی عوامل کی وجہ سے ہوتی ہے۔",
                "overall_health_insight": "کچھ مارکرز معمول کی حد سے باہر ہیں۔ براہ کرم اپنے معالج سے مشورہ کریں۔",
                "suggested_questions_for_doctor": [
                    "کیا ان نتائج کے لیے مزید ٹیسٹ درکار ہیں؟",
                    "کیا غذائی یا لائف سٹائل میں تبدیلی تجویز کی جاتی ہے؟",
                    "کیا ۴ تا ۸ ہفتے بعد دوہرا ٹیسٹ چاہیے؟"
                ],
                "dietary_lifestyle_considerations": [
                    "ڈاکٹر کی مشورہ کے بغیر کوئی دواء نہ لیں",
                    "قدرتی خوراک اور مناسب نیند کا خیال رکھیں"
                ],
                "key_takeaways": [
                    "⚠️ کچھ مارکرز توجہ طلب ہیں — ڈاکٹر سے ملیں",
                    "🥗 غذائی اصلاح اکثر مسائل کو حل کر سکتی ہے",
                    "📋 اپنی رپورٹ ڈاکٹر کو دکھائیں، خود تشخیص نہ لگاۓ"
                ]
            }

        # English
        if not abnormal_items:
            return {
                "abnormal_findings_summary": "• All parameters are within normal reference ranges — no abnormalities detected.",
                "overall_health_insight": "Your laboratory markers demonstrate healthy baseline stability. Continue routine preventative health checkups.",
                "suggested_questions_for_doctor": [
                    "Are there any specific wellness markers we should recheck annually?",
                    "Do my current results support my current lifestyle and exercise regimen?"
                ],
                "dietary_lifestyle_considerations": [
                    "Maintain balanced hydration and whole-food nutrition",
                    "Incorporate regular moderate cardiovascular activity"
                ],
                "key_takeaways": [
                    "✅ All tests normal — no immediate concerns",
                    "📅 Continue annual preventative checkups",
                    "💧 Stay hydrated and maintain balanced nutrition"
                ]
            }

        items_str = ", ".join([f"{b.name} ({b.observed_value} vs {b.reference_range})" for b in abnormal_items])
        return {
            "abnormal_findings_summary": f"• **{items_str}** — Notable variations observed. These changes often correlate with dietary factors, temporary strain, or nutritional needs.",
            "overall_health_insight": "Several markers deviate from standard reference thresholds and warrant clinical review with your primary care physician.",
            "suggested_questions_for_doctor": [
                "Could these out-of-range values indicate an underlying dietary or metabolic factor?",
                "Would you recommend any follow-up blood panels in the next 4 to 8 weeks?",
                "Are there specific lifestyle or nutritional adjustments indicated by these markers?"
            ],
            "dietary_lifestyle_considerations": [
                "Avoid self-prescribing over-the-counter supplements prior to clinical review",
                "Maintain a consistent sleep schedule and hydration"
            ],
            "key_takeaways": [
                "⚠️ Some markers need attention — consult your doctor",
                "🥗 Dietary changes often help normalize values",
                "📋 Share this report with your physician — don't self-diagnose"
            ]
        }
