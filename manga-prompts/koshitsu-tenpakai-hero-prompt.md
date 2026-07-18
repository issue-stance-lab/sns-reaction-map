# 皇室典範改正 — ヒーロー画像生成プロンプト

共通スタイル: `manga-prompts/hero-style-guide.md` の **7. ヒーロー画像テンプレ** を使用する。

保存先:

```
docs/images/koshitsu-hero.webp
```

生成後:

```bash
cwebp -q 78 -resize 1400 0 input.png -o docs/images/koshitsu-hero.webp
```

---

## ヒーロー画像プロンプト

```text
An abstract aerial view of an imperial succession diagram unfolding across a quiet civic document table, with branching family-tree lines, empty circular lineage markers, a soft adoption arrow connecting a distant branch to the main line, and balanced scales of law floating subtly above the composition. The scene should suggest the debate around Japan's Imperial House Law revision: preserving imperial family membership after marriage, adoption from former imperial branches, and male-line versus female-line succession, but without depicting any real royal family members or politicians.

Leave gentle negative space on the left side for HTML title and lead text overlay. Place the main abstract motif on the right or center-right. Use warm neutral tones with pale blue, soft indigo, muted violet, and a very subtle deep red accent. Illustration style: soft watercolor-meets-digital art, muted pastel palette with one dominant accent color, gentle grain texture overlay, minimal detail, dreamy and editorial feel like a Japanese magazine cover. No text, no people's faces, no official imperial crest, no party logos, no government emblems, no real SNS logos, no nationalist symbols, no watermark. 16:9 aspect ratio, 1792x1024px.
```

---

## OGP派生プロンプト

```text
An abstract editorial OGP image about Japan's Imperial House Law revision, based on the same hero visual: branching family-tree lines, empty circular lineage markers, a soft adoption arrow from a distant branch, and balanced scales of law hovering over a civic document table. The image should evoke multiple overlapping issues: imperial family membership after marriage, adoption from former imperial branches, and male-line versus female-line succession. Leave clean space for short Japanese title text to be added later.

Warm neutral tones with pale blue, soft indigo, muted violet, and a subtle deep red accent. Illustration style: soft watercolor-meets-digital art, muted pastel palette, gentle grain texture overlay, minimal detail, dreamy and editorial feel like a Japanese magazine cover. No text baked into the image, no people's faces, no real royal family likeness, no official imperial crest, no politicians, no party logos, no government emblems, no watermark. 1200x630px.
```
