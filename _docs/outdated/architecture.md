# Architecture

Current state as of the initial build. See `_docs/decisions.md` for anything
that has changed since — where the two disagree, `decisions.md` wins.

## Tech stack

- **Django 6.1**, Python >=3.12
- **uv** for dependency management and the virtualenv (`pyproject.toml` +
  `uv.lock`, `.venv/`) — run everything as `uv run python manage.py ...`,
  never a bare `python`
- **SQLite** (`db.sqlite3`), Django's default ORM, no separate database
  server
- **Django's built-in auth** (session-based login/logout via
  `django.contrib.auth.urls`) — no token/JWT auth, no third-party auth
  library
- **Server-rendered Django templates**, no separate frontend framework, no
  JS build step. One small inline `<style>` block in the base template,
  no CSS framework
- **Django's test runner** (`manage.py test`), not pytest — nothing in
  `pyproject.toml` pulls in pytest
- No linter/formatter is configured (no ruff, flake8, or black)
- No background job runner (no Celery/cron) and no email backend

## Project layout

One Django project containing one Django app:

- `chores_config/` — the project: `settings.py`, root `urls.py`,
  `wsgi.py`/`asgi.py`. No feature code lives here.
- `chores_app/` — the app: models, views, admin, templates, migrations,
  the `seed_demo_data` management command, and the test suite
  (`chores_app/tests/`, one file per feature area rather than a single
  `tests.py`).

The app's URL namespace is `chores` (`app_name = 'chores'` in
`chores_app/urls.py`), not `chores_app` — it's a label used in
`{% url 'chores:status_board' %}`, independent of the Python package name.

## Data model

- **`Household`** — just a name. `Chore` has no FK to it; the app assumes
  a single household per deployment.
- **`Profile`** — one per `User` (`OneToOneField`), links a user to a
  `Household`, and carries `is_admin` (a household-admin flag, separate
  from Django's own `is_staff`/`is_superuser`).
- **`Chore`** — the recurring template: `name`, `description`, `priority`
  (low/medium/high), `created_by`. Recurrence and assignment rules live
  directly on this model rather than in separate related models:
  - `recurrence_type` (interval / weekdays / deadline) plus
    `interval_days` or `weekdays` depending on which
  - `assignment_type` (fixed / rotating / pool) plus `fixed_assignee`,
    `rotation_members` (M2M) and `rotation_next_index`
- **`ChoreInstance`** — one dated occurrence of a `Chore`: `due_date`,
  `status` (pending/done/overdue — see Known quirks), `assigned_to`,
  `completed_by`, `completed_at`.

## Key behavior

- `Chore.create_next_instance()` computes both the due date
  (`next_due_date()`) and the assignee (`_next_assignee()`) in one call,
  dispatching on `assignment_type`. Rotating chores advance
  `rotation_next_index` into `rotation_members` ordered by `id`.
- Deadline-recurrence chores generate their next instance from
  `ChoreInstance.mark_done()` on completion. Interval/weekday chores are
  expected to be generated on some external schedule — no cron or
  management command for that exists yet.
- Overdue/unclaimed flagging is computed at read time
  (`ChoreInstance.is_overdue`/`is_unclaimed` properties, and
  `.overdue()`/`.unclaimed()`/`.flagged()`/`.escalated(days=3)` on the
  custom `ChoreInstanceQuerySet` bound as `ChoreInstance.objects`) — not a
  stored/transitioned status.
- The notifications badge (`flagged_count`) is injected into every
  template via a context processor
  (`chores_app/context_processors.py`), not a persisted model.
- Django admin gates add/change/delete on `Chore`/`ChoreInstance` behind
  `Profile.is_admin` (`chores_app/admin.py`); `Household`/`Profile` stay
  on Django's plain defaults. There is no custom create/edit view for
  chores — Django admin is the only place chores are authored.
- All app views (`chores_app/views.py`) are function-based and
  `@login_required`; no other role-based view restrictions — every
  member sees the same data.

## Known quirks worth knowing before touching this code

- `ChoreInstance.STATUS_OVERDUE` exists as a status choice but no code
  path ever sets it — overdue-ness is always derived from `is_overdue`,
  never transitioned into.
- The project package is named `chores_config` and the app `chores_app`,
  but the URL namespace and the demo/seed data both still say `chores` /
  reference the app loosely as "chores" in places — this is intentional,
  not leftover from the rename (see `_docs/decisions.md`).
