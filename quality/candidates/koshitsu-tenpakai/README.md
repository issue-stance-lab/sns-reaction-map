# 皇室典範のページ候補

状態：2026-09-13の非公開・未採用候補。`inputs/` は本番用の入力配置を保持した候補一式であり、通常の更新器から参照されない。`comparison.json` は旧・候補の対照、`manifest.json` は候補と証拠の版を固定する。本文や生の投稿IDは置かない。

判断の範囲、未確認事項、検査結果は [完成記録](../../reviews/2026-09-13-koshitsu-page.md) にまとめた。生成ページは [確認用HTML](../../prototypes/koshitsu-tenpakai-page-preview.html)。

復元はリポジトリのルートから実行する。非公開バックアップの `candidate.private.json` と主張対応表が必要。成功時は「候補入力の復元完了」と表示される。

```sh
python3 scripts/restore_koshitsu_page_candidate.py --private-dir /Volumes/HD-LE-B/issue-stance-private-backups/data-repairs/koshitsu-tenpakai/20260913-page --stage-root /Volumes/HD-LE-B/issue-stance-private-backups/data-repairs/koshitsu-tenpakai/20260913-page/replay
```

候補HTMLを再生成する。成功時は「独自性検査: OK」「候補完成」と表示される。公開ページの元の版が変わっていれば止まる。

```sh
python3 scripts/build_koshitsu_page_candidate.py --stage-root /Volumes/HD-LE-B/issue-stance-private-backups/data-repairs/koshitsu-tenpakai/20260913-page/replay
```

`inputs/scripts/build_koshitsu_process_sections.py` は候補の照合定義を保持するコピーで、公開中の生成器を置き換えてはいない。本番へ適用するには独立監査、数値変更の確認、通常更新経路への接続、公開承認が必要。
