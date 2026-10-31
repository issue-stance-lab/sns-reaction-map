# 課題51: サイト内記事セクションを新設する（検索流入用）


**状態**: 進行中。2026-10-31の公開点検で3テーマ15記事と一覧の公開を確認。公開日・計測条件の整理と公開後の観測を進める。
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

## 2026-10-17 公開先の設計と試作（ブランチ `task/articles-bukatsu`）

**きっかけ**: オーナーから「流入が進まない。停滞を打破する方策を」と相談。28日間の検索表示がサイト全体で99回・クリック3回、
公開URLはテーマ10本＋固定6本だけで、テーマ1本に2.5万〜5万字を詰めていた。検索は「1つの疑問に1ページ」を評価するため、
疑問ごとの記事を足す方針をオーナーが選んだ。題材はラッコキーワードの調査（`content/website/research/rakko-keyword-suggest-2026-10-16.md`）
で部活動に出ていた「費用・親の負担」「問題点・進まない」「反対・賛成」「市区町村名」から選んだ。

**決めたこと（上の「決めること」1〜6への答え）**:
1. URL: `docs/articles/{slug}.html`、一覧は `docs/articles/index.html`
2. テンプレート: 生成器 `scripts/build_articles.py` に内蔵（固定ページと同じ `site-tokens.css`、保護タグはそのまま）
3. 導線: サイトマップには生成器の一覧から自動で載る（`generate_seo_assets.py` / `validate_theme_seo.py` が同じ関数を使う）。
   トップ（「疑問ごとの解説記事」、テーマごとにまとめる）とテーマページ（「記事で詳しく読む」。部活動・免許返納・青切符）から張る。テーマページの欄は `build_articles.theme_entry_band` を各テーマの生成器が呼ぶ。並びは原稿の `order`、生成は `build_top_page.py`・`build_bukatsu_redesign_v2.py` が `build_articles.entry_articles` を読む。課題98の計測中だがオーナー判断で入れた（`quality/reviews/2026-10-17-title-description-change-during-measurement.md`）
4. 記事→テーマページ: 末尾にテーマページ（投票あり）への案内を自動で付ける。クリックは GA4 イベント `article_link_click`
5. 生成: 原稿 `content/articles/{テーマ}/{slug}.md` → `python3 scripts/build_articles.py`。SNSの件数は `{{issue:論点:立場}}` で
   公開データから差し込み、件数の大小を言い切った文は `asserts` で守る（更新で入れ替わると生成が止まる）。CIに `--check` を追加
6. 検査: `verify_page_originality.py` に記事を追加（テーマページ・記事どうしの使い回しを止める）、`verify_ai_tone.py` の下書き対象に
   `content/articles/` を追加、原稿は `review_with_yomiyasu.py --medium seo --strict`、生成後は `--medium website --strict`

**残り**:
- オーナー確認のうえ公開（release スキル）
- 免許返納・自転車の青切符の記事各5本（2026-10-17）。ほかのテーマは build_articles の STANCE_ROLES と test の対象テーマを足してから
- 公開後4週間で、記事の Search Console 表示回数・クリックと、`article_link_click` を確認する


## 2026-10-31 全体点検で公開状態を訂正

索引と冒頭の状態が実際の公開状態に追いついていなかったため訂正した。上の「残り」は10/17時点の記録として残す。

- 公開記事は、部活動5本・自転車5本・高齢者免許5本の計15本。`https://sns-reaction-map.jp/articles/index.html`とサイトマップで確認し、15本と一覧すべてHTTP 200。
- 10/4〜10/30を指定したSearch Consoleのサイト全体は138表示・9クリック。記事では`bike-blue-ticket-unfair.html`が5表示3クリック、`kobe-katsu.html`が33表示3クリック。少数なので、施策の成否や他記事の不振を断定しない。
- 同期間のGA4で`article_link_click`は18回・1人。このイベントには記事への入口なども混在するため、記事→テーマの遷移数とは読めない。`link_type`などで種類を分け、運営者アクセスの除外状態も確認する。
- 375×812pxの部活動賛否記事では、テーマ・投票への主要案内はページ上端から約8,813px。冒頭の短い回答後や該当する理由の直後に、論点へ進む案内を置く改善候補がある。実装はしていない。

次は、記事ごとの実際の公開日を履歴から確かめ、観測日と指標をそろえる。過去の未公開という記載だけを根拠に再公開や作り直しをしない。

証拠: `/Volumes/M2-WorkSpace/Projects/副業/UIデザイン調査/2026-10-31_SNS反応まっぷ_全体点検/evidence/`の`gsc-28d-pages.json`、`ga4-28d-extra.json`、`sitemap-page-audit.json`、`browser-audit.json`。


## 2026-10-31 公開日と次回観測を確定

10/17の[公開時の変更記録](../quality/reviews/2026-10-17-title-description-change-during-measurement.md)で、部活動・免許返納・自転車の記事各5本、計15本が同日公開されたと確認した。次は11/17に10/18〜11/14の28日分の確定データと記事からテーマへの遷移を確認する。テーマ本体の8ページには未登録が出たが、記事の登録状態は今回未検査であり、全記事未登録とは扱わない。今回の検索観測は[10/31判定記録](../quality/reviews/2026-10-31-search-campaign-review.md)。
