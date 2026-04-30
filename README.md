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
- `.apm/skills/security-audit-assessor/tools/`: security audit reference maintenance tools

## Basic workflow

```bash
# validate/install dependencies for this package
apm install

# compile for tools that consume compiled instruction files
apm compile

# produce distributable artifact
apm pack
```

This package also tracks the Linear remote MCP server in `apm.yml`:

```bash
apm install
```

On APM CLI `0.9.2`, remote MCP definitions are recorded correctly, but Codex runtime
installation is skipped for remote servers. In practice that means APM manages the
project-level definition, while each Codex user still registers and authenticates the
server locally.

For Codex, complete setup with:

```bash
codex mcp add linear --url https://mcp.linear.app/mcp
codex mcp login linear
```

If your Codex build requires the remote MCP client flag, enable it in
`~/.codex/config.toml` before logging in.

## Nix dev shell

For a reproducible local toolchain, this repository provides a `flake.nix`.

```bash
# enter the development shell
nix develop

# validate security audit references
.apm/skills/security-audit-assessor/tools/validate-security-corpus

# rebuild generated security audit indexes and mappings
.apm/skills/security-audit-assessor/tools/sync-security-references

# promote a single source corpus into references/corpus, then rebuild indexes
.apm/skills/security-audit-assessor/tools/promote-source-doc ipa-safe-website
```

The dev shell includes the basic CLI utilities used in this repo and a pinned `toon`
wrapper backed by `@toon-format/cli@2.0.1`. The first `toon` invocation may populate
the local npm cache.

The root `scripts/` directory is reserved for repo-wide entrypoints. Skill-specific
reference maintenance commands live under the owning skill, such as
`.apm/skills/security-audit-assessor/tools/`. A compatibility wrapper remains at
`scripts/validate-security-corpus`.

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
