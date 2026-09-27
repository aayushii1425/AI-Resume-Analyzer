# ResumeIQ — AI Resume Analyzer

ResumeIQ is an AI-powered web application that analyzes resumes against job descriptions and provides insights into resume-job alignment, skills, keyword coverage, and resume readiness.

The application extracts information from PDF resumes, identifies relevant technical skills, compares them with job requirements, and generates an automated analysis report.

---

## ✨ Features

- 📄 PDF resume upload
- 🔍 Resume text extraction
- 🧠 Automatic skill extraction
- 🎯 Resume–job description similarity analysis
- 📊 Keyword coverage analysis
- ✅ Matched skills identification
- ⚠️ Missing skills identification
- 📋 Resume readiness checks
- 💡 Resume strengths and improvement suggestions
- 📈 Visual skill analysis
- 📥 Downloadable PDF analysis report
- 🎨 Modern responsive user interface

---

## 🛠️ Technologies Used

### Backend
- Python
- Flask

### Natural Language Processing & Machine Learning
- Scikit-learn
- TF-IDF Vectorization
- Cosine Similarity
- Regular Expressions

### PDF Processing
- PyMuPDF

### Report Generation
- ReportLab

### Frontend
- HTML5
- CSS3
- Jinja2

### Deployment
- Gunicorn
- Render

---

## 🔄 How It Works

```text
Upload Resume
      ↓
Extract PDF Text
      ↓
Preprocess Resume & Job Description
      ↓
Extract Relevant Skills
      ↓
Compare Resume with Job Description
      ↓
Calculate Similarity & Keyword Coverage
      ↓
Run Resume Readiness Checks
      ↓
Generate Strengths & Suggestions
      ↓
Display Visual Results
      ↓
Download PDF Report