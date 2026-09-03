# Household Chores Management Tool — Project Scope

## Core Purpose
Visibility + coordination for household chores. The main pain point is lack of visibility — nobody knows what's been done, what's left, or who owns what. Better visibility is meant to reduce coordination conflicts over who's doing what and when.

## Users
- 3–5 family members
- 1 external helper (cleaner/cook)
- All are **full users** with individual password-protected accounts
- **Multiple admins** (e.g., both parents) can create/edit chores; other members cannot

## Chore Creation
- Fully custom — no presets or templates
- Created/edited only by admins

## Assignment Model
- **Mix**: some chores are fixed or auto-rotated among people, others sit in a pool for self-claiming

## Recurrence
- Flexible, chosen per chore by the admin:
  - Fixed interval (every N days/weeks)
  - Specific days (e.g., Mon/Wed/Fri)
  - Deadline-based (next instance created after completion)

## Priority
- Simple tag: Low / Medium / High
- Used to sort the view, no other logic attached

## Completion
- Self-report — person marks it done, trust-based, no photo proof or approval step

## Conflict Handling
- **Passive flags** — overdue or unclaimed chores are visually flagged
- **Escalation** — unresolved flagged items surface to an admin for reassignment
- No in-app discussion/comment threads

## Accountability
- Factual history log only
- No points, streaks, scores, or gamification

## Views (Full Transparency — everyone sees everything)
1. **Status board** — today's done/pending/overdue at a glance
2. **History log** — who did what over time
3. **Ownership map** — who's responsible for which chores

## Platform & Access
- **Web app** — accessible from any device via browser, no native app
- **Notifications**: in-app only (no email or push)
- **Login**: individual password-protected accounts per person

## Out of Scope (for v1)
- Gamification (points, streaks, badges)
- Photo proof / approval workflows for completion
- Email or push notifications
- Role-based view restrictions (everyone sees the same data)
- Preset chore templates
- In-app comments/discussion threads