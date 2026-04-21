import re
from typing import Literal

from ..core.config import get_settings


def _strip_html(value: str) -> str:
    if not value:
        return ""
    no_tags = re.sub(r"<[^>]+>", " ", value)
    normalized = re.sub(r"\s+", " ", no_tags).strip()
    return normalized


def _load_genai():
    try:
        from google import genai
        from google.genai import types
    except Exception as exc:
        raise ValueError("google-genai package is not installed") from exc
    return genai, types


def _build_client():
    genai, _ = _load_genai()
    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured")
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def generate_draft_from_prompt(
    *,
    prompt: str,
    to: list[str],
    cc: list[str],
    subject: str | None,
) -> str:
    settings = get_settings()
    _, types = _load_genai()
    client = _build_client()

    recipient_context = ", ".join(to) if to else "unspecified recipients"
    cc_context = ", ".join(cc) if cc else "none"
    subject_context = subject or "(no subject yet)"

    system_instruction = (
        "You are an email writing assistant. Generate only an email body in HTML that is ready "
        "for a rich-text editor. Write a substantial, polished draft by default (roughly 180-260 words) "
        "unless the user explicitly asks for a short version. Keep it professional and actionable. "
        "Do not include markdown fences, explanations, or placeholder labels."
    )
    user_prompt = (
        f"User request: {prompt}\n"
        f"To: {recipient_context}\n"
        f"Cc: {cc_context}\n"
        f"Subject: {subject_context}\n"
        "Write a complete email with a strong opening, relevant supporting details, and a clear call-to-action. "
        "Output the final email body only."
    )

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.4,
            max_output_tokens=1400,
        ),
    )
    return (response.text or "").strip()


def generate_reply_suggestion(
    *,
    style: Literal["short", "medium", "formal"],
    subject: str | None,
    from_address: str | None,
    body: str | None,
) -> str:
    settings = get_settings()
    _, types = _load_genai()
    client = _build_client()

    style_map = {
        "short": "Write a concise response in 3-5 sentences.",
        "medium": "Write a balanced response in 1-2 short paragraphs.",
        "formal": "Write a polished formal response with a professional tone.",
    }
    body_text = _strip_html(body or "")

    system_instruction = (
        "You are an email reply assistant. Return only the reply body in HTML. "
        "Do not include subject lines, explanations, markdown, or surrounding commentary."
    )
    user_prompt = (
        f"Reply style: {style}\n"
        f"Instruction: {style_map[style]}\n"
        f"Original sender: {from_address or 'unknown'}\n"
        f"Original subject: {subject or '(no subject)'}\n"
        f"Original body:\n{body_text[:6000]}\n\n"
        "Write a complete reply email body."
    )

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.5,
            max_output_tokens=900,
        ),
    )
    return (response.text or "").strip()
