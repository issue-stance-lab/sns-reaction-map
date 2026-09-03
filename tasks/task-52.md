# 課題52: 既存11ページのAI臭をリライトで落とす


**状態**: 未着手。検査（`scripts/verify_ai_tone.py`）と baseline は 2026-08-27 に設置済み
**発端**: 公開11ページの本文1,007文を実測したところ、「いかがでしたか」の類の安っぽい定型は
**0件**だった一方、**賛否を同じ構文で並べる鏡像**が見つかった。これが読者に「AIが書いた」と
感じさせる最大の要因。

> 推進側の最も強い根拠は、〜ことです。慎重側の最も強い根拠は、〜ことです。

**baseline に登録した既存分**（`configs/ai-tone.json`。ここを0へ減らすのがこの課題）:

| テーマ | 検出 | 件数 |
|---|---|---|
| ai-copyright | 側の最も強い根拠は | 2 |
| bukatsu-chiiki | 側の最も強い根拠は / というのが◯◯側の強い主張 | 各2 |
| elderly-license-revocation | 側の最も強い根拠は / というのが◯◯側の強い主張 | 各2 |
| bike-blue-ticket | というのが◯◯側の強い主張 | 2 |
| school-nickname-ban | ではなく（密度 6.7/100文、上限5.0） | 4 |

**難しさ**: 本文は `scripts/refresh_adapters/*.py` と `configs/prompts/` の発注書から生成される。
ページのHTMLを直接直すと次のデータ更新で戻る。**発注書と adapter 側を直す必要がある**。

**手順の骨子**:
1. 該当テーマの発注書に `WRITING_VOICE.md`「1. 対称にしない」を組み込む
2. 賛否のどちらかを別の入り口（具体的な場面、数字、未解決点）から書き直す
3. `python3 scripts/verify_ai_tone.py` で baseline を下回ることを確認し、`configs/ai-tone.json` の
   baseline を実測値まで下げる（**下げ忘れると次の劣化を検知できない**）
4. `verify_page_originality.py` と `verify_theme_page.py` を通す

**注意**: X の投稿済み台帳（`content/x/posts.md`）に「〜ではないでしょうか」が4件ある。
過去の投稿は取り消せないため検査対象外にしたが、同じ癖が続いていたことは記録に残す
（`x-daily/references/writing.md`「テーマ全体の感想を求めない」に反する）。今後は
`writer-x` と下書き段階の検査で止める。
