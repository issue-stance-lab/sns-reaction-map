# 副首都・対象別点検案の検証記録（2026-09-13）

対象は非公開の分類・表示確認版です。山なみ完成版や本番公開の検証ではありません。

- 全1,733件の位置・本文ハッシュ・投稿キーを照合。欠落・重複・不一致なし。
- 意見候補1,497、除外215、全体保留21。採用候補内の一部地域保留1を合わせ未解決22投稿。
- 同じ入力からJSON・Markdown・HTMLを再生成し、3ファイルのSHA-256一致。
- 375px・1280pxで構想→法案→別案→候補地の切替、地域選択を操作。JavaScriptエラー0・横スクロールなし。
- 原本は作業ツリー・共有ツリーとも SHA-256 `d0d46700f58a2c15f321f7d7d62a372ff5a508ca1a4c2b001e24361aabc43c0d` を維持。
- `docs/`・`data/public/`・投票コード・既存のplanet設定はHEADとの差分なし。
- トップ検査は次回更新日2箇所と収集期限超過でNG。公開ファイルは変更しておらず今回の確認版とは別の問題。NGを成功扱いにしない。
- 編集理由の割当と独立監査は未実施。分類の本文確認を編集再読として申告していない。公開可能フラグは常にfalse。

## 再生成

リポジトリの作業ツリーで次を実行すると、非公開の対照表と表示確認版を再生成します。意見候補1,497・保留21・can_publish:falseと出れば今回の候補と一致します。

```sh
python3 scripts/build_fukushuto_target_review.py --baseline social-samples/work/fukushuto-page/baseline.json --review social-samples/work/fukushuto-page/target-body-review.json --output quality/reviews/2026-09-13-fukushuto-target-review
```

非公開の原文・手動判断・修正前記録・試験分類コード・検査記録は作業ツリーと外部バックアップに保持します。原文をGitへ追加しません。

## 検査出力

### verify_theme_page.py fukushuto

exit=0

```text
=== fukushuto ===
=== 数字の分離 ===
OK  「世論調査ではありません」が存在する
OK  注意書きが最初の数値表示より前にある
OK  参加者投票に n=表記がある
OK  調査条件（取得元・期間・件数）が表示されている（2026-07-14〜2026-08-31）
OK  代表投稿の確認表示が台帳と一致する（AI分類。代表投稿は編集部が選定）
OK  投票ゲート（blur / lockArenaUntilVote）が存在しない
=== 論点カードのデータ整合 ===
OK  公開データJSONの論点別件数が仮名化検証データと一致する（7論点）
OK  全カードの main_issue が公開データJSONに実在する（7ラベル）
=== 母数の統一 ===
OK  母数は issue_counts.basis=public_json（1453件）
OK  論点の合計が母数と一致する（1453件）
OK  マップの合計が母数と一致する（1453件）
OK  賛否の合計が母数と一致する（1453件）
=== 論点カード ===
OK  全カードに件数が併記されている（id付き、6枚）
OK  論点カードの件数が分類結果と一致する（teigi=232 / kohochi=300 / tokoso=407 / bosai=221 / hiyo=64 / yusen=140）
=== 同じ数字は1回だけ ===
OK  意見数はページ全体で1453に統一されている
OK  論点数はページ全体で6に統一されている
=== ページ全体の件数表示 ===
OK  ページ全体に管理対象外の件数が残っていない
=== 最大勢力バッジ ===
OK  論点1・最大勢力・最も熱い が最大論点に付いている（tokoso=407件）
```

### verify_top_page.py

exit=1

```text
=== 数値の出所 ===
収集した投稿   15,815   ← sample_file の実レコード合計（10テーマ）
分析対象の意見 12,404   ← 課題57 公開データcatalog（data/public/catalog.json）
公開テーマ数      10   ← THEMES.yaml published:done
最終更新    2026-09-12  ← THEMES.yaml updated_at 最大
次回更新    2026-09-15  ← THEMES.yaml refresh_at の今日以降の最小

=== 置換の空振り検査 ===
OK  収集した投稿の用語                1件マッチ
OK  hero-total-samples       1件マッチ
OK  公開中のテーマ                  1件マッチ
OK  投票受付中                    1件マッチ
OK  em更新日                    1件マッチ
OK  更新バー本文                   1件マッチ
NG  update-bar次回更新           1件マッチ（値不一致）
NG  JS次回更新                   1件マッチ（値不一致）
OK  JS期限超過表示                 1件マッチ
OK  バッジデータ                   1件マッチ
OK  hero-total-opinions      1件マッチ
OK  注目の問い件数 ai-copyright     1件マッチ
OK  注目の問い件数 bike-blue-ticket 1件マッチ
OK  注目の問い件数 bukatsu-chiiki   1件マッチ
OK  注目の問い件数 consumption-tax-cut 1件マッチ
OK  テーマカード件数 ai-copyright    1件マッチ
OK  テーマカード件数 bike-blue-ticket 1件マッチ
OK  テーマカード件数 bukatsu-chiiki  1件マッチ
OK  テーマカード件数 constitutional-amendment 1件マッチ
OK  テーマカード件数 elderly-license-revocation 1件マッチ
OK  テーマカード件数 school-nickname-ban 1件マッチ
OK  テーマカード件数 henoko-student-accident 1件マッチ
OK  テーマカード件数 fukushuto       1件マッチ
OK  テーマカード件数 koshitsu-tenpakai 1件マッチ
OK  テーマカード件数 consumption-tax-cut 1件マッチ
OK  テーマカード意見数 ai-copyright   1件マッチ
OK  テーマカード意見数 bike-blue-ticket 1件マッチ
OK  テーマカード意見数 bukatsu-chiiki 1件マッチ
OK  テーマカード意見数 constitutional-amendment 1件マッチ
OK  テーマカード意見数 elderly-license-revocation 1件マッチ
OK  テーマカード意見数 school-nickname-ban 1件マッチ
OK  テーマカード意見数 henoko-student-accident 1件マッチ
OK  テーマカード意見数 fukushuto      1件マッチ
OK  テーマカード意見数 koshitsu-tenpakai 1件マッチ
OK  テーマカード意見数 consumption-tax-cut 1件マッチ
OK  テーマカード主要論点数 ai-copyright 1件マッチ
OK  テーマカード主要論点数 bike-blue-ticket 1件マッチ
OK  テーマカード主要論点数 bukatsu-chiiki 1件マッチ
OK  テーマカード主要論点数 constitutional-amendment 1件マッチ
OK  テーマカード主要論点数 elderly-license-revocation 1件マッチ
OK  テーマカード主要論点数 school-nickname-ban 1件マッチ
OK  テーマカード主要論点数 henoko-student-accident 1件マッチ
OK  テーマカード主要論点数 fukushuto    1件マッチ
OK  テーマカード主要論点数 koshitsu-tenpakai 1件マッチ
OK  テーマカード主要論点数 consumption-tax-cut 1件マッチ

=== 件数の網羅検査 ===
OK  ページ内の「○件」表示は全て id 付き（手入力の件数が残っていない）
OK  テーマカード10枚の件数が sample_file と一致する
OK  問いカード4枚の件数が sample_file と一致する
OK  テーマカード合計 15,815 = ヒーロー表示 15,815
OK  件数の用語が「収集」で統一されている

=== 意見数・主要論点数（課題57 公開データcatalog） ===
OK  テーマカードの意見数・主要論点数が公開データcatalogと一致する
OK  ヒーローの意見数合計 12,404 が公開データcatalogと一致する

=== 正典ファイル検査 ===
OK  ai-copyright                 synthetic 0件
OK  bike-blue-ticket             synthetic 0件
OK  bukatsu-chiiki               synthetic 0件
OK  constitutional-amendment     synthetic 0件
OK  elderly-license-revocation   synthetic 0件
OK  school-nickname-ban          synthetic 0件
OK  henoko-student-accident      synthetic 0件
OK  fukushuto                    synthetic 0件
OK  koshitsu-tenpakai            synthetic 0件
OK  consumption-tax-cut          synthetic 0件

=== 日付検査 ===
OK  期限超過 8テーマを「更新予定を確認中」と表示
OK  refresh_at 空欄 0件
NG  collect_at 期限超過: ai-copyright（2026-09-12）, bukatsu-chiiki（2026-09-09）, constitutional-amendment（2026-09-12）, elderly-license-revocation（2026-09-11）, henoko-student-accident（2026-09-07）, fukushuto（2026-09-07）, koshitsu-tenpakai（2026-09-08）, consumption-tax-cut（2026-09-08）
OK  collect_at 空欄 0件

=== 禁止表示 ===
OK  「割れ度」なし
OK  「公開テーマの分類比率」なし
OK  「どっちが多い」なし
OK  30日以上前の日付を含む要素なし
OK  ハードコードされた割合（NN%）なし

=== リンク ===
OK  問いカード 4/4 リンク有効（リンク先HTMLが実在する）
OK  今週の注目テーマ fukushuto が GROWTH.yaml の featured と一致する
OK  #ranking 参照なし
OK  ナビの全リンク先が実在する（5件）

=== レスポンシブ ===
OK  .hero-side に display:none を適用するメディアクエリなし
OK  「世論調査ではありません」がページ内に存在する
OK  注意書きが hero-stats より前に出現する

=== 公開ディレクトリの衛生 ===
OK  docs/ に .md が無い（運用メモは content/website/internal/ へ）
OK  docs/404.html がある
```

### unittest test_fukushuto*

exit=0

```text
......................
----------------------------------------------------------------------
Ran 22 tests in 0.043s

OK
```

### verify_task_board.py

exit=0

```text
OK: 索引 15,580 バイト / 課題 31 件。すべての課題に詳細ファイルがあります
```

