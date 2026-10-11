
import os
import re
import tempfile
from threading import Lock

from flask import (
    Flask,
    render_template,
    request,
    send_file,
    session,
)
from dotenv import load_dotenv

from utils.pdf_parser import extract_text_from_pdf
from utils.text_processor import preprocess_text
from utils.skill_extractor import extract_skills
from utils.similarity import calculate_similarity
from utils.ats_checker import check_ats_requirements
from utils.report_generator import generate_report
from utils.gemini_chatbot import get_chat_response
from utils.ollama_chatbot import get_ollama_chat_response


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

app = Flask(__name__)

# Set SECRET_KEY in your deployment environment.
# The fallback is only for local development.
app.secret_key = os.getenv(
    "SECRET_KEY",
    "resumeiq-local-development-key"
)

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

# IMPORTANT:
# This in-memory store is suitable only for a simple,
# single-process demo. Use per-user storage for production.
analysis_data = {}
analysis_lock = Lock()


# =========================================================
# SKILL RECOGNITION
# =========================================================

# Add to this dictionary when you want to recognize
# additional skills or job requirements.
#
# The app still uses your existing utils.skill_extractor.
# These rules supplement it; they do not replace it.

SKILL_PATTERNS = {
    "full-stack development": [
        r"\bfull[\s-]*stack(?:\s+developer|\s+development|\s+engineer)?\b",
    ],
    "frontend development": [
        r"\bfront[\s-]*end(?:\s+developer|\s+development)?\b",
    ],
    "backend development": [
        r"\bback[\s-]*end(?:\s+developer|\s+development)?\b",
    ],
    "web development": [
        r"\bweb development\b",
        r"\bweb developer\b",
    ],
    "python": [
        r"\bpython\b",
    ],
    "sql": [
        r"\bsql\b",
        r"\bstructured query language\b",
    ],
    "nlp": [
        r"\bnlp\b",
        r"\bnatural language processing\b",
    ],
    "javascript": [
        r"\bjavascript\b",
        r"\bjs\b",
    ],
    "typescript": [
        r"\btypescript\b",
    ],
    "html": [
        r"\bhtml5?\b",
    ],
    "css": [
        r"\bcss3?\b",
    ],
    "react": [
        r"\breact(?:\.js|js)?\b",
    ],
    "angular": [
        r"\bangular\b",
    ],
    "vue": [
        r"\bvue(?:\.js|js)?\b",
    ],
    "node.js": [
        r"\bnode(?:\.js|js)\b",
    ],
    "express.js": [
        r"\bexpress(?:\.js|js)\b",
    ],
    "flask": [
        r"\bflask\b",
    ],
    "django": [
        r"\bdjango\b",
    ],
    "fastapi": [
        r"\bfastapi\b",
    ],
    "java": [
        r"\bjava\b",
    ],
    "c++": [
        r"\bc\+\+\b",
    ],
    "c#": [
        r"\bc#\b",
    ],
    "machine learning": [
        r"\bmachine learning\b",
    ],
    "deep learning": [
        r"\bdeep learning\b",
    ],
    "artificial intelligence": [
        r"\bartificial intelligence\b",
        r"\bai\b",
    ],
    "data analysis": [
        r"\bdata analysis\b",
        r"\bdata analytics\b",
    ],
    "pandas": [
        r"\bpandas\b",
    ],
    "numpy": [
        r"\bnumpy\b",
    ],
    "scikit-learn": [
        r"\bscikit[\s-]?learn\b",
        r"\bsklearn\b",
    ],
    "tensorflow": [
        r"\btensorflow\b",
    ],
    "pytorch": [
        r"\bpytorch\b",
    ],
    "git": [
        r"\bgit\b",
    ],
    "github": [
        r"\bgithub\b",
    ],
    "docker": [
        r"\bdocker\b",
    ],
    "kubernetes": [
        r"\bkubernetes\b",
    ],
    "aws": [
        r"\baws\b",
        r"\bamazon web services\b",
    ],
    "azure": [
        r"\bmicrosoft azure\b",
        r"\bazure\b",
    ],
    "gcp": [
        r"\bgcp\b",
        r"\bgoogle cloud platform\b",
    ],
    "mongodb": [
        r"\bmongodb\b",
    ],
    "postgresql": [
        r"\bpostgresql\b",
        r"\bpostgres\b",
    ],
    "mysql": [
        r"\bmysql\b",
    ],
    "rest api": [
        r"\brest(?:ful)?\s+apis?\b",
        r"\brest api\b",
    ],
    "api development": [
        r"\bapi development\b",
    ],
    "communication": [
        r"\bcommunication skills?\b",
    ],
    "problem solving": [
        r"\bproblem[\s-]solving\b",
    ],
}


def normalize_text(text):
    """Normalize text for consistent matching."""
    return re.sub(
        r"\s+",
        " ",
        str(text or "").lower()
    ).strip()


def find_rule_based_skills(text):
    """Find skills explicitly mentioned in text."""
    text = normalize_text(text)
    found = set()

    for skill, patterns in SKILL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                found.add(skill)
                break

    return found


def extract_all_skills(text):
    """
    Combine existing skill extraction with supplemental rules.

    Keep the original extractor so existing project skills
    continue to work.
    """
    text = str(text or "")

    try:
        existing = extract_skills(text)
    except Exception:
        app.logger.exception("Existing skill extractor failed")
        existing = []

    if not isinstance(existing, (list, tuple, set)):
        existing = []

    # Normalize the existing extractor's output.
    skills = {
        normalize_text(skill)
        for skill in existing
        if skill and normalize_text(skill)
    }

    # Supplement the existing extractor.
    skills.update(find_rule_based_skills(text))

    return sorted(skills)


def split_job_skills(raw_job_skills, original_job_text):
    """
    Use the original job text to catch multi-word phrases
    that preprocessing may have removed or altered.
    """
    combined = {
        normalize_text(skill)
        for skill in raw_job_skills
        if skill and normalize_text(skill)
    }

    combined.update(find_rule_based_skills(original_job_text))

    return sorted(combined)


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


# =========================================================
# ANALYZE RESUME
# =========================================================

@app.route("/analyze", methods=["POST"])
def analyze():
    global analysis_data

    resume = request.files.get("resume")
    job_description = request.form.get(
        "job_description", ""
    ).strip()

    # -------------------------------
    # VALIDATE INPUTS
    # -------------------------------

    if not resume or not resume.filename:
        return "Please upload a resume PDF.", 400

    if not job_description:
        return "Please enter a job description.", 400

    if not resume.filename.lower().endswith(".pdf"):
        return "Please upload a PDF resume.", 400

    # -------------------------------
    # EXTRACT PDF TEXT
    # -------------------------------

    try:
        resume_text = extract_text_from_pdf(resume)
    except Exception:
        app.logger.exception("PDF extraction failed")
        return (
            "Could not read the uploaded PDF. "
            "Please try another text-based PDF.",
            400,
        )

    if not resume_text or not resume_text.strip():
        return (
            "No selectable text was found in this PDF. "
            "If it is a scanned document, OCR may be required.",
            400,
        )

    # -------------------------------
    # PREPROCESS TEXT
    # -------------------------------

    try:
        clean_resume = preprocess_text(resume_text)
        clean_job_description = preprocess_text(job_description)
    except Exception:
        app.logger.exception("Text preprocessing failed")
        return "Could not process the resume or job description.", 500

    # -------------------------------
    # EXTRACT SKILLS
    # -------------------------------

    resume_skills = extract_all_skills(
        clean_resume + "\n" + resume_text
    )

    extracted_job_skills = extract_all_skills(
        clean_job_description + "\n" + job_description
    )

    # Use the original description as well, since preprocessing
    # can remove punctuation or change multi-word expressions.
    job_skills = split_job_skills(
        extracted_job_skills,
        job_description
    )

    # -------------------------------
    # MATCHED AND MISSING SKILLS
    # -------------------------------

    resume_skill_set = set(resume_skills)
    job_skill_set = set(job_skills)

    matched_skills = sorted(
        resume_skill_set & job_skill_set
    )

    missing_skills = sorted(
        job_skill_set - resume_skill_set
    )

    # -------------------------------
    # SIMILARITY SCORE
    # -------------------------------

    try:
        similarity_score = calculate_similarity(
            clean_resume,
            clean_job_description
        )
    except Exception:
        app.logger.exception("Similarity calculation failed")
        similarity_score = 0

    # Normalize a numeric similarity score for display.
    try:
        similarity_score = float(similarity_score)
    except (TypeError, ValueError):
        similarity_score = 0.0

    # Some similarity helpers return a fraction between 0 and 1.
    if 0 <= similarity_score <= 1:
        similarity_score *= 100

    similarity_score = round(
        max(0.0, min(100.0, similarity_score)),
        2
    )

    # -------------------------------
    # KEYWORD COVERAGE
    # -------------------------------

    if job_skill_set:
        keyword_coverage = round(
            len(matched_skills) / len(job_skill_set) * 100,
            2
        )
    else:
        keyword_coverage = 0.0

    # -------------------------------
    # STRENGTHS
    # -------------------------------

    strengths = []

    if matched_skills:
        strengths.append(
            "Your resume includes these detected job skills: "
            + ", ".join(matched_skills)
            + "."
        )

    if "python" in resume_skill_set:
        strengths.append(
            "Python is explicitly detected in your resume."
        )

    if "sql" in resume_skill_set:
        strengths.append(
            "SQL is explicitly detected in your resume."
        )

    if "nlp" in resume_skill_set:
        strengths.append(
            "NLP is explicitly detected in your resume."
        )

    if not strengths:
        strengths.append(
            "No direct matches were found among the detected "
            "job skills. Review the resume and job requirements."
        )

    # -------------------------------
    # IMPROVEMENT SUGGESTIONS
    # -------------------------------

    suggestions = []

    if missing_skills:
        suggestions.append(
            "The following job skills were not detected in your "
            "resume: " + ", ".join(missing_skills) + ". "
            "If you genuinely have this experience, add specific "
            "examples to your resume."
        )

    if not job_skills:
        suggestions.append(
            "No recognized skills were detected in the job "
            "description. Add specific technologies or review "
            "the skill-recognition rules in app.py."
        )

    if keyword_coverage < 50 and job_skills:
        suggestions.append(
            "Your resume currently matches fewer than half of "
            "the detected job skills. Review your relevant "
            "projects, experience, and technical skills."
        )

    if not suggestions:
        suggestions.append(
            "Continue tailoring your resume to the job's "
            "responsibilities and requirements."
        )

    # -------------------------------
    # ATS-STYLE CHECKS
    # -------------------------------

    try:
        ats_results = check_ats_requirements(resume_text)
    except Exception:
        app.logger.exception("ATS checks failed")
        ats_results = {
            "ats_score": 0,
            "checks": [],
            "suggestions": [
                "ATS-style checks could not be completed."
            ],
        }

    if not isinstance(ats_results, dict):
        ats_results = {
            "ats_score": 0,
            "checks": [],
            "suggestions": [],
        }

    ats_score = ats_results.get("ats_score", 0)

    # -------------------------------
    # SAVE ANALYSIS
    # -------------------------------

    # NOTE: This variable is shared by all visitors in one
    # server process. This is not safe for a multi-user
    # production application; use session-specific storage
    # or a database for production.
    new_analysis = {
        "similarity_score": similarity_score,
        "keyword_coverage": keyword_coverage,
        "resume_skills": resume_skills,
        "job_skills": job_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "ats_results": ats_results,
        "strengths": strengths,
        "suggestions": suggestions,
        "job_description": job_description,
        "resume_text": resume_text,
    }

    with analysis_lock:
        analysis_data = new_analysis

    session["chat_history"] = []

    # -------------------------------
    # RENDER EXISTING RESULTS TEMPLATE
    # -------------------------------

    return render_template(
        "result.html",
        similarity_score=similarity_score,
        keyword_coverage=keyword_coverage,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        resume_skills=resume_skills,
        job_skills=job_skills,
        strengths=strengths,
        suggestions=suggestions,
        ats_results=ats_results,
        ats_score=ats_score,
    )


# =========================================================
# CHATBOT — GEMINI / OLLAMA
# =========================================================

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_message = request.form.get(
            "message", ""
        ).strip()

        mode = request.form.get(
            "mode", "online"
        ).strip().lower()

        if not user_message:
            return "Please enter a message.", 400

        if mode not in ("online", "offline"):
            return (
                "Invalid chat mode. Choose Online or Offline.",
                400,
            )

        with analysis_lock:
            current_analysis = dict(analysis_data)

        if not current_analysis:
            return "Please analyze a resume first.", 400

        chat_history = session.get("chat_history", [])

        common_context = {
            "resume_text": current_analysis.get("resume_text", ""),
            "job_description": current_analysis.get(
                "job_description", ""
            ),
            "similarity_score": current_analysis.get(
                "similarity_score", 0
            ),
            "keyword_coverage": current_analysis.get(
                "keyword_coverage", 0
            ),
            "matched_skills": current_analysis.get(
                "matched_skills", []
            ),
            "missing_skills": current_analysis.get(
                "missing_skills", []
            ),
            "ats_score": current_analysis.get(
                "ats_results", {}
            ).get("ats_score", 0),
            "strengths": current_analysis.get("strengths", []),
            "suggestions": current_analysis.get("suggestions", []),
            "chat_history": chat_history,
        }

        if mode == "offline":
            response = get_ollama_chat_response(
                user_message,
                **common_context
            )
        else:
            response = get_chat_response(
                user_message,
                **common_context
            )

        chat_history.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": str(response)},
        ])

        session["chat_history"] = chat_history[-10:]

        return str(response)

    except Exception:
        app.logger.exception("Chat route failed")
        return (
            "The chatbot could not respond. Check the server "
            "logs and verify the selected model configuration.",
            500,
        )


# =========================================================
# DOWNLOAD PDF REPORT
# =========================================================

@app.route("/download-report", methods=["GET"])
def download_report():
    with analysis_lock:
        current_analysis = dict(analysis_data)

    if not current_analysis:
        return (
            "No analysis is available. Please analyze a resume first.",
            400,
        )

    file_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as temp_file:
            file_path = temp_file.name

        generate_report(
            file_path,
            current_analysis["similarity_score"],
            current_analysis["keyword_coverage"],
            current_analysis["resume_skills"],
            current_analysis["job_skills"],
            current_analysis["matched_skills"],
            current_analysis["missing_skills"],
            current_analysis["ats_results"],
            current_analysis["strengths"],
            current_analysis["suggestions"],
        )

        return send_file(
            file_path,
            as_attachment=True,
            download_name="ResumeIQ_Analysis_Report.pdf",
            mimetype="application/pdf",
        )

    except Exception:
        app.logger.exception("PDF report generation failed")
        return "Could not generate the PDF report.", 500

    finally:
        # The response may stream the file, so do not remove
        # it here before Flask has finished sending it.
        # Temporary files are left for OS/container cleanup.
        pass


# =========================================================
# METHOD NOT ALLOWED HANDLER
# =========================================================


@app.errorhandler(405)
def method_not_allowed(error):
    if request.path == "/analyze":
        return (
            "The /analyze route requires a POST form submission. "
            "Please return to the homepage, upload a PDF, enter "
            "a job description, and click Analyze Resume.",
            405,
        )

    return "The requested HTTP method is not supported.", 405

# =========================================================
# RUN LOCALLY
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)
