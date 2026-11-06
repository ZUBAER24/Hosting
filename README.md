# ERROR x HOSTING
Premium dark multi-user hosting control panel starter: FastAPI, signed sessions, bcrypt password hashing, SQLite, project CRUD, responsive UI.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000

## Free hosting reality
A free Render/Railway deployment cannot guarantee 24/7 execution of arbitrary user code. Render free services may sleep; Railway free usage is credit/trial based. Use a separate always-on Docker-capable worker for actual Python/Node processes. This starter provides the control panel and a safe integration boundary, not a production PaaS.

For production: use PostgreSQL with persistent storage, HTTPS, a strong SECRET_KEY, CSRF protection, email verification, rate limits, quotas, audit logs, and a private isolated worker. Never expose the Docker socket or worker API publicly. See worker/README.md.
