
from ollama import chat

MODEL_NAME = "qwen2.5:7b"

# Speed-focused defaults. Actual speed depends on your hardware.
MAX_HISTORY_MESSAGES = 4
MAX_RESPONSE_TOKENS = 180
MAX_RESUME_CHARS = 4000
MAX_JOB_CHARS = 2000


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

    # Limit context to reduce prompt-processing time.
    resume_context = (resume_text or "")[:MAX_RESUME_CHARS]
    job_context = (job_description or "")[:MAX_JOB_CHARS]

    system_prompt = f"""
You are ResumeIQ, a concise and practical resume and career assistant.
Always reply in English only. Never reply in Hindi or Chinese.

Help users improve their resumes for the provided job description.
Use the supplied analysis data when relevant.
Never invent skills, experience, education, projects, or achievements.
An ATS-style score is an estimate, not a guarantee of passing a real ATS.

Keep answers direct, helpful, and easy to understand.
Prefer short paragraphs or up to 4 bullet points.
Answer the exact question first. Avoid repeating the entire resume.
If the user asks for detailed guidance, provide more detail.

RESUME (may be truncated):
{resume_context}

JOB DESCRIPTION (may be truncated):
{job_context}

ANALYSIS:
Resume match: {similarity_score}%
Keyword coverage: {keyword_coverage}%
ATS-style readiness: {ats_score}%
Matched skills: {", ".join(map(str, matched_skills[:30]))}
Missing skills: {", ".join(map(str, missing_skills[:30]))}
Strengths: {", ".join(map(str, strengths[:8]))}
Suggestions: {", ".join(map(str, suggestions[:8]))}
""".strip()

    messages = [{"role": "system", "content": system_prompt}]

    # Keep only recent, valid conversation messages.
    for item in chat_history[-MAX_HISTORY_MESSAGES:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content", "")

        if role not in ("user", "assistant") or not isinstance(content, str):
            continue

        content = content.strip()
        if content:
            messages.append({
                "role": role,
                "content": content[:1500],
            })

    messages.append({
        "role": "user",
        "content": str(user_message)[:2000],
    })

    response = chat(
        model=MODEL_NAME,
        messages=messages,
        stream=False,
        keep_alive="10m",
        options={
            "temperature": 0.3,
            "num_predict": MAX_RESPONSE_TOKENS,
            "num_ctx": 4096,
        },
    )

    # Compatible with Ollama response objects and dictionary-like responses.
    message = response["message"]
    return message["content"].strip()
