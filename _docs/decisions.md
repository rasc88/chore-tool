# Decisions

Calls made while building the app. They are settled here so issues stop
re-litigating them.

Where this file and `_docs/outdated/` disagree, this file wins.

## 1. Recurrence rule lives on `Chore`, not a separate model

`recurrence_type`, `interval_days`, and `weekdays` are plain fields on
`Chore`. There is no `RecurrenceRule` model.

Why: the plan allowed either shape ("fields on Chore" or a separate
model). A chore has exactly one recurrence rule for its whole life, so a
separate model would only add a join for no behavior gained.

## 2. Single household, no `Household` FK on `Chore`

`Household` exists (and `Profile` links a user to one), but `Chore` does
not reference it.

Why: the plan describes one household of 3-5 members plus a helper, not a
multi-tenant product. Adding a household scope to every chore query would
be speculative generality for a requirement that was never asked for.

Cost accepted: this app cannot serve two households from one deployment
without a real migration later. That is fine for what was asked.

## 3. Assignment and instance generation are one call

`Chore.create_next_instance()` resolves both the due date and the
assignee in the same method, dispatching on `assignment_type`
(fixed/rotating/pool).

Why: a chore instance without an assignment decision isn't in a valid
state to hand to a view — splitting date computation and assignment into
two calls would just let a caller forget the second one.

## 4. Rotation advances by index, not by popping a queue

`Chore.rotation_next_index` is a position into `rotation_members`
(ordered by `id`), advanced modulo the member count on each assignment.

Why: an index survives `rotation_members` changing between turns (someone
added or removed from the pool) without losing the rotation's place. A
popped queue would need to be rebuilt every time membership changed.

## 5. Overdue/unclaimed flags are computed, never stored

`ChoreInstance.is_overdue`/`is_unclaimed` are properties evaluated at read
time from `status`/`due_date`/`assigned_to`. `ChoreInstance.STATUS_OVERDUE`
exists as a schema choice but no code path ever sets it.

Why: a stored status needs something to transition it — a cron job or a
save-time check that runs even when nobody looks at the instance. A
computed property is always correct with no background process, at the
cost of recomputing on every read (cheap at this scale).

Do not add a job that writes `STATUS_OVERDUE` without first removing this
decision, since the two approaches disagree about what "overdue" means at
rest.

## 6. Notifications are a live query, not a stored model

The "flagged count" badge (`chores_app/context_processors.py`) is
`ChoreInstance.objects.flagged().count()`, computed on every request. There
is no `Notification` model, no read/unread state.

Why: the plan explicitly asks for in-app-only, no gamification, no extra
state. A stored notification adds a second thing that can drift from the
data it's supposed to summarize.

## 7. Two separate "admin" concepts, not one

Django's own `is_staff`/`is_superuser` gate `/admin/` login. A separate
`Profile.is_admin` flag gates add/change/delete on `Chore`/`ChoreInstance`
inside that admin, via `AdminOnlyModelAdmin` in `chores_app/admin.py`.
`Household`/`Profile` stay on Django's plain admin defaults.

Why: the plan's "admin" is a household role (a parent), not a Django
deployment operator. Conflating the two would mean every household admin
needs Django's `is_staff`, which is a bigger grant than "can edit chores."

## 8. Chore authoring happens through Django admin, not a custom view

There is no custom create/edit page for `Chore`. Admins use `/admin/`.

Why: the plan's views section only lists status board / history /
ownership map as member-facing screens — nothing describes a bespoke
authoring UI, and Django admin already does CRUD + permission-gating for
free once #7 is in place. Building a parallel form would duplicate what
admin gives us.

Supersedes: nothing in `_docs/outdated/architecture.md` — that file leaves
authoring UI unspecified.

## 9. `uv` for dependency management, not plain `venv`/`pip`

The project was set up with plain `venv`, then migrated to `uv`
(`pyproject.toml`, `uv.lock`, `.venv/`) partway through, at the user's
request, once `pip`/`venv` friction came up.

Why: `uv run <cmd>` manages the interpreter and lockfile together, so
there's one fewer thing (`source venv/bin/activate`, remembering to
reinstall after a `requirements.txt` change) to get out of sync.

## 10. Project renamed `chore_tool` -> `chores_config`, app `chores` -> `chores_app`, URL namespace left as `chores`

The Django project package and the app package were renamed for clarity
(project vs. app was hard to tell apart when both were near-synonyms of
the product name). The URL namespace in `chores_app/urls.py`
(`app_name = 'chores'`) was deliberately **not** renamed to match.

Why: a URL namespace is a template-facing label
(`{% url 'chores:status_board' %}`), not a Python import path — renaming
it would mean touching every template for no functional gain, since
nothing breaks by the namespace and the package name differing.

## 11. Tests live in a `chores_app/tests/` package, one file per feature area

Not a single `tests.py`. Files: `test_foundation`, `test_core_models`,
`test_assignment`, `test_completion`, `test_conflict`, `test_views`,
`test_admin_permissions`, `test_seed_command`.

Why: the app was built in exactly these increments (one backlog task per
area), and each area's tests were written independently against the code
as it landed. One file per area keeps that mapping visible and lets
someone touch one area's tests without conflicting with another's.

## 12. `seed_demo_data` clears and recreates its own data, not additive

Running it twice produces the same household/users/chores/instances, not
duplicates - it deletes its own previously-seeded household (cascading
through chores, instances, profiles, users) before reseeding.

Why: a repeatable dev command that silently accumulates rows on every run
makes manual testing unreliable ("is this the 1st or 5th seed?"). It only
ever touches its own named demo household, never other data.
