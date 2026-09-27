from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)


def generate_report(
    file_path,
    similarity_score,
    keyword_coverage,
    resume_skills,
    job_skills,
    matched_skills,
    missing_skills,
    ats_results,
    strengths,
    suggestions
):

    document = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=24,
        leading=30,
        textColor=colors.HexColor("#6541c9"),
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.HexColor("#777777"),
        spaceAfter=25
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#342b4a"),
        spaceBefore=18,
        spaceAfter=10
    )

    normal_style = ParagraphStyle(
        "NormalCustom",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#555555")
    )

    story = []

    # =========================================
    # HEADER
    # =========================================

    story.append(
        Paragraph(
            "ResumeIQ",
            title_style
        )
    )

    story.append(
        Paragraph(
            "AI-Powered Resume Analysis Report",
            subtitle_style
        )
    )

    # =========================================
    # SCORE SUMMARY
    # =========================================

    story.append(
        Paragraph(
            "Analysis Summary",
            heading_style
        )
    )

    summary_data = [
        [
            "Resume Match",
            "Keyword Coverage",
            "Resume Readiness"
        ],
        [
            f"{similarity_score}%",
            f"{keyword_coverage}%",
            f"{ats_results['ats_score']}%"
        ]
    ]

    summary_table = Table(
        summary_data,
        colWidths=[160, 160, 160]
    )

    summary_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#eee8ff")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.HexColor("#6541c9")
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTNAME",
                (0, 1),
                (-1, 1),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                11
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#ddd6f5")
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#ddd6f5")
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                12
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                12
            )
        ])
    )

    story.append(summary_table)

    # =========================================
    # SKILLS
    # =========================================

    story.append(
        Paragraph(
            "Skill Analysis",
            heading_style
        )
    )

    skill_data = [
        ["Category", "Skills"],
        [
            "Resume Skills",
            ", ".join(resume_skills)
            if resume_skills
            else "None detected"
        ],
        [
            "Job Skills",
            ", ".join(job_skills)
            if job_skills
            else "None detected"
        ],
        [
            "Matched Skills",
            ", ".join(matched_skills)
            if matched_skills
            else "None"
        ],
        [
            "Missing Skills",
            ", ".join(missing_skills)
            if missing_skills
            else "None"
        ]
    ]

    skill_table = Table(
        skill_data,
        colWidths=[120, 360]
    )

    skill_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#eee8ff")
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTNAME",
                (0, 1),
                (0, -1),
                "Helvetica-Bold"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#dddddd")
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8
            )
        ])
    )

    story.append(skill_table)

    # =========================================
    # ATS CHECKS
    # =========================================

    story.append(
        Paragraph(
            "Resume Readiness Checks",
            heading_style
        )
    )

    ats_data = [
        ["Check", "Status", "Details"]
    ]

    for check in ats_results["checks"]:

        status = (
            "Passed"
            if check["status"]
            else "Needs Attention"
        )

        ats_data.append([
            check["name"],
            status,
            check["message"]
        ])

    ats_table = Table(
        ats_data,
        colWidths=[130, 100, 250]
    )

    ats_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#eee8ff")
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#dddddd")
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8
            )
        ])
    )

    story.append(ats_table)

    # =========================================
    # STRENGTHS
    # =========================================

    story.append(
        Paragraph(
            "Resume Strengths",
            heading_style
        )
    )

    for strength in strengths:

        story.append(
            Paragraph(
                f"✓ {strength}",
                normal_style
            )
        )

        story.append(
            Spacer(1, 5)
        )

    # =========================================
    # SUGGESTIONS
    # =========================================

    story.append(
        Paragraph(
            "Improvement Suggestions",
            heading_style
        )
    )

    for suggestion in suggestions:

        story.append(
            Paragraph(
                f"• {suggestion}",
                normal_style
            )
        )

        story.append(
            Spacer(1, 5)
        )

    # =========================================
    # DISCLAIMER
    # =========================================

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            "<b>Note:</b> ResumeIQ provides automated "
            "resume analysis based on the information "
            "detected in the uploaded resume and job "
            "description. Resume Readiness is based on "
            "the checks implemented in this application "
            "and does not guarantee acceptance by any "
            "particular Applicant Tracking System.",
            normal_style
        )
    )

    # =========================================
    # BUILD PDF
    # =========================================

    document.build(story)