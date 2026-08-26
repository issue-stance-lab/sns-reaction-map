# 部活動の地域移行：テーマヒーロー v2

## 制作条件

- 用途: テーマページのヒーロー背景
- 制作: OpenAI の画像生成機能（組み込み `imagegen`）
- 画像内文字: なし。見出しと説明は HTML で表示する
- 人物・生徒・教師・学校名・スポーツ用品: 使用しない
- 共通構図: 中央の未解決の問い＋周囲の4視点

## 初回生成プロンプト

```text
Use case: stylized-concept
Asset type: wide website topic hero background for a Japanese editorial data site
Primary request: Create a refined abstract editorial illustration for the topic of moving Japanese school club activities from schools to community organizations, using the site's exact visual language of "one central unresolved question plus four viewpoints."
Scene/backdrop: deep navy #071A3D editorial workspace divided subtly into a structured school-side surface and a varied community-side surface. Use layered tactile paper floor plans, blank schedule fragments, modular venue tiles, folded boundary sheets, and short connecting routes. Show transition and handoff without depicting any real school or town.
Subject: one incomplete open white ring at the central handoff point representing an unresolved question; four clear viewpoint nodes in blue #075EF2, orange #FF5426, green #36B8A3, and purple #9358E8; four short thick rounded routes converge toward the ring. Abstract spatial geometry should suggest teacher workload, children's access to activities, household cost, and regional differences without labels.
Style/medium: premium tactile editorial collage, subtle paper and gym-floor texture, layered cut-paper depth, modern data-journalism art direction, calm and trustworthy, consistent with the previously established navy four-color brand.
Composition/framing: wide landscape; strongest visual cluster in the center-right for desktop cropping; central incomplete white ring and all four viewpoint nodes remain recognizable when the lower central portion is shown on mobile; generous quiet navy negative space on the left for HTML headline text.
Lighting/mood: thoughtful, civic, balanced, practical, quietly optimistic but not promotional.
Color palette: dominant navy, white, exact four accent colors only; no extra school colors.
Text: none.
Constraints: no people, no students, no teachers, no faces, no hands, no silhouettes, no uniforms, no sports team, no mascot, no logos, no trademarks, no school emblem, no school building facade, no readable schedule, no letters, no numbers, no pictograms, no icons, no watermark. No pie chart or conventional infographic. No balls, rackets, bats, trophies, whistles, scoreboards, classroom blackboards, or literal maps of Japan. Keep every symbol abstract and non-linguistic.
```

## 修正プロンプト

初回画像に混ざったブランド外の茶色を除去し、それ以外の構図を維持した。

```text
Edit the provided image while preserving the exact composition, central incomplete white ring, four colored viewpoint nodes and routes, left-side negative space, layered floor-plan collage, lighting, and tactile materials.

Make only these corrections:
1. Remove every tan, beige, brown, wood-colored, and warm neutral paper tile from the right-side community area.
2. Recolor those pieces using only deep navy #071A3D, white, or subdued tints of the exact brand accents #075EF2, #FF5426, #36B8A3, and #9358E8. Keep navy dominant and do not add a fifth accent.
3. Keep the four main viewpoint nodes clearly blue, orange, green, and purple.
4. Ensure there is no readable or pseudo-readable text, no letters, no numbers, no pictograms, no logos, no icons, and no watermark.
5. Do not add people, students, teachers, uniforms, sports equipment, school emblems, buildings, or literal maps.

Do not otherwise redesign, add objects, or reposition the main elements.
```

## 出力

- 生成元: 1672×941 PNG
- Web用正本: `docs/images/topics/bukatsu-chiiki/bukatsu-hero.webp`
- WebP品質: 86
- 採用状態: オーナー確認済み。旧ヒーローを置き換える正本として採用
