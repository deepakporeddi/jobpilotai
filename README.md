# JobPilot AI

A multi-user AI-assisted job application workspace. The first milestone is a generic resume intelligence workflow: each account can upload its own PDF or Word DOCX resume, extract a candidate profile, review/edit that profile, and later tailor it to individual job descriptions.

## Principles

- No hardcoded candidate, employer, skill set, resume, job title, country, or template.
- Each user's resumes are scoped to their authenticated account.
- The uploaded source document is preserved; profile edits update extracted structured data, not the source file.
- Extraction is conservative. Unknown information stays blank and users review the extracted data.
- Never invent candidate experience, metrics, dates, employers, or qualifications.

## Stack

- Frontend: React, TypeScript, Vite
- Backend: Django REST Framework
- Database: SQLite for local quick-start; PostgreSQL when `DATABASE_URL` is configured
- Resume extraction: PyMuPDF (PDF) and python-docx (DOCX)
- Authentication: Django REST Framework token authentication

## Current functionality

- Account registration and login
- Authenticated, user-scoped resume library
- PDF and DOCX uploads (10 MB maximum)
- File extension and basic file-signature validation
- Text extraction from text-based PDFs and DOCX paragraphs/tables
- Conservative profile extraction for contact details and common resume sections
- Profile review and editable JSON profile
- Original resume retained separately from the editable extracted profile

Scanned/image-only PDFs are detected and reported; OCR is not implemented yet. The initial profile extractor is deliberately heuristic and should be reviewed by the user. LLM-based structured extraction, job description analysis, resume generation, and exports are subsequent milestones.

## Local development

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py makemigrations resumes
python manage.py migrate
python manage.py runserver
```

### Frontend

In another terminal:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The frontend runs at http://localhost:5173 and the API at http://127.0.0.1:8000/api.

## API

- `POST /api/auth/register/` — create an account; returns a token
- `POST /api/auth/login/` — log in; returns a token
- `GET /api/resumes/` — list the authenticated user's resumes
- `POST /api/resumes/` — upload a PDF or DOCX as multipart field `file`
- `GET /api/resumes/{id}/profile/` — retrieve extracted profile
- `PATCH /api/resumes/{id}/profile/` — save reviewed profile JSON

Send `Authorization: Token <token>` for protected endpoints.

## Next milestones

1. Better structured extraction and editable field-level profile review.
2. Job description ingestion and requirement analysis.
3. Evidence-grounded, job-specific resume generation.
4. DOCX/PDF export and transparent change reports.
5. Job discovery, application tracking, and recruiter outreach.

For production deployment, set a strong `DJANGO_SECRET_KEY`, disable debug mode, configure PostgreSQL, HTTPS, secure media storage, and appropriate upload scanning and retention policies.
