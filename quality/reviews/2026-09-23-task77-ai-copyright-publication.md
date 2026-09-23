# 課題77 — ai-copyright連動表示・工程6（完成確認と公開）

実施日: 2026-09-23。[6工程計画](../designs/2026-09-22-task77-connected-layout-rollout-guide.md)の工程6。
[工程5の検証記録](2026-09-23-task77-ai-copyright-quality.md)の続き。

## 結論（先に）

**オーナー承認を受け、`docs/ai-copyright-reaction-map.html`を有効化し本番反映した。**
有効化（工程1〜5では一時プレビューでしか確認していなかった、実ファイルへの本適用）で
初めて顕在化する不具合を2件発見し、その場で修正してから反映した。

## 有効化で初めて見つかった問題（工程1〜5の候補確認では気づけなかったもの）

工程1〜5はすべて一時的なプレビュー（`docs/_preview-*.html`、作業ツリー限定）で確認しており、
本番ファイル自体への適用は工程6が最初だった。適用した瞬間に、以下2件が顕在化した。

### 1. `verify_number_provenance.py`の照合モジュール未登録

読書面の理由内訳・共通の心配の件数が「説明できない数字」として検査に引っかかった。
原因は`scripts/verify_number_provenance.py`の`COUNT_PROVENANCE_MODULES`（テーマごとに
専用の照合ロジックを呼び分ける辞書）にai-copyrightの登録が無かったこと。**bukatsu-chiikiも
同日（2026-09-23）に同種の欠落（`refresh_planet_section.py`の仕上げ処理がconsumption-tax-cut
だけ決め打ちだった件とは別に、この照合モジュール側でも同じ型の欠落）が発覚・修正されており、
「共有スクリプトがテーマをconsumption-tax-cut決め打ちで呼ぶ」という同じ形の見落としが、
今回は2つ目のスクリプトで再発した形**。`scripts/ai_copyright_count_provenance.py`を
consumption_tax_count_provenance.py（ai-copyrightは理由の立場別内訳を持たないため、
より単純なこちらを土台にした）を土台に新設し、`COUNT_PROVENANCE_MODULES`へ登録して解消。

### 2. 複数論点にまたがる要素のHTML id重複

`data-aic-concern`（共通の心配/vein）と`data-aic-check`（制度確認）は、1件が複数論点に
またがる場合（例: 学習データの情報開示は学習データ・無断利用と法制度・規制整備の両方に
関係）、各論点の読書面`<template>`へ複製される設計。件数・本文を照合するために付けていた
`id`（`aic-concern-count-{vid}`・`aic-check-note-{cid}`）は論点で区別していなかったため、
複製先の数だけ同じidがページ内に重複し、HTMLとして不正な状態になっていた（`validate()`は
論点ごとのtemplate単体でしか整合を見ておらず、ページ全体でのid一意性は検査していなかった
ため、工程1〜5では気づけなかった）。両方のidを`{論点id}-{元のid}`の形へ変更し、
`scripts/ai_copyright_count_provenance.py`も論点ごとに照合するよう対応。修正後、
ページ全体でid重複が0件であることを機械的に確認した。

いずれも**表示内容そのもの（件数・本文）に誤りは無く**、検査の照合先・HTMLの構造上の
不備だった。修正後、全体1131件・標準検査5種いずれもOK、`verify_number_provenance.py`は
「拾った336／説明できた336／説明できない0」。

## 公開までの手順

1. `scripts/ai_copyright_connected.py`の`apply(activate=True)`を`docs/ai-copyright-reaction-map.html`
   本体へ適用（このコミットで初めて本番ファイルを書き換えた）
2. 上記2件を発見・修正し、再適用して問題が解消したことを確認
3. `release`スキルの手順どおりマージ・検査・push・CI確認・本番URL確認
4. 台帳（`TASK_BOARD.md`・`THEMES.yaml`）を更新

## 次にすること

公開後の初回観察（1週間程度、表示崩れ・操作エラーの有無）。課題90（潮目ウィジェットの
定期更新未反映）は本課題の範囲外のまま、別課題として引き続き未着手。
