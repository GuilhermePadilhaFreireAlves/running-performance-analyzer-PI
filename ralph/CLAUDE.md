# Ralph Agent Instructions — Running Performance Analyzer

You are an autonomous coding agent working on the **running-performance-analyzer** repository.

## Working Environment

- **CWD when you run** = repository root (`/workspace`).
- **Platform**: Linux (WSL2). Use forward slashes in paths; never assume Windows.
- **Python**: use the project venv at `venv/` (activate with `source venv/bin/activate`).
- All Ralph state lives in `ralph/`: PRD at `ralph/prd.json`, progress log at `ralph/progress.txt`.
- Read the root `CLAUDE.md` for project-specific domain knowledge (Portuguese naming, knee-angle convention, cadence state machine, keypoint validity gate). Respect those conventions.

## Your Task (each iteration)

1. Read `ralph/prd.json` and `ralph/progress.txt` (check the `## Codebase Patterns` section at the top of `progress.txt` first).
2. Check the current git branch. PRD `branchName` is `dev/padilha`:
   - If not on that branch, create it from `main` (`git checkout -b dev/padilha`) or check it out if it already exists.
   - **NEVER** create, checkout, push or commit to any branch starting with `ralph/`. All work happens on `dev/padilha`.
   - If there are untracked setup files (`.claude/`, `.devcontainer/`, `CLAUDE.md`, `PRD.MD`, `ralph/`), they are intentional — they'll follow the branch switch; don't delete them.
3. Pick the **highest-priority** user story where `passes: false` (lowest `priority` number wins; ties broken by `id` order).
4. Implement that **single** user story end-to-end.
5. Run quality checks. This project currently has **no test suite, no linter, no typechecker configured**. Minimum bar per iteration:
   - Python files you touched must `python -c "import <module>"` without ImportError.
   - If you add a FastAPI route under `server/`, verify `uvicorn server.src.main:app --reload` boots without error (run briefly and kill).
   - If the story's acceptance criteria mention "Typecheck passes" and no typechecker exists yet, that criterion means: install and configure one (mypy or pyright) as part of the story, then make it pass.
6. Update nearby `CLAUDE.md` files only if you discovered a **reusable pattern** future iterations must know (see "Update CLAUDE.md Files" below).
7. Commit **all** related changes following the rules in "Commit Rules" below.
8. Set `passes: true` for the completed story in `ralph/prd.json` (edit the JSON directly — preserve formatting).
9. Append a progress entry to `ralph/progress.txt` (format below).

## Commit Rules — MANDATORY, NO EXCEPTIONS

These rules are NON-NEGOTIABLE. Violating them breaks the project convention.

- **Subject line ONLY.** No body, no description, no trailing lines, no blank lines. Use `git commit -m "feat: add X"` — single `-m`, nothing more.
- **Conventional Commits prefix required**: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `style:`, `perf:`, `ci:`.
- **Commit message format**: `<type>: [Story ID] - [Story Title]` — nothing else on any line.
- **NEVER** add `Co-Authored-By`, `Signed-off-by`, or any attribution of Claude/Anthropic/any tool. No trailers at all.
- **NEVER** use `--no-verify`, `--no-gpg-sign`, or `--amend`.
- **Git author MUST be** `GuilhermePFA <guilhermepadilhafreirealves@gmail.com>`. Do not run `git config user.*` — the local config is already correct; just verify with `git config user.email` before committing if unsure. If the email is anything other than `guilhermepadilhafreirealves@gmail.com`, STOP and do not commit.
- **Do not stage** `venv/`, `*.pt`, `run/`, or anything in `.gitignore`. Prefer `git add <specific files>`; never `git add -A` without first confirming `git status` is clean of junk.

**Correct example:**
```
git commit -m "feat: US-001 - Criar schema PostgreSQL e migrations"
```

**Forbidden examples (do not do these):**
```
# ❌ Body/description
git commit -m "feat: US-001" -m "Creates USUARIO table..."

# ❌ HEREDOC with trailers
git commit -m "$(cat <<'EOF'
feat: US-001

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# ❌ Amend
git commit --amend
```

## Progress Report Format

APPEND to `ralph/progress.txt` (never replace — always append at the bottom):

```
## [YYYY-MM-DD HH:MM] - [Story ID] [Story Title]
- What was implemented (1–3 bullets)
- Files changed
- **Learnings for future iterations:**
  - Patterns discovered (e.g., "this codebase uses X for Y")
  - Gotchas (e.g., "don't forget to update Z when changing W")
  - Useful context (e.g., "FastAPI app object is at server/src/main.py:app")
---
```

## Consolidate Patterns

If you discover a **reusable, general pattern** that future iterations should know, add a bullet to the `## Codebase Patterns` section at the TOP of `ralph/progress.txt` (create that section on first use).

Only add patterns that are **general and reusable**, not story-specific details.

## Update CLAUDE.md Files

Before committing, check if you should update a nearby `CLAUDE.md`:

1. Identify directories you modified.
2. Check for `CLAUDE.md` in those dirs or parents.
3. Add only **genuinely reusable** knowledge:
   - Module-specific API patterns or conventions
   - Non-obvious gotchas / dependencies between files
   - Testing approaches specific to that area
   - Environment requirements

Do **not** add: story-specific implementation details, temporary notes, info already in `progress.txt`.

## Quality Requirements

- No broken commits.
- Keep changes focused and minimal — one story per iteration.
- Follow existing code patterns (Portuguese variable names in biomechanics code, match the duplicated-pipeline convention in `processing/src/mainYolo.py` / `mainGraph.py` if you touch those).
- Never commit secrets, credentials, `.env` files, or model weights (`*.pt`).

## Stop Condition

After completing a user story, check `ralph/prd.json`: if **ALL** stories have `passes: true`, output **exactly** this on its own line at the end of your response:

<promise>COMPLETE</promise>

If any story still has `passes: false`, end your response normally — the next iteration will pick up.

CRITICAL: Only output `<promise>COMPLETE</promise>` when every user story genuinely passes. Do not emit it to escape the loop.

## Important

- ONE story per iteration.
- Commit at the end of each iteration — subject line only, no co-author, correct email (see Commit Rules).
- Read the `## Codebase Patterns` block in `ralph/progress.txt` at the start of every iteration.
- NEVER touch any `ralph/*` branch. All work goes to `dev/padilha`.
