# 数え方の統一を検査で固定する — 2026-08-08

このファイルをそのまま新しいセッションに貼って実行する。

> **前提**: 辺野古・皇室典範・高齢者免許・憲法改正の4本がすべて完了していること。
> 完了していないテーマがあると、追加した検査がそのテーマでNGになり作業が進まない。

---

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのハブAI（Claude Code）です。

- リポジトリ: `/Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator`
- 正典: `LOOP.md` ⓪（作業場所の確保）/ データ台帳: `DATA_SHEET.md`

## なぜこの作業をするか

11テーマの数え方を「意見のみ」に統一する作業が終わった。
**これが二度と壊れないように、検査で固定する。**

### 今回いちばん大事な背景

問題が起きたとき、**検査は存在していたのに素通りしていた**。

- 論点カードの件数を正典から自動生成する仕組み（`sync_issue_counts.py`）はあり、
  生成された件数（`explainer-count`）は**11テーマすべて正しかった**
- 同じページの**見出しには手書きの件数**（`issue-count`）が別にあり、
  4テーマで古い数字のまま残っていた
- `verify_theme_page.py` の「ハードコードされた件数が残っていない」検査は
  `<article class="explainer-card">` の**内側しか見ていない**ため、
  別要素である見出しの古い数字を検出できなかった
- 結果、`verify_theme_page.py` は **NG 0件で通っていた**

つまり原因は「検査が無いこと」ではなく「**検査の射程が狭かったこと**」。
だから今回は、**検査を足すだけで終わらせず、わざと壊して効くことを確かめる**。

---

## 手順

### 1. 作業ツリーを用意する

```bash
cd /Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator && git fetch origin && git worktree add ../isa-wt-check -b task/denominator-check origin/main
```

成功の形: `Preparing worktree` と `Switched to a new branch` が出る。

> **末尾の `origin/main` を省かないこと。** 省くと共有ツリーの現在のブランチから
> 枝分かれする。共有ツリーは他セッションの作業中で、main より遅れていたり
> 無関係なコミットが載っていたりする（2026-08-08 の皇室典範では、30コミット遅れ・
> 7コミット先行の状態だった）。そのままPRを出すと他人の変更を巻き込む。

### 2. 非公開の正典データを復元する

何をするか: Git管理外の本文付きデータを、バックアップから作業ツリーへ展開する。
**これをしないと検査で落ちる。** 不足していても `git status` には出ない。
外付けディスク `/Volumes/HD-LE-B` が未接続だとここで止まる。

```bash
cd ../isa-wt-check && tar xzf "$(ls -t /Volumes/HD-LE-B/issue-stance-private-backups/private-data-*.tar.gz | head -1)" -C . --exclude=manifest.json && python3 -c "import yaml,os; th=yaml.safe_load(open('THEMES.yaml'))['themes']; print('欠落:', [v['sample_file'] for v in th.values() if not os.path.exists(v['sample_file'])])"
```

成功の形: `欠落: []`（空のリスト）。

### 3. 前提を確認する（ここで止まる可能性がある）

```bash
python3 scripts/build_data_sheet.py && cat DATA_SHEET.md
```

成功の形: **全11テーマ**で「意見 / 論点の合計 / 賛否の合計 / マップの点」が同じ数。

ずれているテーマが1つでもあれば、**そのテーマの作業が未完了**なので着手しない。
どのテーマがどうずれているかを報告して止まる。

| テーマ | 担当した指示文 |
|---|---|
| 辺野古 | `20260808_henoko-opinion-only.md` |
| 皇室典範 | `20260808_arena-opinion-only.md` |
| 高齢者免許・自転車 | `20260808_elderly-opinion-only.md` |
| 憲法改正 | `20260808_constitutional-amendment-opinion.md` → `20260808_constitutional-arena.md` |

> 副首都（意見229 / 論点227）と高市（意見360 / マップ359）に1〜2件の差がある場合、
> 原因は `main_issue` が空のレコードである可能性が高い。**今回はこの差を無理に
> 埋めようとせず、原因だけ調べて報告する。**

### 4. `verify_theme_page.py` に検査を足す

対象ファイル: `scripts/verify_theme_page.py`

#### 4-1. 4つの数が一致することを検査する

```text
意見件数 = 論点カードの件数合計 = マップの点の数 = 賛否区分の件数合計
```

`configs/{theme}-reaction-map.json` の `issue_counts.basis` が宣言している母数を基準にする。
除外条件などで一致しない場合は、**その差分と理由が設定ファイルに明記されていること**を
条件にする（黙って許さない）。

#### 4-2. ハードコードされた件数の検査を、ページ全体に広げる

現在の実装（380行目付近）は次のようになっている。

```python
for block in re.finditer(r'<article class="explainer-card".*?</article>', page, re.DOTALL):
```

**この `explainer-card` の内側に限定しているのが、見逃しの原因だった。**
ページ全体を対象にする。生成スクリプトが書き込む span 以外の場所に件数が
書かれていたらNGにする。

#### 4-3. 「最大勢力」バッジの検査を足す

「最大勢力」「論点1」などの強調表示が、**実際に件数が最大の論点に付いていること**を
検査する。自転車の青切符では、16件の論点4（免許制）に「最大勢力」が付いていた
（実際の最大は38件の取締り強化賛成）。

### 5. データ台帳が古くなったら落ちるようにする

`tests/` に、`DATA_SHEET.md` が正典と一致していることを確認するテストを追加する。

```bash
python3 scripts/build_data_sheet.py --check
```

これが exit 0 であることをテストにする。データを更新して台帳を作り直し忘れると、
テストが落ちるようになる。

### 6. 全部通ることを確認する

```bash
python3 -m unittest discover -s tests -q && python3 scripts/verify_theme_page.py && python3 scripts/verify_top_page.py
```

成功の形: すべて exit 0。

### 7. わざと壊して、検査が効くことを確かめる（省略禁止）

**この手順を省かないこと。** 今回の問題は「検査があるのに素通りしていた」ことが原因で、
検査を足しただけでは効いているかどうか分からない。

次の3つをそれぞれ試し、**毎回NGが出ることを確認してから元に戻す**。

| 壊し方 | 期待する結果 |
|---|---|
| いずれかのページの見出しに `<span>999件</span>` を手で足す | 4-2 の検査がNG |
| いずれかのページのマップの点を1つ削る | 4-1 の検査がNG |
| 「最大勢力」の表示を件数の少ない論点へ移す | 4-3 の検査がNG |

戻し方は、変更したファイルを**パス指定で**戻す。

```bash
git checkout -- docs/{壊したファイル}
```

**`git checkout -- <ディレクトリ>` を使わない。** ディレクトリ単位で戻すと、
他セッションの未追跡ファイルを巻き込む事故になる。

### 8. 記録を残す

- `TASK_BOARD.md` に、数え方を「意見のみ」に統一したことと、検査を固定したことを記録する
- 課題29（ページ内件数表示と sample_file の突き合わせ）が完了していれば完了に更新する
- `DATA_REFRESH.md` に「数えるのは意見のみ」という1行のルールを追記する

### 9. コミットする

コミット対象:

- `scripts/verify_theme_page.py`
- `tests/`（追加したテスト）
- `TASK_BOARD.md`
- `DATA_REFRESH.md`

push して main へPRを出す。

### 10. 片付ける

```bash
git worktree remove ../isa-wt-check
```

---

## 制約・注意

- **公開ページを書き換えない。** このセッションは検査を足すだけ。手順7で壊したものは
  必ず元に戻す
- **`scripts/inject_tide_widget.py` を実行しない。** 公開中のページを古いデータへ
  巻き戻す不具合がある（TASK_BOARD 課題38）
- **`social-samples/` 配下の未追跡ファイルを消さない。** 非公開の正典は gitignore 対象で、
  古いブランチからは不要ファイルに見える（2026-08-07 に正典1,606件が削除されかけた）
- **`git checkout -- <ディレクトリ>` を使わない。** 戻すなら自分が変更したファイルだけを
  パス指定で
- 保護タグ（GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP）を壊さない
- main への直接コミット禁止

## 完了報告に含めること

1. 手順3で全11テーマがそろっていたか（ずれていたテーマがあればその内容）
2. 追加した検査の一覧
3. **手順7で、3つの壊し方それぞれに対して検査が何と言ったか（実際の出力）**
4. 副首都・高市の1〜2件の差の原因（調べた結果）
5. オーナーへの依頼事項があれば1つだけ
