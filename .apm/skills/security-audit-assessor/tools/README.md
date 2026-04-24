# security-audit-assessor tools

このディレクトリは `security-audit-assessor` の参照データを更新・再生成するための保守用ツールを置く。
`apm` 配布先で通常実行されるものではなく、`references/` を更新するタイミングだけ使う。

## 役割

- `fetch-source`: 原典 URL を `tools/work/raw/` へ取得する
- `normalize-source`: 原典を機械処理しやすい JSON へ正規化する
- `build-source-corpus`: 正規化 JSON を TOON に変換する
- `refresh-source-doc`: `fetch -> normalize -> build` を一気通しする
- `validate-security-corpus`: `references/corpus/*.toon`、`references/index/*.json`、`references/mappings/*.json` の整合確認
- `source-profiles.json`: 原典ごとの抽出戦略、共通正規化器、個別ハンドラ要否の manifest
- `show-source-profile`: どの原典をどう潰すかを `doc_id` 単位で確認する補助コマンド

## 方針

- repo に残す正本は `references/` 配下の最終成果物だけ
- raw HTML/PDF や正規化中間生成物は、このディレクトリ配下で扱っても repo 正本にはしない
- repo 共通の実行物はルートの `scripts/` に置き、skill 専用メンテナンスはここに置く
- 原典は一つずつ見て潰すが、手で TOON を書くのではなく `source-profiles.json` に抽出ルールを寄せる

## 次の実装単位

1. `source-profiles.json` の優先順に原典を処理する
2. 各原典で `fetch -> normalize -> build-corpus` の差分点を handler に閉じる
3. 共通で吸える部分は shared normalizer に寄せる
4. 生成後は `validate-security-corpus` を通す

## 現在の対応状況

- `ipa-safe-website`: `fetch-source`、`normalize-source`、`build-source-corpus`、`refresh-source-doc` まで実装済み
- `ipa-nfr-grade`: `fetch-source`、`normalize-source`、`build-source-corpus`、`refresh-source-doc` まで実装済み
- `ipa-requirements-guide`: `fetch-source`、`normalize-source`、`build-source-corpus`、`refresh-source-doc` まで実装済み
- `nist-csf-2-0`: `fetch-source`、`normalize-source`、`build-source-corpus`、`refresh-source-doc` まで実装済み
- `nist-sp-800-53-r5`: `fetch-source`、`normalize-source`、`build-source-corpus`、`refresh-source-doc` まで実装済み
