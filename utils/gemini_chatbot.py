
import os
import time
import logging

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logger = logging.getLogger(__name__)

# Set GOOGLE_API_KEY in your environment or .env file.
API_KEY = os.getenv("GOOGLE_API_KEY")

client = None

if API_KEY:
    try:
        client = genai.Client(
            api_key=API_KEY,
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(attempts=1)
            ),
        )
    except Exception:
        logger.exception("Could not initialize Gemini client")


# Use one fast model to avoid delays from sequential fallback attempts.
# If this model is unavailable for your API account, choose a supported
# Flash model from Google's AI Studio model list.
PRIMARY_MODEL = "gemini-2.5-flash"

MAX_RESUME_CHARS = 3000
MAX_JOB_CHARS = 1800
MAX_HISTORY_MESSAGES = 4
MAX_HISTORY_CHARS = 1000
MAX_OUTPUT_TOKENS = 220


def _short_list(items, limit=8):
    """Format a short list without sending excessive prompt context."""
    return ", ".join(str(item) for item in (items or [])[:limit]) or "None"


def get_chat_response(
    user_message,
    resume_text="",
    job_description="",
    similarity_score=0,
    keyword_coverage=0,
    matched_skills=None,
    missing_skills=None,
    ats_score=0,
    strengths=None,
    suggestions=None,
    chat_history=None,
):
    """Generate a concise ResumeIQ response using Gemini."""

    if client is None:
        return (
            "ResumeIQ cannot connect to Gemini because the API client "
            "is not configured. Please check GOOGLE_API_KEY."
        )

    matched_skills = matched_skills or []
    missing_skills = missing_skills or []
    strengths = strengths or []
    suggestions = suggestions or []
    chat_history = chat_history or []

    resume_context = (resume_text or "")[:MAX_RESUME_CHARS]
    job_context = (job_description or "")[:MAX_JOB_CHARS]

    # Keep only recent, valid, short messages.
    history_lines = []

    for item in chat_history[-MAX_HISTORY_MESSAGES:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content", "")

        if role not in ("user", "assistant") or not isinstance(content, str):
            continue

        content = content.strip()[:MAX_HISTORY_CHARS]
        if content:
            label = "User" if role == "user" else "ResumeIQ"
            history_lines.append(f"{label}: {content}")

    history_text = "\n".join(history_lines) or "No previous conversation."

    prompt = f"""
You are ResumeIQ, an AI resume and career assistant.

RULES:
- Always answer in clear English.
- Answer the user's exact question first.
- Be concise and practical; usually use 3-5 bullet points.
- Never invent skills, qualifications, projects, or achievements.
- Use the analysis data when relevant.
- An ATS-style score does not guarantee passing a real ATS.
- If asked for a language other than English, explain that English
  is the currently supported response language.

ANALYSIS:
Resume-job similarity: {similarity_score}%
Keyword coverage: {keyword_coverage}%
ATS-style readiness: {ats_score}%
Matched skills: {_short_list(matched_skills, 20)}
Missing skills: {_short_list(missing_skills, 20)}
Strengths: {_short_list(strengths)}
Suggestions: {_short_list(suggestions)}

RESUME EXCERPT:
{resume_context}

JOB DESCRIPTION EXCERPT:
{job_context}

RECENT CONVERSATION:
{history_text}

CURRENT QUESTION:
{str(user_message)[:1500]}

Give a direct, useful answer without repeating all the supplied context.
""".strip()

    start_time = time.perf_counter()

    try:
        response = client.models.generate_content(
            model=PRIMARY_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                thinking_config=types.ThinkingConfig(
                    thinking_level="low"
                ),
            ),
        )

        answer = getattr(response, "text", None)

        if answer and answer.strip():
            logger.info(
                "Gemini response generated in %.2f seconds using %s",
                time.perf_counter() - start_time,
                PRIMARY_MODEL,
            )
            return answer.strip()

        logger.warning("Gemini returned an empty response")

    except Exception:
        logger.exception(
            "Gemini request failed after %.2f seconds",
            time.perf_counter() - start_time,
        )

    # Avoid slow sequential model fallback attempts.
    return (
        "Sorry, ResumeIQ could not get a response from Gemini right now. "
        "Please try again shortly. If this keeps happening, check the "
        "server logs and verify the selected model is available."
    )
