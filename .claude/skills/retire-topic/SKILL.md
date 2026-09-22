---
name: retire-topic
description: 既存テーマ（トピック）を1本、サイトから廃止するための手順。「このテーマ削除して」「◯◯を非公開にして終わりにしたい」「公開する見込みがないテーマをどうするか」「unlistedのまま放置されているテーマを整理したい」といった作業では必ずこのスキルを読むこと。廃止は new-topic（追加）の逆操作だが、参照が全方向に散っているため「THEMES.yamlから消しただけ」では静かに壊れる箇所が多い（課題38のinject_tide_widget.py・recompute_public_unreviewed.pyの件数チェック・decision-evidence.jsonのトピック突合など）。Git履歴からの完全消去はできない前提（課題78）。データ追加・更新はDATA_REFRESH.mdを見ること。「一時的に隠す」だけならTHEMES.yamlのpublishedを`unlisted`にするだけで足り、本スキルは不要（課題78のtakaichi、2026-08-21）。
---

# 既存テーマの廃止

## 初めての実施（2026-09-22、takaichi）

このサイトでテーマを丸ごと廃止したのはtakaichi（高市文春問題）が最初。
このスキルはその作業から作った。経緯は
[archive/tasks/task-88.md](../../../archive/tasks/task-88.md)、
[archive/themes/takaichi.md](../../../archive/themes/takaichi.md) を参照。

## この作業で本当に危ないこと

new-topicと対称で、**削除も「消せた」ことは分かりやすいが、壊れた場所は検査を
実際に走らせるまで分からない。** `grep -rn "{slug}"` だけでは見えない依存が3種類ある。

**① テストの中の手打ちリスト**

THEMES.yamlをループで読むテストは自動で追従するが、`BUILDERS = (...)` のような
**手打ちのタプル・辞書**はテーマ名を書いた本人しか知らない場所に残る。
takaichiでは `scripts/verify_builder_rebuildability.py` の `BUILDERS` タプル、
`tests/test_theme_hero_assets.py` の `REMAINING_HEROES` 辞書、
`tests/test_refresh_topic.py` の冒頭 `from scripts.refresh_adapters import {slug}`
（**無条件import**。アダプタファイルを消すとテストファイル全体が読み込めなくなる）
の3箇所で見つかった。

**② テストに一切捕捉されない「静かな罠」**

`scripts/recompute_public_unreviewed.py` の `expected_canonical_files=11` は
CLIのデフォルト引数で、**ユニットテストは別の値を明示的に渡すため検知されない**。
THEMES.yamlのテーマ数が変わった瞬間、実運用で走らせたときだけ
`ValueError('canonical topic count changed')` で落ちる。
→ **`grep -n "11\|len(themes)\|expected_.*=" scripts/*.py` で、テーマ総数を
定数で持っているスクリプトを別途洗うこと。テストが通ることは「壊れていない」の
証明にならない。**

**③ 「現在のTHEMES.yamlの部分集合であること」を要求する検証ファイル**

`data/verification/adoption/decision-evidence.json` の `decisions` と
`cohorts.*.topics` は、`verify_adoption_registry.py` が
`set(seed["decisions"]) <= set(現行THEMES.yamlのテーマ)` を検査する。
廃止するテーマのキーが残っていると「decision topic unknown」で落ちる。
**この検査に引っかかるファイルは、過去の意思決定記録であっても該当テーマの
キーを削除してよい**（Gitの履歴には残る。DATA_REFRESH.mdの「元の保存回は
書き換えない」原則は`social-samples/updates/`の更新回そのものに対するもので、
この種の「現行テーマとの突合台帳」には適用されない）。

**削除できる範囲には上限がある。** Git履歴からの完全消去（`git filter-repo`等＋
強制push）は[課題78](../../../archive/tasks/task-78.md)で「対象コミットが履歴の
97%・作業ツリー25個/並行セッション36個へ影響」という理由で技術的に見送り済み。
**このスキルの「削除」は常に「今後の追跡・表示から外す」を意味し、過去の
コミットは消えない。** 「消せます」と安請け合いしない。

---

## 進め方

### ⓪ 本当に廃止すべきか確認する

以下のどれかに当てはまるまでは、廃止ではなく`published: unlisted`化（データ・
ページは残しつつ検索・サイト内導線・sitemapから外すだけ）で十分。

- 公開する見込みが将来にわたって無い（policy上・データ品質上の理由が解消しない）
- `unlisted`のまま`collect_at`だけが残り、催促（`build_admin_dashboard.py`の
  遅れ検知）が目的なく繰り返されている（`collect_mode: event-driven`化でも
  解消しない場合。まずそちらを試す方が手数が少ない）
- オーナーが「中途半端に残すより閉じたい」と判断した

**私（AI）が自分の判断だけで実行しない。** 公開判断・データ削除に近い性質を
持つため、オーナー承認を得てから着手する。

### ① 作業場所を用意する（new-topicの⓪と同じ）

```sh
git worktree add ../isa-wt-{slug}-retire-{日付} -b task/{slug}-retire-{日付}
cd ../isa-wt-{slug}-retire-{日付}
tar xzf "$(ls -t /Volumes/HD-LE-B/issue-stance-private-backups/private-data-*.tar.gz | head -1)" \
  -C . --exclude=manifest.json
cp -R ../issue-stance-aggregator/node_modules .
```

### ② 影響範囲を洗い出す

`grep -rn "{slug}"` だけでは①の3種類の依存を見落とす。**読み取り専用のExploreエージェントに
「{slug}を完全に削除する場合、各ファイルをどう変更すべきか」を種類別（THEMES.yaml本体／
scripts・tests のハードコード／configs／docs の画像資産／data/verification／company／
tasks・TASK_BOARD.md／archive〈触らない〉）に洗わせ、特に「テストには捕捉されないが実運用で
壊れるもの」を優先度付きで報告させる。** 手動のgrepだけで進めると、画像ファイル
（`docs/images/topics/{slug}/`等）のようなテキスト検索に出てこ��い資産を取りこぼす。

### ③ THEMES.yamlからエントリを削除する

```yaml
# themes: 直下の {slug}: ブロックを丸ごと削除
```

### ④ 壊れるテスト・スクリプトを直す（必須）

②の報告に沿って、少なくとも次を確認する。

- テーマ別adapter/classifier/ビルダースクリプトを手打ちで列挙している箇所
  （`configs/refresh-pipeline.yaml`、`scripts/verify_builder_rebuildability.py`の
  `BUILDERS`、`tests/test_theme_hero_assets.py`の`REMAINING_HEROES`等）
- そのテーマ専用のテストファイル（`tests/test_{slug}_adapter.py`等）→ファイルごと削除
- 他のテストファイル冒頭の**無条件import**（`from scripts.refresh_adapters import {slug}`）
- テーマ総数を定数で持つスクリプト（①の「静かな罠」参照）

### ⑤ ファイルを削除する

```sh
git rm -f docs/{slug}-*.html docs/{slug}-arena-data.js docs/ogp/{slug}.png
git rm -rf docs/images/topics/{slug}/
git rm -f configs/topics/{slug}.yaml configs/{slug}-*.json
git rm -f scripts/refresh_adapters/{slug}.py scripts/*_{slug}_*.* scripts/classify_{slug}*.py
git rm -f data/verification/{slug}.json
git rm -rf data/verification/updates/{slug}/
```

`scripts/inject_tide_widget.py`のような「THEMESという名の手打ちリストにテーマ辞書を
持つスクリプト」があれば、そこからも該当エントリを削除する（課題38がまさにこの形で
takaichiを固定ファイル名のまま持っていた）。

**非公開正典（`social-samples/`配下）は削除しない。** Gitに追跡されていないので
このコマンド群では消えないが、念のため触らないことを確認する。バックアップにも残る。

### ⑥ 台帳・生成物を再生成する（手で直さない）

```sh
python3 scripts/build_adoption_registry.py      # data/verification/adoption/registry.json
python3 scripts/verify_sample_periods.py --generate  # data/verification/sample-periods.json
python3 scripts/build_data_sheet.py             # DATA_SHEET.md
python3 scripts/sync_portal_stats.py            # docs/index.htmlの件数（unlisted済みなら通常「変更なし」）
python3 scripts/data_asset_inventory.py         # company/data-assets.json（Git追跡変更を反映）
```

`build_adoption_registry.py`が`KeyError: '{slug}'`で落ちたら、
`data/verification/adoption/decision-evidence.json`の`decisions`と`cohorts.*.topics`に
該当テーマのキーが残っている（①の③）。該当キーを削除してから再実行する。

### ⑦ 生きたドキュメントを更新する

削除して終わりではなく、**このテーマを名指しした「まだ有効な」記述**を探して直す。
`archive/`配下と、既に完了扱いのtasksは触らない（過去の記録として妥当）。

- `TASK_BOARD.md`・対応する`tasks/task-N.md`：該当テーマを名指しした**未解決**の記述
  （「◯◯は未対応」等）から名前を落とす
- `company/HANDOFFS.yaml`：該当テーマの再開を前提にした`next_action`があれば、
  実行不能な指示のまま残さず書き換える。`canonical_sources`に消したファイルへの
  パスが残っていると`tests/test_company_operations.py`が落ちる
- `themes/{slug}.md`：`archive/themes/{slug}.md`へ`git mv`し、廃止の経緯を追記する
  （`scripts/verify_themes_yaml.py`がTHEMES.yamlと`themes/`の双方向対応を検査するため、
  削除しないと「登録簿に無いテーマのメモが残っている」でNGになる）

### ⑧ 検査を通す

```sh
python3 -m unittest discover -s tests ; echo "exit=$?"
python3 scripts/run_public_checks.py ; echo "exit=$?"
python3 scripts/verify_theme_page.py ; echo "exit=$?"
python3 scripts/verify_number_provenance.py ; echo "exit=$?"
python3 scripts/verify_top_page.py ; echo "exit=$?"
python3 scripts/verify_themes_yaml.py ; echo "exit=$?"
python3 scripts/verify_task_board.py ; echo "exit=$?"
```

いずれも「Nテーマ」の件数表示が、廃止後の正しい件数（元の件数−1）になっていることを
目視で確認する。件数だけ合っていて中身が違う、というより「NG 0件」の脇に出る
テーマ数の表示そのものが更新漏れの一番わかりやすいサインになる。

### ⑨ 経緯を記録する

- このテーマ廃止そのものの作業記録を`tasks/task-N.md`として作り、完了後は
  `archive/tasks/task-N.md`へ移す（TASK_BOARD.mdの索引からも外す）
- 初めての実施でなければ、本スキルに新たに見つかった落とし穴を追記する

### ⑩ releaseスキルの手順でmainへ反映する

このスキル自体は「ページを直す」作業に含まれるので、mainへの反映は
`.claude/skills/release/SKILL.md`に従う。バックアップの取り直し・
CI（「公開ファイルの検査」）の実際の結果確認まで省略しない。

---

## 落とし穴（実際に踏んだもの）

- **`recompute_public_unreviewed.py`の`expected_canonical_files`はテストでは検知されない。**
  デフォルト引数を手で数え直して直す（④参照）
- **`decision-evidence.json`のcohortsが複数テーマにまたがる追跡集合を持っていると、
  1テーマの削除で他テーマの集計まで巻き込んで落ちる。** `build_adoption_registry.py`側に
  「result['topics']に無いトピックは追跡対象から静かに外す」防御を入れておくと、
  今後同種の廃止をするときにdecision-evidence.json側の対応漏れがあっても検査で
  はっきり気づける（クラッシュではなく後続の`verify_adoption_registry.py`のNGとして出る）
- **`run_public_checks.py`の`PRIVATE_DATA_TESTS`除外リストに、削除したテスト名が
  残っていると`SystemExit`で止まる。** 除外リストは「存在するテストだけを許す」検査を
  自前で持っているので、テストファイルを消したら必ずここも見る
- **`docs/images/topics/{slug}/`のような画像ディレクトリは`grep -rn "{slug}"`のテキスト
  検索に出てこない。** ファイル名・ディレクトリ名での検索を別途行う
- **孤立した旧世代の画像**（現行ページのどこからも参照されていない）がテーマ削除より前から
  残っていることがある。ついでに片付けるかは任意だが、見つけたら報告する

## 完了条件

- `THEMES.yaml`に対象テーマのエントリが無い
- 公開ページ・画像・専用スクリプト・専用テストが削除されている
- ⑧の検査がすべて exit=0、かつ表示されるテーマ数が正しい
- `TASK_BOARD.md`・`company/HANDOFFS.yaml`に、廃止済みテーマを前提にした
  実行不能な指示が残っていない
- 廃止の経緯が`archive/themes/{slug}.md`と`archive/tasks/task-N.md`に記録されている
- mainへ反映し、CI（「公開ファイルの検査」）が成功している

## 完了報告に含めること

- 削除した理由（unlisted化からの経緯があれば、その理由が解消していないこと）
- 削除した範囲（ページ／画像／スクリプト／設定／非公開データは対象外であること）
- Git履歴には残ること（完全消去はしていないこと）を明記する
- 今後の再開手段（社会的サンプルは`social-samples/`に残るため、将来必要になれば
  `refresh_topic.py`で再収集できること）
