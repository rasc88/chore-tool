# chore-tool

Web app for managing shared household chores — visibility into what's done, what's pending, and who owns what, for a household of full-access members plus admins. See [_docs/outdated/_plan.md](_docs/outdated/_plan.md) for the full scope and [_docs/backlog.md](_docs/backlog.md) for the implementation breakdown.

Chores support fixed, rotating, or self-claim ("pool") assignment, and recur on a fixed interval, specific weekdays, or after the previous instance is completed. Overdue or unclaimed chores are flagged and escalate to admins. Everyone sees the same status board, history log, and ownership map — no gamification, no approval workflow.

## Requirements

- Python >= 3.12
- SQLite — bundled with Python, nothing separate to install or run
- [uv](https://docs.astral.sh/uv/) for dependency management

## Getting started

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

The app is served at `http://127.0.0.1:8000/`. There's no login yet at this point — either `uv run python manage.py createsuperuser` to make your own account, or run `uv run python manage.py seed_demo_data` for a ready-made household (see [Demo data](#demo-data) below).

## Commands

Run from the repo root:

| Command | What it does |
|---|---|
| `uv run python manage.py runserver` | Start the dev server |
| `uv run python manage.py migrate` | Apply database migrations |
| `uv run python manage.py makemigrations` | Generate new migrations after a model change |
| `uv run python manage.py test chores_app` | Run the full test suite |
| `uv run python manage.py seed_demo_data` | Reset and populate the DB with demo data (household, users, chores) for manual testing |
| `uv run python manage.py createsuperuser` | Create an account that can log into `/admin/` |
| `uv add <package>` | Add a new dependency |

No linter is configured in this project.

## Accounts

There's no email backend and no self-serve password reset. If someone forgets their password, an admin resets it directly:

```bash
uv run python manage.py changepassword <username>
```

## Demo data

`seed_demo_data` is deterministic and idempotent — running it again clears and rebuilds the same household from scratch rather than accumulating duplicates. It creates one household ("The Demo Household") with 5 users, all sharing the password **`demo1234`**:

| username | role | notes |
|---|---|---|
| `alice` | admin | created most of the demo chores; assigned to today's "Wash dishes" |
| `bob` | admin | created and is fixed assignee for "Mow the lawn" (deadline-based) |
| `charlie` | member | fixed assignee for "Take out trash"; rotates on "Wash dishes" |
| `dana` | member | rotates on "Wash dishes" and "Vacuum living room" |
| `erin` | member | rotates on "Vacuum living room"; completed "Clean kitchen" yesterday |

Plus 6 chores covering every assignment/recurrence combination (fixed, rotating, pool; interval, weekdays, deadline) and 12 chore instances spanning pending, done, overdue, and unclaimed states — so the status board, history log, and ownership map all have something to show immediately.

Log in at `/accounts/login/` to use the app, or `/admin/` (as `alice` or `bob`) to manage chores directly.

## Contributing / agent-driven workflow

New work is filed as a GitHub issue and picked up through a groomed
PM → Engineer → QA pass (an agent or a person can fill any of those
roles):

- [`AGENTS.md`](AGENTS.md) — architecture, tech stack, and commands
  (Claude Code reads this as `CLAUDE.md`, which just imports it)
- [`_docs/process.md`](_docs/process.md) — how issues move from filed to
  merged: labels, worktrees, waves, integration
- [`_docs/decisions.md`](_docs/decisions.md) — the calls already made,
  with reasons; read before reopening one
- [`_docs/team/`](_docs/team/) — the PM, engineer, and QA role
  definitions, and [`_docs/task-template.md`](_docs/task-template.md) for
  the groomed issue format (Goal / Acceptance criteria / Out of scope /
  Constraints)

Example, using Claude Code: file a rough issue on GitHub (it doesn't need
the groomed format — that's the PM's job), then let it self-pace through
the backlog:

```
/goal work through the backlog
```

This finds each open issue, grooms it (PM), implements it (Engineer),
verifies it against the acceptance criteria and posts a PASS/FAIL
(QA), then closes it and moves to the next one — stopping once the
backlog is empty. Point it at one specific issue instead by asking
directly, e.g. "groom and implement issue #4".
