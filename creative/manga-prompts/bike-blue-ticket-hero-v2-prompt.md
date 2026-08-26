# 自転車の青切符：テーマヒーロー v2

## 制作条件

- 用途: テーマページのヒーロー背景
- 制作: OpenAI の画像生成機能（組み込み `imagegen`）
- 画像内文字: なし。見出しと説明は HTML で表示する
- 人物・顔・乗り手・車両・標識・ロゴ: 使用しない
- 共通構図: 中央の未解決の問い＋周囲の4視点

## 初回生成プロンプト

```text
Use case: stylized-concept
Asset type: wide website topic hero background for a Japanese editorial data site
Primary request: Create a refined abstract editorial illustration for the topic of bicycle traffic violation tickets and road safety, using the exact same visual language as a brand built around "one central unresolved question plus four viewpoints."
Scene/backdrop: deep navy #071A3D editorial road-map workspace, spacious and calm, with layered tactile paper lanes, crossing route segments, intersection markings, clipped regulation sheets, and a single blank cobalt-blue ticket-like paper rectangle with a subtle perforated edge. The blue ticket must have no text, symbols, numbers, barcode, seal, or logo.
Subject: one incomplete open white ring at the central junction representing an unresolved question; four clear viewpoint nodes in blue #075EF2, orange #FF5426, green #36B8A3, and purple #9358E8; four short thick rounded routes converge toward the central ring. Abstract route geometry should suggest pedestrian safety, enforcement, road infrastructure, and freedom of movement without literal labels.
Style/medium: premium tactile editorial collage, subtle paper grain, layered cut-paper depth, modern data-journalism art direction, restrained and trustworthy, visually consistent with a sophisticated editorial brand.
Composition/framing: wide landscape; strongest visual cluster in the center-right for desktop cropping; the incomplete white ring, all four colored nodes, and key intersection should remain recognizable when the lower central portion is shown on mobile; generous quiet navy negative space on the left for HTML headline text.
Lighting/mood: thoughtful, investigative, balanced, civic, calm.
Color palette: dominant navy, white, exact four accent colors only; the blank ticket is brand blue, not fluorescent.
Text: none.
Constraints: no people, no faces, no hands, no riders, no characters, no logos, no trademarks, no police insignia, no Japanese road signs, no identifiable place, no letters, no numbers, no watermark. No pie chart or conventional infographic. No realistic crash, injury, vehicle, bicycle, courthouse, gavel, scales of justice, robot, AI brain, glowing cyberpunk effects, or photorealistic street scene. Keep every symbol abstract and non-linguistic.
```

## 修正プロンプト

初回画像に混ざった自転車記号と文字に見える罫線を除去し、それ以外の構図を維持した。

```text
Edit the provided image while preserving its overall composition, colors, lighting, tactile paper-collage style, central incomplete white ring, four colored routes and nodes, blank blue ticket, and left-side negative space.

Make only these corrections:
1. Remove the small bicycle pictogram from the upper curved road strip. Replace that area with plain dark navy tactile road material and non-symbolic lane texture.
2. Remove the ruled lines, punched hole, and paperclip from the cream paper in the upper-right. Replace it with layered blank abstract paper fragments with no marks or office hardware.
3. Ensure the entire image contains no readable or pseudo-readable text, no letters, no numbers, no pictograms, no logos, no icons, no barcodes, and no watermark.
4. Keep the blue ticket completely blank and abstract.
5. Do not add any people, riders, vehicles, bicycles, traffic signs, police insignia, or recognizable place.

Do not otherwise redesign or reposition the main central composition.
```

## 出力

- 生成元: 1536×1024 PNG
- Web用正本: `docs/images/topics/bike-blue-ticket/bike-blue-ticket-hero.webp`
- WebP品質: 86
- 採用状態: オーナー確認済み。旧ヒーローを置き換える正本として採用
