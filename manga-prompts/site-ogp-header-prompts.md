# サイトOGP画像・Xヘッダー画像 生成プロンプト

対応課題: `TASK_BOARD.md` 課題32
作成: 2026-08-02

---

## 差し替えの背景

現行の `docs/ogp/default.png`（2026-06-27作成）には、サイトから削除済みの要素が残っている。

| 現在入っているもの | 状態 |
|---|---|
| 「その話題、SNSでは実はどっちが多い？」 | S2でトップから削除した旧コピー |
| 賛成42% / 保留18% / 中立20% / 反対20% | **根拠のないダミー値** |
| 「トレンド上昇中」「12.5K」「話題沸騰中」 | 実データではない演出値 |

X固定ポストの本文が「世論調査ではありません」と明記しているのに、
同じ投稿のOGPカードが円グラフで割合を出しているため、**投稿内で矛盾している**。

---

## 絶対に入れてはいけない要素

**新しい画像でも、以下は1つも入れないこと。** 課題32の再発になる。

- ❌ **数値・割合・パーセント**（42%、20% など。実データでも入れない — 画像は更新されないため必ず古くなる）
- ❌ **円グラフ・棒グラフで割合を示す表現**
- ❌ 「どっちが多い」「意見が真っ二つ」「どっち派？」
- ❌ 「トレンド上昇中」「話題沸騰中」「12.5K」などの演出値
- ❌ 「リアルタイム」「世論」「世論調査」

**画像に数字を入れない**のがこの課題の核心。画像はコードから生成されず更新もされないため、
どんな数字も時間とともに嘘になる。

## 入れるべき要素

- ✅ サイト名「SNS反応まっぷ」
- ✅ コピー「**その話題を、数ではなく問いから読む。**」（トップページ h1 と統一）
- ✅ 賛成と反対の「理由」が並んでいることを示す視覚表現（数値なし）
- ✅ 現行サイトの配色（青 `#075ef2` / 橙 `#ff5426` / 緑 `#36b8a3` / 紫 `#9358e8` / 紺 `#071a3d`）

---

## 1. OGP画像（1200×630）

出力先: `docs/ogp/default.png`

### プロンプト（英語・画像生成AI用）

```
A clean, modern Open Graph card illustration for a Japanese civic-discussion website.

Layout: horizontal, 1200x630 pixels.

Left side (about 55% of the width): Japanese text on a white background.
- Large bold headline in Japanese: 「その話題を、数ではなく問いから読む。」
  Use a modern Japanese gothic typeface (Noto Sans JP Bold), dark navy (#071a3d),
  set on three lines, generous line spacing, strong left alignment.
- Below it, smaller subtext in Japanese: 「SNSの公開投稿から、賛成と反対それぞれの理由を整理」
  in muted gray-blue (#61708a).
- Small logo mark in the upper left: six small dots in blue, orange, green, purple
  arranged in a loose circle, crossed by two thin ellipse outlines (like an atom or orbit),
  with the site name 「SNS反応まっぷ」 in bold beside it.

Right side (about 45%): an abstract illustration of two opposing viewpoints in conversation.
- Two rounded speech-bubble shapes facing each other, one in blue (#075ef2),
  one in orange (#ff5426), each containing three short horizontal gray lines
  suggesting written reasons (NOT numbers, NOT charts, NOT percentages).
- Between them, a few small neutral dots in green (#36b8a3) and purple (#9358e8),
  suggesting conditional and undecided positions.
- Thin connecting lines between the bubbles, suggesting dialogue rather than conflict.

Style: flat vector illustration, soft watercolor texture on the background only,
generous white space, calm and trustworthy, editorial rather than promotional.
Light background (#f8faff) with a subtle grid pattern at very low opacity.

ABSOLUTELY NO numbers, percentages, pie charts, bar charts, gauges, or metrics
of any kind anywhere in the image.

Output image: landscape, exactly 1200x630 pixels.
```

### 確認事項

- [ ] 画像内に数字が1つも無いこと
- [ ] 「どっちが多い」等の旧コピーが無いこと
- [ ] 1200×630 であること
- [ ] X・Facebook・LINE のカードで文字が切れないこと（安全域: 中央1000×520）
- [ ] ファイルサイズを1MB以下に圧縮（現行は1.4MB）

---

## 2. Xヘッダー画像（1500×500）

X プロフィール上部のバナー。現行は「その話題、SNSでは実はどっちが多い？」入り。

### プロンプト（英語・画像生成AI用）

```
A wide banner illustration for a Japanese civic-discussion website's social media header.

Layout: very wide horizontal, 1500x500 pixels.

Center-left area: the site name 「SNS反応まっぷ」 in large bold Japanese gothic type
(Noto Sans JP Black), dark navy (#071a3d), with the six-dot orbit logo mark to its left.
Below the name, a single line of smaller Japanese text:
「その話題を、数ではなく問いから読む。」in medium weight, muted gray-blue (#61708a).

Right area: an abstract illustration of two opposing viewpoints.
- Two rounded speech-bubble shapes facing each other, one blue (#075ef2),
  one orange (#ff5426), each containing three short horizontal gray lines
  suggesting written reasons (NOT numbers, NOT charts).
- Scattered small dots in green (#36b8a3) and purple (#9358e8) between them.
- Thin connecting lines suggesting dialogue.

IMPORTANT — safe area: On X, the profile picture overlaps the lower-left corner
(roughly a 300x300 pixel circle) and the bottom edge may be cropped on mobile.
Keep all text and important elements within the central horizontal band,
away from the left 350 pixels and the bottom 100 pixels.

Style: flat vector illustration, light background (#f8faff), soft watercolor texture,
generous negative space, calm and editorial.

ABSOLUTELY NO numbers, percentages, pie charts, bar charts, or metrics anywhere.

Output image: landscape, exactly 1500x500 pixels.
```

### 確認事項

- [ ] 画像内に数字が1つも無いこと
- [ ] 左下300×300（プロフィール画像の重なり）に文字が無いこと
- [ ] 下端100pxに重要要素が無いこと（モバイルで切れる）
- [ ] 1500×500 であること
- [ ] PC・モバイル両方で表示確認

---

## 3. 差し替え後の作業

### ファイルの配置

```
docs/ogp/default.png   ← 新しいOGP画像で上書き
```

Xヘッダーは X の「プロフィールを編集」から直接アップロード（リポジトリには入れない。
参照用に `docs/images/site/` へ置いてもよい）。

### OGPキャッシュの更新

画像を差し替えても、X側のキャッシュが残ると古い画像が表示され続ける。

1. https://cards-dev.twitter.com/validator を開く
2. `https://issue-stance-lab.github.io/sns-reaction-map/` を入力
3. 新しい画像が表示されることを確認

Facebook のキャッシュは https://developers.facebook.com/tools/debug/ で更新できる。

### 記録

- `TASK_BOARD.md` 課題32 を完了に更新
- `THEMES.yaml` には影響しない（サイト共通画像のため）

---

## 4. 余力があれば：テーマ別OGP 9枚の点検

`docs/ogp/` に9枚（2026-07-02作成）。同様のダミー数値が入っていないか確認する。

```
ai-copyright.png / bike-blue-ticket.png / bukatsu-chiiki.png
constitutional-amendment.png / elderly-license-revocation.png
henoko-student-accident.png / school-nickname-ban.png / takaichi.png
```

数字が入っているものがあれば、上記と同じ方針（数値を入れない）で作り直す。
`consumption-tax-cut` `fukushuto` `koshitsu-tenpakai` はテーマのhero画像を
OGPに流用しているため、こちらも合わせて確認する。
