# apm-registry

This repository is an APM package source.

## Structure

- `apm.yml`: package manifest
- `.apm/instructions/`: instruction primitives (`*.instructions.md`)
- `.apm/prompts/`: prompt primitives (`*.prompt.md`)
- `.apm/skills/`: skills (`SKILL.md`)
- `.apm/agents/`: agent definitions (`*.agent.md`)
- `.apm/hooks/`: hook definitions (`*.json`)
- `scripts/agent-orchestrator`: shared command for provider execution and post-stop checks

## Basic workflow

```bash
# validate/install dependencies for this package
apm install

# compile for tools that consume compiled instruction files
apm compile

# produce distributable artifact
apm pack
```

## Publish and consume

After pushing this repo to a git host, consumers can install via:

```bash
apm install <host>/<org>/<repo>
```

## Shared Orchestration

The repository includes a common execution command that can be called from both skills and hooks:

```bash
./scripts/agent-orchestrator review --provider codex
./scripts/agent-orchestrator review --provider codex --model gpt-5.4
./scripts/agent-orchestrator run --provider claude --goal "Review and fix test failures"
./scripts/agent-orchestrator post-stop
```

Artifacts are always written to:

```text
.apm/runs/<run-id>/
```

This keeps invocation paths consistent across:

- skill execution (`.apm/skills/review-orchestrator/SKILL.md`)
- hook execution (`.apm/hooks/stop-local-ci.hook.json`)
