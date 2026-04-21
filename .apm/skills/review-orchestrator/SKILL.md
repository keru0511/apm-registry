---
name: review-orchestrator
description: Run a structured code review workflow via the shared agent-orchestrator command and produce reproducible review artifacts.
---

# Review Orchestrator

Use this skill when you want consistent code review execution from any agent surface (skill invocation or hook).

## Inputs

- `provider`: `claude` | `codex` | `cursor`
- `model` (optional): provider-specific model name (defaults to provider CLI default)
- `repo` (optional): target repository path
- `tests` (optional): command to run after review output

## Command

```bash
./scripts/agent-orchestrator review --provider <provider> --model <model> --repo <repo> --tests "<tests-command>"
```

Examples:

```bash
./scripts/agent-orchestrator review --provider codex
./scripts/agent-orchestrator review --provider codex --model gpt-5.4
./scripts/agent-orchestrator review --provider claude --repo /home/kk/workspace/freee-internal-app --tests "npm run worker:test"
```

## Output Contract

Read and report:

- `.apm/runs/<run-id>/result.json`
- `.apm/runs/<run-id>/summary.txt`
- `.apm/runs/<run-id>/provider.stdout.log`
- `.apm/runs/<run-id>/tests.log`

## Review Focus

Prioritize:

1. Behavioral regressions
2. High-risk changes and rollback concerns
3. Missing tests and validation gaps
4. Concrete, minimal next fixes
