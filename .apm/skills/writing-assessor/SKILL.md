---
name: writing-assessor
description: 作成済みの文書をテクニカルライティング観点で評価し、用途別チェックリストを作成または調整したうえで、根拠付きスコア、改善優先度、改稿方針をMarkdownで出力するスキル。設計書、仕様書、手順書、運用文書、API説明、提案資料に加えて、メールやレビューコメントで指摘されがちな主語、省略、文分割、送り仮名、外来語表記、句読点、禁則処理、段落の流れ、説明順序、文書型の混在まで確認したいときに使う。
---

# テクニカルライティング評価スキル

このスキルは、文書を感覚で添削するのではなく、`toon corpus + index + mapping` から根拠を引いて、再現可能なレビューと採点に落とすために使う。

## 最初に読むファイル

1. `references/index/documents.json`
2. `references/index/README.md`
3. 評価モードに応じて次のいずれか、または複数
   - `references/mappings/structure-controls.json`
   - `references/mappings/explanation-controls.json`
   - `references/mappings/sentence-controls.json`
   - `references/mappings/notation-controls.json`
   - `references/mappings/layout-controls.json`
   - `references/mappings/house-rules-controls.json`
4. 必要に応じて次を追加
   - `references/index/topics.json`
   - `references/index/rules.json`
   - `references/index/aliases.json`

通常は `mappings/*.json` から観点を選び、`topics.json` と `aliases.json` で関連 subsection を特定し、必要な `key_points` と `source_passages` だけ `references/corpus/*.toon` から読む。説明品質や文書型の診断では、まず `official / standard` の根拠を優先し、不足時のみ `framework / style-guide` を補助根拠に使う。

## 参照データの性格

- `references/corpus/*.toon`: 一次ソース由来の要点を `section -> subsection -> key_points/source_passages` で持つ正本
- `references/index/*.json`: topic、rule、用語ゆれから relevant subsection を逆引きする索引
- `references/mappings/*.json`: レビュー観点ごとの評価項目定義

公的基準と補助ガイドを分けて扱う。

- `official`: 文化庁、内閣告示、JIS
- `standard`: ISO
- `framework`: Divio
- `style-guide`: Google、Microsoft、GitHub Docs
- `house-rule`: チームや組織で運用する数値目安やメール細則

`1文60字目安` や `2行超なら分割` のような社内運用ルールは、この skill では一次ソース由来の観点と分けて `house-rule` 扱いにする。社内細則が無い場合は、style-guide を補助根拠として使う。

## 評価モード

最初に次のいずれかを選ぶ。

- `structure`: 文書全体の構成、目的、見出し、読者適合、行動可能性を見る
- `explanation`: 段落の流れ、説明順序、段落内の視線停止点、スクロール前提の密度過多、文書型の混在、表や箇条書きの説明不足を見る
- `sentence`: 主語、省略、1文1義、文分割、曖昧表現、受け身の多用を重点確認する
- `notation`: 漢字かな、送り仮名、外来語、表記ゆれ、用語統一を見る
- `layout`: 句読点、記号、箇条書き化、禁則処理、参照しやすい配置を見る
- `house-rules`: 1文の長さ目安、段落長、空行による段落分割、1画面あたりの情報密度、件名、メール要件先出しなどの運用細則を見る
- `full`: 上の6つを順に実施し、重複指摘を統合する

ユーザー指定がなければ、メール・レビューコメント起点の依頼は `explanation + sentence + house-rules`、文書レビュー全体は `full` を既定とする。

## 実行手順

1. 対象文書の読者、用途、利用場面を1-2文で要約する。
2. 文書タイプを `procedure / specification / reference / proposal / correspondence` から決める。
3. `tutorial / how-to / reference / explanation` のどれに近いかも補助判定し、混在があれば記録する。
4. 評価モードを決める。
5. `mappings/*.json` から該当 control を読み、`related_subsections` を優先して根拠候補を集める。
6. 用語ベースで探すときは `aliases.json` を先に使い、足りなければ `topics.json`、次に `rules.json` を辿る。
7. 文書の記述を読んで、各 control を `適合 / 要改善 / 不適合 / 要確認` で判定する。
8. 各 control を `0点 / 1点 / 2点` で採点し、重み付きで `100点満点` に正規化する。
9. 重大な欠陥は `Critical / High / Medium / Low` で別掲する。
10. 最後に「まず直すべき3点」と、章頭説明文や文書再構成の改稿方針を出す。

## 採点ルール

- `0点`: 欠落している、または誤読・誤操作・誤判断リスクが高い
- `1点`: 一部満たすが、曖昧さ、抜け、表記ゆれ、読みにくさが残る
- `2点`: 期待水準を満たし、読み手の迷いが少ない
- `N/A`: 文書種別に存在しない観点。分母から除外する

重み付き点は `観点重み * (点数 / 2)`、総合点は `重み付き点の合計 / 適用観点重み合計 * 100` で算出する。

## 判定原則

- 文書に書かれている事実だけで採点する
- 推測で満点にしない
- 文体の好みより、理解容易性、検索性、判断可能性、再現性を優先する
- 指摘は必ず修正可能な粒度にする
- 公的基準、規格、style-guide、house-rule を混同しない
- `文字が滑る` のような感覚的違和感は、段落流れ、段落内の視線停止点、空行不足、説明順序、文書型混在、説明不足へ分解して評価する
- `house-rule` は既定では減点理由に使えるが、公的違反とは別枠で表示する
- `。` で文が切れていても同一段落で連続して読みにくい場合は、文分割ではなく `段落分割が必要` として出す

## 出力要件

出力はMarkdownで、最低限次の見出しを含める。

- `評価対象`
- `想定読者と用途`
- `文書タイプ判定`
- `評価モード`
- `評価に使ったチェックリスト`
- `スコア概要`
- `観点別評価`
- `流れの問題`
- `重要な問題点`
- `優先改善項目`
- `改稿方針`
- `冒頭リライト案`
- `適用基準`
- `総評`

`観点別評価` では最低限、`観点 | 重み | 点数 | 判定 | 根拠 | 改善方針 | 出典` を含める。

## 品質チェック

- 評価モードと文書タイプが合っている
- 出典が `official / standard / framework / style-guide / house-rule` のどれか明確
- `N/A` の理由が妥当
- 点数とコメントが矛盾しない
- 重要度と改善順が一致している
