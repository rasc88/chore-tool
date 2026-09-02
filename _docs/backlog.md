# Backlog

Derived from [_plan.md](_plan.md). Ordered roughly by dependency.

## 1. Foundation
- [ ] `User` model: extend Django's built-in auth user (or a profile model) with an `is_admin` flag and household membership
- [ ] Django admin registration for all models below, for quick data inspection during development

## 2. Core models
- [ ] `Chore` model: name, description, priority (low/medium/high), recurrence type, created_by (admin)
- [ ] `RecurrenceRule` (or fields on `Chore`): fixed interval, specific weekdays, or deadline-based (next instance on completion)
- [ ] `ChoreInstance` model: one occurrence of a chore, with due date, status (pending/done/overdue), assigned_to (nullable for pool chores), completed_by, completed_at
- [ ] Logic to generate the next `ChoreInstance` per recurrence rule (management command or signal on completion for deadline-based chores)

## 3. Assignment
- [ ] Fixed assignment: chore always assigned to the same person
- [ ] Auto-rotation: assign to next person in a rotation list each time a new instance is generated
- [ ] Pool/self-claim: instance starts unassigned, any member can claim it

## 4. Completion & accountability
- [ ] "Mark as done" action (self-report, no approval step) that updates `ChoreInstance` and writes a history entry
- [ ] `HistoryLog` model (or query over completed instances) for the history view — who did what, when

## 5. Conflict handling
- [ ] Passive flag: mark instances as overdue/unclaimed based on due date vs. today
- [ ] Escalation: surface flagged instances older than a threshold to admins for reassignment

## 6. Views (all members see everything)
- [ ] Status board: today's pending/done/overdue instances
- [ ] History log: chronological list of completions
- [ ] Ownership map: chores grouped by assigned person
- [ ] In-app notifications: simple list/badge for overdue or newly-assigned chores (no email/push)

## 7. Auth & access
- [ ] Login/logout with individual accounts (Django auth)
- [ ] Admin-only permission checks on chore create/edit (no role-based view restrictions otherwise)

## 8. Polish
- [ ] Basic responsive templates (mobile + desktop browser)
- [ ] Seed/fixture data for manual testing with 3-5 users
