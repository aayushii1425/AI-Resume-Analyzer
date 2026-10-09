# ResumeIQ — AI Resume Analyzer

🚀 **Live Demo:** [Launch ResumeIQ](https://ai-resume-analyzer-4322.onrender.com/)

📂 **GitHub Repository:** [AI-Resume-Analyzer](https://github.com/aayushii1425/AI-Resume-Analyzer)

ResumeIQ is an AI-powered web application that analyzes resumes against job descriptions and provides insights into resume-job alignment, skills, keyword coverage, and resume readiness.

The application extracts information from PDF resumes, identifies relevant technical skills, compares them with job requirements, and generates an automated analysis report.

---
✨ **Features**

Resume Parsing: Extract text from uploaded PDF resumes.

Job Description Matching: Compare resumes with job descriptions using TF-IDF and cosine similarity.

Skill Gap Analysis: Identify matching and missing skills.

ATS-Style Checks: Evaluate resume structure and common application-readiness factors.

Improvement Suggestions: Highlight resume strengths and areas for improvement.

PDF Report: Download the resume analysis report.

AI Support Chatbot: Ask questions about resume weaknesses, missing skills, and improvement strategies.

Online AI Mode: Use the Gemini API for AI-powered assistance.

Offline AI Mode: Use Ollama with a locally installed language model.



🧠 **Technology Stack**

Backend: Python, Flask

Frontend: HTML, CSS, JavaScript

NLP and Matching: TF-IDF, cosine similarity

PDF Processing: Python PDF extraction utilities

Online LLM: Google Gemini API

Offline LLM: Ollama with a local model such as Qwen 2.5 7B

Planned RAG Framework: LangChain

Planned Vector Storage: FAISS


🔄 **Planned RAG Architecture**

The planned Retrieval-Augmented Generation (RAG) pipeline consists of:

Extracting text from uploaded resumes.

Splitting text into manageable chunks.

Generating embeddings for the chunks.

Storing embeddings in a vector database.

Retrieving relevant resume information based on user queries.

Using LangChain to coordinate retrieval, prompt construction, and LLM interaction.

Generating contextual responses using Gemini online or Ollama offline.

⚙️ **AI Modes**

<p><ins>Online Mode</ins></p>

Uses the Gemini API and requires a valid API key configured securely in the environment.

<p><ins>Offline Mode</ins></p>

Uses Ollama and a locally installed language model. Ollama and the required model must be installed on the computer running the application.

Note: Offline inference on your computer is separate from the Render-hosted deployment. The deployed website does not automatically have access to your local Ollama installation.



💻 **Local Setup**

Clone the repository:

git clone https://github.com/aayushii1425/AI-Resume-Analyzer.git

Enter the project directory:

cd AI-Resume-Analyzer

Create and activate a virtual environment:

python -m venv .venv
.venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Configure the Gemini API key using an environment variable if you want online AI functionality.

For offline mode, install Ollama and download the required model.

Start the Flask application:

python app.py

Open http://127.0.0.1:5000 in your browser.


👩‍💻 **Project Goal**

ResumeIQ aims to make resume evaluation more accessible by combining job-description matching, actionable feedback, and AI-powered resume assistance in one application.



📌 **Future Enhancements**

Complete the LangChain-based RAG pipeline.

Integrate FAISS or Chroma for semantic retrieval.

Improve contextual resume question answering.

Expand resume evaluation and job-specific recommendations.
