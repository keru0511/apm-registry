# apm-registry

このリポジトリは、APM 形式で配布する instructions / prompts / skills / hooks / MCP 定義の公開元です。

## 構成

- `apm.yml`: パッケージ定義
- `.apm/instructions/`: instruction primitives
- `.apm/prompts/`: prompt primitives
- `.apm/skills/`: 配布する skill 本体
- `.apm/agents/`: agent 定義
- `.apm/hooks/`: hook 定義
- `scripts/agent-orchestrator`: 共通レビュー実行コマンド
- `scripts/install-codex-skill`: Codex 用 skill の個別インストーラ

## 基本コマンド

```bash
# 依存関係を解決
apm install

# 配布用にコンパイル
apm compile

# バンドル作成
apm pack

# 利用可能なスクリプト一覧
apm list
```

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

このパッケージは `apm.yml` 内で `linear` の remote MCP も配布します。Codex 側では別途ローカル登録が必要です。

```bash
codex mcp add linear --url https://mcp.linear.app/mcp
codex mcp login linear
```

## 配布中の Codex skills

- `comparison-proposal-builder`: 比較提案資料、評価軸、重み付きスコアリング、推奨案整理
- `empirical-prompt-tuning`: skill やプロンプトを実行評価ベースで反復改善
- `review-orchestrator`: `scripts/agent-orchestrator` を使った構造化コードレビュー
- `security-audit-assessor`: IPA + NIST 観点の静的セキュリティ監査
- `writing-assessor`: 主語、省略、文分割、送り仮名、外来語、句読点、禁則処理を含む文書評価

## Codex skill を1つだけ入れる

Codex には `skill-installer` という system skill が同梱されています。  
このリポジトリでは、その内部スクリプトを直接意識しなくてよいように、薄いラッパー `scripts/install-codex-skill` を用意しています。

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

このコマンドは `keru0511/apm-registry/.apm/skills/<skill-name>` を取得し、次へインストールします。

```text
~/.codex/skills/<skill-name>
```

インストール後は Codex を再起動してください。

## Nix 開発シェル

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
