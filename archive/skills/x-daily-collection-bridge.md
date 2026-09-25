> **廃止（2026-09-25）。** 収集と公開は同じセッションで行うことになり、X日次での収集は行わない。
> 現在の手順は `DATA_REFRESH.md`「収集と公開は同じセッションで」。

# テーマ収集の橋渡し（課題81）

X日次の**候補提示が終わったあと、20時以降（夜枠）のときだけ**読む。収集が遅れているテーマを
最大1本だけ収集する。本文確認・正典反映・公開はしない（`DATA_REFRESH.md`の16ステップ中、
収集・自動分類・非公開保存の1ステップだけ）。X日次は1日に複数回（朝・昼・夕・夜など）呼ばれる
運用が通常だが、収集は夜枠だけに絞る（朝・昼・夕は候補作成だけの軽い作業のままにする）。

**2026-09-22、初回実運用で朝の候補作成と収集がほぼ同じ時間帯に重なり負担が大きくなったため、
「開始時・最大1テーマ」から「候補提示後・夜枠のみ・最大1テーマ」へ変更した。** 1日1回までに
絞る理由（X日次は朝・昼・夕・夜と1日に複数回呼ばれる）は変わらない。夜枠が無い日は、その日の
収集チェックは行わない（翌日以降の夜枠、または課題69の個別収集セッションで追いつく）。

## -1. 時刻を確認する（夜枠かどうか）

```bash
date +%H:%M
```

20:00より前なら収集チェックはせず、候補作成へ戻る。20:00以降のときだけ次へ進む。

## 0. 今日すでに収集済みか確認する

```bash
grep last_refresh_attempt_at THEMES.yaml
```

いずれかのテーマが今日の日付なら、収集はスキップして本日の手順3（読む）へ進む。
課題69など、X日次を経由しない収集がその日すでに走っていた場合もこれで二重収集を避けられる。

## 1〜2. 収集遅れを確認し、最も遅れている1本を選ぶ

```bash
python3 scripts/build_admin_dashboard.py
```

`collect_at` を過ぎている、または当日のテーマがなければ、収集はせず手順3へ進む。
あれば最も遅れている1本だけを選ぶ。複数まとめない（期限超過が積み上がっている日でも
今日の負荷は一定にする）。

## 3. 収集する

```bash
# 既存の収集専用worktreeがあれば使い回す(無ければ固定名で新規作成)
cd /Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator
if git worktree list | grep -q "isa-wt-collect-<テーマ>"; then
  cd ../isa-wt-collect-<テーマ>
  git fetch origin && git merge origin/main
else
  git worktree add ../isa-wt-collect-<テーマ> -b task/collect-<テーマ>
  cd ../isa-wt-collect-<テーマ>
fi

# 非公開正典の復元・node_modules複製(OPERATIONS.md ⓪。gitignore対象でworktreeには無い)
tar xzf "$(ls -t /Volumes/HD-LE-B/issue-stance-private-backups/private-data-*.tar.gz | head -1)" \
  -C . --exclude=manifest.json
cp -R /Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator/node_modules .

RUN_DATE=<今日の日付>
RUN_ID=$(date +%Y%m%d_%H%M%S)
python3 scripts/refresh_topic.py \
  --topic <テーマ> --date "$RUN_DATE" --run-id "$RUN_ID" \
  --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups
```

`--promote` は付けない。正典・公開ページには触れない。worktree名・ブランチ名はテーマごとに
固定する（`isa-wt-collect-<テーマ>` / `task/collect-<テーマ>`）。日付や実行のたびの連番を
名前に入れない。後から「このテーマの収集worktreeがどれか」を探すため、かつ次回このテーマの
収集で使い回すために、固定名であることが要る。

## 3.5 収集直後にJevをシャドー観測する（課題91）

収集・Hermes分類が成功した場合だけ、今回の新規分をJevへ送る。これは品質測定用であり、
正典・公開ページ・X投稿・世論の潮目を変更しない。

```bash
python3 scripts/run_jev_shadow.py \
  --topic <テーマ> --date "$RUN_DATE" \
  --input ".staging/refresh/<テーマ>/$RUN_ID/new-only.json" \
  --output "social-samples/updates/<テーマ>/$RUN_DATE/jev-shadow.json" \
  --verification-output "data/verification/updates/<テーマ>/$RUN_DATE/jev-shadow.json" \
  --env-file /Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator/.env \
  || echo "WARN: Jev shadow failed; continue the normal collection handoff"
```

`new-only.json`だけを入力にする。`TYPESAFE_API_KEY`が無ければスクリプトが
`skipped_no_key`を記録して終了する。APIエラー時も再試行を重ねず、失敗を短く記録して
手順4へ進む。Jevのレポートには入力本文をコピーせず、非公開側にはハッシュ化したレコード識別子と
構造化された回答だけを保存する。公開側サマリにも本文・URL・投稿IDを入れない。

**失敗したら**（外付けバックアップディスク未接続・hermes障害・`node_modules`不足など、
`DATA_REFRESH.md`に前例あり）、その日の収集は見送ったものとして手順3へ進む。
無理に復旧を試みない。原因を短く記録し、後続の手順（候補作成）を止めない。

## 4. コミットしてmainへ反映する

```bash
cd /Volumes/M2-WorkSpace/Projects/副業/isa-wt-collect-<テーマ>
# 新しい更新回を採用台帳と保全台帳へ載せる（載せないと公開ファイルの検査が
# 「new verification wave is outside snapshot」で落ちる。2026-09-22の初回運用で発覚）
python3 scripts/build_adoption_registry.py
python3 scripts/build_adoption_registry.py --check
python3 scripts/data_asset_inventory.py

git add THEMES.yaml themes/<テーマ>.md data/verification/updates/ \
  data/verification/adoption/registry.json company/data-assets.json company/data-backup-status.json
git commit -m "収集: <テーマ> <日付>"
python3 scripts/run_public_checks.py   # 終了コード0を確かめてからマージへ進む

cd /Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator
git merge --no-ff task/collect-<テーマ> -m "Merge branch 'task/collect-<テーマ>'"
python3 scripts/verify_themes_yaml.py
python3 scripts/verify_update_provenance.py
git push
```

成功の形: `git merge` が `Merge made by the 'ort' strategy.`、2つの `verify_*.py` が
ともに終了コード0、`git push` が `main -> main` の行を出す。

**共有ツリーに別セッションの未コミット変更があってマージできないとき**（`company/data-backup-status.json`
などの台帳は、別セッションのバックアップでよく書き換わっている）は、共有ツリーのファイルに触れない。
収集worktreeの中で `git merge origin/main -m "..."` → 上の検査を再実行 → `git push origin HEAD:main` で送る
（2026-09-22の初回運用で実施）。

- **ページ整合性検査一式（`verify_theme_page.py` / `verify_number_provenance.py` /
  `unittest discover` / `run_public_checks.py`）は実行しない。** ページを変えていないため
  的外れで、時間もかかる。これらは本文確認・公開のときに`release`スキルの正規手順で通す
- 検査（`verify_themes_yaml.py` / `verify_update_provenance.py`）は**マージした後のmainで**
  通す。作業ツリーで通したかどうかは根拠にならない（`release`スキルと同じ理由）
- 検査で落ちたら、収集worktree側で直してコミットし直し、マージからやり直す。
  衝突したらその場で直さずオーナーへ報告する（`release`スキルの規定と同じ）
- `social-samples/` 配下の非公開データは収集worktreeに残したままでよい
  （`refresh_topic.py` が更新回確定時に自動でバックアップ済み）。共有ツリーへのrsyncは
  本文確認・公開のタイミングでまとめて行う
- **worktreeは削除しない。** 次にこのテーマを本文確認・公開するとき、または次回このテーマが
  再び収集対象になったときに、同じworktreeを手順3の「使い回す」経路で再利用する

## 5. 直近の収集・公開を今日の候補作成に活かす

`X_POSTING_GUIDE.md` §5「どのテーマを投稿するか」の「直近収集・公開したテーマ」基準に従う。
収集しただけ（本文確認前）のテーマは投稿の具体的な根拠にしない。

## 6. 候補作成へ進む

収集の有無にかかわらず、SKILL.md の「日次手順」をいつも通り進める。
