from utils.gemini_chatbot import get_chat_response


response = get_chat_response(
    "What skills should I improve for this job?",

    resume_text="""
    Python, Java, SQL, Git, Machine Learning.
    Built an AI Resume Analyzer using Flask and Scikit-learn.
    """,

    job_description="""
    We are looking for a software developer with
    Python, SQL, React, Docker, AWS and Git experience.
    """
)

print("\nGemini Response:\n")
print(response)