## タスク: 部活動の地域移行に「両側の強い論拠」を追加する（S7）

### 出典

`WORK_PLAN_2026-08.md` §4 B-2 の横展開1本目
`WORK_PLAN_2026-08_SESSIONS.md`

### なぜこのテーマか

GSC実測（28日間）で、表示回数の上位4テーマが全46表示のうち38表示（83%）を占める。

| テーマ | 表示 | クリック | 順位 | arguments |
|---|---|---|---|---|
| elderly-license-revocation | 11 | 1 | 8.9 | ✅ 完了 |
| ai-copyright | 11 | 0 | 7.1 | 未 |
| **bukatsu-chiiki** | **9** | **1** | **9.7** | **← 今回** |
| bike-blue-ticket | 7 | 0 | 12.7 | 未 |
| 残り7テーマ合計 | 8 | 0 | — | 未 |

残り7テーマは合計8表示しかないため、**全10テーマへの横展開は行わない。**
上位3テーマ（bukatsu → ai-copyright → bike-blue-ticket）のみを対象とし、
残りは流入の兆しが出てから判断する。

このテーマはクリックが発生している2テーマのうちの1つ。

---

### 前提（S5 で型が確定済み）

`configs/elderly-license-revocation-reaction-map.json` の `arguments` が実装の参照元。
**同じスキーマ・同じ描画位置・同じ検査で通すこと。**

```json
"arguments": {
  "summary_30s": "…",
  "side_a": { "label": "…", "strongest": "…", "basis": "…" },
  "side_b": { "label": "…", "strongest": "…", "basis": "…" },
  "shared_premise": "…",
  "real_conflict": "…",
  "unresolved": "…",
  "sources": [ {"label": "…", "url": "…"} ]
}
```

`scripts/build_reaction_map.py` は既に `arguments` に対応済み。
**スキーマの変更は行わない。** 変更が必要だと判断した場合は、実装前に報告すること。

---

### 調査済みの事実（再調査不要）

**正典データ**: `social-samples/bukatsu-chiiki_hermes_classified_20260723.json`（467件）

**論点別の分布**（Hermes分類）

| 論点 | 件数 |
|---|---|
| 制度・移行プロセス | 124 |
| 教員の働き方 | 120 |
| 教育的意義・機会 | 85 |
| 受け皿・指導者 | 74 |
| 費用・家庭負担 | 39 |
| 地域格差 | 2 |
| その他 | 23 |

**既存の `conflict_axes`**

- 移行推進派: 教員の働き方改革と持続可能な部活動
- 慎重・反対派: 費用増と学校文化喪失への懸念

**既存の `background`** に、少子化・教員の長時間労働・休日部活からの段階的移行・受け皿不足・会費負担・都市部と地方の環境差が記述済み。**重複させず、論拠として掘り下げること。**

**⚠️ このテーマには専用ビルドスクリプトがある**

`scripts/build_bukatsu_arena.py` が `docs/bukatsu-chiiki-reaction-map.html` を扱う。
参照している JSON が `bukatsu-chiiki_2d_classified.json`（旧2D）で、
`THEMES.yaml` の `sample_file`（`_hermes_classified_20260723.json`、467件）と**異なる**。

**着手前にどちらの経路でHTMLが生成されているかを確認し、報告すること。**
経路を誤ると、再ビルド時に arguments が消える。

---

### やること

#### Step 1: 生成経路を確認する

- `docs/bukatsu-chiiki-reaction-map.html` が `build_reaction_map.py` と `build_bukatsu_arena.py` のどちらで生成されるか
- `build_bukatsu_arena.py` 経由なら、そちらにも `arguments` 描画を実装する
- **再ビルドしても arguments が失われないこと**を確認する

#### Step 2: 執筆する（このタスクの本体）

**コード作業より時間をかけること。**

論点分布から、対立の中心は「教員の働き方（120件）」と「費用・家庭負担（39件）＋受け皿・指導者（74件）」の間にある。
最多の「制度・移行プロセス（124件）」は賛否というより**進め方への不満**なので、
`real_conflict` や `unresolved` で扱うほうが自然な可能性が高い。

**執筆の必須要件**

- `strongest` は**相手側が読んでも「確かに一理ある」と思える水準**で書く。藁人形にしない
- 自分の側の弱点を認めたうえで主張する形にする（elderly-license の書き方を参照）
- `basis` には**検証可能な出典を必ず伴わせる**。数値を書くなら出典必須
- `unresolved`（まだ確認できていない点）を省略しない。**ここがこのサイトの独自性**
- SNS投稿の引用ではなく、**論拠そのものを編集して書く**

**出典は公的機関を優先**

- スポーツ庁・文化庁（部活動の地域連携・地域クラブ活動に関する方針、実態調査）
- 文部科学省（教員勤務実態調査）
- 各自治体の実証事業報告

**推測で数値を書かない。** 確認できない論点は `unresolved` に回す。

#### Step 3: 表示を確認する

- `arguments` が「6つの論点」の直後、「SNS反応マップ」より前に出ること
- 代表投稿（「7つの論点とXの声」）より**上**にあること
- 既存の `background` と内容が重複していないこと

#### Step 4: 検査を通す

- `python3 scripts/verify_theme_page.py` で **bukatsu-chiiki も arguments 検査の対象になること**
  （現在 elderly-license のみが対象になっている場合は、`arguments` を持つテーマを自動判定する形に拡張する）
- sources のリンクが全て HTTP 200
- 全11テーマで exit 0
- `verify_top_page.py` が exit 0（件数 467 が変わらないこと）

---

### やらないこと

- `arguments` スキーマの変更（必要なら実装前に報告）
- 他テーマへの展開（次は ai-copyright、別タスク）
- `sample_period` の unknown 埋め（TASK_BOARD 課題28）
- トップページの変更
- 既存の `background` の書き換え

---

### 制約（必ず守る）

- 保護タグを壊さない: GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP
- ブランチ: `task/bukatsu-arguments`。main 直接コミット禁止
- **出典のない主張を書かない。** 数値には必ず一次情報のURLを付ける
- **再ビルドで arguments が消えないこと**（Step 1 の確認結果を実装に反映する）
- 他10テーマが壊れていないこと

---

### 完了条件

- [ ] 生成経路が特定され、再ビルドしても arguments が保持される
- [ ] 6項目（30秒要約／両側の論拠／共有前提／真の対立点／未確認点／一次情報）がすべて埋まっている
- [ ] `strongest` が双方とも、相手側から見ても筋の通る内容になっている
- [ ] 一次情報が公的資料で、リンクがすべて有効
- [ ] `background` と内容が重複していない
- [ ] arguments が代表投稿より前に表示される
- [ ] `verify_theme_page.py` が bukatsu-chiiki の arguments も検査し、全11テーマで exit 0
- [ ] `verify_top_page.py` が exit 0

---

### 完了報告に必ず含めること

1. `git diff --stat`
2. **Step 1 の生成経路の確認結果**（どちらのスクリプトか、再ビルド耐性をどう担保したか）
3. **執筆した両側の論拠の全文**（内容のレビュー対象。ここが本体）
4. 引用した一次情報の一覧とURL
5. `python3 scripts/verify_theme_page.py` の出力（全テーマ）
6. `python3 scripts/verify_top_page.py` の出力
7. 検査の負のテスト結果（arguments を欠損させて NG / exit 1 を確認）
8. 判断に迷った点、`unresolved` に回した論点とその理由
