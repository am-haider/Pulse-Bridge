import httpx

from backend.core.config import settings


SYSTEM_PROMPT = (
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
    "   • \"Would you like me to explain anything in more detail?\"\n"
)


async def call_openrouter_chat(user_message: str) -> str:
    """Send a chat request to OpenRouter API."""
    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set in the environment")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://pulsebridge.healthcare",
        "X-Title": "Pulse Bridge Healthcare",
    }
    # Use a reliable free/cheap model
    models_to_try = [
        settings.OPENROUTER_CHAT_MODEL,
        "meta-llama/llama-3.1-8b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "google/gemma-2-9b-it:free",
        "meta-llama/llama-3.1-70b-instruct",
        "mistralai/mixtral-8x7b-instruct",
    ]

    for model in models_to_try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.95,
        }
        timeout = httpx.Timeout(connect=3.0, read=15.0, write=5.0, pool=3.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                if resp.status_code in (404, 401, 402, 429):
                    continue  # Try next model
                resp.raise_for_status()
                data = resp.json()
                reply = data["choices"][0]["message"]["content"]
                if isinstance(reply, str) and reply.strip():
                    return reply.strip()
        except Exception:
            continue  # Try next model

    raise RuntimeError("All OpenRouter models unavailable")