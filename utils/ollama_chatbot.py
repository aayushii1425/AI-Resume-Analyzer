from ollama import chat


MODEL_NAME = "qwen2.5:7b"


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
    chat_history=None
):

    matched_skills = matched_skills or []
    missing_skills = missing_skills or []
    strengths = strengths or []
    suggestions = suggestions or []
    chat_history = chat_history or []


    system_prompt = f"""
You are ResumeIQ, an AI resume and career assistant.

You are running locally using Qwen through Ollama.

==============================
LANGUAGE POLICY
==============================

IMPORTANT:

1. ALWAYS respond in English.
2. NEVER respond in Chinese.
3. NEVER respond in Hindi.
4. NEVER mix multiple languages.
5. Even if the user writes in another language,
   respond only in English.
6. If the user asks you to respond in another
   language, politely explain that ResumeIQ
   currently supports English responses only.
7. Keep your English clear, professional,
   natural, and easy to understand.

==============================
RESUME INFORMATION
==============================

Resume:
{resume_text}

==============================
JOB DESCRIPTION
==============================

{job_description}

==============================
ANALYSIS RESULTS
==============================

Resume Match:
{similarity_score}%

Keyword Coverage:
{keyword_coverage}%

ATS-style Readiness:
{ats_score}%

Matched Skills:
{", ".join(matched_skills)}

Missing Skills:
{", ".join(missing_skills)}

Strengths:
{", ".join(strengths)}

Suggestions:
{", ".join(suggestions)}

==============================
BEHAVIOR
==============================

Help the user understand and improve their resume.

When answering:

- Focus on the user's resume.
- Relate advice to the job description.
- Explain weaknesses clearly.
- Give practical suggestions.
- Do not invent skills, experience,
  education, projects, or achievements.
- Do not claim that the ATS score guarantees
  passing a real ATS.
- Use the analysis results when relevant.
- Keep answers concise unless the user asks
  for more detail.
"""


    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]


    # Add previous conversation
    for message in chat_history[-10:]:

        role = message.get(
            "role",
            "user"
        )

        content = message.get(
            "content",
            ""
        )

        if role not in ["user", "assistant"]:
            continue

        messages.append({
            "role": role,
            "content": content
        })


    # Add current user question
    messages.append({
        "role": "user",
        "content": user_message
    })


    response = chat(
        model=MODEL_NAME,
        messages=messages
    )


    return response["message"]["content"]