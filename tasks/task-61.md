# 課題61: 一次資料メモを「使う」側の運用がない

**状態**: 未着手（2026-09-03 起票）
**優先度**: 中（課題58の前段。ページ実装より先に、社内の書き手が資料を使う状態にする）

## 問題

`quality/research/{テーマ}-primary-sources.md` は10テーマ分そろい、**維持**の仕組み
（`status.yaml` の `last_verified`、管理ダッシュボードの90日検知、
`.claude/skills/primary-research/`）も動いている。しかし**使用**の側が空で、
資料を実際に読ませる導線がない。

- `.claude/agents/writer-note.md` / `writer-seo.md` は「一次資料に当てる」と書いてあるだけで、
  `quality/research/` というパスがどこにも出てこない
- `.claude/agents/writer-x.md`・`.claude/skills/x-daily/SKILL.md`・`.claude/skills/new-topic/SKILL.md`
  は「一次資料」の語すら含まない（`grep -c` で0件）
- `OPERATIONS.md` にあるのは「再確認」の行だけで、「使うとき」の行がない

ファイル名が書かれていない指示は、別セッションのAIには存在しないのと同じ。
実際、記事も投稿も一次資料メモを開かないまま書かれている。

## 段階1: 参照の入口をつくる

1. `.claude/agents/writer-note.md` / `writer-seo.md` / `writer-x.md` に、
   `FACT_CHECK_GUIDE.md` の隣で `quality/research/{テーマ}-primary-sources.md` をパスで名指しする
2. `.claude/skills/x-daily/SKILL.md` に、数字・事実を含む投稿を書く前に該当テーマのメモを読む手順を足す
3. `.claude/skills/new-topic/SKILL.md` に、新テーマ公開時に一次資料メモを1本作り
   `quality/research/status.yaml` に行を足す手順を足す（**いまはメモの無いテーマが増え続ける**）
4. `OPERATIONS.md` に「一次資料メモを使うとき」の行を足す（現状は再確認の行のみ）

**完了条件**: 上の4ファイルすべてに `quality/research/` のパスが書かれており、
新テーマ追加手順に一次資料メモの作成が含まれていること。

## 段階2: 検査にする

「ルールは検査にしないと守られない」（指示文の禁止事項は別セッションで破られる）。
段階1が定着したら、記事・投稿の数字に出典を残す欄を設け、空欄を
`verify_*.py` + `tests/` で落とす。
**段階2の設計は段階1の運用実績を見てから決める。先に作らない。**

## 着手前に知っておくこと（資料側の穴）

- `school-nickname-ban` は `last_verified: null` の**未着手**。使ってよい資料がまだない
- `koshitsu-tenpakai` は改正法（令和8年法律第66号）の本文が未確認。施行は 2026-10-24 頃

この2テーマは段階1の対象に含めてよいが、「メモがある＝裏が取れている」ではないことを
手順書に明記する。

## この課題でやらないこと

テーマページ（`docs/*.html`）への「投稿の主張を一次資料と突き合わせる」セクション実装は
課題58の担当。あちらは読者向け、こちらは社内の書き手向け。混ぜない。
