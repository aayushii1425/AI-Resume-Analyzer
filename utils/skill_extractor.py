import re


SKILLS = [
    "python",
    "java",
    "c++",
    "sql",
    "html",
    "css",
    "javascript",
    "react",
    "node.js",
    "machine learning",
    "deep learning",
    "natural language processing",
    "nlp",
    "artificial intelligence",
    "data analysis",
    "data visualization",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "flask",
    "django",
    "streamlit",
    "mongodb",
    "mysql",
    "postgresql",
    "git",
    "github",
    "docker",
    "aws",
    "azure",
    "power bi",
    "tableau",
    "excel"
]


def extract_skills(text):
    text = text.lower()
    found_skills = []

    for skill in SKILLS:
        pattern = (
            r"(?<![a-z0-9+#.])"
            + re.escape(skill)
            + r"(?![a-z0-9+#.])"
        )

        if re.search(pattern, text):
            found_skills.append(skill)

    return sorted(set(found_skills))