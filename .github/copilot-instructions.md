# GitHub Copilot Instructions for Hot_Mall (肥猫商城)

Purpose: Short, actionable guidance so an AI coding agent is productive immediately in this Django + Celery + Haystack project.

## Big picture 🏗️
- This is a Django e-commerce monolith (apps under `hot_mall/apps/`) with web views, search, payments, and async tasks.
- Major components:
  - Web: Django apps (e.g., `goods`, `users`, `orders`, `payment`, `contents`) located in `hot_mall/apps/` (sys.path is extended in `hot_mall/settings/dev.py`).
  - Async: Celery tasks live in `celery_tasks/` (entry: `celery_tasks/main.py`, config: `celery_tasks/config.py`).
  - Search: Haystack with Whoosh (index in `hot_mall/whoosh_index/`, example: `hot_mall/apps/goods/search_indexes.py`).
  - Payments: Alipay integration configured in `hot_mall/settings/dev.py` (`django-alipay`).

## Where to look first (high-value files) 🔍
- `manage.py` — default settings module: `hot_mall.settings.dev` (so environment assumes dev config).
- `hot_mall/settings/dev.py` — DB, cache (Redis), mail, logging, Haystack, Celery expectations.
- `celery_tasks/main.py` and `celery_tasks/config.py` — how Celery app is created and broker configured.
- `hot_mall/utils/models.py` — `BaseModel` pattern (adds `create_time`/`update_time`).
- `hot_mall/utils/jinja2_env.py` — Jinja2 environment, available globals (`static`, `url`).
- `hot_mall/apps/users/*` — custom user model (`users.User`) and auth backend (`users.utils.UsernameModelBackend`) — login accepts username or mobile.

## Developer workflows & commands (copy-paste) ▶️
- Setup virtualenv, install deps: `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- DB & migrations:
  - `python manage.py makemigrations`
  - `python manage.py migrate`
  - `python manage.py createsuperuser`
- Run dev server: `python manage.py runserver` (defaults to `hot_mall.settings.dev` via `manage.py`).
- Static files: `python manage.py collectstatic --noinput` (if needed for deployment).
- Celery (requires Redis running):
  - Start Redis: `redis-server` (or use your system's redis service / Docker)
  - Start worker: `celery -A celery_tasks.main worker -l info`
  - (Optional) Start Flower: `flower -A celery_tasks.main --port=5555`
- Haystack/Whoosh index:
  - Rebuild: `python manage.py rebuild_index --noinput` or `python manage.py update_index` (Haystack commands).
- Tests: `python manage.py test` or `python manage.py test <app>` (uses Django test runner).

## Project-specific conventions & gotchas ⚠️
- App imports use top-level app names because `sys.path` is modified in `dev.py` (e.g., use `from goods.models import SKU`).
- Custom user model: `AUTH_USER_MODEL = 'users.User'`; authentication backend supports username or phone number (see `users.utils.get_user_by_account`).
- Most model classes inherit from `BaseModel` (adds `create_time`/`update_time` fields automatically).
- Templates use Jinja2 engine with custom environment providing `static` and `url` globals, plus `add_class` filter for form fields.
- Redis is used for multiple purposes (cache/ session/verify_code/ carts) — see `CACHES` in `hot_mall/settings/dev.py` and Celery broker in `celery_tasks/config.py` (`redis://127.0.0.1/10`).
- Whoosh engine requires `jieba` for Chinese tokenization (see `requirements.txt` includes `jieba`).
- Logging writes to `logs/fatcat.log` (path configured in `dev.py`). Check this file for server-side errors when debugging.
- Sensitive defaults: `dev.py` contains hard-coded DB and email credentials — treat as dev-only and avoid exposing secrets.

## How to extend / where to make common changes 🛠️
- Add a new Django app: create under `hot_mall/apps/`, it will be importable as a top-level package.
- Add a new Celery task: add file under `celery_tasks/<feature>/tasks.py`, import or ensure autodiscovery (e.g., `celery_tasks.main` uses `autodiscover_tasks(['celery_tasks.email'])` — follow that pattern).
- Add search fields: create or update `search_indexes.py` under the app (example: `hot_mall/apps/goods/search_indexes.py`). Haystack is configured with real-time signals.

## Examples (copy into PR description or patch) 💡
- To add a Celery email task:
  - `celery_tasks/email/tasks.py` — use `from celery_tasks.main import celery_app` and annotate with `@celery_app.task(...)` (see existing `send_verify_email`).
- To lookup code handling email verification: `hot_mall/apps/users/utils.py` (`generate_verify_email_url`, `check_verify_email_token`).

## Tests & CI notes
- No CI configs discovered in repo (no `.github/workflows/` files). Use `python manage.py test` locally. If adding CI, ensure Redis and MySQL (or SQLite fallback) are available in job environment.

## Quick reference (file map)
- Project root: `manage.py`, `requirements.txt`, `db.sqlite3` (committed example DB)
- Apps: `hot_mall/apps/{users,goods,orders,payment,contents,...}`
- Celery: `celery_tasks/{main.py,config.py,email/tasks.py}`
- Settings: `hot_mall/settings/{dev.py,prod.py}`
- Search index: `hot_mall/whoosh_index/`, `hot_mall/apps/goods/search_indexes.py`

---
If anything here is unclear or you want more examples (e.g., common PR templates, typical bugfix examples, or how to ramp new contributors), tell me which areas to expand or any local practices you'd like captured and I'll iterate. ✅
