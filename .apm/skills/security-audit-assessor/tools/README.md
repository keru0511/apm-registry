# security-audit-assessor tools

このディレクトリは `security-audit-assessor` の参照データを更新・再生成するための保守用ツールを置く。
`apm` 配布先で通常実行されるものではなく、`references/` を更新するタイミングだけ使う。

## 役割

- `fetch-source`: 原典 URL を `tools/work/raw/` へ取得する
- `normalize-source`: 原典を機械処理しやすい JSON へ正規化する
- `build-source-corpus`: 正規化 JSON を TOON に変換する
- `refresh-source-doc`: `fetch -> normalize -> build` を一気通しする
- `build-audit-corpus`: `tools/work/corpus/*.toon` と annotation policy から `references/corpus/*.toon` を生成する
- `build-audit-index`: `references/corpus/*.toon` から `references/index/*.json` と `references/mappings/*.json` を再生成する
- `promote-source-doc`: 1 文書ぶんの `build-audit-corpus -> build-audit-index -> validate` を通す
- `sync-security-references`: `build-audit-index` の後に validator を通して `references/` を同期する
- `validate-security-corpus`: `references/corpus/*.toon`、`references/index/*.json`、`references/mappings/*.json` の整合確認
- `source-profiles.json`: 原典ごとの抽出戦略、共通正規化器、個別ハンドラ要否の manifest
- `show-source-profile`: どの原典をどう潰すかを `doc_id` 単位で確認する補助コマンド
- `policies/`: index の補助メタデータと mapping の人手管理部分

## 方針

- repo に残す正本は `references/` 配下の最終成果物だけ
- `references/corpus/*.toon` を意味づけ付き正本として扱い、`index` と `mappings` はここから再生成する
- `tools/work/corpus/*.toon` は原文寄りの中間表現で、`tools/policies/annotations/` と結合して `references/corpus` へ昇格する
- raw HTML/PDF や正規化中間生成物は、このディレクトリ配下で扱っても repo 正本にはしない
- repo 共通の実行物はルートの `scripts/` に置き、skill 専用メンテナンスはここに置く
- 原典は一つずつ見て潰すが、手で TOON を書くのではなく `source-profiles.json` に抽出ルールを寄せる
- `priority`、`checkpoints`、`reference_map` のような監査 policy は `policies/` に残し、`related_*` は再生成する

## 更新手順

1. `source-profiles.json` の対象文書について `refresh-source-doc <doc_id>` で `tools/work/corpus` を更新する
2. `promote-source-doc <doc_id>` か `build-audit-corpus --doc-id <doc_id>` で `references/corpus` へ昇格する
3. 全体更新時は `sync-security-references`、確認だけなら `validate-security-corpus` を使う

## 現在の対応状況

- `ipa-safe-website`: `fetch-source`、`normalize-source`、`build-source-corpus`、`refresh-source-doc` まで実装済み
- `ipa-nfr-grade`: `fetch-source`、`normalize-source`、`build-source-corpus`、`refresh-source-doc` まで実装済み
- `ipa-requirements-guide`: `fetch-source`、`normalize-source`、`build-source-corpus`、`refresh-source-doc` まで実装済み
- `nist-csf-2-0`: `fetch-source`、`normalize-source`、`build-source-corpus`、`refresh-source-doc` まで実装済み
- `nist-sp-800-53-r5`: `fetch-source`、`normalize-source`、`build-source-corpus`、`refresh-source-doc` まで実装済み
- `ipa-safe-website`: annotation から `build-audit-corpus` で `references/corpus` へ昇格可能
- `ipa-nfr-grade`: annotation から `build-audit-corpus` で `references/corpus` へ昇格可能
- `ipa-requirements-guide`: annotation から `build-audit-corpus` で `references/corpus` へ昇格可能
- `nist-csf-2-0`: annotation から `build-audit-corpus` で `references/corpus` へ昇格可能
- `nist-sp-800-53-r5`: annotation から `build-audit-corpus` で `references/corpus` へ昇格可能
- `references/index/*.json` と `references/mappings/*.json`: `build-audit-index` で再生成可能
