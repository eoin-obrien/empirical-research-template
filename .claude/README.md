# .claude/

Project configuration for Claude Code.

| Directory | Contents                                                              |
| --------- | --------------------------------------------------------------------- |
| `agents/` | Subagent definitions, one Markdown file per agent.                    |
| `hooks/`  | Scripts that hooks configured in `.claude/settings.json` call.        |
| `skills/` | Project skills, one directory per skill containing a `SKILL.md`.      |

This README lives here rather than inside the subdirectories because
Claude Code reads every `.md` file in `agents/` as an agent definition.
