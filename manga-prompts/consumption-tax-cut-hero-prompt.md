# 消費税減税 — ヒーロー画像生成プロンプト

共通スタイル: `manga-prompts/hero-style-guide.md` の **8.5 抽象俯瞰ヒーロー画像テンプレ**（構図パターンD）を使用する。

このテーマは政党・政治家への評価が意見の43.6%を占めるため、具体的な人物・政党記号を描くと偏って見える。
抽象俯瞰型で「税率・買い物・財源」の関係だけを示す。

保存先:

```
docs/images/consumption-tax-cut-hero.webp
```

生成後:

```bash
cwebp -q 78 -resize 1400 0 input.png -o docs/images/consumption-tax-cut-hero.webp
```

---

## ヒーロー画像プロンプト

```text
An abstract aerial view of a household grocery scene reorganized as a civic policy diagram: a shopping basket holding simple everyday food items, a long paper receipt unrolling across the surface and turning into a line chart, small price tags where one group of tags is marked with a lowered rate and another group stays unchanged, and a dividing line separating food items from non-food items. A pair of balanced scales floats subtly above, with light coins on one side and small abstract icons of pensions and medical care on the other. The scene should suggest the debate around Japan's consumption tax cut: whether to limit the cut to food or apply it across the board, where the lost revenue comes from, and whether household prices actually fall, without depicting any real politicians, parties, or retailers.

Leave gentle negative space on the left side for HTML title and lead text overlay. Place the main abstract motif on the right or center-right. Use white, pale blue, and soft indigo as the base, with warm amber as the dominant accent and very subtle green and red touches to hint at divided opinion. Illustration style: soft watercolor-meets-digital art, muted pastel palette with one dominant accent color, gentle grain texture overlay, minimal detail, dreamy and editorial feel like a Japanese magazine cover. No text, no numbers, no percent signs, no people's faces, no real banknotes or portraits on money, no store brand logos, no politicians, no party logos, no government emblems, no real SNS logos, no watermark. 16:9 aspect ratio, 1792x1024px.
```

### 差し替え候補（構図が弱い場合）

主モチーフをレシートではなく「税率のダイヤル」にする案:

```text
An abstract aerial view of a large circular tax-rate dial resting on a civic document table, its pointer sitting between marks, with a shopping basket of simple food items on one side and household bills, ledgers, and small pension and medical-care icons on the other, connected by soft flowing lines. A dividing line runs through the composition, separating food items from everything else. The scene should suggest the debate over how far to cut Japan's consumption tax and who pays for it, without depicting any real politicians, parties, or retailers.

Leave gentle negative space on the left side for HTML title and lead text overlay. Place the main abstract motif on the right or center-right. Use white, pale blue, and soft indigo as the base, with warm amber as the dominant accent. Illustration style: soft watercolor-meets-digital art, muted pastel palette with one dominant accent color, gentle grain texture overlay, minimal detail, dreamy and editorial feel like a Japanese magazine cover. No text, no numbers, no percent signs, no people's faces, no real banknotes, no store brand logos, no politicians, no party logos, no government emblems, no watermark. 16:9 aspect ratio, 1792x1024px.
```

---

## OGP派生プロンプト

```text
An abstract editorial OGP image about Japan's consumption tax cut debate, based on the same hero visual: a shopping basket of simple food items, an unrolling receipt that becomes a line chart, price tags split between a lowered group and an unchanged group, and balanced scales weighing light coins against small pension and medical-care icons. The image should evoke multiple overlapping issues: limiting the cut to food versus an across-the-board cut, the funding source, and whether prices actually fall. Leave clean space for short Japanese title text to be added later.

White, pale blue, and soft indigo base with warm amber as the dominant accent. Illustration style: soft watercolor-meets-digital art, muted pastel palette, gentle grain texture overlay, minimal detail, dreamy and editorial feel like a Japanese magazine cover. No text baked into the image, no numbers, no people's faces, no real banknotes, no store brand logos, no politicians, no party logos, no government emblems, no watermark. 1200x630px.
```

---

## 生成後の反映手順

**2026-07-28 実施済み**。上段のプロンプト（レシート版）で生成した画像を採用した。

1. WebP変換して `docs/images/consumption-tax-cut-hero.webp` に保存する
   （1672×941 PNG 2.3MB → 1400px幅 WebP 65KB）
2. `scripts/build_consumption_tax_page.py` の `HERO_IMAGE` を画像パスに変更する
3. `python3 scripts/build_consumption_tax_page.py` を再実行する
4. `THEMES.yaml` の `manga_img` を更新する

`OGP_IMAGE` もこのヒーロー画像を指すようにした（他テーマと同じ扱い）。

> **注意**: `docs/topic-modern.css` の `.hero::before` は `--topic-hero-image` が未指定だと
> `images/ai-copyright-hero.webp` にフォールバックする。必ず body の inline style で指定すること。

---

## 品質チェック

- 消費税・買い物・税率の話だと一目で分かる
- 左側にタイトルとリード文を重ねる余白がある（ページ側は画像を右47%に配置し、左へフェードさせる）
- 数字・パーセント記号が焼き込まれていない（税率が変わると画像が陳腐化するため）
- 実在の紙幣・硬貨の肖像、店舗ロゴ、政党記号が入っていない
- 賛成側・反対側のどちらかに肩入れして見えない
- 暗すぎず、白文字が乗る前提で明度が保たれている
- スマホでトリミングされても買い物カゴまたはダイヤルが残る
