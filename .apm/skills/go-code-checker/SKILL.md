---
name: go-code-checker
description: GoコードのPRレビュー、実装修正、設計レビューを行うスキル。公式の Go ドキュメントを一次根拠として、`context`、error handling、並行性、API設計、package境界、テスト、doc comment、`go vet` で拾える典型不具合を観点別に確認し、必要に応じてローカル検証も組み合わせて判断したいときに使う。
---

# Go Code Checker

このスキルは、Go コードチェックを `重い corpus` ではなく、`軽い公式資料索引 + 観点別ルール + 必要時だけ原典参照` で回す。

通常は `references/sources.json` と `references/rules/*.json` だけを読む。指摘の根拠補強が必要なときだけ `canonical_url` を開く。

## モード

最初に次のいずれかを選ぶ。

- `review`: PR や差分レビュー。バグ、回帰、テスト不足、設計崩れを重大度順に指摘する
- `fix`: 問題発見だけでなく、必要なら修正まで進めて `go test` `go vet` で確認する
- `design`: package 境界、公開 API、interface、`context` / error 設計、テスト構造を重点確認する

ユーザー指定がなければ、差分や PR があるときは `review`、エラー修正や lint 修正依頼なら `fix`、設計相談や分割相談なら `design` を選ぶ。

## 最初に読むファイル

1. `references/sources.json`
2. モードに関係なく次を優先
   - `references/rules/context.json`
   - `references/rules/errors.json`
   - `references/rules/testing.json`
3. 対象に応じて追加
   - 並行処理がある: `references/rules/concurrency.json`
   - 公開 API や package 設計を見る: `references/rules/api-design.json`
   - package comment や公開コメントを見る: `references/rules/documentation.json`
4. 必要なら `canonical_url` を使って公式原典を確認する

## 参照データの考え方

- `references/sources.json`: 公式資料の台帳。`kind`、`authority`、`stability`、`when_to_use` を持つ
- `references/rules/*.json`: レビュー観点の正本。`signals` と `source_refs` から必要な論点を引く

このスキルでは、`toon` 化した全文 corpus を既定にしない。Go の公式資料は、`pkg.go.dev` と `go.dev` の構造が比較的安定しており、レビューでは全文検索より観点選択のほうが重要だから。

## 実行手順

1. 対象を決める。
   - PR / 差分
   - 特定ファイル
   - 特定 package
   - リポジトリ全体
2. `go.mod`、`go.work`、対象 package、関連 `_test.go` を読む
3. `go.mod` の `go` バージョンと build constraint を見て、言語仕様や `vet` の挙動差を踏まえる
4. モードを決める
5. `references/rules/*.json` から適用観点を選ぶ
6. 先にコードと差分を読み、どの rule に該当しそうかを整理する
7. 根拠補強が必要な指摘だけ `references/sources.json` から対応する公式 URL を開く
8. `fix` または必要時のみ、対象に応じてローカル検証を行う
9. 結果を重大度順で返す。問題がなければ残留リスクと未実施検証を明記する

## 推奨コマンド

対象 package が分かる場合:

```bash
go test ./path/to/package
go test -race ./path/to/package
go vet ./path/to/package
```

対象が広い場合:

```bash
go test ./...
go vet ./...
```

フォーマット修正が必要な場合:

```bash
gofmt -w <files>
```

環境にあれば追加で使ってよい:

```bash
staticcheck ./...
```

## 判定原則

- 仕様逸脱、データ破壊、panic、リーク、race、互換性破壊を優先する
- 推測で `安全` と断定しない
- `go vet` の結果は有力な補助根拠だが、正しさの完全証明として扱わない
- Go 1.22 以降で意味が変わった論点は、`go.mod` の `go` バージョンに合わせて判定する
- `Effective Go` は補助資料扱いに留め、一次根拠はより新しい `pkg.go.dev` / `go.dev` の資料を優先する
- `review` では指摘中心、`fix` では修正と再検証まで進める

## よく使う観点

- `context`: 伝搬、`CancelFunc` 解放、`WithValue` 誤用、nil context
- `errors`: wrap、比較可能性、情報不足、sentinel/error type の扱い
- `testing`: table-driven test、subtest、parallel test、fuzz、回帰テスト
- `concurrency`: goroutine lifetime、共有状態、lock、channel、memory model に反する実装
- `api-design`: package 境界、公開名、ゼロ値、interface 粒度、`internal/` の使い方
- `documentation`: package comment、exported symbol の doc comment、bool 戻り値コメント

## 出力要件

レビュー結果は Markdown で返し、最低限次を含める。

- `対象とモード`
- `実施した確認`
- `重要指摘`
- `追加したいテスト`
- `未実施検証 / 残留リスク`

問題を指摘するときは最低限次を含める。

- 何が問題か
- どの条件で表面化するか
- 適用した観点または rule_id
- 必要なら公式根拠
- どう直すべきか

問題が見つからない場合でも、未実施の `go test` `go vet` `-race` や、確認できていない設計前提は残す。
