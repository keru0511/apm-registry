# Go Code Checker 参照データの使い方

このディレクトリでは、Go コードチェックに使う公式資料台帳と観点別ルールを管理する。

このスキルは `toon corpus` を正本にしない。通常は `sources.json` と `rules/*.json` を読んで観点を選び、根拠補強が必要なときだけ `canonical_url` を開く。

## 既定の運用

1. まず `sources.json` を読む
2. 対象に応じて `rules/*.json` を選ぶ
3. `signals` を手掛かりにコードや差分へ当てる
4. 指摘の確度や説明責任を上げたいときだけ `source_refs` に対応する公式原典を開く
5. 原典確認が不要な軽微指摘では、rule と観点の説明だけで返してよい

## ファイル構成

- `sources.json`: 公式資料の台帳。`doc_id`、`canonical_url`、`when_to_use` を持つ
- `rules/context.json`: Context 伝搬、cancel、WithValue の観点
- `rules/errors.json`: error wrap、握りつぶし、error string の観点
- `rules/testing.json`: 回帰テスト、subtest、parallel test、fuzz の観点
- `rules/concurrency.json`: goroutine lifetime、共有状態、loop closure の観点
- `rules/api-design.json`: package 境界、命名、ゼロ値、interface 設計の観点
- `rules/documentation.json`: package comment、doc comment、並行安全性コメントの観点

## 設計方針

- 主軸は `review-guide` と `package-doc`
- `language-reference` は高難度の根拠補強だけに使う
- `Effective Go` は補助資料扱いに留める
- `go vet` は観点抽出には使うが、絶対判定には使わない
