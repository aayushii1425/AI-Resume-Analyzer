import re


def check_ats_requirements(text):

    text_lower = text.lower()

    checks = []

    # --------------------------------------------------
    # NORMALIZE PDF EXTRACTED TEXT
    # --------------------------------------------------

    normalized_text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    normalized_lower = normalized_text.lower()

    # --------------------------------------------------
    # EMAIL
    # --------------------------------------------------

    email_pattern = (
        r"[A-Za-z0-9._%+-]+\s*@\s*"
        r"[A-Za-z0-9.-]+\s*\.\s*[A-Za-z]{2,}"
    )

    email_found = re.search(
        email_pattern,
        normalized_text
    )

    checks.append({
        "name": "Email Address",
        "status": bool(email_found),
        "message": (
            "Email address detected."
            if email_found
            else "No email address detected."
        )
    })

    # --------------------------------------------------
    # PHONE
    # --------------------------------------------------

    phone_pattern = (
        r"(?:\+?\d{1,3}[\s.-]?)?"
        r"(?:\d[\s.-]?){10}"
    )

    phone_found = re.search(
        phone_pattern,
        normalized_text
    )

    checks.append({
        "name": "Phone Number",
        "status": bool(phone_found),
        "message": (
            "Phone number detected."
            if phone_found
            else "No phone number detected."
        )
    })

    # --------------------------------------------------
    # EDUCATION
    # --------------------------------------------------

    education_keywords = [
        "education",
        "academic",
        "university",
        "college",
        "degree",
        "bachelor",
        "master",
        "b.tech",
        "m.tech",
        "b.e.",
        "m.e.",
        "undergraduate",
        "postgraduate"
    ]

    education_found = any(
        keyword in normalized_lower
        for keyword in education_keywords
    )

    checks.append({
        "name": "Education Section",
        "status": education_found,
        "message": (
            "Education information detected."
            if education_found
            else "Education section was not clearly detected."
        )
    })

    # --------------------------------------------------
    # EXPERIENCE
    # --------------------------------------------------

    experience_keywords = [
        "experience",
        "work experience",
        "professional experience",
        "internship",
        "internships",
        "employment",
        "work history"
    ]

    experience_found = any(
        keyword in normalized_lower
        for keyword in experience_keywords
    )

    checks.append({
        "name": "Experience Section",
        "status": experience_found,
        "message": (
            "Experience information detected."
            if experience_found
            else "Experience section was not clearly detected."
        )
    })

    # --------------------------------------------------
    # PROJECTS
    # --------------------------------------------------

    project_keywords = [
        "projects",
        "project",
        "portfolio",
        "personal projects",
        "academic projects"
    ]

    projects_found = any(
        keyword in normalized_lower
        for keyword in project_keywords
    )

    checks.append({
        "name": "Projects Section",
        "status": projects_found,
        "message": (
            "Projects section detected."
            if projects_found
            else "Projects section was not clearly detected."
        )
    })

    # --------------------------------------------------
    # SKILLS
    # --------------------------------------------------

    skills_keywords = [
        "skills",
        "technical skills",
        "technical expertise",
        "technologies",
        "technical proficiencies",
        "core competencies"
    ]

    skills_found = any(
        keyword in normalized_lower
        for keyword in skills_keywords
    )

    checks.append({
        "name": "Skills Section",
        "status": skills_found,
        "message": (
            "Skills section detected."
            if skills_found
            else "Skills section was not clearly detected."
        )
    })

    # --------------------------------------------------
    # RESUME CONTENT
    # --------------------------------------------------

    word_count = len(normalized_text.split())

    if word_count >= 150:
        length_status = True
        length_message = (
            f"Resume contains approximately {word_count} words."
        )
    else:
        length_status = False
        length_message = (
            f"Resume contains approximately {word_count} words. "
            "Consider providing more relevant detail."
        )

    checks.append({
        "name": "Resume Content",
        "status": length_status,
        "message": length_message
    })

    # --------------------------------------------------
    # READINESS SCORE
    # --------------------------------------------------

    passed_checks = sum(
        1
        for check in checks
        if check["status"]
    )

    total_checks = len(checks)

    ats_score = round(
        (passed_checks / total_checks) * 100,
        2
    )

    return {
        "checks": checks,
        "ats_score": ats_score,
        "word_count": word_count
    }