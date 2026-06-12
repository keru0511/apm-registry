# apm-registry

instructions / prompts / skills / hooks / MCP 定義をAPMで配布します。

## 構成

- `apm.yml`: パッケージ定義
- `.apm/instructions/`: instruction primitives
- `.apm/prompts/`: prompt primitives
- `.apm/skills/`: 配布する skill 本体
- `.apm/agents/`: agent 定義
- `.apm/hooks/`: hook 定義
- `scripts/agent-orchestrator`: 共通レビュー実行コマンド
- `scripts/install-codex-skill`: Codex 用 skill の個別インストーラ

## 配布対象一覧

このパッケージでは、APM で配布する定義を次の単位で管理しています。

| 種類 | 名前 | 用途 | 配置 |
|---|---|---|---|
| `instruction` | `base.instructions.md` | 共通の基本指示を配布する | `.apm/instructions/` |
| `prompt` | `orchestrated-review.prompt.md`, `release-check.prompt.md` | レビューやリリース確認に使う prompt を配布する | `.apm/prompts/` |
| `skill` | `comparison-proposal-builder`, `empirical-prompt-tuning`, `review-orchestrator`, `security-audit-assessor`, `writing-assessor` | Codex / Claude / Copilot から利用する skill を配布する | `.apm/skills/` |
| `hook` | `stop-local-ci.hook.json` | セッション終了時の確認処理を配布する | `.apm/hooks/` |
| `MCP 定義` | `linear` | APM パッケージに含める remote MCP 定義を配布する | `apm.yml` |

現時点では、`.apm/agents/` に配布中の agent 定義はありません。実際の定義値は `apm.yml` と `.apm/` 配下を参照してください。

## APM パッケージとして導入する

このリポジトリ全体を APM パッケージとして導入する場合:

```bash
apm install keru0511/apm-registry
```

既定では、導入先は `apm install` を実行した **現在のプロジェクト** です。  
グローバル導入したい場合は `-g` を使います。

```bash
apm install -g keru0511/apm-registry
```

グローバル導入時の配置先は:

```text
~/.apm/
```

## Codex で skill を入れる

このパッケージの skill は APM としてまとめて配布していますが、Codex 側では別途 skill 単位でローカル導入します。  
このリポジトリでは、そのためのラッパー `scripts/install-codex-skill` を用意しています。

使い方:

```bash
./scripts/install-codex-skill <skill-name> [git-ref]
```

例:

```bash
./scripts/install-codex-skill writing-assessor
./scripts/install-codex-skill security-audit-assessor
./scripts/install-codex-skill review-orchestrator main
```

指定できる `skill-name` は、上の `配布対象一覧` の `skill` 行にある名前です。

このコマンドは `keru0511/apm-registry/.apm/skills/<skill-name>` を取得し、次へインストールします。

```text
~/.codex/skills/<skill-name>
```

インストール後は Codex を再起動してください。

## Nix 開発シェル

この節以降は、主にこのリポジトリを保守する開発者向けの補足です。APM 自体の基本操作は、この README では扱いません。必要な場合は [APM 公式ドキュメント](https://microsoft.github.io/apm/) と [公式リポジトリ](https://github.com/microsoft/apm) を参照してください。

再現性のあるローカル環境が必要な場合は `flake.nix` を使えます。

```bash
nix develop

# security-audit-assessor の参照データ検証
.apm/skills/security-audit-assessor/tools/validate-security-corpus

# index / mapping の再生成
.apm/skills/security-audit-assessor/tools/sync-security-references
```

`toon` は `@toon-format/cli@2.0.1` に固定されています。初回実行時は npm キャッシュを作ることがあります。

## Shared Orchestration

レビュー系 skill / hook から共通で使うコマンドです。

```bash
./scripts/agent-orchestrator review --provider codex
./scripts/agent-orchestrator review --provider codex --model gpt-5.4
./scripts/agent-orchestrator run --provider claude --goal "Review and fix test failures"
./scripts/agent-orchestrator post-stop
```

実行成果物は常に次へ出力されます。

```text
.apm/runs/<run-id>/
```
