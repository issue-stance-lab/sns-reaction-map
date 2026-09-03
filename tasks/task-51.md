# 課題51: サイト内記事セクションを新設する（検索流入用）


**状態**: 未着手。`writer-seo` エージェントは作成済みだが、公開先が無いため下書きのみで待機中
**発端**: 2026-08-27、編集部にライター3名（`.claude/agents/`）を採用した際、`writer-seo` の
担当媒体「サイト内SEO記事」が**実在しない**ことが分かった。`docs/` にあるのは11本のテーマページと
法務ページだけで、`sitemap.xml` にも記事は0本。

**なぜやるか**: 90日目標に月3,000ページ表示がある（`company/GOALS.yaml`）。テーマページは
1テーマ1本しか作れず、検索語の幅を取れない。「〇〇 賛否」「〇〇 どっちが正しい」で流入する
読者向けの記事があれば、既存の投票ページへ送れる。

**決めること**:
1. URL設計（`docs/articles/{slug}.html` か、テーマ配下か）
2. HTMLテンプレート（テーマページの `topic-modern.css` を流用するか、専用にするか）
3. `index.html` からの導線と `sitemap.xml` への登録
4. 記事から投票ページへの導線の形
5. 記事の生成方法。**手書きHTMLを `docs/` へ直接置かない**
   （`verify_builder_rebuildability.py` が落ちる。課題47と同じ事故）
6. 記事に対する `verify_page_originality.py` / `verify_ai_tone.py` の掛け方

**完了条件**: 記事1本が公開され、上記6つの検査・導線がすべて通ること。
**関係する文書**: `WRITING_VOICE.md` / `.claude/agents/writer-seo.md` / `company/GOALS.yaml`
