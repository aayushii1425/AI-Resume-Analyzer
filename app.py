
from flask import Flask, render_template, request, send_file, session
import os
import tempfile

from dotenv import load_dotenv

from utils.pdf_parser import extract_text_from_pdf
from utils.text_processor import preprocess_text
from utils.skill_extractor import extract_skills
from utils.similarity import calculate_similarity
from utils.ats_checker import check_ats_requirements
from utils.report_generator import generate_report
from utils.gemini_chatbot import get_chat_response
from utils.ollama_chatbot import get_ollama_chat_response

# =========================================
# LOAD ENVIRONMENT VARIABLES
# =========================================

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# =========================================
# FLASK APPLICATION
# =========================================

app = Flask(__name__)

app.secret_key = "resumeiq-development-key"


# =========================================
# STORE LAST ANALYSIS
# =========================================

analysis_data = {}


# =========================================
# HOME PAGE
# =========================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================
# ANALYZE RESUME
# =========================================

@app.route(
    "/analyze",
    methods=["POST"]
)
def analyze():

    global analysis_data

    # -----------------------------------------
    # GET INPUTS
    # -----------------------------------------

    resume = request.files.get(
        "resume"
    )

    job_description = request.form.get(
        "job_description"
    )

    # -----------------------------------------
    # VALIDATE RESUME
    # -----------------------------------------

    if not resume:

        return "Please upload a resume."

    # -----------------------------------------
    # VALIDATE JOB DESCRIPTION
    # -----------------------------------------

    if not job_description:

        return "Please enter a job description."

    # -----------------------------------------
    # CHECK FILE TYPE
    # -----------------------------------------

    if not resume.filename.lower().endswith(".pdf"):

        return "Please upload a PDF resume."

    # -----------------------------------------
    # EXTRACT RESUME TEXT
    # -----------------------------------------

    resume_text = extract_text_from_pdf(
        resume
    )

    # -----------------------------------------
    # CHECK EXTRACTED TEXT
    # -----------------------------------------

    if not resume_text.strip():

        return (
            "Could not extract text from the "
            "uploaded PDF. Please make sure the "
            "PDF contains selectable text."
        )

    # -----------------------------------------
    # PREPROCESS TEXT
    # -----------------------------------------

    clean_resume = preprocess_text(
        resume_text
    )

    clean_job_description = preprocess_text(
        job_description
    )

    # =========================================
    # SKILL EXTRACTION
    # =========================================

    resume_skills = extract_skills(
        clean_resume
    )

    job_skills = extract_skills(
        clean_job_description
    )

    # =========================================
    # DEBUG INFORMATION
    # =========================================

    print(
        "\n========================================="
    )

    print(
        "RESUME SKILLS:"
    )

    print(
        resume_skills
    )

    print(
        "\nJOB DESCRIPTION SKILLS:"
    )

    print(
        job_skills
    )

    print(
        "\n=========================================\n"
    )

    # =========================================
    # MATCHED SKILLS
    # =========================================

    matched_skills = sorted(
        set(resume_skills)
        &
        set(job_skills)
    )

    # =========================================
    # MISSING SKILLS
    # =========================================

    missing_skills = sorted(
        set(job_skills)
        -
        set(resume_skills)
    )

    # =========================================
    # RESUME / JOB SIMILARITY
    # =========================================

    similarity_score = calculate_similarity(
        clean_resume,
        clean_job_description
    )

    # =========================================
    # KEYWORD COVERAGE
    # =========================================

    if job_skills:

        keyword_coverage = round(
            (
                len(matched_skills)
                /
                len(job_skills)
            ) * 100,
            2
        )

    else:

        keyword_coverage = 0

    # =========================================
    # RESUME STRENGTHS
    # =========================================

    strengths = []

    if len(matched_skills) >= 5:

        strengths.append(
            "Strong alignment with the technical "
            "skills required for the role."
        )

    elif len(matched_skills) > 0:

        strengths.append(
            "Your resume contains some of the "
            "technical skills required for this role."
        )

    if "python" in resume_skills:

        strengths.append(
            "Python experience is present in your resume."
        )

    if "machine learning" in resume_skills:

        strengths.append(
            "Machine Learning experience is detected."
        )

    if "data analysis" in resume_skills:

        strengths.append(
            "Data analysis skills are present."
        )

    if (
        "git" in resume_skills
        or
        "github" in resume_skills
    ):

        strengths.append(
            "Version-control experience is mentioned."
        )

    if not strengths:

        strengths.append(
            "Your resume contains identifiable "
            "technical skills."
        )

    # =========================================
    # IMPROVEMENT SUGGESTIONS
    # =========================================

    suggestions = []

    if missing_skills:

        suggestions.append(
            "Consider highlighting relevant missing "
            "skills if you genuinely have experience "
            "with them."
        )

    if not job_skills:

        suggestions.append(
            "No recognized technical skills were "
            "detected in the job description. "
            "Consider reviewing the job description "
            "for specific technologies or requirements."
        )

    if keyword_coverage < 50:

        suggestions.append(
            "Review the job description and make sure "
            "relevant experience and technologies are "
            "clearly mentioned in your resume."
        )

    if (
        "python" in job_skills
        and
        "python" not in resume_skills
    ):

        suggestions.append(
            "If you have Python experience, make it "
            "clearly visible in your skills or project "
            "descriptions."
        )

    if (
        "sql" in job_skills
        and
        "sql" not in resume_skills
    ):

        suggestions.append(
            "If applicable, mention SQL experience and "
            "describe how you used it in projects."
        )

    if (
        "machine learning" in job_skills
        and
        "machine learning" not in resume_skills
    ):

        suggestions.append(
            "If applicable, highlight Machine Learning "
            "projects and the techniques or libraries "
            "you used."
        )

    if not suggestions:

        suggestions.append(
            "Continue tailoring your resume to the "
            "specific responsibilities and requirements "
            "of the role."
        )

    # =========================================
    # ATS-STYLE RESUME CHECKS
    # =========================================

    ats_results = check_ats_requirements(
        resume_text
    )

    # =========================================
    # SAVE ANALYSIS DATA
    # =========================================

    analysis_data = {

        "similarity_score":
            similarity_score,

        "keyword_coverage":
            keyword_coverage,

        "resume_skills":
            resume_skills,

        "job_skills":
            job_skills,

        "matched_skills":
            matched_skills,

        "missing_skills":
            missing_skills,

        "ats_results":
            ats_results,

        "strengths":
            strengths,

        "job_description":
            clean_job_description,

        "resume_text":
            clean_resume,

        "suggestions":
            suggestions
    }

    # =========================================
    # RESET CHAT FOR NEW ANALYSIS
    # =========================================

    session["chat_history"] = []

    # =========================================
    # RENDER RESULTS
    # =========================================

    return render_template(

        "result.html",

        similarity_score=
            similarity_score,

        keyword_coverage=
            keyword_coverage,

        matched_skills=
            matched_skills,

        missing_skills=
            missing_skills,

        resume_skills=
            resume_skills,

        job_skills=
            job_skills,

        strengths=
            strengths,

        suggestions=
            suggestions,

        ats_results=
            ats_results,

        ats_score=
            ats_results["ats_score"]
    )

# =========================================
# GEMINI CHATBOT
# =========================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    try:

        user_message = request.form.get(
            "message"
        )

        mode = request.form.get(
            "mode",
            "online"
        ).strip().lower()

        # =====================================
        # VALIDATE CHAT MODE
        # =====================================

        if mode not in ("online", "offline"):

            return (
                "Invalid chat mode. Choose Online or Offline.",
                400
            )

        # =====================================
        # VALIDATE MESSAGE
        # =====================================

        if not user_message:

            return (
                "Please enter a message.",
                400
            )

        # =====================================
        # CHECK ANALYSIS
        # =====================================

        if not analysis_data:

            return (
                "Please analyze a resume first.",
                400
            )

        # =====================================
        # GET CHAT HISTORY
        # =====================================

        chat_history = session.get(
            "chat_history",
            []
        )

        # =====================================
        # LOG CHAT REQUEST
        # =====================================

        print(
            "\n========================================="
        )

        print(
            "CHAT REQUEST:"
        )

        print(
            user_message
        )

        print(
            f"ResumeIQ Chat Mode: {mode.upper()}"
        )

        print(
            "=========================================\n"
        )

        # =====================================
        # OFFLINE MODE — OLLAMA / QWEN
        # =====================================

        if mode == "offline":

            response = get_ollama_chat_response(

                user_message,

                resume_text=analysis_data.get(
                    "resume_text",
                    ""
                ),

                job_description=analysis_data.get(
                    "job_description",
                    ""
                ),

                similarity_score=analysis_data.get(
                    "similarity_score",
                    0
                ),

                keyword_coverage=analysis_data.get(
                    "keyword_coverage",
                    0
                ),

                matched_skills=analysis_data.get(
                    "matched_skills",
                    []
                ),

                missing_skills=analysis_data.get(
                    "missing_skills",
                    []
                ),

                ats_score=analysis_data.get(
                    "ats_results",
                    {}
                ).get(
                    "ats_score",
                    0
                ),

                strengths=analysis_data.get(
                    "strengths",
                    []
                ),

                suggestions=analysis_data.get(
                    "suggestions",
                    []
                ),

                chat_history=chat_history
            )

        # =====================================
        # ONLINE MODE — GEMINI
        # =====================================

        else:

            response = get_chat_response(

                user_message,

                resume_text=analysis_data.get(
                    "resume_text",
                    ""
                ),

                job_description=analysis_data.get(
                    "job_description",
                    ""
                ),

                similarity_score=analysis_data.get(
                    "similarity_score",
                    0
                ),

                keyword_coverage=analysis_data.get(
                    "keyword_coverage",
                    0
                ),

                matched_skills=analysis_data.get(
                    "matched_skills",
                    []
                ),

                missing_skills=analysis_data.get(
                    "missing_skills",
                    []
                ),

                ats_score=analysis_data.get(
                    "ats_results",
                    {}
                ).get(
                    "ats_score",
                    0
                ),

                strengths=analysis_data.get(
                    "strengths",
                    []
                ),

                suggestions=analysis_data.get(
                    "suggestions",
                    []
                ),

                chat_history=chat_history
            )

        # =====================================
        # SAVE USER MESSAGE
        # =====================================

        chat_history.append({
            "role": "user",
            "content": user_message
        })

        # =====================================
        # SAVE AI RESPONSE
        # =====================================

        chat_history.append({
            "role": "assistant",
            "content": response
        })

        # =====================================
        # KEEP LAST 10 MESSAGES
        # =====================================

        chat_history = chat_history[-10:]

        session["chat_history"] = chat_history

        print(
            "\nResumeIQ: Chat response completed."
        )

        return response

    # =========================================
    # CATCH UNEXPECTED ERROR
    # =========================================

    except Exception as error:

        print(
            "\n========================================="
        )

        print(
            "CHAT ROUTE ERROR:"
        )

        print(
            repr(error)
        )

        print(
            "=========================================\n"
        )

        return (
            "ResumeIQ backend error: "
            + str(error),
            500
        )

# =========================================
# DOWNLOAD PDF REPORT
# =========================================

@app.route(
    "/download-report"
)
def download_report():

    # -----------------------------------------
    # CHECK WHETHER ANALYSIS EXISTS
    # -----------------------------------------

    if not analysis_data:

        return (
            "No analysis available. "
            "Please analyze a resume first."
        )

    # -----------------------------------------
    # CREATE TEMPORARY PDF FILE
    # -----------------------------------------

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )

    file_path = temp_file.name

    temp_file.close()

    try:

        # -----------------------------------------
        # GENERATE REPORT
        # -----------------------------------------

        generate_report(

            file_path,

            analysis_data[
                "similarity_score"
            ],

            analysis_data[
                "keyword_coverage"
            ],

            analysis_data[
                "resume_skills"
            ],

            analysis_data[
                "job_skills"
            ],

            analysis_data[
                "matched_skills"
            ],

            analysis_data[
                "missing_skills"
            ],

            analysis_data[
                "ats_results"
            ],

            analysis_data[
                "strengths"
            ],

            analysis_data[
                "suggestions"
            ]
        )

        # -----------------------------------------
        # SEND PDF
        # -----------------------------------------

        return send_file(

            file_path,

            as_attachment=True,

            download_name=
                "ResumeIQ_Analysis_Report.pdf",

            mimetype=
                "application/pdf"
        )

    except Exception as error:

        print(
            "PDF REPORT ERROR:",
            error
        )

        return (
            "Could not generate the PDF report.",
            500
        )


# =========================================
# RUN FLASK APPLICATION
# =========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
