# note 記事執筆セッション 指示文

## このセッションがやること

「SNS反応まっぷ」の note 記事を書く。
まず `Skill("note-operation")` を読んでから作業を始めること。

---

## 確定済みの方針（変更不要）

- 目的: SEO被リンク獲得
- 形式: テーマごとに個別記事（型A）を1本ずつ
- 更新: 同じ記事を「新論点が出たとき」だけ更新
- 下書き渡し: **Artifact（HTML）で出力**。オーナーが確認後コピペ投稿
- 画像: Claude がブラウザでスクショ → `note-drafts/images/<theme>_map.png` に保存

---

## 今回書く記事

### AI著作権（優先度1位）

| 項目 | 内容 |
|---|---|
| タイトル | 「生成AIと著作権、SNS投稿708件を分析したら見えてきた6つの論点」 |
| UTM キャンペーン | `note_ai_copyright_20260821` |
| テーマページ URL | `https://issue-stance-lab.github.io/sns-reaction-map/ai-copyright-reaction-map.html?utm_source=note&utm_medium=referral&utm_campaign=note_ai_copyright_20260821` |

**使うデータ（確認済み・変更不要）：**
- 有効分類: 708件 / 収集元: Yahooリアルタイム検索 / 基準日: 2026-06-27
- 6論点の件数:
  - 学習データ・無断利用: 126件（18%）
  - 法制度の整備: 79件（11%）
  - 利用者モラル: 73件（10%）
  - クリエイター保護: 46件（6%）
  - 技術競争・産業振興: 40件（6%）
  - AI生成物の権利: 31件（4%）
  - その他・分類困難: 274件（39%）

---

## 作業手順

1. `Skill("note-operation")` を読む
2. ブラウザでテーマページを開き、スタンスマップのスクリーンショットを撮る
   - URL: `https://issue-stance-lab.github.io/sns-reaction-map/ai-copyright-reaction-map.html`
   - 保存先: `note-drafts/images/ai-copyright_map.png`
3. 記事本文を書く（SKILL.md 型A の構成に従う）
4. **Artifact（HTML）で出力する**（オーナーが見やすい形で）
5. 出力後、オーナーに「この内容で問題なければ note にコピペして投稿してください」と伝える
6. 投稿完了の連絡を受けたら `note-posts.md` に記録する

---

## 次に書く記事（今回は不要。参考まで）

| 順 | テーマ | 理由 |
|---|---|---|
| 2 | 高齢者免許返納 | GSCで「免許返納 義務化」クリックあり |
| 3 | 消費税減税 | UTM流入が1件あり。新規に1本書く |
| 4〜 | 残り8テーマ | 週1本ペースで追加 |

---

## 参照ファイル

- `note-posts.md` — 投稿履歴・計測記録
- `.claude/skills/note-operation/SKILL.md` — 執筆ルール正典
- `THEMES.yaml` — テーマ一覧と件数
