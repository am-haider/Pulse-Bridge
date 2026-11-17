import asyncio

from google import genai
from google.genai import types

from backend.core.config import settings


async def call_gemini_chat(user_message: str) -> str:
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set in the environment")

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=15_000),
    )
    prompt = (
        "You are Pulse Bridge's health information assistant. Provide accurate, "
        "relevant, and well-structured health information. Follow these guidelines:\n\n"
        "1. **Format**: Use bullet points (•) or numbered lists for multi-part answers. "
        "Use bold for key terms. Keep paragraphs short.\n"
        "2. **Tone**: Professional, empathetic, and clear. No jargon without explanation.\n"
        "3. **Scope**: General health information only. Never diagnose, prescribe, or "
        "replace a doctor's advice. Always include a disclaimer to consult a qualified "
        "healthcare professional for personal medical decisions.\n"
        "4. **Relevance**: Answer the specific question asked. Don't give generic "
        "advice unless requested.\n"
        "5. **Follow-up**: End every response with a helpful follow-up question like:\n"
        "   • \"How can I assist you further?\"\n"
        "   • \"Do you have any more questions about this topic?\"\n"
        "   • \"Would you like me to explain anything in more detail?\"\n\n"
        f"User message: {user_message}"
    )
    response = await asyncio.wait_for(
        asyncio.to_thread(
            client.models.generate_content,
            model=settings.GEMINI_CHAT_MODEL,
            contents=prompt,
        ),
        timeout=20,
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty chat response")
    return response.text
