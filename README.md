
🚀 AI-Powered Resume Screening System

An intelligent web application that automates resume screening and ranks candidates based on job requirements using NLP and semantic analysis.

📌 Overview

The AI Resume Screening System helps recruiters and hiring managers quickly filter and rank candidates by analyzing resumes against job descriptions.

It leverages Natural Language Processing (NLP) and semantic matching to provide accurate candidate scoring and insights.

✨ Features
📄 Upload multiple resumes (CSV/Text)
🧠 AI-based resume analysis
🔍 Semantic matching with Job Description
📊 Candidate scoring system
🏆 Ranked results dashboard
📈 Clean and interactive UI
🌙 Dark/Light mode (if added)
⚡ Fast and automated screening


🛠️ Tech Stack

Frontend

HTML, CSS, Bootstrap
JavaScript

Backend

Python (Flask)

Machine Learning / NLP

NLTK / SpaCy
Semantic similarity models

Database

SQLite


📂 Project Structure
resume-ai/
│── app.py
│── config.py
│── requirements.txt
│
├── routes/
│   └── screening.py
│
├── services/
│   ├── scorer.py
│   ├── semantic_matcher.py
│   └── notifications.py
│
├── templates/
│   ├── base.html
│   ├── index.html
│   └── result.html
│
├── static/
│   ├── css/
│   ├── js/
│
└── uploads/


⚙️ How It Works
Upload resumes
Provide job description
System extracts and processes text
Calculates:
Keyword match
Semantic similarity
Generates final score
Displays ranked candidates


🚀 Installation & Setup
1. Clone the repository
git clone https://github.com/payalmane1908/ai-resume-screening-system.git
cd ai-resume-screening-system
2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
3. Install dependencies
pip install -r requirements.txt
4. Run the app
python app.py
5. Open in browser
http://127.0.0.1:5000/

📸 Screenshots

![Dashboard](c:\Users\Nikhil\Pictures\Screenshots\Screenshot 2026-03-31 220626.png)
![Results](c:\Users\Nikhil\Pictures\Screenshots\Screenshot 2026-03-31 220647.png)



🔥 Future Enhancements
📄 PDF resume parsing
📊 Advanced analytics dashboard
🤖 AI feedback on resume improvement
☁️ Cloud deployment (AWS/GCP)
📥 Downloadable candidate reports

🎯 Use Cases
Recruitment automation
HR candidate filtering
Resume ranking systems
Hiring workflow optimization


👤 Author

Payal Mane
🔗 GitHub: https://github.com/payalmane1908