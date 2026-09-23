# 課題77 — 消費税版「連動表示」データ構造リファレンス

記録日: 2026-09-22。bukatsu-chiiki移植の工程1調査で作成した副産物。他テーマへの移植（工程2以降）で
`scripts/consumption_tax_connected*.py` 相当を新規実装するときの起点として使う。
[別テーマへの適用手順](2026-09-22-task77-connected-layout-rollout-guide.md)の「実装を読む順序」表を補う、より詳細な版。

## データの流れ（パイプライン全体）

```
非公開正典（social-samples等）
  → data/public/themes/consumption-tax-cut.json（公開契約JSON。issue別件数・claim_verification・editorial_summary・ocean_layerを持つ）
  → scripts/build_planet_data.py :: build()
      configs/planet/consumption-tax-cut.yaml（issue/stance の 日本語key⇄英語id⇄icon 対応表、sub_issues の再読ファイル参照）
      を突き合わせて window.PLANET_DATA を作る（<script id="planet-data">）
  → scripts/consumption_tax_connected.py :: content_index()
      PLANET_DATA を読み、論点⇄理由⇄投稿⇄制度⇄資料の「接続表」を作って <script id="tax-connected-data"> に埋め込む
  → scripts/consumption_tax_connected_content.py :: render_templates()
      接続表をたどって <template id="tax-reading-{issue_id}"> を1論点ずつ生成
  → scripts/consumption_tax_connected_vote.py
      投票UIのJSに id/slot を注入。件数や表示順とは無関係の固定台帳で保存番号を守る
```

設計原則: **すべての接続はID（英語スラッグ）だけで結ぶ**（表示文言=labelでは結ばない）。
例外は1箇所だけ（後述の`modes[].id`）。

## 各要素のID命名規則とJSON構造

### 論点（issue）
- ID: `consumption-tax-cut-{英語slug}`。7件固定。
- 日本語key⇄ID⇄iconの対応表: `configs/planet/consumption-tax-cut.yaml`の`issues:`。
- `PLANET_DATA.issues[]`のフィールド:

| キー | 型 | 必須/任意 | 内容 |
|---|---|---|---|
| `id` | str | 必須 | `consumption-tax-cut-*` |
| `key`/`label` | str | 必須 | yamlの日本語key |
| `icon` | str | 必須 | 絵文字 |
| `count` | int | 必須 | 意見件数 |
| `share_pct` | float | 必須 | 意見全体比 |
| `stances` | dict[str,int] | 必須 | **キーが立場の日本語key**（IDではない）→件数 |
| `top_stance`/`purity_pct` | str/float | 必須 | 最多立場と占有率 |
| `intensity` | {high,medium,low:int} | 必須 | 強度別件数 |
| `high_pct`/`high_adjusted_pct` | float | 必須 | 山の高さ算出用 |
| `sub` | dict | 必須 | 理由データ（下記） |
| `verdict` | str\|null | 任意 | 論点内で最も厳しい資料照合判定 |
| `claims` | list[dict] | 必須(空可) | 紐づく資料照合オブジェクト本体 |
| `veins` | list[str] | 必須(空可) | 紐づく「共通の心配」ID一覧 |

### 立場（stance）
- ID: `consumption-tax-cut-{support|conditional|cautious|neutral}`。4件固定。
- 定義元: yamlの`stances:`（`key`=日本語, `id`, `label`, `color`, `pattern`）。
- `PLANET_DATA.stances[]` = yaml各要素 + `count`（自動計算）。
- **落とし穴**: 立場フィルター`PLANET_DATA.modes[].id`は`"all"`か**立場の日本語`key`**（英語idではない）。
  `content_index()`は`stances[].mode_id = key`として明示的に保持し、
  `{mode_id}∪{"all"} == {modes[].id}`を検査する（英語IDだけで完結しない唯一の箇所）。

### 理由（reason、コード内は「sub-issue / bucket」）
- ID: 単一の英大文字（`A`,`B`,`C`…）＋特殊値`__unread__`。**論点をまたいで一意ではない**
  （`scope`の`A`と`effect`の`A`は別物。常に(issue_id, reason_id)の組で識別）。
- 発生元: `data/{topic}_4issues-reread.json`。7論点中4論点だけが再読済み
  （`hani`対象範囲/`kouka`効果/`kyufu`給付/`jigyosha`事業者負担）。各サブissueは:
  - `buckets`: `{reasonId: {label, count}}`
  - `items`: `{tweet_id, url, stance, bucket, bucket_label, summary, text_sha256}[]`
- 論点→ファイル/パス対応: yamlの`sub_issues:`（`file`,`path`,`items_path`,`coverage`,`coverage_note`,`read_at`）。
- `PLANET_DATA.issues[].sub`:
  - 再読済み: `{status:"reread", coverage, coverage_note, show_coverage_note, source_file, reread_count, unread_count, skipped_count, grown_count, unknown_timing_count, items:[{id,label,count,pct_in_issue,unread?}], classification_review_pending?}`
  - 未再読: `{status:"not_reviewed", note}`

### 投稿（post）— 2系統ある

1. **論点直下「実際の投稿を読む」用**（各論点2件、理由とは無関係）
   - 定義元: `scripts/build_consumption_tax_page.py`の`ISSUE_CARDS_POSTS: dict[issue_id, list[tuple[url,label]]]`
     （Pythonリテラル直書き）。IDを持たずURL自体が識別子（`data-tax-post-url`属性）。
2. **理由（reason）ごとの投稿例**（1理由につき1〜2件、後日追加された機能）
   - 選定ファイル: `configs/consumption-tax-reason-posts.json` … `{theme_id, selected_on, selection_note, issues:{issueId:{reasonId:[tweet_id,...]}}}`。値はtweet_id文字列のみ。
   - 解決: `scripts/consumption_tax_reason_posts.py::load()`が再読ファイルの`items`に突き合わせ、
     `bucket`/`bucket_label`一致を検査した上で`{tweet_id, url, summary}`を取り出す。
     URLは正規表現`https://(x|twitter)\.com/[A-Za-z0-9_]+/status/{tweet_id}`で検証。

### 資料側項目（`ocean.sunk_continents`＝資料にあり投稿で見つからなかったこと）
- ID: `consumption-tax-cut-sc-{n}`（4件）。
- 供給元: **`data/public/themes/consumption-tax-cut.json`の`ocean_layer.sunk_continents`**
  （さらに遡ると`data/verification/consumption-tax-cut-sunk-continents.json`。＝公開JSONへの昇格ステップがある）。
- フィールド: `id, topic, life_impact, nearest_issue_id, sns_count, sns_base, checked_on, reviewer_type, sources:[{name,url,location?,date?}]`
- `build_planet_data.py::build()`が実行時付加: `opinion_count_now`, `base_stale`, `short_label`。

### 共通の心配（`ocean.veins`）
- ID: `consumption-tax-cut-vein-{n}`（2件）。
- 供給元: 同じく`ocean_layer.veins`（元`data/verification/consumption-tax-cut-veins.json`）。
- フィールド: `id, issue_ids:list[str](複数可), shared_concern, diverging_reason, checked_on, reviewer_type, sides:[{stance_label, post_count}]`。

### 年表（`consumption-tax-background.json`の`timeline`）
- ID: `timeline-{YYYY-MM-DD}`。
- フィールド: `id, date, title, body, links:[[url,label],...], issue_ids:list[str]`。

### 資料照合（claim）— background.jsonとは別ファイル系統
- ID: 英語の短い記号（`rate10`,`register`,`cost5cho`,`welfare`,`refund`,`firstcut`、6件）。
- 正典: `data/public/themes/consumption-tax-cut.json`の`claim_verification.claims[]`
  （`id, issue_ids, claim, verdict(fact/gap/miss), finding, matched_post_count, sources`）。
- `scripts/build_consumption_tax_page.py`の`CLAIM_AUDIT`（クイズ用`key`が同じID）と1:1対応をテストが検査。

### 制度（policy）
- ID: `policy-{slug}`。`consumption-tax-background.json`の`policies`（`id,key,question,body,links,issue_ids`）。

### 連動表示専用「接続表」スキーマ（`<script id="tax-connected-data">`）
`consumption_tax_connected.py::content_index()`が生成する中核データ:

```
{
  schema: 1,
  theme_id: "consumption-tax-cut",
  default_issue_id: "consumption-tax-cut-scope",
  stances: [{id, mode_id, short_label}],
  issues: {
    "<issue_id>": {
      static_id: "fb-<issue_id>",
      posts_id: "issue-<issue_id>",
      post_urls: [url,...],
      claim_ids: [...],
      source_only_ids: [...],
      shared_concern_ids: [...],
      policy_ids: [...],
      timeline_ids: [...],
      method_link: "about.html#method" | null   // "-other" 論点だけ非null
    }, ...
  },
  background_checked_on: "2026-09-19",
  scope_note: "理由の分類・投稿例・資料は、この論点全体の内容です。"
}
```

## IDの関係

- **論点ID⇄理由ID**: 1対多（0〜7個程度）。理由IDはテーマ全体で一意でなく、常に(issue_id, reason_id)の組。
- **理由ID⇄投稿ID**: 1対1〜2。`consumption-tax-reason-posts.json`で選定（重複禁止、`load()`が強制）。
  論点直下2件固定の`ISSUE_CARDS_POSTS`とは別物。
- **論点ID⇄claim/policy/timeline/vein/sunk_continent**: 多対多寄り。各アイテムが`issue_ids`
  （または`nearest_issue_id`の単数版）を持ち、`content_index()`が逆引きして論点ごとの接続配列を組む。

## 投票の固定番号（`configs/consumption-tax-vote-choices.json`）

```
{ theme_id, topic_id, storage_key, note,
  issues:  [{id, slot, label}, ... 7件],
  stances: [{id, slot, label}, ... 4件] }
```

- 各要素が明示的な整数`slot`を持つ。`consumption_tax_connected_vote.py::registry()`が
  `slot`の並びが`0..len-1`と連続していること、`issues`7件・`stances`4件（＝28通り）を検査。
- 保存番号（0〜27）は **`choice_idx = issue.slot * 4 + stance.slot`** で計算。表示順・件数順
  とは完全独立のため、山の並び替えがあっても既存投票の保存先はズレない。
- `apply()`は既存の投票JS内`k:'<label>'`文字列（どの論点/立場かの意味）が変化していないかを
  正規表現で突き合わせてからid/slotを注入する二重防御。

## 対象テーマを限定する仕組み（3段構え）

1. モジュール定数`TOPIC = "consumption-tax-cut"`。
2. `apply()`冒頭: `if topic != TOPIC or not (activate or enabled(source)): return source`
   （呼び出し元は必ず`topic=<処理中のテーマID>`を渡す。`consumption-tax-cut`以外は完全無操作）。
3. `planet_data()`が埋め込み済み`PLANET_DATA.theme_id`を読み、`!= TOPIC`なら`ValueError`
   （マーカーだけコピーされた場合の二重防御）。

呼び出し元（全テーマ共通パイプライン）: `scripts/seo/apply_theme_trust.py`・
`scripts/seo/apply_classroom_section.py`・`scripts/refresh_planet_section.py`・
`scripts/refresh_adapters/consumption_tax.py`。いずれも`topic=theme_id`を渡す。
有効化そのもの（`activate=True`）は`build_consumption_tax_page.py`内でCLIフラグ`--connected-layout`
経由。一度HTMLに`<!-- TAX_CONNECTED_START -->`マーカーが入ると`enabled(source)`が真になり、
以後`activate`を渡さなくても「連動表示あり」として扱われ続ける（マーカーがページ単位の恒久フラグ）。

## `tests/test_consumption_tax_connected.py`（26件）が守っていること

移植先でも同等の検査を新設する前提で、対応させたい項目の一覧（1行要約）。

| テスト名 | 要約 |
|---|---|
| `test_activation_is_explicit_and_other_themes_are_unchanged` | マーカー未有効化・他テーマではapply()が完全無操作 |
| `test_same_input_does_not_accumulate_assets_or_bridges` | 同じ入力への再適用でマーカーが重複しない（冪等性） |
| `test_relationships_do_not_depend_on_rank_or_display_labels` | 論点の並び順・labelを変えても接続結果は不変 |
| `test_missing_post_in_its_issue_fails_even_if_url_exists_elsewhere` | 投稿URLが所属論点から消えると、他所にあっても検出 |
| `test_stance_ids_do_not_depend_on_data_order` | 立場の並び反転でもバーのID対応は不変、未知IDは検出 |
| `test_missing_claim_source_fails_even_if_url_exists_in_other_sections` | 資料照合カードの出典URL破壊を、他欄に同URLがあっても検出 |
| `test_missing_static_issue_fails` | 静的本文`id="fb-..."`欠落を検出 |
| `test_content_can_move_without_weakening_its_checks` | ブロック移動後も検査が機能し続けることを確認 |
| `test_mismatched_index_is_rejected` | 接続表と表示データのズレを検出 |
| `test_missing_runtime_or_source_only_content_is_rejected` | CSS/JS参照・資料側項目クラス・BRIDGEマーカー欠落を個別検出 |
| `test_reading_templates_have_local_sources_and_distinct_empty_states` | 7論点分の読書面存在、空状態文言、出典欠落検出 |
| `test_reading_reason_loss_is_rejected` | `data-tax-reason`属性欠落を検出 |
| `test_all_reviewed_reasons_have_a_matching_post_and_lazy_embed` | 再読済み25理由すべてに投稿例・URL・要旨一致・遅延埋め込みがある |
| `test_reason_post_swaps_summary_edits_and_missing_links_are_rejected` | 投稿例の入替・要旨改変・リンク破壊をいずれも検出 |
| `test_selected_post_must_belong_to_its_reason` | 別理由の投稿ID流用でload()が例外 |
| `test_reading_timeline_and_source_only_need_their_own_sources` | 年表・資料側項目の出典欠落を欄ごとに独立検出 |
| `test_corrections_follow_changed_counts_and_keep_confirmation_dates` | 件数変更で訂正文が追従、確認日は不変 |
| `test_focus_follows_counts_by_id_without_changing_vote_order` | 「議論の中心」が件数最大論点IDに追従、投票指紋は不変 |
| `test_source_only_items_keep_their_checked_population` | sunk_continentsの母数変更が本文・確認日に反映 |
| `test_bar_colors_match_the_mountains` | バーの立場配色とPLANET_DATA配色の一致 |
| `test_reading_counts_have_original_record_provenance` | DOM上の数字が元記録と照合可能、未有効化ページは空 |
| `test_wrong_reason_count_fails_even_when_another_bucket_has_that_number` | 理由件数差し替えを、別理由の数字と一致しても検出 |
| `test_selected_post_and_search_counts_cannot_drift` | 共通の心配・資料側項目の件数表示改ざんを検出 |
| `test_vote_ids_preserve_all_published_storage_numbers` | content-contract.jsonのvote.choicesとページ内CHOICESが28通り全一致 |
| `test_unregistered_vote_issue_is_rejected` | 未登録論点IDでのregistry()呼び出しが例外 |
| `test_changed_vote_meaning_is_rejected` | 投票JS内ラベル文字列の書き換えをapply()が検出 |

## bukatsu-chiikiとの構造比較（要点）

- 論点7・立場4は共通。**タックスは28通りの投票を「issue.slot×4+stance.slot」の単発計算式**で
  守っているが、bukatsu-chiikiの実際の保存式は本調査では未確認（`docs/topic-modern.js`等を工程2で確認要、
  [内容確定書](2026-09-22-task77-bukatsu-chiiki-content-contract.md)の`open_gaps`参照）。
- タックスは7論点中4論点のみ再読済み。bukatsu-chiikiは7論点中5論点が再読済み（母数が違う）。
- タックスの資料側4項目は`nearest_issue_id`（単数）を持つが、bukatsu-chiikiの沈んだ大陸は
  `issue_bucket`という名前で1件（sc-1）のみに存在し、残り3件は無タグ（編集部推定で補完要）。
- 論点直下の投稿2件は両テーマとも「理由とは無関係の別系統」という設計が共通。
