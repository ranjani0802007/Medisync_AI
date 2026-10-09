# MediSync AI (Django backend)

Privacy-first healthcare collaboration prototype with a Django backend. Accounts, doctors, cases, opinions, timelines and privacy logs are saved in a SQLite database, so refreshing the page keeps your data.

## Run on Windows

Open Command Prompt in this folder (the one with `manage.py`):

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations core
python manage.py migrate
python manage.py runserver
```

Then open http://127.0.0.1:8000 in Chrome or Edge.

Optional: `python manage.py createsuperuser`, then open http://127.0.0.1:8000/admin/ to see Doctors, Cases and logs.

## How it is connected

- `core/models.py`: Doctor, Case (full de-identified case as JSON) and KV (privacy logs, case counter)
- `core/views.py`: JSON API at `/api/` (register, login, logout, demo sign-in, state, sync)
- `frontend/static/js/app.js`: signs in through the API, loads state on every refresh and after each action saves changes back (`/api/sync/`)
- First sign-in fills the empty database with the demo doctors and cases
- Session login: refresh keeps you signed in

## Demo sign-in

The Doctor, Admin and Specialist buttons work because `DEMO_MODE = True` in `medisync/settings.py`. Set it to `False` for real use. Registered doctors sign in with their email and password.

## Limits

- The same data is shared by all users and the last save wins. A production version needs per-case permissions and per-row API calls.
- CSRF protection is switched off on the API views for simplicity.
- Doctor verification, PII detection and risk scoring are rule-based simulations. Do not use real patient data.
- PDF and Word reading use CDN libraries, so the page needs internet access.
