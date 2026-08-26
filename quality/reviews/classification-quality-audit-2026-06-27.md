# 分類品質監査 2026-06-27

課題7「現在テーマのデータ補充」後に、Hermes相当サブエージェントで分類結果をサンプリング監査した。

## 総評

100件をカテゴリ別に抽出して確認した。

- 比較的よい: `takaichi`, `constitutional`
- 再分類・設計見直し優先: `school-nickname-ban`, `henoko`
- 中程度だが改善余地あり: `ai-copyright`

## テーマ別結果

| テーマ | 正分類 | 誤分類 | 判断困難 | 評価 |
| --- | ---: | ---: | ---: | --- |
| `ai-copyright` | 11/20 | 7/20 | 2/20 | `category` と `stance` の矛盾、逆分類が目立つ |
| `school-nickname-ban` | 13/20 | 6/20 | 1/20 | 保留自体は妥当だが、分類可能投稿の保留・誤分類あり |
| `takaichi` | 15/20 | 3/20 | 2/20 | 比較的よいが、高市批判/擁護の逆分類が一部あり |
| `henoko` | 10/20 | 7/20 | 3/20 | 批判対象の混同が多く、再分類推奨 |
| `constitutional` | 14/20 | 4/20 | 2/20 | 比較的よいが、単語だけの投稿を賛成扱いする例あり |

## 重大な誤分類例

- `ai-copyright_classified.json`
  - 例: 生成AI廃止が妥当という趣旨
  - 現分類: `AI技術推進・過度な規制は競争力を損なう`
  - 推奨: `著作権厳格保護・クリエイターの権利回復を最優先` または批判系カテゴリ
  - 理由: 生成AIに全面否定的で、推進ではない。

- `school-nickname-ban_classified_v2.json`
  - 例: あだ名禁止でよいという趣旨
  - 現分類: 一律禁止に反対
  - 推奨: いじめ防止・心理的安全系
  - 理由: 本文はあだ名禁止を肯定している。

- `takaichi_realtime_ollama_final_reclassified_editorial.json`
  - 例: 高市氏の発言・疑惑を批判する趣旨
  - 現分類: `高市氏擁護・報道批判`
  - 推奨: `高市氏批判・責任追及`
  - 理由: 投稿者は高市氏を批判している。

- `henoko_realtime_expanded_classified_editorial.json`
  - 例: 文科省判断に反対する趣旨
  - 現分類: `学校・教育委員会批判`
  - 推奨: `文科省判断への反発・平和教育萎縮を懸念`
  - 理由: 批判対象は学校ではなく文科省判断。

- `constitutional_amendment_classified_refreshed.json`
  - 例: 緊急事態条項という単語のみ
  - 現分類: `緊急事態条項に賛成`
  - 推奨: `その他・分類保留`
  - 理由: 単語だけで賛成とは判断できない。

## 改善案

- `school-nickname-ban` は賛否分類をやめ、論点分類に寄せる。
  - 体験談
  - 一律禁止への違和感
  - いじめ防止
  - さん付け・敬称
  - 柔軟運用
  - 情報共有・立場不明

- `henoko` は構造化分類を強める。
  - `actor_target`
  - `criticized_target`
  - `reaction_type`
  - `risk`

- `article_usable` を厳しくする。
  - ニュース共有のみ
  - URL紹介のみ
  - 単語のみ
  - 引用元の見出しだけ
  - 上記は原則 `false`

- `stance` はカテゴリごとに再定義する。
  - `ai-copyright` の `規制反対` / `規制賛成` は揺れが大きい。
  - 政治系は `政策賛否` と `人物批判` を分ける。

- 代表投稿は `confidence` だけで選ばない。
  - `article_usable: true`
  - `risk: low`
  - ニュース共有のみではない
  - `stance` と `category` が矛盾していない

## 次アクション

- 課題9で `school-nickname-ban` と `henoko` を優先して分類設計を再構築する。
- 公開集計では、分類精度の低いテーマに「検索サンプル整理であり、分類誤差を含む」旨の注記を強める。

