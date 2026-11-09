# DocForensics

DocForensics is an AI-assisted document forensics platform for organizing investigations, extracting information from PDFs and images, comparing documents, reviewing potential inconsistencies, keeping an investigator journal, and generating PDF dossiers.

Automated results are observations for human review; they are not proof of fraud or document tampering.

## Features

- Create investigations and upload PDF or image evidence.
- Extract text and common fields with OCR, then classify documents.
- Run visual and contextual checks and compare fields across documents.
- Track findings, investigator notes, and audit activity.
- Preview evidence and generate investigation dossiers as PDFs.

## Run locally

### Backend

Requires Python and Tesseract OCR installed on the system.

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set a private `SECRET_KEY` in `backend/.env` before starting the API:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the printed value into `SECRET_KEY` in the environment file. Set `GOOGLE_CLIENT_ID` if Google sign-in is enabled. `LLM_API_KEY` is optional; the application has a local explanation fallback.

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

In another terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Set `VITE_GOOGLE_CLIENT_ID` in `frontend/.env` if Google sign-in is enabled. Open the Vite URL printed in the terminal (normally `http://localhost:5173`).

Local environment files, databases, uploads, and generated dossiers are excluded from Git.
