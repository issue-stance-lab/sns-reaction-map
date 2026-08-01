## タスク: 件数の正典を定義し、検証ハーネスを作る（S1）

### 出典

`WORK_PLAN_2026-08.md` §2「着手前に確定させること」＋ §3 A-5（自動検査の土台を前倒し）
`WORK_PLAN_2026-08_SESSIONS.md` §4

### 背景（調査済みの事実。再調査不要）

`scripts/sync_portal_stats.py` の `parse_themes_yaml()` は THEMES.yaml の**コメント**を正規表現で拾っている。

```python
c2d_match = re.search(r"classify2d:\s*done\s*#\s*(\d+)件", block)
```

実行した結果：

- トップページの表示値: **5,953**
- スクリプトの計算値: **2,946**
- 公開11テーマ中**2テーマが count=0**
  - `bukatsu-chiiki`: コメントが `# 旧2D 245件は履歴保持。...` で `# ` の直後が数字でないため外れる
  - `consumption-tax-cut`: `classify2d: n-a` のため対象外になる

さらに `update_html()` に**マッチせず、エラーも出さずに成功する置換**が存在する。

```python
r'(<em>)\d+/\d+更新 \+[\d,]+件追加(</em>)'   # 期待: "7/29更新 +452件追加"
# 実際のHTML: <em>7/29更新</em>  → 0件マッチ。黙って何もしない
```

この結果、update-bar は「最終更新: 2026年7月26日」、hero は「7/29更新」で食い違ったまま放置されている。

また `social-samples/` には1テーマに複数の候補ファイルがある。

```
ai-copyright_classified.json        475件
ai-copyright_2d_classified.json     708件
ai-copyright-v2_samples_refresh...  458件
```

**「どれを分析対象と呼ぶか」が決まっていない**ことが、数字が腐り続けた根本原因。

---

### 目的

トップページに出る数値の出所を1つに確定させ、以降の変更で数値が壊れたら**必ず気づける状態**にする。

---

### やること

#### Step 1: 各テーマの正典ファイルを特定する

公開中の11テーマそれぞれについて、**現在の公開HTMLがどのJSONから生成されたか**を確定する。
`run_pipeline.py` と各テーマの生成履歴（git log）を追跡する。

判断に迷うテーマがあれば、**勝手に決めず、完了報告に「候補と迷った理由」を書く**。

#### Step 2: THEMES.yaml に明示フィールドを追加する

全11テーマに以下を追加。コメントではなくフィールドとして書く。

```yaml
  ai-copyright:
    title: 生成AIと著作権
    sample_file: social-samples/ai-copyright_2d_classified.json
    sample_period: "2026-06-10〜2026-07-26"
    sample_source: "Yahooリアルタイム検索"
```

- `sample_file`: 公開ページの生成元となった JSON への相対パス
- `sample_period`: 収集期間（既存の notes から拾えるものは拾う。不明なら `unknown` と書く。**推測で埋めない**）
- `sample_source`: 取得元

#### Step 3: sync_portal_stats.py を書き換える

- 件数は **`sample_file` を実際に開いてレコード数を数える**。コメント抽出も手入力フィールドも使わない
- `classify2d` コメントからの抽出コードを削除する
- `sample_file` が存在しない／読めない／0件のテーマがあれば**異常終了する**（黙って0を足さない）
- **各 `re.sub` が最低1件マッチしたことを検証し、0件なら異常終了する**
- 用語を「分析済み投稿」から「**分類済み投稿**」に統一する（数えているのは分類済みの有効件数であり収集件数ではないため）

#### Step 4: 次回更新日を THEMES.yaml から生成する

現在 `2026-08-02` が2箇所にハードコードされている。

- `docs/index.html` の `<strong id="hero-next-update">8/2</strong>`
- 同 `:254` のインラインJS `new Date('2026-08-02T00:00:00+09:00')`

THEMES.yaml の `refresh_at` の**最小値**から両方を生成するようにする。
日付超過時の分岐（`本日更新予定` / `更新済み`）は既に実装済みなので**そのまま残す**。

#### Step 5: scripts/verify_top_page.py を新規作成する

以降のすべてのレビューで使う検証ハーネス。出力形式は以下に固定する。

```
=== 数値の出所 ===
分類済み投稿   2,946   ← sample_file の実レコード合計（11テーマ）
公開テーマ数      11   ← THEMES.yaml published:done
最終更新    2026-08-02  ← THEMES.yaml updated_at 最大
次回更新    2026-08-09  ← THEMES.yaml refresh_at 最小

=== 置換の空振り検査 ===
OK  hero-total-samples        1件マッチ
OK  公開中のテーマ             1件マッチ
NG  em更新日                   0件マッチ

=== 禁止表示 ===
OK  「割れ度」なし
...

=== リンク ===
OK  #ranking 参照なし
```

- NG が1件でもあれば **exit code 1** で終了する
- 「禁止表示」「リンク」の検査項目は**この時点では空でよい**。以降のPRで1つずつ追加していく（枠だけ作る）
- `tests/` からも呼べるようにする

#### Step 6: 実行して差分を確認する

`python3 scripts/sync_portal_stats.py` を実行し、トップの数字が新しい正典値に更新されることを確認する。

**重要**: 表示値が 5,953 から大きく下がる可能性が高い。それは正しい挙動。
下がった値が実データと一致していることを確認したうえで、完了報告に**変更前後の値と差の理由**を書く。

---

### やらないこと

- トップページの見た目の変更（ドーナツ・割れ度の削除は **S2** で行う）
- 新しい検査ルールの追加（枠だけ作る。ルールは各PRで足す）
- `social-samples/` のファイル整理・統合
- テーマページ側の表示変更

---

### 制約（必ず守る）

- 保護タグを壊さない: GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP
- ブランチ: `task/sample-count-canonical`。main 直接コミット禁止
- `docs/index.html` を `build_site_portal.py` で生成しない
- 数値をハードコードしない。必ず THEMES.yaml か実データファイルから導出する
- **不明な値を推測で埋めない。** わからないものは `unknown` と書き、完了報告に列挙する

---

### 完了条件

- [ ] 11テーマすべてに `sample_file` / `sample_period` / `sample_source` がある
- [ ] `sync_portal_stats.py` が `sample_file` の実レコード数から件数を計算する
- [ ] count=0 のテーマがあれば異常終了する
- [ ] 各 `re.sub` の空振りを検出し、0件マッチで異常終了する
- [ ] 次回更新日が `refresh_at` から生成され、ハードコードが残っていない
- [ ] `scripts/verify_top_page.py` が存在し、NG時に exit 1 する
- [ ] トップの表示値がスクリプト実行結果と一致する
- [ ] 「この数字はこのファイルのレコード数です」と1行で説明できる

---

### 完了報告に必ず含めること

1. `git diff --stat`
2. `python3 scripts/verify_top_page.py` の出力を**そのまま貼る**
3. **11テーマそれぞれの `sample_file` と件数の一覧表**
4. 分類済み投稿数の**変更前後の値と、差が生じた理由**
5. `sample_period` を `unknown` にしたテーマの一覧
6. 正典ファイルの選定に迷ったテーマと、その候補
7. 実行したテストコマンドと結果
