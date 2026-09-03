# Backlog

Derived from [_plan.md](outdated/_plan.md). Ordered roughly by dependency.

All 8 tasks below are implemented and covered by the test suite
(`uv run python manage.py test chores_app`, 69 tests). See `AGENTS.md`
for how each one actually landed, and `_docs/decisions.md` for the calls
made along the way (e.g. recurrence fields on `Chore` instead of a
separate `RecurrenceRule` model, no separate `HistoryLog` model).

## 1. Foundation
- [x] `User` model: extend Django's built-in auth user (or a profile model) with an `is_admin` flag and household membership
- [x] Django admin registration for all models below, for quick data inspection during development

## 2. Core models
- [x] `Chore` model: name, description, priority (low/medium/high), recurrence type, created_by (admin)
- [x] `RecurrenceRule` (or fields on `Chore`): fixed interval, specific weekdays, or deadline-based (next instance on completion)
- [x] `ChoreInstance` model: one occurrence of a chore, with due date, status (pending/done/overdue), assigned_to (nullable for pool chores), completed_by, completed_at
- [x] Logic to generate the next `ChoreInstance` per recurrence rule (management command or signal on completion for deadline-based chores)

## 3. Assignment
- [x] Fixed assignment: chore always assigned to the same person
- [x] Auto-rotation: assign to next person in a rotation list each time a new instance is generated
- [x] Pool/self-claim: instance starts unassigned, any member can claim it

## 4. Completion & accountability
- [x] "Mark as done" action (self-report, no approval step) that updates `ChoreInstance` and writes a history entry
- [x] `HistoryLog` model (or query over completed instances) for the history view — who did what, when

## 5. Conflict handling
- [x] Passive flag: mark instances as overdue/unclaimed based on due date vs. today
- [x] Escalation: surface flagged instances older than a threshold to admins for reassignment

## 6. Views (all members see everything)
- [x] Status board: today's pending/done/overdue instances
- [x] History log: chronological list of completions
- [x] Ownership map: chores grouped by assigned person
- [x] In-app notifications: simple list/badge for overdue or newly-assigned chores (no email/push)

## 7. Auth & access
- [x] Login/logout with individual accounts (Django auth)
- [x] Admin-only permission checks on chore create/edit (no role-based view restrictions otherwise)

## 8. Polish
- [x] Basic responsive templates (mobile + desktop browser)
- [x] Seed/fixture data for manual testing with 3-5 users
