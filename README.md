# AIcore

**License: MIT License © 2026 Bob Wang**

AIcore is an open-source task governance framework for AI-assisted software
development. It helps developers and small teams use coding agents such as
OpenAI Codex, Claude Code, and other automation tools without losing control of
scope, review, traceability, and rollback discipline.

Instead of asking an agent to "just implement it", AIcore turns every change
into a lightweight, reviewable task: define the request, freeze the entrypoints,
record the allowed files, capture risks and acceptance criteria, approve the
task, log agent writes, create checkpoints, and update a system ledger only when
the result is confirmed.

The goal is simple: make AI-generated code easier to review, safer to iterate,
and more useful for real projects.

---

## Why AIcore Exists

AI coding tools can move quickly, but that speed often creates a different
problem: unclear task boundaries, duplicated implementations, inconsistent
naming, missing acceptance criteria, and changes that are hard to audit later.

AIcore provides a small but practical control layer around that workflow:

- Start every change from an explicit task draft.
- Require a task-level architecture review before approval.
- Keep implementation scope, entrypoints, risks, and rollback plans visible.
- Record agent write events and stable checkpoints.
- Maintain a current-state ledger for confirmed capabilities and known limits.

AIcore is not a replacement for Git, test suites, security audits, or code
review. It is the missing workflow layer between "AI wrote files" and "this
change is actually safe to accept".

---

## Project Highlights

- **Task-level architecture gate**: Capture main entrypoints, compatibility
  entrypoints, allowed files, baseline references, success criteria, risks, and
  rollback plans before implementation.
- **Human approval workflow**: Move tasks through `draft`, `reviewing`,
  `approved`, `rejected`, and `superseded` states instead of letting an agent
  silently expand scope.
- **Vibe Coding contract**: A dedicated contract checklist helps prevent
  accidental rewrites, duplicated APIs, naming drift, and unapproved refactors.
- **Agent write history**: `log-write` records which session changed which files
  and stores recoverable snapshots under `.aicore/history`.
- **Checkpoints**: Bundle one or more write events into an explicit stable point
  with a manifest.
- **System ledger**: `ledger-confirm` writes confirmed capabilities,
  entrypoints, limits, compatibility notes, and known risks into
  `.aicore/system-ledger.md`.
- **Multi-session visibility**: `status` detects pending write events and files
  touched by multiple sessions.
- **Cross-platform Python CLI**: Installable Python package with console scripts
  and local helper scripts under `bin/`.
- **Claude Code integration**: Project-level commands and hooks are included for
  teams that want AI-agent workflow reminders inside Claude Code.
- **Test-covered MVP**: The repository includes focused pytest coverage for CLI
  smoke tests, task state transitions, history, ledger, status, task updates,
  and wrapper files.

---

## OpenAI Codex Usage Plan

AIcore is designed to be a useful open-source companion for Codex-driven
development. Codex can help this project by:

- Implementing small, well-scoped CLI and service modules.
- Generating and maintaining pytest coverage for workflow edge cases.
- Improving documentation, examples, and onboarding guides.
- Refactoring internal modules while preserving task contracts.
- Creating repeatable demos that show safer AI-assisted development practices.

In return, AIcore provides a concrete OSS workflow that makes Codex-generated
changes easier to constrain, inspect, test, and accept. The project is therefore
not just a consumer of AI coding capacity; it is a tool for making AI coding
workflows more accountable for the wider developer community.

---

## Quick Start

### Requirements

- Python 3.11+
- pip
- Git

### Install locally

```bash
git clone https://github.com/wangbo12bob2-source/aicore.git
cd aicore
python3 -m pip install -e '.[dev]'
```

Verify the CLI:

```bash
aicore --help
```

If you are developing directly inside this repository, you can also run the
package without installing it:

```bash
python3 -m aicore --help
./bin/aicore --help
```

---

## Minimal Workflow

AIcore writes task state to the current workspace under `.aicore/`.

### 1. Start a task

```bash
aicore start "Implement JWT login"
```

This creates:

```text
.aicore/tasks/<task-id>/task.yaml
.aicore/tasks/<task-id>/brief.md
```

At this point the task is only a draft. No implementation has been approved.

### 2. Fill in the task boundary

```bash
aicore update task-2026-06-12-001 \
  --main-entrypoint "API: POST /auth/login" \
  --allowed-file "src/auth/login.py" \
  --baseline-ref "tests/test_auth.py" \
  --success-criteria "JWT login succeeds for valid credentials" \
  --assumption "Only the login endpoint is in scope" \
  --risk "Refresh token flow is not covered in this task" \
  --review-summary "Entrypoint, scope, baseline, and risks are confirmed" \
  --rollback-plan "Revert the login module and related tests" \
  --dual-write-required false \
  --dual-write-reason "Only one primary login entrypoint is changed"
```

### 3. Check the contract

```bash
aicore checklist task-2026-06-12-001
```

The checklist reports missing approval requirements in plain Chinese, so the
task can be corrected before implementation begins.

### 4. Review and approve

```bash
aicore review task-2026-06-12-001
aicore approve task-2026-06-12-001 --by "alice"
```

`approve` records that the task boundary has been confirmed. It does not
automatically start implementation.

### 5. Record agent writes

After an agent changes files, record the write:

```bash
aicore log-write task-2026-06-12-001 \
  --session codex-session-1 \
  --file src/auth/login.py \
  --file tests/test_auth.py \
  --summary "Implemented JWT login and tests"
```

AIcore stores the event and snapshots under `.aicore/history/`.

### 6. Create a checkpoint

```bash
aicore checkpoint task-2026-06-12-001 \
  --event event-20260612000000000000-example \
  --summary "JWT login implementation reached a stable point"
```

### 7. Confirm the system ledger

Only after review and verification should a capability be written to the
ledger:

```bash
aicore ledger-confirm task-2026-06-12-001 \
  --event event-20260612000000000000-example \
  --capability "Supports JWT login for valid credentials" \
  --entrypoint "API: POST /auth/login" \
  --limit "Refresh token flow is out of scope" \
  --compatibility "Works on Python 3.11+" \
  --risk "Additional negative-path coverage may be needed"
```

### 8. Inspect collaboration status

```bash
aicore status
```

This shows sessions, pending events, and files touched by multiple sessions.

---

## CLI Commands

| Command | Purpose |
| --- | --- |
| `start` | Create a task draft and brief |
| `update` | Add entrypoints, allowed files, acceptance criteria, risks, and rollback plan |
| `checklist` | Validate whether a task has enough information for approval |
| `review` | Move a draft into human review |
| `approve` | Approve a reviewed task after required fields are complete |
| `reject` | Reject a task when scope or risk is unclear |
| `list` | List task drafts in the current workspace |
| `show` | Show details for one task |
| `log-write` | Record an agent write event and file snapshots |
| `checkpoint` | Create a manifest from one or more write events |
| `status` | Show multi-session write state and pending events |
| `ledger-confirm` | Add confirmed project facts to `.aicore/system-ledger.md` |

---

## Shortcut Scripts

The repository includes local helper scripts for fast use inside a Codex or
terminal workflow:

```bash
./bin/astart "Improve task boundary validation"
./bin/alist
./bin/ashow task-2026-06-12-001
./bin/acheck task-2026-06-12-001
./bin/aupdate task-2026-06-12-001 --main-entrypoint "CLI: aicore update"
./bin/aapprove task-2026-06-12-001 --by "h12"
```

After editable install, the same shortcuts are available as console scripts:

```bash
astart "Improve task boundary validation"
acheck task-2026-06-12-001
aupdate task-2026-06-12-001 --main-entrypoint "CLI: aicore update"
aapprove task-2026-06-12-001 --by "h12"
```

When run from another project, AIcore writes `.aicore/` to that project's
current working directory.

---

## Claude Code Wrapper

AIcore also includes project-level Claude Code wrapper files for teams that want
workflow reminders inside an agent session:

- `CLAUDE.md`: Project rules for the AIcore workflow.
- `.claude/commands/aicore-start.md`: `/aicore-start`
- `.claude/commands/aicore-save.md`: `/aicore-save`
- `.claude/commands/aicore-log-write.md`: `/aicore-log-write`
- `.claude/commands/aicore-checkpoint.md`: `/aicore-checkpoint`
- `.claude/commands/aicore-ledger.md`: `/aicore-ledger`
- `.claude/agents/aicore-guard.md`: Guard agent for workflow checks.
- `.claude/settings.json`: `PostToolUse` hook wiring.

The recommended Claude Code sequence is:

```text
/aicore-start
# Let Claude Code edit files inside the approved task boundary.
/aicore-save
/aicore-ledger
```

The wrapper does not keep a separate state store. It writes through the same
`.aicore/` task, history, checkpoint, and ledger files used by the CLI.

---

## Vibe Coding Contract

The contract in [`docs/contracts/vibe-coding-contract.md`](docs/contracts/vibe-coding-contract.md)
defines the expected collaboration rules for AI-assisted implementation.

It focuses on practical failure modes:

- Scope creep during implementation.
- Agents inventing extra scenarios.
- Unclear main entrypoints.
- Unapproved rewrites or "cleanup" refactors.
- Mixed naming, status, pagination, or error semantics.
- Missing acceptance criteria.
- Claims of completion before verification and ledger confirmation.

For Vibe Coding tasks, run `aicore checklist <task-id>` before approval and keep
the implementation inside the approved task boundary.

---

## Project Structure

```text
AIcore/
├─ aicore/                 # Local import shim for python3 -m aicore
├─ bin/                    # Local CLI helper scripts
├─ docs/
│  ├─ contracts/           # Vibe Coding task contract
│  └─ superpowers/         # Design notes and implementation plans
├─ src/aicore/             # Main Python package
│  ├─ cli.py               # CLI parser and command dispatch
│  ├─ task_service.py      # Task lifecycle operations
│  ├─ task_update_service.py
│  ├─ task_contract_service.py
│  ├─ history_service.py
│  ├─ ledger_service.py
│  └─ status_service.py
├─ tests/                  # Pytest coverage for CLI and services
├─ CLAUDE.md               # Claude Code workflow guidance
├─ LICENSE                 # MIT license
├─ pyproject.toml          # Package metadata and console scripts
└─ README.md
```

Runtime state is intentionally written under the current workspace:

```text
.aicore/
├─ tasks/                  # Task drafts, briefs, and state
├─ history/                # Agent write events, snapshots, checkpoints
└─ system-ledger.md        # Confirmed capabilities, entrypoints, limits, risks
```

---

## Development

Install development dependencies:

```bash
python3 -m pip install -e '.[dev]'
```

Run the test suite:

```bash
python3 -B -m pytest -p no:cacheprovider tests -q
```

Run a focused smoke test:

```bash
python3 -B -m pytest -p no:cacheprovider tests/test_cli_smoke.py -q
```

---

## Roadmap

- JSON output mode for easier integration with other tools.
- Richer task reports for maintainers and reviewers.
- Git-aware restore helpers built on top of recorded snapshots.
- More examples for multi-agent development workflows.
- Additional integration guides for Codex, Claude Code, and CI pipelines.
- Documentation for using AIcore across multiple repositories.

---

## Community And Contributions

AIcore is intended to be a community-oriented OSS project for developers who
want safer AI-assisted development workflows.

Contributions are welcome:

- Open issues for workflow problems, unclear documentation, or missing edge
  cases.
- Submit pull requests for CLI improvements, tests, examples, and docs.
- Keep changes scoped and include tests when behavior changes.
- Use the task contract when proposing larger workflow changes.

The most valuable contributions are practical: examples, tests, and workflow
improvements that help real teams use AI coding tools with less ambiguity.

---

## Contact

- GitHub: [wangbo12bob2-source/aicore](https://github.com/wangbo12bob2-source/aicore)
- Issues and pull requests: [GitHub Issues](https://github.com/wangbo12bob2-source/aicore/issues)

---

## License

Released under the MIT License. Copyright (c) 2026 Bob Wang.
