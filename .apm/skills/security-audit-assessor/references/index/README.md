# セキュリティ標準インデックスの使い方

このディレクトリでは、標準文書そのものではなく「どの文書を、いつ、何のために参照するか」を管理する。
通常は `security-standards.json` と `mappings/*.json` だけを読み、原文は必要時だけ公式 URL に降りる。

## 既定の運用

1. 監査モードを選ぶ。
2. 対応する `mappings/*.json` を読む。
3. `related_documents` で参照される文書を `security-standards.json` から引く。
4. `reference_map` で framework 別のカテゴリやファミリを取り出す。
5. まずは文書名、版、framework 別カテゴリ、URL だけで根拠を整理する。
6. `Critical` または `High` の指摘で補強が必要な場合だけ `canonical_url` を開く。

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
- `../mappings/system-controls.json`: 技術監査用の監査項目対応表
- `../mappings/governance-controls.json`: 統制監査用の監査項目対応表
