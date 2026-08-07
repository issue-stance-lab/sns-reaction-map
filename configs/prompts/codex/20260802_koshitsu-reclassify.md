## タスク: koshitsu-tenpakai の論点を正典データから再分類する（S8-fix）

### 出典

S8 レビューでの差し戻し1件
`TASK_BOARD.md` 課題29・課題30

---

### 問題

`data/issue-counts/koshitsu-tenpakai.json`（268件）と正典 `sample_file`（347件）の
**URLの共通が0件**。部分集合ですらなく、まったく別の投稿群から件数が作られている。

| テーマ | issue-counts | sample_file | URL共通 |
|---|---|---|---|
| constitutional-amendment | 422 | 646 | 422 ✅ |
| elderly-license-revocation | 211 | 211 | 211 ✅ |
| henoko-student-accident | 265 | 363 | 265 ✅ |
| **koshitsu-tenpakai** | **268** | **347** | **0** ❌ |

**原因**: S1 で `sample_file` を合成データ `_prev_synthetic.json`（273件）から
実データ `_hermes_cur_20260726.json`（347件）へ差し替えたが、
公開ページのアリーナは差し替え前のデータのままだった。
そこから抽出したため、旧データセットの件数が固定されている。

S1 で除去したはずの旧系統の数字が、論点カードとして復活しかけている。

---

### ⚠️ 調査済み：**再分類は不要かもしれない**

**`sample_file`（347件）は既に `main_issue` を持っている。**

```python
# social-samples/koshitsu-tenpakai_hermes_cur_20260726.json
# classification.main_issue の分布（合計347件）
男系vs女系            104
旧宮家養子縁組         74
その他                58
立法手続き・民主主義    54
女性天皇・女系天皇      40
愛子さま・皇族の地位    17
```

つまり**分類作業そのものは済んでいる**。問題は分類ラベルとカードのタクソノミーが一致していないこと。

| カード（config `issue_counts.cards`） | 対応する `main_issue` |
|---|---|
| `dankei` 男系維持 vs 女系容認 | 男系vs女系（104）|
| `yoshi` 旧宮家男系男子の養子制度 | 旧宮家養子縁組（74）|
| `kokkai` 国会審議・成立手続き | 立法手続き・民主主義（54）|
| `josei` 女性天皇・愛子天皇 | 女性天皇・女系天皇（40）|
| `koseki` 女性皇族の皇籍維持 | **対応なし** |
| `kenpo` 憲法・制度上の妥当性 | **対応なし** |
| （カードなし） | 愛子さま・皇族の地位（17）… `josei` か `koseki` か曖昧 |
| （カードなし） | その他（58）|

**2枚のカードに対応するラベルが存在しない。** ここが本質的な問題。

---

### やること

#### Step 1: 方針を決めて報告する（実装前）

以下の2案から選び、**理由とともに報告してから実装に進むこと。**

**案A: 既存の main_issue をカードに写像する（安価・推奨）**

- 再分類なし。`sample_file` の6ラベルをカードへ対応づける
- 対応先のない `koseki` `kenpo` の2枚は**カードから削除**する
- `愛子さま・皇族の地位`（17）の扱いを決める（`josei` に統合が自然）
- カードは4枚になる（dankei / yoshi / kokkai / josei）
- **利点**: 追加のAI実行が不要。データと表示が完全一致する
- **欠点**: 論点カードの解説文2枚を落とすことになる

**案B: カードのタクソノミーで再分類する（高価）**

- `sample_file` 347件を、カードの6分類へAIで分類し直す
- 既存スクリプト `scripts/classify_koshitsu_arena_hermes.py` を参照して実装
- **利点**: 論点カード6枚を維持できる
- **欠点**: AI実行コスト、分類精度の検証が必要、既存の `main_issue` と二重管理になる

> **推奨は案A。** 論点カードは「実データにある論点」を見せるものであり、
> データに存在しない論点のカードを維持するために再分類するのは本末転倒。
> 課題30 の発端も「実データと表示のズレ」だった。
> ただし編集上カードを残したい判断があれば案Bでよい。**先に相談すること。**

#### Step 2: 選んだ案を実装する

**案Aの場合**

1. `configs/koshitsu-tenpakai-reaction-map.json` の `issue_counts` を書き換える
   - `source` を `social-samples/koshitsu-tenpakai_hermes_cur_20260726.json` に変更
   - `cards` を実在する `main_issue` のみに絞る
2. `data/issue-counts/koshitsu-tenpakai.json` を**削除する**（正典から直接数えられるため不要）
3. `sync_issue_counts.py` が `sample_file` から直接読めるようにする
4. 削除するカード（`koseki` `kenpo`）の解説文を、対応するカードへ統合するか削除する

**案Bの場合**

1. `scripts/classify_koshitsu_arena_hermes.py` を参照し、カード6分類での再分類を実行
2. 出力を `social-samples/koshitsu-tenpakai_cards_classified_YYYYMMDD.json` に保存
3. **分類精度の抜き取り検査**（20件以上を目視）を行い、結果を報告
4. `data/issue-counts/koshitsu-tenpakai.json` を再生成
5. **正典 `sample_file` と URL が完全一致すること**を確認

#### Step 3: 検査を追加する

**このタスクで最も重要。同じ事故を二度起こさないための仕掛け。**

`scripts/verify_theme_page.py` に追加：

```
=== 論点カードのデータ整合 ===
OK  issue-counts の URL が sample_file の部分集合である（全11テーマ）
OK  issue-counts の件数合計が sample_file の件数以下である
OK  全カードに対応する分類ラベルが実在する
```

- **URLレベルで部分集合であることを検査する。** 件数の一致だけでは今回の事故を検出できなかった
- 全11テーマに適用する
- **負のテストで NG / exit 1 を確認すること**

#### Step 4: アリーナ表示との整合を確認する

ページ内 JS の `arenaIssueOf()` が SM_RAW を振り分けている。
アリーナの扇とカード件数が矛盾しないことを確認する（矛盾する場合は報告）。

---

### やらないこと

- 他10テーマの issue-counts の変更（3テーマは部分集合であることを確認済み）
- `arguments` の変更
- トップページの変更
- 課題29 の残作業（h3 件数の体系統一）

---

### 制約（必ず守る）

- 保護タグを壊さない: GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP
- ブランチ: `task/ai-copyright-arguments` に追加コミット（S8のPRに含める）
- **合成データ（`_prev_synthetic.json`）を一切参照しない**
- 数値をハードコードしない
- `verify_top_page.py` が exit 0（koshitsu 347件が変わらないこと）

---

### 完了条件

- [ ] Step 1 の方針が報告され、承認を得ている
- [ ] koshitsu の issue-counts が `sample_file` と URL レベルで整合している
- [ ] 論点カードの件数とアリーナ表示が矛盾しない
- [ ] `verify_theme_page.py` に部分集合検査が入り、全11テーマで exit 0
- [ ] 負のテストで NG / exit 1 を確認済み
- [ ] `verify_top_page.py` が exit 0

---

### 完了報告に必ず含めること

1. **Step 1 で選んだ案と理由**
2. `git diff --stat`
3. 修正後の koshitsu 論点カード件数の一覧
4. issue-counts と sample_file の URL 重複数（全11テーマ）
5. `verify_theme_page.py` / `verify_top_page.py` の出力
6. 部分集合検査の負のテスト結果
7. 案Bを選んだ場合は分類精度の抜き取り検査結果
8. 削除・統合したカードがあればその内容
