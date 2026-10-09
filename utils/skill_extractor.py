import re


# =========================================
# SKILLS DATABASE
# =========================================

SKILLS = [

    # Programming Languages
    "python",
    "java",
    "c",
    "c++",
    "c#",
    "javascript",
    "typescript",
    "sql",

    # Frontend
    "html",
    "css",
    "react",
    "angular",
    "vue",

    # Backend
    "node.js",
    "express",
    "flask",
    "django",
    "spring",
    "spring boot",
    "rest api",
    "api",

    # Artificial Intelligence / Machine Learning
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "natural language processing",
    "nlp",
    "data science",
    "data analysis",
    "data visualization",

    # Machine Learning Libraries
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "keras",
    "opencv",

    # Databases
    "mongodb",
    "mysql",
    "postgresql",
    "oracle",
    "redis",

    # Cloud
    "aws",
    "azure",
    "google cloud",

    # DevOps / Infrastructure
    "docker",
    "kubernetes",
    "jenkins",
    "terraform",

    # Version Control
    "git",
    "github",

    # Data / Business Intelligence
    "power bi",
    "tableau",
    "excel",

    # Operating Systems
    "linux",

    # Additional
    "streamlit"
]


# =========================================
# SKILL EXTRACTION
# =========================================

def extract_skills(text):

    if not text:
        return []

    text = text.lower()

    found_skills = []

    for skill in SKILLS:

        # Escape special regex characters
        escaped_skill = re.escape(skill)

        # Match skill as a complete term
        pattern = (
            r"(?<![a-z0-9+#.])"
            + escaped_skill
            + r"(?![a-z0-9+#.])"
        )

        if re.search(pattern, text):
            found_skills.append(skill)

    return sorted(set(found_skills))