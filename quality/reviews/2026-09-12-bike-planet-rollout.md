# 自転車の青切符：3テーマ目の山なみ展開（2026-09-12）

課題54の3テーマ目。bukatsu-chiiki・elderly-license-revocationに続き、
bike-blue-ticketを「議論の山なみ」形式へ本番反映した。

## 段階0：編集部の横断整理・地下水脈・背景

- `data/verification/bike-blue-ticket-editorial.json`（5件、3観点とも有）を新設。
  `data/public/themes/bike-blue-ticket.json` の論点×立場クロス集計から、placeholder
  差し込みだけで本文を作成（数字は直書きしない）
- `data/verification/bike-blue-ticket-sunk-continents.json`（4件）を新設。
  `quality/research/bike-blue-ticket-primary-sources.md` の一次資料メモから、
  371件の意見本文を実際にgrepして各件のsns_count・machine_hitsを検証した上で作成。
  「指導警告は青切符の約63倍」「側方通過という自動車側の新義務」など、SNSでほぼ
  語られていない一次資料の事実を採用
- `data/verification/bike-blue-ticket-background.json`（旧ブランチ70f8792が作成した
  ものを継承）に `checklist.title`/`subtitle` を追加。**副産物として見つけた不具合**：
  `build_background()`（`scripts/build_planet_page_preview.py`）の第2部見出しが
  「学校の外へ出した後、だれが続けるか」という bukatsu-chiiki 専用の固定文言のまま
  だった。bike-blue-ticketの背景データには元々checklistが付いていた（elderly-license
  -revocationには無かったため2テーマ目では気づけなかった）。関数側をパラメータ化し、
  `bukatsu-chiiki-background.json` にも同じキーを追加して後方互換を確認

## 段階1：定例更新スクリプトへのガード

- `scripts/build_bike_arena.py` の `apply_public_counts()`/`build()` に
  `planet_mode` ガードを追加（elderly-license-revocationと同じパターン）
- `scripts/build_bike_process_sections.py` の `main()` に、山なみ形式では
  STEP1〜3のHTML差し替えを飛ばし、一次資料クイズの投稿対応表
  （`write_provenance_records`）だけ更新する分岐を追加

## 段階2：検査設定・自転車固有の不具合2件

- `configs/bike-blue-ticket-reaction-map.json` の `number_provenance` に
  `sides`/`legend`（cross_tab）と `islands`/`findings`/`sunk`/`srclist`/`claims`/
  `#planet-data`（exclude_selectors）を追加。背景セクションの一次情報3件
  （24,549／2,147／135,855）を `allow` リストへ追加
- **不具合A（自転車固有・データの食い違い）**: `configs/planet/bike-blue-ticket.yaml`
  の `stances[0].label` が「賛成（取締り強化）」のまま、正典
  （`social-samples/bike-blue-ticket_2d_classified.json` の `classification.stance`）
  の実際のラベル「賛成（取締り強化支持）」と食い違っていた。旧ブランチ70f8792が
  作成した時点のラベルが、その後の分類確定で変わったまま同期されていなかったと
  見られる。`verify_number_provenance.py` が「84の集計に84は無い」という形で検出。
  config側を正典に合わせて修正
- **不具合B（共通コード・2テーマでは気づけなかった）**:
  `scripts/build_planet_page_preview.py` の `build_generic()` が
  `issue-arena-section`（旧2Dアリーナ）を削除しても、隣接するデータ描画用
  `<script>`（SM_RAW配列・canvas描画）はセクションの外にあるため残ってしまうと判明
  （elderly-license-revocationの本番ページにも同じ取り残しがあり、無害だが
  ページを肥大化させている）。既存の `drop_orphan_scripts()`（bukatsu-chiiki専用）を
  流用しようとしたが、そのDEAD_SCRIPT_IDSは `explainer-modal`/`explainer-card`
  （山なみでも残す「5つの論点」画像カードの拡大表示）も含んでおり、そのまま使うと
  山なみでも生きている機能を壊す。`GENERIC_DEAD_SCRIPT_IDS`（アリーナ関連のみ）を
  別途新設し、`build_generic()` から安全な部分集合だけを渡すよう修正

## 段階3：実差し替え・検査・テスト更新

- `data/public/themes/bike-blue-ticket.json` を `build_public_registry.py` で
  再生成（editorial_summary/sunk_continentsを正典から反映）してから
  `build_planet_page_preview.py --for-docs` で docs/ を実差し替え
- 標準4検査：`verify_theme_page.py`・`verify_number_provenance.py`・
  `verify_page_originality.py` いずれもNG0、`verify_top_page.py` は既知の
  `collect_at` 期限超過（自転車以外のテーマ、無関係）のみ
- 山なみ形式化で前提が変わったテスト3件を更新：`tests/test_bike_adapter.py`
  （2件）・`tests/test_issue_count_sync.py`・`tests/test_planet_reread_evidence.py`
  （後者は不具合Aのラベル修正に合わせた期待値更新も兼ねる）。917件全て合格

## オーナー確認と見本の不具合

Artifactへ公開ページ全体をそのまま貼り付けたところ、色や見た目を決める外部CSS
（`site-tokens.css`／`topic-modern.css`）が見本の仕組みの外にあり読み込めず、
画面が真っ黒になった（オーナー報告「見本が見れません」）。原因はページが自己完結
していないこと。CSS 2本・JS 4本（topic-modern.js／vote-config.js／vote-store.js／
share-x-btn.js）をすべて埋め込み、GA/AdSense/Twitter埋め込みなど見本に無関係な
外部参照を除いて自己完結させ、再公開して解消（ローカルサーバーとArtifact実機の
両方でスクロール・クリック・画像拡大まで確認）。**本番の公開ページ自体には
この問題はない**（外部CSS/JSは実際に存在する）。

## 本番反映（2026-09-12）

作業ツリー `isa-wt-bike-planet` の分岐元から48コミット進んでいたmainへマージ。
`data/public/catalog.json` のみ `generated_from` ハッシュが衝突（生成専用ファイル）。
他15ファイルは自動マージ。`build_public_registry.py --all` で作り直して解消した際、
bukatsu-chiiki（1139→1140）・elderly-license-revocation（353→354）の意見数が
連動して変わったが、いずれも別セッションの完了済み作業（部活動分類器修正・
高齢者の課題63対応）で本番ページ側は既に反映済みと確認してから採用した。
マージ `8ac7fef`。標準4検査NG0（既知のcollect_at超過を除く）、917テストOK。
push・公開反映確認・非公開データバックアップ・作業ツリー削除まで完了。

これで山なみ形式は3/10テーマが公開済み。段階2で見つけた2件はいずれも
共通コード側（build_generic・drop_orphan_scripts）または自転車固有のconfig側で
解消済みのため、残り7テーマの展開では再発しない。
