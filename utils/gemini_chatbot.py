from dotenv import load_dotenv
import os

from google import genai
from google.genai import types


# =========================================
# LOAD ENVIRONMENT VARIABLES
# =========================================

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

client = None

if api_key:
    # =========================================
    # GEMINI CLIENT
    # =========================================
    #
    # retry_options:
    # max_retries = 0
    #
    # This is important because the Google SDK
    # normally retries transient 5xx errors.
    #
    # We want EACH model to be attempted ONLY ONCE.
    # =========================================

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                attempts=1
            )
        )
    )


# =========================================
# MODEL ORDER
# =========================================

PRIMARY_MODEL = "gemini-3.8-flash"

FALLBACK_MODELS = [
    "gemini-3.7-flash",
    "gemini-3.5-flash"
]


# =========================================
# CHAT RESPONSE
# =========================================

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
    chat_history=None
):

    if client is None:
        return (
            "ResumeIQ could not authenticate with the Gemini API. "
            "Please check your GOOGLE_API_KEY."
        )

    matched_skills = matched_skills or []

    missing_skills = missing_skills or []

    strengths = strengths or []

    suggestions = suggestions or []

    chat_history = chat_history or []


    # =========================================
    # FORMAT SKILLS
    # =========================================

    matched_skills_text = (
        ", ".join(matched_skills)
        if matched_skills
        else "None detected"
    )

    missing_skills_text = (
        ", ".join(missing_skills)
        if missing_skills
        else "None detected"
    )


    # =========================================
    # FORMAT STRENGTHS
    # =========================================

    strengths_text = (
        "\n".join(
            f"- {item}"
            for item in strengths
        )
        if strengths
        else "None provided"
    )


    # =========================================
    # FORMAT SUGGESTIONS
    # =========================================

    suggestions_text = (
        "\n".join(
            f"- {item}"
            for item in suggestions
        )
        if suggestions
        else "None provided"
    )


    # =========================================
    # CONVERSATION HISTORY
    # =========================================

    conversation_history = ""

    for message in chat_history:

        role = message.get(
            "role",
            "user"
        )

        content = message.get(
            "content",
            ""
        )

        if role == "user":

            conversation_history += (
                f"User: {content}\n"
            )

        elif role == "assistant":

            conversation_history += (
                f"ResumeIQ: {content}\n"
            )


    if not conversation_history:

        conversation_history = (
            "No previous conversation."
        )


    # =========================================
    # PROMPT
    # =========================================

    prompt = f"""
You are ResumeIQ, an AI resume and career assistant.

Answer the user's question using the resume,
job description, and analysis information.

IMPORTANT RULES:

- Answer directly.
- Keep the answer concise.
- Use bullet points when useful.
- Focus on the most important points.
- Do not unnecessarily repeat the resume.
- Do not unnecessarily repeat the job description.
- Do not invent experience, skills, education,
  projects, certifications, or achievements.
- If something is missing, clearly identify it.
- Give practical and actionable recommendations.
- Do not guarantee ATS success.
- Similarity score is not a guaranteed ATS score.
- Use previous conversation when answering follow-up
  questions.

========================================
RESUME ANALYSIS
========================================

Resume-Job Similarity:
{similarity_score}%

Keyword Coverage:
{keyword_coverage}%

ATS Readiness:
{ats_score}%

Matched Skills:
{matched_skills_text}

Missing Skills:
{missing_skills_text}

Resume Strengths:
{strengths_text}

Resume Suggestions:
{suggestions_text}

========================================
RESUME
========================================

{resume_text}

========================================
JOB DESCRIPTION
========================================

{job_description}

========================================
PREVIOUS CONVERSATION
========================================

{conversation_history}

========================================
CURRENT USER QUESTION
========================================

{user_message}

========================================
ANSWER
========================================

Give the most useful answer first.

Keep the response concise and actionable.
"""


    # =========================================
    # MODEL ORDER
    # =========================================

    models_to_try = [
        PRIMARY_MODEL,
        *FALLBACK_MODELS
    ]


    # =========================================
    # TRY EACH MODEL ONLY ONCE
    # =========================================

    for model_name in models_to_try:

        print(
            "\n========================================="
        )

        print(
            f"ResumeIQ: Trying model: {model_name}"
        )

        print(
            "ResumeIQ: This model will be attempted "
            "ONLY ONCE."
        )

        print(
            "=========================================\n"
        )


        try:

            # =====================================
            # FAST GENERATION CONFIG
            # =====================================

            config = types.GenerateContentConfig(

                temperature=0.3,

                max_output_tokens=300,

                thinking_config=types.ThinkingConfig(
                    thinking_level="low"
                )
            )


            print(
                f"ResumeIQ: Sending request to "
                f"{model_name}..."
            )


            # =====================================
            # SINGLE API REQUEST
            # =====================================

            response = client.models.generate_content(

                model=model_name,

                contents=prompt,

                config=config
            )


            # =====================================
            # CHECK RESPONSE
            # =====================================

            if response is None:

                print(
                    f"ResumeIQ: {model_name} "
                    "returned no response."
                )

                print(
                    "ResumeIQ: Moving to next model..."
                )

                continue


            if not response.text:

                print(
                    f"ResumeIQ: {model_name} "
                    "returned an empty response."
                )

                print(
                    "ResumeIQ: Moving to next model..."
                )

                continue


            # =====================================
            # SUCCESS
            # =====================================

            print(
                "\n========================================="
            )

            print(
                f"ResumeIQ: SUCCESS"
            )

            print(
                f"ResumeIQ: Model used: {model_name}"
            )

            print(
                "=========================================\n"
            )


            return response.text


        # =========================================
        # ERROR HANDLING
        # =========================================

        except Exception as error:

            error_text = str(error)


            print(
                "\n========================================="
            )

            print(
                "GEMINI ERROR:"
            )

            print(
                error_text
            )

            print(
                f"MODEL: {model_name}"
            )

            print(
                "=========================================\n"
            )


            # =====================================
            # 503 / UNAVAILABLE
            # =====================================

            if (
                "503" in error_text
                or
                "UNAVAILABLE" in error_text
                or
                "overloaded" in error_text.lower()
            ):

                print(
                    f"ResumeIQ: {model_name} "
                    "returned 503/unavailable."
                )

                print(
                    "ResumeIQ: NO RETRY."
                )

                print(
                    "ResumeIQ: Moving immediately "
                    "to the next model."
                )

                continue


            # =====================================
            # 429 RATE LIMIT
            # =====================================

            if (
                "429" in error_text
                or
                "RESOURCE_EXHAUSTED" in error_text
            ):

                print(
                    f"ResumeIQ: {model_name} "
                    "returned 429 rate limit."
                )

                print(
                    "ResumeIQ: NO RETRY."
                )

                print(
                    "ResumeIQ: Moving immediately "
                    "to the next model."
                )

                continue


            # =====================================
            # 404 MODEL NOT FOUND
            # =====================================

            if (
                "404" in error_text
                or
                "NOT_FOUND" in error_text
            ):

                print(
                    f"ResumeIQ: {model_name} "
                    "was not found."
                )

                print(
                    "ResumeIQ: NO RETRY."
                )

                print(
                    "ResumeIQ: Moving immediately "
                    "to the next model."
                )

                continue


            # =====================================
            # AUTHENTICATION / PERMISSION
            # =====================================

            if (
                "401" in error_text
                or
                "403" in error_text
                or
                "API key" in error_text
                or
                "PERMISSION_DENIED" in error_text
            ):

                print(
                    "ResumeIQ: Authentication or "
                    "permission problem."
                )


                return (
                    "ResumeIQ could not authenticate "
                    "with the Gemini API. Please check "
                    "your GOOGLE_API_KEY."
                )


            # =====================================
            # OTHER ERROR
            # =====================================

            print(
                f"ResumeIQ: Unexpected error from "
                f"{model_name}."
            )

            print(
                "ResumeIQ: NO RETRY."
            )

            print(
                "ResumeIQ: Moving to next model."
            )

            continue


    # =========================================
    # ALL MODELS FAILED
    # =========================================

    print(
        "\n========================================="
    )

    print(
        "ResumeIQ: ALL GEMINI MODELS FAILED."
    )

    print(
        "=========================================\n"
    )


    return (
        "ResumeIQ could not generate a response "
        "right now. The available Gemini models "
        "are temporarily unavailable. Please "
        "try again shortly."
    )