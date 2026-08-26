## タスク: OGP画像を新デザインに差し替える（S10）

### 出典

`TASK_BOARD.md` 課題32
`creative/manga-prompts/site-ogp-header-prompts.md`（生成プロンプト）

---

### 背景（調査済み・再調査不要）

現行の `docs/ogp/default.png`（2026-06-27作成）に、サイトから削除済みの要素が残っている。

| 画像内の要素 | 問題 |
|---|---|
| 「その話題、SNSでは実はどっちが多い？」 | S2でトップから削除した旧コピー |
| 賛成42% / 保留18% / 中立20% / 反対20% | **根拠のないダミー値**（S1〜S6で潰した性質の数字） |
| 「12.5K」「トレンド上昇中」「話題沸騰中」 | 実データではない演出値 |

この画像は**トップページと usage.html のOGP**であり、サイトURLを共有するたびに表示される。
2026-08-02にX固定ポストを「世論調査ではありません」に差し替えた結果、
**同じ投稿内で本文と画像が矛盾している**状態になっている。

新デザインはサイトのヒーロー（4色のドット群＋角丸ピル＋天秤）に準拠して生成済み。

---

### ⚠️ 着手前に確認すること

**新画像のファイルパスをユーザーに確認する。** 生成済みだがリポジトリには未配置。

```
OGP画像（1200×630）: ________________________
ヘッダー画像（1500×500）: ________________________
```

パスが不明なまま進めないこと。

---

### やること

#### Step 1: 新OGP画像を検証する

配置前に以下を確認し、**満たしていなければ報告して止まる**。

- [ ] 寸法が **1200×630** ちょうど
- [ ] 画像内に**数字・パーセント・円グラフ・棒グラフ・トレンド矢印が1つも無い**
- [ ] 「どっちが多い」「話題沸騰中」等の旧コピーが無い
- [ ] ロゴマークがドット6個＋交差する楕円2本になっている
- [ ] 文字が端で切れていない（安全域: 中央1000×520）

#### Step 2: 配置と最適化

```
docs/ogp/default.png  ← 新画像で上書き
```

- **1MB以下に圧縮する**（現行は1,396,582バイト＝約1.4MB）
- PNG のまま。形式は変えない（`og:image` の参照を壊さないため）
- 圧縮前後のファイルサイズを報告する
- 旧画像は `git` の履歴に残るため、別途バックアップは不要

#### Step 3: ヘッダー画像を参照用に保存

X へのアップロードは人手で行うが、**リポジトリにも原本を残す**。

```
docs/images/site/x-header.png   （1500×500）
```

HTMLからは参照しない。将来の作り直し時の基準として保管する。

#### Step 4: 検査を追加する

`scripts/verify_top_page.py` に以下を追加する。

```
=== OGP画像 ===
OK  docs/ogp/default.png が存在する
OK  寸法が 1200x630 である
OK  ファイルサイズが 1MB 以下である
OK  index.html / usage.html の og:image が default.png を指している
```

- 寸法の取得は標準ライブラリで可能（PNGヘッダの8バイト目以降を読む。Pillow不要）
- **負のテストで NG / exit 1 を確認すること**（寸法違いのダミーPNGを置いて検出されるか）

#### Step 5: 動作確認

- `python3 scripts/verify_top_page.py` → exit 0
- `python3 scripts/verify_theme_page.py` → 全11テーマ exit 0（回帰確認）
- ローカルで `docs/index.html` を開き、表示崩れが無いこと

---

### やらないこと

- テーマ別OGP9枚の差し替え（`ogp/ai-copyright.png` 等。**内容確認は Step 6 で報告のみ**）
- X へのアップロード（人手作業）
- OGPキャッシュの更新（人手作業）
- `og:image` のパス変更
- トップページのデザイン変更

#### Step 6: テーマ別OGPの点検（報告のみ）

`docs/ogp/` の9枚に、同種のダミー数値が入っていないか目視で確認し、**一覧で報告する**。

```
ai-copyright.png / bike-blue-ticket.png / bukatsu-chiiki.png
constitutional-amendment.png / elderly-license-revocation.png
henoko-student-accident.png / school-nickname-ban.png / takaichi.png
```

`consumption-tax-cut` `fukushuto` `koshitsu-tenpakai` はテーマの hero 画像を
OGP に流用しているため、そちらも合わせて確認する。

**このタスクでは修正しない。** 問題があれば課題32に追記する。

---

### 制約（必ず守る）

- 保護タグを壊さない: GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP meta
- ブランチ: `task/ogp-header-replace`。main 直接コミット禁止
- `og:image` の URL・パスを変更しない
- `docs/index.html` を `build_site_portal.py` で生成しない

---

### 完了条件

- [ ] `docs/ogp/default.png` が新画像に差し替わり、1200×630・1MB以下
- [ ] `docs/images/site/x-header.png` に1500×500の原本が保存されている
- [ ] `verify_top_page.py` にOGP検査が入り、負のテストで NG / exit 1 を確認済み
- [ ] `verify_top_page.py` / `verify_theme_page.py` が exit 0
- [ ] テーマ別OGP9枚＋hero流用3枚の点検結果が報告されている

---

### 完了報告に必ず含めること

1. `git diff --stat`
2. 新OGP画像の寸法・圧縮前後のファイルサイズ
3. Step 1 のチェックリスト結果（特に「数字が無いこと」の確認方法）
4. `verify_top_page.py` の出力
5. OGP検査の**負のテスト結果**
6. テーマ別OGP12枚の点検結果一覧（問題の有無）
7. 判断に迷った点

---

## 【人手作業】マージ後にやること

Codexの作業完了後、**あなたが手動で行う**。

### 1. Xヘッダー画像のアップロード

X → プロフィールを編集 → ヘッダー画像を差し替え

- 左下300×300（プロフィール画像の重なり）とその下100pxに文字が隠れないか、
  PC・モバイル両方で確認する

### 2. OGPキャッシュの更新

画像を差し替えても、X側のキャッシュが残ると古い画像が表示され続ける。

1. https://cards-dev.twitter.com/validator
2. `https://issue-stance-lab.github.io/sns-reaction-map/` を入力
3. 新しい画像が表示されることを確認

Facebook は https://developers.facebook.com/tools/debug/ で同様に更新できる。

### 3. 固定ポストの再確認

8/2に差し替えた固定ポストのカード画像が、新しいものに変わっているか確認する。
変わっていなければ、**固定ポストを一度削除して投稿し直す**（キャッシュ更新後）。

### 4. 記録

- `TASK_BOARD.md` 課題32 を完了に更新
- `content/x/posts.md` にヘッダー差し替えを記録
