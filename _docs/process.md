- Tasks are GitHub issues
- Commit regularly

Labels

- `mvp` - needed for the MVP defined in `_docs/outdated/_plan.md`
- `post-mvp` - real work, deliberately not now
- Every issue carries exactly one of the two, new ones included

Background

- `_docs/decisions.md` - the calls already made, with reasons. Read it before
  grooming or implementing, and do not reopen a decision without changing it
  there first
- `_docs/outdated/` holds the original plan and architecture. They are
  reference, not the backlog - where they disagree with `decisions.md` or
  an issue, they lose
- `AGENTS.md` is the standing architecture/commands reference for whoever
  (agent or human) is working in the repo day to day (`CLAUDE.md` is just
  `@AGENTS.md`, so Claude Code picks it up the same way)

Roles

- PM - grooms a task before anyone implements it, follows _docs/team/pm.md
- Engineer - implements one groomed task, follows _docs/team/software-engineer.md
- QA - checks the result against the acceptance criteria, follows _docs/team/qa-engineer.md


Orchestrator

The main session is the orchestrator. It launches the PM, the engineer
and QA as subagents. It does not groom, implement or test itself.

The orchestrator owns three things the subagents cannot see: the
dependency order of the backlog, the worktrees, and the merge queue.


Working in parallel

Work runs in waves. A wave is a set of issues that can be built at the
same time without waiting on each other.

- Up to 5 agents run at once
- Every issue in a wave gets its own git worktree and its own branch
- Nothing is implemented in the main checkout. Main is for grooming,
  integration and the docs

An issue may enter a wave only when all of these hold:

- Every issue it depends on is closed and merged into main
- No other issue in the same wave adds migrations to `chores_app` (there
  is only one app, so two issues touching models at once will conflict on
  migration numbering)
- The orchestrator has read its Constraints section and knows which
  shared files it will touch

Everything else waits for the next wave. A wave is often smaller than 5
because the backlog runs out of independent work, not because the limit
was reached - that is normal, do not pad a wave to fill it.


Worktrees

One issue, one worktree, one branch:

    git worktree add ../wt/<issue> -b issue-<issue> main

Each worktree is a full checkout and needs its own setup before an agent
touches it:

- `uv sync` - the worktree has its own `.venv`

That's the whole setup. This project uses SQLite with no `DATABASE_URL`
or `.env` - `chores_config/settings.py` points `db.sqlite3` at
`BASE_DIR / 'db.sqlite3'`, and `BASE_DIR` resolves relative to wherever
the checkout lives. Every worktree gets its own database file for free,
with nothing to configure and no server to share or collide on. There is
no equivalent of a shared Postgres container to worry about here - if
this project ever moves to a real database server, this section needs
rewriting to add the isolation that SQLite gives away for free.

One suite at a time inside a worktree. Two `manage.py test` runs started
together in the same worktree will step on the same `db.sqlite3`. It
produces a scatter of failures that look like a real regression and are
not - a run that fails strangely gets repeated alone before it is
believed.

The suite currently runs in under a minute, so waiting for it costs
little - run it in the foreground and read the result. That does not mean
skip the wait: nothing wakes an agent that has stopped, so "I will report
when it finishes" is where the work ends if the command was backgrounded
and never checked. If the suite ever grows slow enough that waiting stops
being free, poll it with a ceiling and say so if it does not finish in
time - "did not finish within two minutes" is a finding, not silence.

Never `pkill -f manage.py` or similar to clean up. If you did not start
it, do not kill it - kill a background job by the id the tool gave you,
or let it finish.

One agent per worktree at a time. An implementer commits, pushes and is
done before a reviewer is pointed at that worktree; the orchestrator does
not overlap them.

A merged worktree is left where it is. Reuse it for the next issue that
lands in the same area, or leave it alone.


Destructive commands stall the run

The harness checks commands that destroy things and asks the person
running the session to approve them. That is the right behaviour, but it
means the work stops dead until someone is at the keyboard. A wave of
five agents can sit idle overnight on one `rm`.

So nothing in this process deletes. Not worktrees, not branches, not
temporary files.

- Restore a file you changed on purpose with `git checkout -- <path>` or
  `git restore <path>`, never by copying it aside and deleting the copy
- Beware the version of that command with a commit in it.
  `git checkout <commit> -- <path>` *stages* what it writes, so the later
  `git checkout -- <path>` meant to undo it finds nothing to do and
  silently leaves the old file in place. Someone proved a fix worked by
  checking out the pre-fix file, and nearly shipped the branch with it.
  After restoring anything, `git status` and `git diff HEAD` both have to
  be empty before the work is called done
- Write temporary files to the session scratchpad, which is outside the
  repository and needs no cleanup, never to `/tmp` and never next to the
  code
- Leave worktrees and branches in place when an issue closes. They are a
  few megabytes each

If something genuinely has to be removed, that is the user's call. Say
what should go and why, and let them run it. Do not put a deletion in
front of an agent and hope it goes through.


Integration

Branches merge one at a time, never in parallel, in dependency order:

1. Rebase the branch on current main
2. Run the whole suite (`uv run python manage.py test chores_app`) and
   `uv run python manage.py makemigrations --check --dry-run` again, in
   the worktree, after the rebase
3. Merge to main only if both are clean
4. Push main
5. Close the issue
6. Rebase every still-open branch in the wave onto the new main

Step 6 is what keeps the wave honest. The second branch to merge is
being tested against code its author never saw, so it re-runs against
the merged result before it is trusted.

Step 4 is not bookkeeping. A local commit is invisible: the person whose
project this is opens GitHub, sees nothing, and has no way to tell a
working session from a stalled one. Push main as soon as it moves.

Engineers push their own branch too, as soon as it has a commit on it,
and again after each round of QA fixes. A branch nobody can see is a
branch nobody can review, and the whole wave's work is otherwise
invisible until it merges.

Once the orchestrator rebases a branch, that branch's history no longer
matches the one on origin, and every later push from it is a force push
- which stops and waits for a human. So after a rebase the engineer
stops pushing and says so; the orchestrator merges and pushes main, and
main carries the work. Nobody force-pushes to repair the branch. The
stale copy on origin is superseded the moment main moves, and a stale
branch costs nothing while a blocked push costs the whole run.

Conflicts concentrate in a few shared files - `chores_config/settings.py`,
`chores_config/urls.py`, `AGENTS.md`, `chores_app/templates/chores/base.html`.
The orchestrator resolves them at integration. An engineer who finds a
conflict is looking at a stale branch and should rebase, not merge main
into their branch.

A rebase that breaks the branch goes back to that branch's engineer with
the failure, as a FAIL. The orchestrator does not fix it.


Lifecycle

1. Pick the next wave: open issues whose dependencies are all merged
2. PM grooms each ungroomed issue in the wave
3. Set up a worktree per issue, then launch one engineer per issue, in
   parallel
4. QA verifies each one in its own worktree, in parallel, as its
   engineer finishes - QA does not wait for the whole wave
5. On FAIL, back to step 3 for that issue alone, with the QA comment as
   input. The rest of the wave carries on
6. On PASS, integrate that branch through the merge queue and close the
   issue
7. Leave the worktree in place
8. Repeat until the backlog is empty

Rules

- One issue per worktree, one engineer per issue
- Do not skip step 2, even when the task looks obvious
- The engineer does not close the issue, QA does not fix the code
- Do not commit until the tests pass
- An agent stays inside its own worktree. Reading main is fine, writing
  to it or to another worktree is not
- Only the orchestrator merges, closes issues, and deletes worktrees
