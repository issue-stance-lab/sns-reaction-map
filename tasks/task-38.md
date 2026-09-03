# 課題38: inject_tide_widget.py が公開中のページを古いデータへ巻き戻す

**状態**: 進行中（自転車青切符だけ 2026-08-17 に解消。ai-copyright / takaichi は未対応で、実行すると巻き戻る）
**発見**: 2026-08-08

**概要**: `scripts/inject_tide_widget.py` は引数を取らず、実行すると `THEMES` の全8テーマの HTML を書き換える。ところが `adapter` 方式のテーマは `refresh_topic.py` 経由で更新されており、スクリプト内の `THEMES` に書かれた更新回のほうが**古い**。そのため実行すると、公開中のページが過去のデータへ戻る。

| テーマ | 公開中 | 実行後（巻き戻り先） |
|---|---|---|
| ai-copyright | 7月26日 → 8月3日 | 7月12日 → 7月26日 |
| takaichi | 7月26日 → 8月7日 | 7月12日 → 7月26日 |

**なぜ危険か**: 1テーマの潮目を直すだけのつもりで実行すると、無関係な2テーマが黙って後退する。`git status` を見て戻さない限り、そのままコミットされて公開される。検査は通ってしまう（日付の新しさを見る検査がない）。

**やること**: 次のいずれか。①`--slug` 引数を足して対象テーマだけ書き換えられるようにする ②`adapter` 方式のテーマを `THEMES` から外し、adapter 側に一本化する ③実行前に「`THEMES` の更新回がページの現状より古くないか」を検査して止める。②が筋が良いが、adapter 側が潮目を生成できるか未確認。

**2026-08-17 自転車青切符**: ②を1テーマ分だけ実施。`THEMES` の `bike-blue-ticket` の `prev_file` / `cur_file` を `None` にして、単体実行では飛ばすようにした（`constitutional-amendment` と同じ形）。潮目は `scripts/refresh_adapters/bike.py` が更新回どうしを比較して作る。残るのは ai-copyright / takaichi / 部活動など、まだ固定ファイル名を持つテーマ。

**暫定の回避策**: 実行後に必ず `git status --porcelain` を見て、対象外の `docs/*.html` が出ていたら `git restore` する。この手順は `.claude/skills/taxonomy-migration/SKILL.md` の「落とし穴」に記載済み。
