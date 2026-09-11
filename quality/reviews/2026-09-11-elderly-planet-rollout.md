# 高齢者の運転免許返納：山なみ形式への展開（2026-09-11）

部活動に続く2テーマ目。[[reference_planetpage_rollout]] に沿って進めた
（このメモ自体、下記の発見を反映して更新済み）。作業ツリー `../isa-wt-elderly-planet`
（ブランチ `task/elderly-planet-adapter`）。

## 段階0：編集部の横断整理・資料にあるのに、SNSにないこと

- `data/verification/elderly-license-revocation-editorial.json`：共通する前提1件・
  本当の対立2件・まだ分からないこと2件、計5件をAI下書き。オーナー確認済み
- `data/verification/elderly-license-revocation-sunk-continents.json`：一次資料メモ
  （`quality/research/elderly-license-revocation-primary-sources.md`）から、
  SNS投稿では0〜2件しか触れられていない4件を選定。実データで機械照合し、
  検査（verify_ocean_layer.py の個別検査）はエラー0件。「立場をこえて同じ心配」
  （地下水脈、最低2本）は今回見送り、単独では全体検査の対象に含まれない
  既知の制限として残した

## 段階1：定例更新スクリプトのガード

`build_elderly_arena.py`（`apply_public_counts`/`build`）・`build_elderly_process_sections.py`
（`build`）の計3関数。部活動と同じ不具合クラス（削除済みセクションへの無条件操作・
目印コメントだけ残る復活バグ）に加え、**部活動では出なかった新しい不具合**：
削除される旧セクションと同じクラス名・見出し文言を、山なみ本体側が別の意味で
再利用しており、置換が「1箇所一致」でエラーなく成立してしまい、**新デザイン側を
誤って上書きするところだった**（サイレントな誤爆。エラーで気づける不具合より
危険）。実際に山なみへ差し替えた見本を作り、各関数を新旧両方のページに対して
実行して確認した。

STEP2の投稿対応表（`{theme}-claims.json`）は一次資料クイズが引き続き読むため、
HTML差し込みだけを止め、対応表の更新は山なみ形式でも継続するよう分岐した
（部活動には無かった配慮。理由は build_elderly_process_sections.py 側のコメント）。

## 段階2：ページ検査の確認 → 差し替え機能そのものの不具合を発見

`verify_theme_page.py` の山なみ対応ロジックはテーマ名を問わない作りで、
そのまま使えた（新規コードはほぼ不要）。ただし実際に差し替えて検査したところ、
2つの新規不具合が見つかった。

1. **`build_generic()`（bukatsu-chiiki以外の汎用差し替え関数）の削除対象が不完全**。
   「論点別サマリー」「スタンス集計」という2つの旧デザインの表を消し忘れており、
   山なみと二重表示になっていた。「最大勢力バッジ」検査が検出。共通関数側を直した
   （bike-blue-ticket 等、今後同じ関数を使う他テーマにも効く）
2. **「同じ数字は1回だけ」検査の誤検知**。論点の中の島の分類名（例:
   「安全技術・自動運転による対策を求める意見」）がたまたま「意見」で終わり、
   ページ全体の意見数の誤記と誤認識していた。`verify_theme_page.py` 側の
   地の文抽出から `class="islands"` を除外して解消（全テーマ実行で影響なしを確認）

## 段階3：実際の差し替えと数字の出所・文章の使い回し

`configs/elderly-license-revocation-reaction-map.json` の `number_provenance` に、
新設の内訳表示（凡例・立場別シェア＝`sides`/`legend`）を機械集計対象へ、
編集部手作業の内訳（`islands`）・一次資料クイズの引用文（`srclist`/`claims`）・
編集部横断整理（`findings`）・地下水脈（`sunk`）・埋め込みJSON（`#planet-data`）を
除外対象へ追加。拾った281件中34件の「説明できない」を0件まで解消（部活動と
同じ作業内容）。

**2テーマ目で初めて分かったこと**：`verify_page_originality.py`（ページ間の
文章使い回し検査）が、共通テンプレートの定型文（見出し・凡例・操作説明）を
「使い回し」と誤検知した。1テーマだけのときは比較対象が無く気づけなかった。
`configs/page-originality.json` の `shared_selectors` に、山なみ本体が生成する
定型の見出し・キャプション類（`sec`/`subsec`/`hint`/`dot-cap`/`tap-hint`/
`floor-note`/`meta`/`sub`/`caution`）を追加。編集部が書く本文（クイズの判定文・
横断整理・島・地下水脈）は対象に含めていないため、意図的な複製は今まで通り
検出される。

## 結果

標準4検査（ページ検査・数字の出所・再生成可能性・文章の使い回し）NG0件、
917テスト全てOK、冪等性（同一入力2回で完全一致）確認済み。マージ `6813bf1`
（作業ツリー内。**main への統合・pushはまだしていない**）。
