# Claude Code

Read and follow:

@AGENTS.md

Before modifying existing code, read the relevant implementation and tests.

Do not introduce new dependencies, tools, workflow engines, or repository
conventions without explicit approval.

Do not edit generated artifacts directly.

Do not modify repository guardrails, CI workflows, hooks, or research-integrity
rules unless the user explicitly asks for those changes. These are the paths
under `permissions.ask` in `.claude/settings.json`.

Run `just check` after code changes. Run `just verify` after changes to data,
the protocol, results or the manuscript.
