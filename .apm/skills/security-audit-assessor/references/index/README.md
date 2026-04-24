# セキュリティ標準インデックスの使い方

このディレクトリでは、標準文書の索引、逆引き、検索用メタデータを管理する。
正本は `../corpus/*.toon` にあり、通常は `documents.json` と `mappings/*.json` から必要 section を引いてから corpus を読む。

## 既定の運用

1. 監査モードを選ぶ。
2. 対応する `mappings/*.json` を読み、`related_sections` を確認する。
3. `documents.json` か `security-standards.json` で文書メタデータと corpus path を引く。
4. `topics.json` と `aliases.json` を使って、監査観点や用語ゆれから section を逆引きする。
5. 必要 section だけ `../corpus/*.toon` から読む。
6. `reference_map` で framework 別のカテゴリやファミリを取り出す。
7. まずは文書名、版、framework 別カテゴリ、URL だけで根拠を整理する。
8. `Critical` または `High` の指摘で補強が必要な場合だけ `canonical_url` を開く。

## 出力時のルール

- 既定では逐語引用しない。
- 監査結果には少なくとも次を残す。
  - 文書名
  - 版
  - framework 別カテゴリまたはコントロールファミリ
  - 公式 URL
- 原文まで確認した場合だけ、必要最小限の短い抜粋を付けてよい。
- 公式 URL を確認できなかった場合は `原典未確認` と明記する。
- `combined` では `overlap_group` が同じ項目を統合候補として扱う。

## ファイル構成

- `security-standards.json`: 標準文書の索引
- `documents.json`: 文書メタデータと corpus 参照先
- `topics.json`: topic から section を引く逆引き索引
- `controls.json`: control_id から section を引く逆引き索引
- `aliases.json`: 用語ゆれと検索キーワード索引
- `../mappings/system-controls.json`: 技術監査用の監査項目対応表
- `../mappings/governance-controls.json`: 統制監査用の監査項目対応表
- `../corpus/*.toon`: 文書全文を正規化した TOON 正本
