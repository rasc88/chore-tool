# chore-tool

Web app for managing shared household chores — visibility into what's done, what's pending, and who owns what, for a household of full-access members plus admins. See [_docs/_plan.md](_docs/_plan.md) for the full scope and [_docs/backlog.md](_docs/backlog.md) for the implementation breakdown.

Chores support fixed, rotating, or self-claim ("pool") assignment, and recur on a fixed interval, specific weekdays, or after the previous instance is completed. Overdue or unclaimed chores are flagged and escalate to admins. Everyone sees the same status board, history log, and ownership map — no gamification, no approval workflow.

Built with Django, managed with [uv](https://docs.astral.sh/uv/).

## Setup

```
uv sync
```

Installs Django and all dependencies into `.venv/`.

## Commands

Run from the repo root:

| Command | What it does |
|---|---|
| `uv run python manage.py runserver` | Start the dev server at `http://127.0.0.1:8000/` |
| `uv run python manage.py migrate` | Apply database migrations |
| `uv run python manage.py makemigrations` | Generate new migrations after a model change |
| `uv run python manage.py test chores_app` | Run the full test suite |
| `uv run python manage.py seed_demo_data` | Reset and populate the DB with demo data (household, users, chores) for manual testing |
| `uv run python manage.py createsuperuser` | Create an account that can log into `/admin/` |
| `uv add <package>` | Add a new dependency |

## Demo data

`seed_demo_data` creates a household with 5 users — `alice` and `bob` as admins, `charlie`, `dana`, and `erin` as regular members — all with password `demo1234`, plus a mix of chores and chore instances in various states (pending, done, overdue, unclaimed).

Log in at `/accounts/login/` to use the app, or `/admin/` (as `alice` or `bob`) to manage chores directly.
