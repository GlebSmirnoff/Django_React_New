# 🚀 Project Quickstart — Django + PostgreSQL + Vite/React (pnpm)

This doc is a practical checklist to clone and run the project on any machine. Keep it in `Doc/QUICKSTART.md`.

---

## Prerequisites
- **Windows 10/11** (PowerShell) — commands below use PowerShell.
- **Python 3.11+** (we used 3.13).
- **Node.js 18+** (we used 22.x) with **pnpm** (`corepack enable`).
- **PostgreSQL 16** (running on `localhost`, port **5433** in our setup).

> If your Postgres runs on 5432 — just change the port in `.env`.

---

## 1) Clone & create virtual env
```powershell
git clone <YOUR_REPO_URL> project
cd project

# create venv (ignored by git)
python -m venv .venv
& .\.venv\Scripts\Activate.ps1

# install backend deps
python -m pip install --upgrade pip
pip install -r requirements.txt
```
> If PyCharm is used: set interpreter to `.venv\Scripts\python.exe`.

---

## 2) PostgreSQL: create DB & user (first time on a machine)
Open PowerShell and run psql (adjust version/path if needed):
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -h localhost -p 5433
```
Then in `psql`:
```sql
CREATE DATABASE autobuy_db ENCODING 'UTF8' TEMPLATE template0;
CREATE USER autobuy_user WITH PASSWORD 'change_me_strong';
ALTER DATABASE autobuy_db OWNER TO autobuy_user;
\q
```

---

## 3) Environment variables
Copy `.env.example` to `.env` and adjust values:
```powershell
Copy-Item .env.example .env
# then edit .env and set your secrets/ports
```

**`.env` variables used by Django** (loaded in `settings.py` via `python-dotenv`):
```
POSTGRES_DB=autobuy_db
POSTGRES_USER=autobuy_user
POSTGRES_PASSWORD=change_me_strong
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
```

> Do **NOT** commit `.env`. Only commit `.env.example`.

---

## 4) Django: migrate & run
```powershell
cd autobuy
python manage.py migrate
python manage.py createsuperuser   # optional
python manage.py runserver
```
Open http://127.0.0.1:8000/

---

## 5) Frontend: install & run (pnpm)
In a new terminal:
```powershell
cd frontend

# enable pnpm once per machine
corepack enable
corepack prepare pnpm@latest --activate

pnpm i

# If pnpm 10 shows "Ignored build scripts: esbuild":
#   pnpm approve-builds esbuild @esbuild/win32-x64
#   pnpm rebuild

pnpm dev
```
Open http://localhost:5173/

The dev server proxies `/api` to `http://127.0.0.1:8000` (see `vite.config.ts`).

---

## 6) Project structure (expected)
```
project/
  autobuy/
    manage.py
    autobuy/          # Django settings/urls
    assistant/        # your app(s)
  frontend/
    src/
    index.html
    vite.config.ts
    package.json
    pnpm-lock.yaml
  Doc/
    QUICKSTART.md
  requirements.txt
  .env.example
  .gitignore
```
> `.venv/`, real `.env`, `node_modules/`, build artifacts are ignored by git.

---

## 7) How to push to GitHub
```powershell
git init
git add .
git commit -m "Initial skeleton"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo>.git
git push -u origin main
```

---

## 8) Troubleshooting (common)
- **`ModuleNotFoundError: No module named 'src'`** — clean env var `DJANGO_SETTINGS_MODULE`; it must be `autobuy.settings`. In PowerShell:
  ```powershell
  Remove-Item Env:DJANGO_SETTINGS_MODULE -ErrorAction SilentlyContinue
  ```
  Also check **Run/Debug** configs (no `src.settings`).

- **`python-dotenv could not parse statement at line 1`** — your `.env` contains extra text. Keep only `KEY=VALUE` pairs.

- **`could not connect to server`** — check Postgres is running and port in `.env` is correct (5433/5432). Test:
  ```powershell
  & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U autobuy_user -h localhost -p 5433 -d autobuy_db -c "select 1;"
  ```

- **pnpm + esbuild approval** (pnpm v10+):
  ```powershell
  pnpm config get ignored-built-dependencies --location project
  pnpm approve-builds esbuild @esbuild/win32-x64
  pnpm rebuild
  ```

- **Windows PowerShell execution policy** (to activate venv):
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  & .\.venv\Scripts\Activate.ps1
  ```

---

## 9) Production note
For production, switch to Postgres (already supported via `.env`), set `DEBUG=False`, set `ALLOWED_HOSTS`, collect static, and use a proper WSGI/ASGI server (gunicorn/uvicorn) behind Nginx/Reverse proxy. Not covered here, this is a dev quickstart.
