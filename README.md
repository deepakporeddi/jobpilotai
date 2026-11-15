# JobPilot AI

A multi-user AI-assisted job application workspace. Users can upload PDF or Word DOCX resumes, extract a candidate profile, review it, and run evidence-grounded resume analysis and job-description matching.

## Principles

- No hardcoded candidate, employer, skill set, resume, job title, country, or template.
- Each user's resumes and AI results are scoped to their authenticated account.
- The uploaded source document is preserved; profile edits update extracted structured data, not the source file.
- Extraction is conservative. Unknown information stays blank and users review the extracted data.
- Never invent candidate experience, metrics, dates, employers, or qualifications.

## Stack

- Frontend: React, TypeScript, Vite
- Backend: Django REST Framework
- Database: SQLite for local quick-start; PostgreSQL when `DATABASE_URL` is configured
- Resume extraction: PyMuPDF (PDF) and python-docx (DOCX)
- AI intelligence: configurable OpenAI-compatible chat-completions API; provider credentials remain on the backend
- Authentication: Django REST Framework token authentication

## Current functionality

- Account registration and login
- Authenticated, user-scoped resume library
- PDF and DOCX uploads (10 MB maximum)
- Text extraction and conservative profile extraction
- Profile review and editable JSON profile
- AI resume analysis and job-description matching
- Strict validation of AI JSON output and score ranges
- Versioned, per-resume persistence of analysis and job-match results
- Retrieval of the latest saved result after refresh
- Per-user API throttling for AI operations
- AI request usage telemetry (operation, provider/model label, latency, status and success); prompts and resume text are not copied into telemetry
- Provider credentials remain on the backend; provider error bodies are not returned to clients

Scanned/image-only PDFs are detected and reported; OCR is not implemented yet. The initial profile extractor is heuristic and should be reviewed by the user. Resume generation and exports remain future milestones.

## Local development

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
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
- `POST /api/resumes/ai/analyze/` — create a new analysis version (`{ "resume_id": 1 }`)
- `GET /api/resumes/ai/analyze/?resume_id=1` — retrieve the latest saved analysis
- `POST /api/resumes/ai/job-match/` — create a new match version (`{ "resume_id": 1, "job_description": "..." }`)
- `GET /api/resumes/ai/job-match/?resume_id=1` — retrieve the latest saved match

Send `Authorization: Token <token>` for protected endpoints. A new successful POST creates a new version; GET returns the latest version for the authenticated owner. Job descriptions are stored with their match history so users can revisit prior comparisons. Deleting a resume cascades to its AI result history and usage records associated with that resume.

## Configure AI provider

Set these values in `backend/.env` (never in the frontend `.env`):

```env
AI_PROVIDER=openai_compatible
AI_API_KEY=your-provider-api-key
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=your-enabled-model-name
AI_TIMEOUT_SECONDS=45
AI_ANALYSIS_RATE=10/hour
AI_JOB_MATCH_RATE=20/hour
```

`AI_BASE_URL` can point to an OpenAI-compatible provider or a local gateway. Non-HTTPS URLs are accepted only for localhost. Keep the API key server-side. Set `AI_PROVIDER=disabled` to turn AI features off. The API key is never sent to the frontend. Provider/model availability and pricing depend on your chosen service.

Resume text and job descriptions are sent to the configured AI provider only when the user explicitly runs an analysis or match. Saved AI results and job descriptions remain in your application database until the resume is deleted or your retention policy removes them. Configure database backups, access controls and retention/deletion policies appropriate to your users. AI outputs are suggestions, not hiring predictions; users should verify all claims.

## Production checklist

- Set a strong, unique `DJANGO_SECRET_KEY`; set `DJANGO_DEBUG=false`.
- Configure PostgreSQL, HTTPS, secure media storage, upload scanning and backups.
- Set `SECURE_SSL_REDIRECT=true` only after HTTPS and trusted reverse-proxy headers are configured correctly.
- Tune `AI_ANALYSIS_RATE`, `AI_JOB_MATCH_RATE`, and provider timeouts for your plan and expected traffic.
- Restrict who can access usage telemetry and define retention periods for uploaded resumes, stored job descriptions and AI results.
- Configure monitoring/alerting around provider failures and request latency.

## Next milestones

1. Better structured extraction and editable field-level profile review.
2. Evidence-grounded, job-specific resume generation.
3. DOCX/PDF export and transparent change reports.
4. Job discovery, application tracking, and recruiter outreach.
