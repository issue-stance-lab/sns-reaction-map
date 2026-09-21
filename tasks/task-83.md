# 課題83: GROWTH.yamlの継続作業(recurring)がOPERATIONS.mdの定例作業表にもダッシュボードの検知にも入っていない

**状態**: 進行中。汎用の遅延アラートを実装・OPERATIONS.mdへ反映済み(2026-09-21)。gsc-reviewが実際に停滞していないかの確認のみ残る

## 経緯

2026-09-21、オーナー依頼「課題管理の棚卸し・旧課題管理で行っていないものの抽出」で発見。

2026-08-23に運用ループ(`LOOP.md` / `GROWTH_LOOP.md`)を廃止し、`OPERATIONS.md` の期日駆動へ
切り替えた(`archive/OPERATIONS_HISTORY.md`)。廃止理由は「見えている作業は続き、周回に埋め込まれた
見えない作業だけが誰の担当でもなくなった」こと。この切り替えで `build_admin_dashboard.py` を
「遅れの見つけ方の唯一の入口」と位置づけた。

ところが `GROWTH.yaml` の `recurring` には5項目あるうち、`x-posting` 以外の4項目が
この「唯一の入口」から漏れている。

| recurring項目 | cadence | 定義された場所 | OPERATIONS.mdの定例作業表 | ダッシュボードの遅れ検知 |
|---|---|---|---|---|
| `x-posting` | daily | GROWTH.yaml | ○(X日次運用) | ○(render.py で last_run>3日を警告) |
| `x-profile` | weekly・priority: critical | GROWTH.yaml | × | × |
| `gsc-review` | weekly | GROWTH.yaml | × | × |
| `kpi-snapshot` | weekly | GROWTH.yaml | ○(KPIスナップショット) | △(`kpi.snapshots`の最新日で代替検知。recurring自体のlast_runは見ていない) |
| `note-posting` | 3日に1本目安 | GROWTH.yaml | ○(note 記事) | × |

`scripts/admin_dashboard/collect.py` の `_collect_recurring()` は5項目とも収集しているが、
`render.py` でアラートに使っているのは `x-posting` だけ(該当箇所: render.py 646〜661行)。
残り4項目は集計されるだけで、画面のどこにも「遅れています」という警告が出ない。

**実例**: `x-profile`(初期トラクション最優先・priority: critical)の `last_run` が
2026-07-09のまま2026-09-21まで74日間更新されていなかった。これは
`archive/OPERATIONS_HISTORY.md` が旧ループ崩壊の証拠として名指ししていたのと同じ値。
実際にはbio・固定ポストは8/2に、Xヘッダー画像も(いつかは記録が無いが)既に更新されており
実害は無かったが、それが分かったのはオーナーが「フォロワーが増えない」と相談した際の
アドホックな確認(9/16)と、今回の棚卸しでの実機確認(9/21)によるもので、
**どちらも「唯一の入口」であるはずのダッシュボードは何も警告していなかった。**
(x-profileのlast_run更新とtask-32.mdの訂正は本課題の発見と合わせて実施済み)

`gsc-review` も同様に `last_run: 2026-07-26` のまま(57日間)。こちらは実際に停滞している
可能性があるが未確認(本課題の対応範囲外。確認自体は次にすることの1つ)。

## 対応方針 → 実装内容(2026-09-21)

当初は「`cadence` 文字列(`daily` / `weekly` / …)から警告閾値を機械的に出す」案を考えていたが、
実装前に実データを確認したところ `cadence` は自由記述で、`x-posting` は
「daily（候補確認…）+ per-theme-publish（告知）+ weekly（レビュー）」、`note-posting` は
「3日に1本を目安（候補なしは見送り可）+ per-theme-publish（新テーマ公開時）」のような
複合文だった。これを文字列解析で機械的に閾値化するのは無理があり、誤検知
（例: note-postingは「候補なしは見送り可」なので単純な日数超過が遅れとは言えない）を生む。

そのため方針を変更し、**recurring項目ごとに `stale_after_days`（警告を出すまでの日数）を
GROWTH.yaml側で明示的に持たせる**方式にした。この値を持つ項目だけを汎用チェックの対象にする。

- `scripts/admin_dashboard/collect.py` `_collect_recurring()`: `stale_after_days` を収集するよう追加
- `scripts/admin_dashboard/render.py` `section_alerts()`: `x-posting`(既存の専用ロジックを維持)
  以外で `stale_after_days` を持つ項目を汎用ループでチェックする処理を追加
- `GROWTH.yaml`: `x-profile`・`gsc-review` に `stale_after_days: 10` を設定
  （既存の週次KPI・X週次レビューのアラートと同じ「7日+3日の猶予」に合わせた）
- `kpi-snapshot` には設定していない。`kpi.snapshots` の最新日で別途検知済みのため、
  二重・矛盾するアラートを避けた
- `note-posting` には設定していない。「候補なしは見送り可」という個別事情があり、
  単純な日数超過では誤検知になるため(汎用チェックの対象外にする、という判断自体をテストで固定)
- `tests/test_admin_dashboard.py` に `RecurringStallTests` を追加（4件）
- `OPERATIONS.md` の「遅れの見つけ方」の一覧と「定例作業の一覧」表を更新

## 次にすること

1. `gsc-review` の `last_run`(2026-07-26)以降、Search Consoleの表示回数・CTRを実際に見直したか確認する。していなければ実施する

## 影響範囲

`scripts/admin_dashboard/`・`GROWTH.yaml`・`OPERATIONS.md`・テストのみ。
公開ページには影響しない。`run_public_checks.py`には`tests/`が含まれるため、テスト追加分もCIで確認される。
