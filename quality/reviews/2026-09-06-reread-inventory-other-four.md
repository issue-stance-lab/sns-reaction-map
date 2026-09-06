# 再読棚卸し：消費税・副首都・憲法・皇室

2026-09-06。親担当による既存証拠の照合。新規再読は行っていない。

| テーマ | 現行意見 | 論点編集再読 | 主張確認の保存ID | うち現行意見 | 本文確認記録未確認 |
|---|---:|---:|---:|---:|---:|
| 消費税減税 | 3358 | 0 | 72 | 64 | 3294 |
| 副首都 | 1453 | 0 | 15 | 15 | 1438 |
| 憲法改正 | 1372 | 0 | 34 | 34 | 1338 |
| 皇室典範 | 1282 | 0 | 21 | 15 | 1267 |

主張候補を1件ずつ本文で確認した旨が、claim_postsの方法欄または生成器の説明にある。採用IDを現行の意見集合へ照合した。消費税の8件・皇室の6件は正典にはあるが非意見なので主表から除外。副首都の古いテーマ記録の「延べ14・実質13」は最新データと異なり、現行は延べ16・一意15で数えた。

これらは特定の主張をしているかという限定目的の確認であり、論点全体を細かく整理した編集再読ではない。自動抽出をそのまま数えたものとは区別する一方、読了時点の全本文指紋を持たないので、最新本文に対する新たな精査済みとはしない。

確認者はGitのClaude共著記録からAI支援の編集作業と分かる。オーナーが投稿ごとに読んだ証拠は確認できない。

全ローカルbranch tipのdata/とconfigs/planet/を検索し、この4テーマで新ページ用の編集再読・論点設定等は見つからなかった。各claim_postsの異なるGit版も調べ、mainにない追加IDはなかった。稼働worktreeの同領域も確認。スキャンの一覧と証拠は非公開JSONへ保存。

data/review-ledger.jsonのreviewed表示は代表要旨とAI要約の差分を機械集計したものなので、本文再読へは計上しない。

## 再現

[再現コード](reproduce/reread_inventory_other_four_20260906.py) は原本・claim記録・Git版を読み、private出力先にID集合を保存する。正典本文は出力しない。出力はリポジトリ外の新しい場所へ指定する。

```sh
python3 quality/reviews/reproduce/reread_inventory_other_four_20260906.py \
  --root . \
  --out /Volumes/HD-LE-B/issue-stance-private-backups/data-repairs/reread-inventory/other-four-recheck
```

成功の形：対象意見64 / 15 / 34 / 15、論点編集再読は各0。新しい未調査の再読ファイル・過去版固有ID・正典変更があれば、その内容を調べてから集計を更新する。

## 固定したprivate JSONの指紋

- consumption-tax-cut: `4db072542fb954a59653653b74daaddfa1a477fc8fd105b96f0dee385d18da1f`
- fukushuto: `367b73bb749373221850fbc27290d29a88c34b84ce38d868069e6615ecdb9a35`
- constitutional-amendment: `64ff141001914980cd816ed7f8f2b26580eab3a47077cde09c20c0547c687fce`
- koshitsu-tenpakai: `67a91c4ce7f5e8d66355f238d8f2f62aca0ffc437ee5960c0d0b1b0116c92781`
