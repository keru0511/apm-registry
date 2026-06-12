# テクニカルライティング索引の使い方

このディレクトリでは、一次ソース由来の文書評価基準を逆引きするための索引を管理する。
正本は `../corpus/*.toon` にあり、各文書は `section -> subsection -> key_points/source_passages` の階層を持つ。通常は `documents.json` と `mappings/*.json` から候補 subsection を引き、必要な観点だけ読む。

## 既定の運用

1. 評価モードを選ぶ。
2. 対応する `mappings/*.json` を読む。
3. `related_subsections` を優先して根拠候補を集める。
4. 用語ゆれで探すときは `aliases.json` を先に見る。
5. 観点から引くときは `topics.json`、control 単位で辿るときは `rules.json` を使う。
6. `documents.json` で文書メタデータと `corpus_file` を確認する。
7. 説明品質の診断では `official` と `standard` を優先し、不足時だけ `framework` と `style-guide` を使う。
8. 必要な `key_points` と `source_passages` だけ本文に降りる。

## 出力時のルール

- 既定では逐語引用しない
- 結果には少なくとも `文書名` `版` `カテゴリ` `URL` を残す
- 公的基準と style-guide を混在させる場合は、どちらを一次根拠にしたか明記する
- `house-rule` は一次ソースとは分けて表示する

## ファイル構成

- `documents.json`: 文書メタデータ、corpus 参照先
- `topics.json`: 論点から section/subsection を引く逆引き索引
- `rules.json`: rule_id から section/subsection を引く逆引き索引
- `aliases.json`: 用語ゆれや検索語から subsection に着地する索引
- `../mappings/*.json`: 評価モードごとの control 定義
- `../corpus/*.toon`: 正本
