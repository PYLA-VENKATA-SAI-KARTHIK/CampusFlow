# CampusFlow

College Placement Management & Opportunity Assurance Platform.

## Architecture
- **Frontend**: React + TypeScript + Vite + TailwindCSS + Zustand
- **Backend**: FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + Alembic
- **Pattern**: Modular Monolith

## Prerequisites
- Node.js 18+
- Python 3.9+
- PostgreSQL 15+

## Local Setup

### 1. Database
1. Create a local PostgreSQL database named `campusflow_dev` and a test database named `campusflow_test`.
2. Update the credentials in `backend/.env`.

### 2. Backend
1. `cd backend`
2. Create virtual environment: `python -m venv venv`
3. Activate it: `.\venv\Scripts\Activate.ps1` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy configuration: `cp .env.example .env`
6. Run migrations to initialize schema and seed branches: `alembic upgrade head`
7. Start server: `fastapi run app/main.py --reload`
   API runs at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

#### Running Tests
```bash
cd backend
pytest -v
```

### 3. Frontend
1. `cd frontend`
2. Install dependencies: `npm install`
3. Copy configuration: `cp .env.example .env.local`
4. Start dev server: `npm run dev`
   App runs at `http://localhost:5173`.

## Security Notes
- JWT uses RS256 with key rotation support via JWKS.
- Development keys are safe to commit or keep in `.env.example`, but **NEVER** use them in production.
- Always generate new secure RSA keys for production.
- Emails are mocked in development. Change `EMAIL_PROVIDER=sendgrid` and provide an API key in production.
