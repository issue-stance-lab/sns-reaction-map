# 段階D：保存回と正典の採用状態を照合する

## 目的と範囲

保存した投稿が正典（集計の基になるデータ）にあるか、正典外ならどんな判断が残っているかを、本文なしで確認する。採用・再分類・削除を実行する機能ではない。

対象は全11登録テーマ（公開10＋高市）、`social-samples/updates/` と `data/verification/updates/` の保存回の和集合、および `configs/adoption-sources.yaml` に明示した旧保存回。初回は46回のraw/classified各2ファイルと旧回10ファイル、計102ファイル。実験・旧再設計・合成データを日付だけで採用候補にしない。プロジェクト内の全ファイルを評価済みという意味ではない。資産の保管境界は段階Eで扱う。

今回の照合元には本文付き原本がなく検証用サマリだけ残る4回（高齢者9/4、あだ名・皇室典範・消費税9/1）も記録する。本文は未確認として残す。私有側だけに残る2回（部活8/9、高市8/29）も含める。片側raw/classifiedの欠落は `missing` で残す。

## ファイルと意味

- `data/verification/adoption/registry.json`: 現時点の所在照合。原文・生の投稿ID・投稿URLを含まない。投稿は既存検証用データと同じ `sha256:SHA256(tweet:<ID>)` で関連付ける。
- `data/verification/adoption/decision-evidence.json`: 既存の採否根拠と固定比較集合。移行日時を過去の判断日時に読み替えない。
- `configs/adoption-sources.yaml`: 追加で追跡する旧回と、今回の対象外の理由。

`in_canonical` は同じ投稿IDが現在正典に存在する意味。保存した当時の本文・分類版がそのまま採用された証明ではない。`observations` に保存ファイル単位の本文・4分類項目の一致／相違／確認不能を残す。同じ投稿を何回観測しても投稿件数は1件。本文差は強調タグ・訂正などでも起こるため、壊れたデータとは断定しない。

`pending_review` は確認待ちの根拠あり、`decision_unknown` は採否を確定できない、`excluded_confirmed` は明示的な除外判断あり、`unresolved` は判断記録なし。今回の正典外525件に `excluded_confirmed` は0件。正典に含まれる意見外の投稿と、正典から除外する判断は別である。将来正典に入った投稿にも過去の判断があれば残し、現在の所在を優先したことを明示する。

`public_opinion_presence` は、原本の指紋と収集・意見数が一致する公開JSONの**集計母数への所属**。ページでその投稿を引用・埋め込み表示した証拠ではない。未公開テーマはfalse、公開JSON未確認ならnull。論点別集計を含む公開JSON全体は既存の `verify_public_registry.py --against-private` で別途再生成検査する。

`kind` は取得内容と証拠形式を表す。`verification` は本文なしサマリからの照合で、raw/classifiedの別は `source_id` 末尾に残す。過去のrun_idが記録されていなければnullのまま。欠けた情報を推測で補わない。

## 運用

原本・保存回・公開集計・判断根拠を変更した担当が、同じ隔離作業ツリーで台帳を再生成する。原本と公開JSONが異なる版なら止まる。判断根拠を変えた場合は先に根拠と判断一覧をレビューし、以前の指紋だけを機械的に更新しない。初回移行スクリプト `import_adoption_decisions_20260906.py` は2026-09-06の証拠専用で、将来の承認登録APIではない。

再生成（原本と外付け保存先が必要）:

```sh
python3 scripts/build_adoption_registry.py --evidence-root /Volumes/HD-LE-B/issue-stance-private-backups/data-repairs
```

成功時は「採用台帳を作成しました」とテーマ別の保存投稿数・正典外件数が表示される。書き換えるのは台帳だけ。元の台帳のsnapshot_atを保持するので、実際の再照合日時を更新する場合は `--snapshot-at` でISO日時を指定する。これは採否決定日時ではない。

現在の入力と完全に一致するか確認する:

```sh
python3 scripts/build_adoption_registry.py --check
python3 scripts/verify_adoption_registry.py
python3 scripts/verify_public_registry.py --against-private
```

成功時は各コマンドがOK・終了コード0。最初の検査は非公開の保存回・正典・採否根拠まで再照合する。2つ目はGit管理ファイルだけで検査でき、公開自動検査にも組み込む。公開側だけでは失われた本文を復元したり、非公開ファイルの変更を検知したりはできない。

同じ外付け保存先が無い環境では `--evidence-root` に移設先を渡す。元資料が無いまま空の配列で上書きして検査を通さない。

## 次の工程との境界

課題59の複数回統合は、この台帳のsource_id・run_id・指紋と、別途レビュー・承認した採用対象を入力にする。`unresolved` や `pending_review` を自動採用する機能は作っていない。課題59の統合／承認適用APIは未実装のまま。

段階Eで保管対象・復元・管理画面へ接続する。課題54の新ページ横展開は独立した工程であり、この台帳の作成だけで公開準備完了にはしない。
