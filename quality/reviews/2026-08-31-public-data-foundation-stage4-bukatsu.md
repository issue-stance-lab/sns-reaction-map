# 課題57 段階4：部活動の地域移行を公開データJSONへ接続

作成日: 2026-08-31
状態: 論点カードの件数（explainer card / lead文）を接続完了。公開ページ・sitemap・一般公開は未変更
対象: bukatsu-chiiki（段階4の1本目。着手順は部活動→あだ名禁止→消費税減税→残り7テーマ）

---

## 1. 番号→固定IDの対応表（最重要）

`configs/public-data-taxonomy.json` のキー順（辞書順）は、ページ内で論点が「番号」として
参照される順序と**一致しない**。この対応表を経由せずに並びを触ると、過去の投票と地図の点が
別の論点に紐づく（[[reference_pinned_issue_order]] / TASK_BOARD 課題34参照）。

### 論点（page index は VOTE_ISSUES / ARENA_JS ISSUES / arena_taxonomy.issues の共通の並び）

| page index (i:N) | key | 表示ラベル | 固定ID（public-data-taxonomy.json） | kind |
|---|---|---|---|---|
| 0 | hiyo | 費用・家庭負担 | `bukatsu-chiiki-hiyo` | named |
| 1 | ukezara | 受け皿・指導者 | `bukatsu-chiiki-ukezara` | named |
| 2 | kyoin | 教員の働き方 | `bukatsu-chiiki-kyoin` | named |
| 3 | kyoiku | 教育的意義・機会 | `bukatsu-chiiki-kyoiku` | named |
| 4 | kakusa | 地域格差 | `bukatsu-chiiki-kakusa` | named |
| 5 | seido | 制度・移行プロセス | `bukatsu-chiiki-seido` | named |
| 6 | sonota | その他 | `bukatsu-chiiki-sonota` | other |

**`configs/public-data-taxonomy.json` の論点順（教員→制度→教育→受け皿→費用→地域格差→その他）は
上表と並びが違う。** これは辞書順で書かれた設定ファイルであり、ページ側の番号を表す配列ではない。
段階4以降、ページ側で論点を並べて表示する処理を書くときは、必ずこの表（page index順）に
沿わせること。`public-data-taxonomy.json` の順で `issues[]` をそのまま列挙してはいけない。

`data/public/themes/bukatsu-chiiki.json` の `issues[]` 配列も、生成器が
`public-data-taxonomy.json` の辞書順で書き出すため、**同じくpage indexとは順序が違う。**
論点カードの件数接続（本記録の本体）はラベル名でマッチングしており順序に依存しないため
影響していないが、今後「並び」そのものを扱う接続作業ではこの対応表を必ず経由すること。

### 立場（4種、arena_taxonomy.stances = 論点内の内訳表示・公開データJSONのstances配列と同じ概念）

| index | key | 表示ラベル | 固定ID |
|---|---|---|---|
| 0 | support | 移行支持 | `bukatsu-chiiki-transition-support` |
| 1 | conditional | 条件付き・改善要求 | `bukatsu-chiiki-conditional` |
| 2 | oppose | 慎重・反対 | `bukatsu-chiiki-cautious` |
| 3 | neutral | 中立・情報 | `bukatsu-chiiki-neutral` |

### 投票の立場（3種、vote_stances = 2ステップ投票UI専用。上の4種とは別物）

| vote stanceIdx | key | 表示ラベル |
|---|---|---|
| 0 | oppose | 反対・慎重 |
| 1 | neutral | どちらでもない |
| 2 | support | 賛成・推進 |

### 投票の保存値（Supabase choiceIdx）

`choiceIdx = issueIdx(0-6, 上表page index) * 3(vote_stances件数) + voteStanceIdx(0-2)`
（`V2I` は部活動では恒等写像 `[0,1,2,3,4,5,6]`。VOTE_ISSUESとARENA_JS ISSUESの並びが
たまたま同じため）。`topic_id = bukatsu-chiiki-issue-stance-v1`。範囲は0〜20（7×3=21通り）。

**この3つ（Supabase choiceIdx算出用のissueIdx、地図の点`i:`、ページの論点カード表示順）は
すべてpage index（上表）で揃っている。段階4のどの接続作業も、この並びを変えない。**

---

## 2. 今回接続したもの

`configs/bukatsu-chiiki-reaction-map.json` の `issue_counts.basis` を `"opinion"` から
`"public_json"` に変更した。

- `scripts/issue_card_counts.py` に `count_by_issue_from_public_json(theme)` を追加。
  `data/public/themes/{theme}.json` の `issues[].label / .count` を読むだけで、
  正典（social-samples）を再計算しない
- `card_counts()` / `other_count()` は `basis == "public_json"` のとき上の関数を使う
  （既存の9テーマは `all` / `opinion` のままで無変更・無影響）
- 影響範囲: `explainer-card` の件数span（6枚）と、リード文「分析対象となった意見N件を
  AIが7つの論点に整理しました」（`issue_counts.sync: ["lead"]`）

**この変更で表示上の数字は1件も変わらない。** 接続前後でバイト一致することを
`sync_issue_counts.py bukatsu-chiiki --check` で確認済み（`OK` = 差分0）。

## 3. まだ接続していないもの（正直な現状）

論点の件数を独自に再計算している箇所は他にも残っている。

- **SNS反応マップのセクター配列 `const ISSUES=[{k:'ラベル',n:N}]`（角度・面積を決める）**:
  `scripts/update_bukatsu_tide.py`（696行）が通常のデータ更新のたびに正典から直接数え直して
  埋めている。今回は接続していない。現在の表示（97/143/283/189/9/227/45）は正しい値で、
  重複計算による食い違いも今のところ起きていないため緊急度は低いが、公開データJSONと
  二重に数え続けている状態ではある
- **`scripts/build_bukatsu_arena.py` の `ARENA_JS` 定数（n:16,34,58,28,8,51,50という
  古いプレースホルダーを含む）**: これは実行されない死んだコード経路。ページに
  `<!-- RESEARCH_CONDITIONS_START -->` が既にあるため、`transform()` は729行目以降の
  「セクション全置換」を通らず、`update_existing_html()` への早期returnで終わる
  （715-723行目）。**削除候補**（4節参照）
- 「調査条件」ブロック（取得元・期間・件数）は今回移していない。書き手は
  `refresh_adapters/bukatsu.py` の `finalize()` → `build_bukatsu_arena.py` の
  `update_existing_html()` のまま（[[reference_research_conditions_owner]] のとおり、
  promote後にfinalizeが貼り直す構造を崩していない）

## 4. ビルダーのどの関数が要らなくなったか（棚卸し）

`scripts/build_bukatsu_arena.py`（811行）を今回精査した結果:

| 関数/ブロック | 現在の状態 | 段階4後の判断材料 |
|---|---|---|
| `transform()` の729-786行目（`EXPLAINER_SECTION`/`VOTE_SECTION`/`ARENA_SECTION`/`ARENA_JS`定数を丸ごと差し込む経路） | **既に死んでいる。** 719行目の早期return（`<!-- RESEARCH_CONDITIONS_START -->` があれば通らない）により、現在の公開ページでは実行されない | 削除候補。ただしtransform()自体はfinalize()から呼ばれ続けるため、削除するなら`transform()`を「早期returnの中身だけ」に単純化し、719行目より下を丸ごと関数ごと落とす。実施は段階4の本体作業ではなく別課題にする |
| `ARENA_JS`定数のn:16,34,58,28,8,51,50 | 上記と同じ理由で未使用 | 同上。削除時に一緒に消える |
| `card_counts()` 呼び出し（811行目、`apply_counts`経由） | **現役。** 今回`basis: public_json`化により、内部の集計元だけが`data/public/themes/`へ切り替わった。呼び出し側のコードは無変更 | 変更なし。他9テーマも同じ関数を共有しているため、この呼び出し自体は残す |
| `update_bukatsu_tide.py`（696行、アリーナのn:とSM_RAWを実際に更新している現行の主経路） | **現役。** 今回は未接続（3節参照） | 次に接続するなら最有力候補。ただし696行あり、潮目（前回比較）ロジックを含むため、段階4の後半か、課題57完了後の共通化検討で扱うのが妥当 |
| `classify_bukatsu_arena_hermes.py`（228行、分類器） | 現役。公開データJSON生成の入力（social-samples）を作る側であり、接続対象外 | 変更なし |

**規模感**: builder 811行 + classifier 228行 + adapter(refresh_adapters/bukatsu.py) 94行 +
update_bukatsu_tide.py 696行 = 約1,829行。今回接続したのは`issue_card_counts.py`
（共有関数、40行追加）経由の一部だけで、テーマ別コードそのものへの変更は
「configの1行（basis値）」のみ。テーマ別コードの実装一致度が低い
（[[reference_theme_page_code_variance]]）理由は、この`update_bukatsu_tide.py`のような
テーマ固有の大きなロジックが個別に存在するため。

## 5. 検査結果

- `python3 scripts/verify_theme_page.py bukatsu-chiiki` → 全項目OK（`verify_issue_count_source`
  と `verify_denominators` を `basis: public_json` に対応させる必要があり、対応済み）
- `python3 scripts/sync_issue_counts.py bukatsu-chiiki --check` → `OK`（差分0）
- `python3 -m unittest discover -s tests` → 327件中326件成功（唯一の失敗は本作業と無関係な
  既存の遅れ。着手前に確認済み）
- 他9テーマの `verify_theme_page.py` を実行し、全テーマNG 0件を確認（今回の変更が
  他テーマに影響していないことの確認）

## 6. 次にすること

段階4の2本目、`school-nickname-ban`へ進む。あだ名禁止は唯一の文字列ID形式
（`"issue":"experience"`）を使っており、固定IDへの移行先の答え合わせになる
（[[project_task57_stage4_order]] 参照）。
