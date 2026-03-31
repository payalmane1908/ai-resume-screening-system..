# Automated Resume Screening System

Flask-based ATS platform for bulk resume ingestion, NLP skill extraction, semantic JD matching, weighted ranking, and interactive analytics.

## Run

1. Create and activate virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Start app:
   - `python app.py`
4. Open:
   - `http://127.0.0.1:5000`

## Features

- Bulk upload: PDF, DOCX, CSV
- Skill extraction with synonym support
- Semantic scoring using `sentence-transformers`
- Weighted scoring (keyword + semantic + experience)
- Dashboard with filters, status updates, and charts
- Export to Excel/PDF
- Login/registration with hashed passwords
