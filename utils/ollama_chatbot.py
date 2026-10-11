
from ollama import chat

MODEL_NAME = "qwen2.5:3b"

MAX_HISTORY_MESSAGES = 4
MAX_RESUME_CHARS = 2500
MAX_JOB_CHARS = 1200
MAX_RESPONSE_TOKENS = 120


def get_ollama_chat_response(
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
    matched_skills = matched_skills or []
    missing_skills = missing_skills or []
    strengths = strengths or []
    suggestions = suggestions or []
    chat_history = chat_history or []

    # Keep the context small to reduce processing time.
    resume_text = (resume_text or "")[:MAX_RESUME_CHARS]
    job_description = (job_description or "")[:MAX_JOB_CHARS]

    system_prompt = f"""
You are ResumeIQ, a concise AI resume and career assistant.

Rules:
- Reply in English.
- Answer the user's question directly.
- Give short, practical answers.
- Use bullet points when useful.
- For resume advice, use the provided analysis.
- Never invent skills or resume details.
- If information is missing, say so.

Resume:
{resume_text}

Job description:
{job_description}

Similarity score: {similarity_score}
Keyword coverage: {keyword_coverage}
ATS score: {ats_score}
Matched skills: {", ".join(map(str, matched_skills[:12]))}
Missing skills: {", ".join(map(str, missing_skills[:12]))}
Strengths: {"; ".join(map(str, strengths[:4]))}
Suggestions: {"; ".join(map(str, suggestions[:4]))}

Keep responses focused and normally under 100 words.
"""

    messages = [{"role": "system", "content": system_prompt}]

    for item in chat_history[-MAX_HISTORY_MESSAGES:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content", "")

        if role in ("user", "assistant") and content:
            messages.append({
                "role": role,
                "content": str(content)[:800],
            })

    messages.append({
        "role": "user",
        "content": str(user_message)[:1200],
    })

    response = chat(
        model=MODEL_NAME,
        messages=messages,
        stream=False,
        keep_alive="10m",
        options={
            "temperature": 0.2,
            "num_predict": MAX_RESPONSE_TOKENS,
            "num_ctx": 4096,
        },
    )

    return response["message"]["content"].strip()
