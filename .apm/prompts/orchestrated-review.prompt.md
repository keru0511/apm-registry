---
description: Run shared orchestrator-based review and summarize risks
---

Run the shared review command and summarize the result artifacts.

1. Execute:
   `./scripts/agent-orchestrator review --provider codex`
2. Read:
   - `.apm/runs/<run-id>/result.json`
   - `.apm/runs/<run-id>/summary.txt`
   - `.apm/runs/<run-id>/provider.stdout.log`
   - `.apm/runs/<run-id>/tests.log`
3. Report:
   - top risks
   - missing tests
   - minimal next fixes
