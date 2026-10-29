
import os
import time
import logging

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

load_dotenv()

logger = logging.getLogger(__name__)


class GeminiChatError(RuntimeError):
    """A Gemini failure that can be returned safely to the chat client."""

    def __init__(self, message, status_code=503):
        super().__init__(message)
        self.status_code = status_code


def _public_api_error(error):
    """Translate a Gemini API error into a safe user-facing message."""
    code = getattr(error, "code", None)
    status = getattr(error, "status", None)

    if code in (401, 403) or status == "PERMISSION_DENIED":
        return GeminiChatError(
            "Gemini could not authenticate this request. Check the API key "
            "and Google Cloud project configuration.",
            503,
        )

    if code == 429 or status == "RESOURCE_EXHAUSTED":
        return GeminiChatError(
            "Gemini's request limit has been reached. Wait a little and try "
            "again, or switch to Offline mode.",
            503,
        )

    if code == 503 or status == "UNAVAILABLE":
        return GeminiChatError(
            "Gemini is temporarily unavailable. Please try again shortly, "
            "or switch to Offline mode.",
            503,
        )

    if code == 504 or status == "DEADLINE_EXCEEDED":
        return GeminiChatError(
            "Gemini took too long to respond. Please try again.",
            504,
        )

    if code == 404 or status == "NOT_FOUND":
        return GeminiChatError(
            "None of the configured Gemini models is available. Check the "
            "model names in the server configuration.",
            503,
        )

    return GeminiChatError(
        "Gemini could not complete the request. Please try again shortly.",
        502,
    )


# =========================================================
# GEMINI CLIENT
# =========================================================

API_KEY = os.getenv("GOOGLE_API_KEY")

client = None

if API_KEY:
    try:
        client = genai.Client(
            api_key=API_KEY,
            http_options=types.HttpOptions(
                timeout=12000,
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        )
    except Exception:
        logger.exception("Could not initialize Gemini client")


# Keep all four configured fallback models.
MODELS_TO_TRY = [
    "gemini-2.5-flash-lite",
     "gemini-2.5-flash",
     "gemini-3.5-flash-lite",
     "gemini-3.5-flash",
     "gemini-3.7-flash",
     "gemini-3.8-flash",
]


# =========================================================
# RESPONSE AND CONTEXT LIMITS
# =========================================================

MAX_RESUME_CHARS = 3000
MAX_JOB_CHARS = 1800
MAX_HISTORY_MESSAGES = 4
MAX_HISTORY_CHARS = 1000

# Increased from 220 to allow more complete answers.
MAX_OUTPUT_TOKENS = 1000


def _short_list(items, limit=8):
    """Format a short list without excessive prompt context."""
    return ", ".join(
        str(item) for item in (items or [])[:limit]
    ) or "None"


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
        raise GeminiChatError(
            "Gemini is not configured. Add a valid GOOGLE_API_KEY, or switch "
            "to Offline mode.",
            503,
        )

    matched_skills = matched_skills or []
    missing_skills = missing_skills or []
    strengths = strengths or []
    suggestions = suggestions or []
    chat_history = chat_history or []

    resume_context = (resume_text or "")[:MAX_RESUME_CHARS]
    job_context = (job_description or "")[:MAX_JOB_CHARS]

    history_lines = []

    for item in chat_history[-MAX_HISTORY_MESSAGES:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content", "")

        if role not in ("user", "assistant"):
            continue

        if not isinstance(content, str):
            continue

        content = content.strip()[:MAX_HISTORY_CHARS]

        if content:
            label = "User" if role == "user" else "ResumeIQ"
            history_lines.append(f"{label}: {content}")

    history_text = (
        "\n".join(history_lines)
        or "No previous conversation."
    )

    prompt = f"""
You are ResumeIQ, an AI resume and career assistant.

RESPONSE RULES:
- Answer the user's exact question first.
- Use clear, natural English.
- For a normal question, provide a complete answer in 3-5 bullet points.
- Explain technical terms briefly when helpful.
- Use the supplied analysis and resume details when relevant.
- Give practical, specific suggestions based on the available information.
- Never invent skills, qualifications, projects, or achievements.
- Do not simply repeat the analysis figures without explaining them.
- An ATS-style score does not guarantee passing a real ATS.
- Finish every answer with a complete sentence.
- Do not stop mid-sentence or mid-word.
- If the user asks for a language other than English, explain that English
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

Give a direct, complete, useful answer. Do not repeat all the supplied
context. Use only as much detail as needed to answer the question.
""".strip()

    start_time = time.perf_counter()
    last_api_error = None
    saw_empty_response = False

    for model_name in MODELS_TO_TRY:
        try:
            logger.info("Trying Gemini model: %s", model_name)

            generation_config = types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                thinking_config=types.ThinkingConfig(
                    thinking_level="low"
                ),
            )

            chat = client.chats.create(model=model_name)

            response = chat.send_message(
                prompt,
                config=generation_config,
            )

            answer = getattr(response, "text", None)

            # Inspect the finish reason to help diagnose incomplete answers.
            candidates = getattr(response, "candidates", None) or []
            finish_reason = None

            if candidates:
                finish_reason = getattr(
                    candidates[0],
                    "finish_reason",
                    None,
                )

            logger.info(
                "Gemini model %s finish reason: %s",
                model_name,
                finish_reason,
            )

            if answer and answer.strip():
                answer = answer.strip()

                finish_reason_text = str(finish_reason).upper()

                if "MAX_TOKENS" in finish_reason_text:
                    logger.warning(
                        "Model %s reached the output token limit.",
                        model_name,
                    )
                    saw_empty_response = True
                    continue

                logger.info(
                    "Gemini response generated using %s in %.2f seconds",
                    model_name,
                    time.perf_counter() - start_time,
                )

                return answer


            logger.warning(
                "Model %s returned an empty response; trying next model",
                model_name,
            )

            saw_empty_response = True

        except genai_errors.APIError as error:
            logger.warning(
                "Gemini model %s failed with API status %s (%s)",
                model_name,
                error.code,
                error.status,
            )

            last_api_error = error

            if (
                error.code in (401, 403)
                or error.status == "PERMISSION_DENIED"
            ):
                raise _public_api_error(error) from error

            # Try the next model for model-specific or temporary failures.
            if (
                error.code == 404
                or error.status == "NOT_FOUND"
                or error.code == 429
                or error.status == "RESOURCE_EXHAUSTED"
                or error.code in (500, 503, 504)
                or error.status in (
                    "INTERNAL",
                    "UNAVAILABLE",
                    "DEADLINE_EXCEEDED",
                )
            ):
                continue

            raise _public_api_error(error) from error

        except httpx.TimeoutException as error:
            logger.warning(
                "Gemini model %s timed out: %s",
                model_name,
                type(error).__name__,
            )
            last_api_error = error

        except (httpx.TransportError, ConnectionError) as error:
            logger.warning(
                "Gemini model %s could not be reached: %s",
                model_name,
                type(error).__name__,
            )
            last_api_error = error

        except Exception as error:
            logger.exception(
                "Unexpected error while requesting Gemini model %s",
                model_name,
            )
            raise GeminiChatError(
                "ResumeIQ encountered an unexpected error while contacting "
                "Gemini. Please try again.",
                502,
            ) from error

    logger.error(
        "All Gemini models failed after %.2f seconds",
        time.perf_counter() - start_time,
    )

    if isinstance(last_api_error, genai_errors.APIError):
        raise _public_api_error(last_api_error) from last_api_error

    if isinstance(last_api_error, httpx.TimeoutException):
        raise GeminiChatError(
            "Gemini took too long to respond. Please try again.",
            504,
        ) from last_api_error

    if isinstance(last_api_error, (httpx.TransportError, ConnectionError)):
        raise GeminiChatError(
            "ResumeIQ could not connect to Gemini. Check your network "
            "connection and try again.",
            503,
        ) from last_api_error

    if saw_empty_response:
        raise GeminiChatError(
            "Gemini returned an empty response. Please try again.",
            502,
        )

    raise GeminiChatError(
        "ResumeIQ could not connect to Gemini. Check your network connection "
        "and try again.",
        503,
    )
