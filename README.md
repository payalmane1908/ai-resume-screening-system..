# 🤖 AI Resume Screening System

A production-ready AI-powered Applicant Tracking System (ATS) that automates resume screening using NLP, semantic matching, and explainable AI to help recruiters make faster and smarter hiring decisions.

---

## 🚀 Overview

Traditional resume screening is time-consuming and inefficient.  
This system leverages **Artificial Intelligence + NLP + Semantic Matching** to automatically analyze, rank, and explain candidate suitability for a given job role.

---

## ✨ Key Features

### 🧠 AI-Powered Screening
- NLP-based resume parsing & skill extraction  
- Semantic similarity using Sentence Transformers  
- Weighted scoring (skills + experience + semantic match)

---

### 🔍 Explainable AI (XAI)
- Understand **why a candidate is selected**
- Shows:
  - ✅ Strengths
  - ❌ Weaknesses
  - 📊 Final reasoning
- Also includes **“Why Not Selected”** insights

---

### 📊 Advanced Analytics Dashboard
- 📈 Score Distribution Chart  
- 🥧 Skill Match Pie Chart  
- 📊 Top Candidates Visualization  
- Real-time filtering & search  

---

### 🎯 Smart Recruiter Tools
- 🥇 Top Candidate Highlight  
- 🟢 Status Pills (Selected / Rejected / Pending)  
- 🔎 Candidate Search & Filtering  
- 🆚 Candidate Comparison  

---

### 📄 AI Report Generation
- Download candidate evaluation reports (PDF)
- Includes:
  - Score
  - Strengths & Weaknesses
  - AI Explanation

---

### 🧬 Candidate Insights
- Skill match percentage  
- Missing skills  
- Experience gap analysis  
- AI confidence score  

---

### 📌 Job Description Intelligence
- Extracts:
  - Required skills  
  - Experience level  
  - Role category  

---

### ⏳ Real-time Processing Experience
- Step-based progress:
  - Parsing resumes  
  - Extracting skills  
  - AI matching  
- Smooth loading animations  

---

### 🎨 Premium UI/UX
- Glassmorphism design  
- Smooth animations & hover effects  
- Gradient buttons  
- Clean typography (Inter font)  
- Fully responsive layout  

---

## 🧠 How It Works

```mermaid
graph TD
A[Upload Resumes] --> B[Text Extraction]
B --> C[Skill Extraction]
C --> D[Semantic Matching]
D --> E[Score Calculation]
E --> F[Explainable AI]
F --> G[Ranking & Dashboard]

--------------------------------------------------------------------------------------------------------------
🛠 Tech Stack
Layer	Technology
Backend	Flask (Python)
NLP	spaCy, Sentence-Transformers
Database	SQLite
Frontend	HTML, CSS, Bootstrap, JS
Charts	Chart.js
Deployment	Docker / Render

-------------------------------------------------------------------------------------------------------------------
..INSTALLATION PROCESS..

git clone https://github.com/payalmane1908/ai-resume-screening-system.git
cd ai-resume-screening-system

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
python app.py

-----------------------------------------------------------------------------------------------------------------------

📁 Project Structure

resume-ai/
│── routes/
│── services/
│── templates/
│── static/
│── models/
│── utils/
│── uploads/
│── app.py
│── config.py
│── requirements.txt

-----------------------------------------------------------------------------------------------------------------------------

🔮 Future Enhancements
AI interview recommendation system
Resume summarization
Multi-job dashboard
Cloud storage integration
Advanced recruiter analytics

------------------------------------------------------------------------------------------------------------------------------

💡 Why This Project?

This system transforms traditional hiring by:

Reducing manual effort
Providing data-driven insights
Increasing screening accuracy
Improving recruiter productivity

---------------------------------------------------------------------------------------------------------------------------

👩‍💻 Author

Payal Mane

