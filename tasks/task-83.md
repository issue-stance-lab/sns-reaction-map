# 課題83: GROWTH.yamlの継続作業(recurring)がOPERATIONS.mdの定例作業表にもダッシュボードの検知にも入っていない

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

## 対応方針(未着手)

`render.py` の `_collect_recurring()` が返す全項目について、`x-posting` と同じ要領で
「cadenceに対してlast_runが古すぎる」ときにアラートを出す**汎用のチェック**に置き換える。
項目ごとの個別ハードコードを増やすのではなく、`cadence` 文字列(`daily` / `weekly` / …)から
警告閾値を機械的に出す関数にすることで、今後 `recurring` に項目を足したときも
自動的に検知対象へ入るようにする(OPERATIONS.md 70行目「新しく定例にしたい作業があるときは
…ダッシュボードが遅れを検知できるようにすること」の原則にも合致する)。

## 次にすること

1. `gsc-review` の `last_run`(2026-07-26)以降、Search Consoleの表示回数・CTRを実際に見直したか確認する。していなければ実施する
2. `render.py` に汎用の recurring 遅延チェックを実装し、`tests/test_admin_dashboard.py` にテストを足す
3. `OPERATIONS.md` の「定例作業の一覧」表に `x-profile` と `gsc-review` の行を足す

## 影響範囲

`GROWTH.yaml` の記録・`company/dashboard/dashboard.html` の表示のみ。
公開ページ・検査(CI)には影響しない。
