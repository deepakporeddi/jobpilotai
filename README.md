# JobPilot AI

AI-assisted job application workspace. The first milestone focuses on resume intelligence: upload a master resume, extract a structured candidate profile, analyze a job description, and generate a job-specific resume with a transparent change report.

## Architecture

- `backend/`: Django REST Framework API
- `frontend/`: React + TypeScript + Vite client
- PostgreSQL: application data
- Redis + Celery: background processing (introduced as the workflow grows)
- Resume parsing: PyMuPDF and python-docx

The initial repository scaffold establishes the API and frontend foundations. Resume tailoring and document export will be added in the next implementation steps.

## Local development

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The API is available at http://127.0.0.1:8000/api/ and the Vite app at http://localhost:5173.

## Current status

- [x] Initial project structure
- [x] Resume upload API foundation
- [ ] PDF/DOCX text extraction and profile review
- [ ] Job description analysis
- [ ] Evidence-grounded resume tailoring
- [ ] DOCX/PDF export and change report

Never invent candidate experience, metrics, dates, employers, or qualifications. Generated content must be traceable to the candidate's source material and require user review before use.
