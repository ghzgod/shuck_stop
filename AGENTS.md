AI Coding Assistant Guidelines (AGENTS.md)

Purpose
This file instructs AI coding assistants (Cursor, Roo Code, Claude Code etc.) exactly how to behave in this repository. Treat this file as a contract: do not modify it without a human-approved pull request. The agent must follow these rules strictly when generating code or changes.

Prerequisites & preflight

Read all documents in the project_rules folder

* Required tool: uv. Provide installation instructions and required minimum version in README or a referenced doc.

  * Example install hints:

    * Linux/macOS: curl -sSL [https://install.uv.sh](https://install.uv.sh) | bash  (or use the distro package manager if available)
    * Windows: use WSL or the provided PowerShell installer link in docs
* Preflight check script: scripts/check-uv.sh must exist and be run before any codegen or CI step. The script should:

  * Verify uv is installed and meets minimum version
  * Run uv sync dry-run (or equivalent) and exit non-zero on failure
  * Confirm pyproject.toml and uv.lock are consistent
* If uv cannot be installed, the agent must STOP and request human guidance. Do not attempt to use pip, poetry, or other package managers as a fallback without explicit human approval.

Project Initialization (with uv)

* Initialize projects with uv only:

  * To initialize current directory in-place: uv init .
  * To create a new project directory from parent: uv init <project-name>
* Never run uv init <project-name> inside an existing project directory (this creates nested projects). If a pyproject.toml already exists, do not run uv init and ask the human for instruction.

Dependency Management (Python)

* Use uv exclusively for dependency operations:

  * Add package: uv add <package>  or  uv add 'package==X.Y.Z'
  * Remove package: uv remove <package>
  * Sync environment: uv sync
  * Upgrade a specific package: uv lock --upgrade-package <package>
  * Upgrade all packages: uv lock --upgrade
* Always commit pyproject.toml and uv.lock produced by uv. Do not hand-edit lockfiles or pyproject.toml.
* If uv commands fail in CI or locally, abort and ask for human intervention. Do not replace uv commands with pip or other package manager calls.

Running and Building the Project

* Use uv run for all runtime, test, and tooling commands:

  * Example commands:

    * uv run main.py            (run a script)
    * uv run -m package.module  (run a module)
    * uv run pytest             (run tests)
    * uv run ruff               (run linter)
    * uv build                  (build distributions into dist/)
* Do not prepend python or call tools directly outside uv run unless the human explicitly requests it.
* Before building or releasing, ensure tests and linters pass via uv run and that progress.md contains a release entry.

Security and Environment Variables

* Never reveal or print secret values. Use environment variable keys only. Example in code: os.getenv("API_KEY") or os.environ["DATABASE_URL"] — do not print or log the value.
* Use .env to list environment variable names (keys) only; do not include any actual secret values in the repo.
* If a new env var is required, add it to .env and update README with a description; do not add secrets to the repo.
* Avoid logging environment variables. If logging is required for debugging, redact values.

AI Assistant Governance Rules (non-negotiable)

* Ask before committing: The agent must prompt the human for approval before creating commits or PRs. The prompt should include the intended commit message and changed files summary.
* Do not modify agents.md, rules.md, or progress.md without a human-created PR that explicitly lists the change and a maintainer approval. The agent may propose edits as files in /ai-output/ but cannot commit them directly.
* Always append progress.md with a timestamped, one-line entry for every AI-made change. Format: YYYY-MM-DD HH:MM — Step X — short description — actor:AI
* No mock data in production code: Use test fixtures stored in a clearly named test-only directory. Label test-only data as such.
* If a request conflicts with these rules, stop and ask for clarification.

No unsolicited summaries

* After making code changes, do not add a verbose summary or commentary unless explicitly requested. Return the code diffs or files only. If the human requests a summary, provide a concise, structured summary referencing the PR or commit.

CI & Enforcement (ONLY IF USER ASKS!)

* Add a GitHub Actions workflow (or equivalent CI) that runs on PRs and enforces:

  * scripts/check-uv.sh
  * uv sync
  * uv run pytest
  * uv run ruff
* If any step fails, the workflow must block merging.
* Add .github/CODEOWNERS entries so only approved maintainers can change agents.md and rules.md.

Progress Logging & Error Handling

* Always update progress.md when starting or finishing significant steps.
* On unexpected errors, append a short entry to current_issues.md, stop further codegen, and notify the human with the failure context and the exact failing command output (no secrets).
* Use current_issues.md to list blocking problems; new attempts must read current_issues.md before proceeding.

Connection & Environment Guide

* The agent must read connection_guide.md before creating or changing network-facing code. Respect ports, endpoints, and hostnames listed there.
* Do not invent new endpoints or port numbers. If a change requires a new port, propose it and wait for approval.

Cursor-specific browser rule (critical)

* Use Cursor's built-in browser tab only for any web browsing or web UI tasks. Do not use external browser automation tools or frameworks such as Playwright, Selenium, Puppeteer, or similar from the agent.
* If a task appears to require automated browser interaction, the agent must:

  * Propose a manual workflow using Cursor's built-in tab or a documented, human-approved alternative.
  * If automation is essential, stop and request explicit human approval naming the automation tool to use.
* Rationale: Cursor's built-in tab preserves auditability and avoids side-effectful automation that can break local dev environments or violate local privacy requirements.

Repository Structure & Where to Place Outputs

* Follow structure.md for file placement and naming conventions.
* For AI-generated patches that the agent is not permitted to commit, write them to /ai-output/ as complete files or patch files and append a small note to progress.md describing the intent.

Scripts & Tooling (required artifacts)

* scripts/check-uv.sh (bash) must exist and perform the preflight checks described above. The agent may generate a draft script in /ai-output/ but must not commit it without approval.
* Provide a Dockerfile fallback that installs uv and runs the check script. The agent may propose the Dockerfile but must not publish or push images without human approval.

Platform & Edge Cases

* Windows: prefer WSL. If a change targets Windows users, include PowerShell snippets and test commands for WSL compatibility.
* If uv cannot be installed, do not proceed. Propose one of these options and wait for instruction:

  * Human installs uv locally.
  * Use the provided Docker fallback (agent generates Dockerfile and instructions) — agent must wait for human approval before proceeding with Docker-based generation.
  * Use a CI-run build instead (agent outlines what CI job will run).
* Do not proceed with pip, poetry, or conda unless human-authorized in writing.

Secrets & Telemetry

* Telemetry is off by default. If telemetry is requested, the agent must:

  * Provide the human a short privacy plan describing exactly what is collected.
  * Implement telemetry as opt-in only and allow the user to revoke consent.
* Never hardcode API keys, tokens, or credentials. Use environment variables and secret stores.

What to do if uv is missing (exact fallback behavior)

* Detect missing uv via scripts/check-uv.sh. If missing:

  * Abort any codegen.
  * Write an entry to progress.md: YYYY-MM-DD HH:MM — uv missing — aborted — actor:AI
  * Produce a human-facing message that lists install options: local install, Docker fallback, or WSL instructions.
  * Wait for human approval to proceed with any alternative.

Commit & PR policy

* Agent-generated commits must be approved by a human. The agent may create a draft PR but must not merge.
* Draft PR content must include:

  * Title
  * One-line summary
  * Files changed (list)
  * Tests run and results (or note if tests were not run and why)
  * Any manual steps the reviewer should execute locally

Assumptions & Confidence

* Assumes uv is the canonical package manager for this project. Confidence: medium-high. If uv is an internal tool, include a README link that documents installation and expected behavior.
* Assumes Cursor environment supports a built-in browser tab and that agents can interact with it. Confidence: high.

Enforcement & Audit

* Add CODEOWNERS for agents.md and rules.md. Only specified maintainers may approve modifications to these files.
* Agent must leave a trace in progress.md for every action attempted or completed.
