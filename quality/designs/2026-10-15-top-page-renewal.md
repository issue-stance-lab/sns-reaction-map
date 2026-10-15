# トップページのリニューアル（2026-10-15）

全10テーマのページを「検索した疑問→制度の答え→SNSの意見」の型にそろえたあと、トップページを同じ考え方で作り直した。検索の根拠は UIデザイン調査フォルダー `61_トップページ_検索根拠_2026-10-15`。

## 検索の根拠から決めたこと

1. **サイトの考え方そのものへの検索需要は無い。** ラッコキーワードで「SNS 反応」（個人の悩み）「みんなの意見」（Yahoo!の機能名）「世論 まとめ」（3件）。唯一近いのは「意見が分かれる 社会問題／最近のニュース」で、これも小さい。→ トップは検索の受け皿ではなく、**来た人を、その人が検索した疑問のテーマへ最短で送る**ページにする。
2. **トップに来るのは直接入力・X・ChatGPT経由**（GA4 90日: 直接56・X 49・AI 5・検索4セッション）。検索から来た人はテーマページに直接着地する（Search Console: トップ7表示、憲法25表示）。
3. **テーマごとの入口の疑問は、各ページの冒頭見出し**（フォルダー25・52・57で検索語から決めたもの）。トップはそれを10本並べ、1行の答えと「いまの段階」を添える。
4. **並び順は検索需要**（Trends直近週・プランナー・節目）: 消費税 → 免許返納 → 憲法 → 皇室（10/24施行）→ 副首都（10/30施行予定）→ 生成AI → 辺野古 → 部活動 → 自転車 → あだ名。
5. **疑問の言葉で絞り込める**（いつから・何歳から・どこ・メリット・デメリット・財源・子ども・学校）。検索語の型（フォルダー25の横断結果）そのまま。

## 画面の構成（上から）

| 区画 | 中身 | 375pxの高さ（目安） |
|---|---|---|
| 冒頭 | 見出し「いま意見が分かれている話題を、検索した疑問から読む。」、世論調査ではない注記、「疑問から選ぶ」ボタン。PCだけ論点整理のイメージ（canvas） | 約500px |
| 数字4枚 | 収集した投稿・分析対象の意見・公開中のテーマ・データの集め方 | 約200px |
| **その疑問、どのテーマ？** | 絞り込み欄＋言葉のチップ6個、テーマ10枚（分類・疑問・1行の答え・いまの段階・よく一緒に検索される言葉（PCのみ）） | 約2,300px |
| 最近データを更新したテーマ | 更新バー、注目1枚、続けて更新した4テーマ（スマホは横スクロール） | 約1,100px |
| 話題のテーマ | 画像つき10枚（スマホ2列）。`refresh_featured_slots.py` が画像・分類の正典として読む | 約1,000px |
| 折りたたみ | 10テーマの論点アトラス／このサイトの作り方と読み方（4ステップ＋読み方） | 閉じて約110px |
| 注記・フッター | 変更なし | 約500px |

計測（Playwright、ネットワーク遮断）: 375pxで **9,840px → 5,677px**、可視文字 2,363 → 2,678字（疑問10本と答えのぶん増。説明文は折りたたみへ）。1280pxで 7,325px → 4,080px。横はみ出しなし、コンソールエラー0。絞り込み「いつから」で消費税・部活動・自転車、「何歳から」で免許返納・自転車、該当なしの文言、「すべて表示」を確認。

## 仕組み

- **手書き文言は `configs/top-page.json`**（見出し・疑問・1行の答え・並び順・画像とカテゴリの登録・折りたたみの本文・フッター）。件数・更新日・注目枠は書かない。
- **生成は `scripts/build_top_page.py`**。THEMES.yaml・公開データcatalog（`sync_portal_stats.compute_stats`）、注目枠（`select_featured_themes`、`refresh_featured_slots` の描画関数）、各テーマの `configs/{テーマ}-opening.json` の日付（「いまの段階」）から `docs/index.html` を書く。`--check` で再生成と一致するかを見る。
- **「いまの段階」は日付で切り替わる**: 皇室（10/24施行）・副首都（10/30施行予定）は施行日を過ぎると「施行後の条文は未確認」に変わり、`enforcement_confirmed_on` を入れると「施行済み」になる。消費税は `enacted_on` が入ると「成立」に、辺野古は `report.published_on` で「公表」に、部活動は改革実行期間の年数で変わる。テーマ側の設定だけ直せばトップも追随する（再生成は必要）。
- **既存の更新経路との互換**: `sync_portal_stats.py` と `refresh_featured_slots.py` を生成後に流しても差分0（`tests/test_top_page_build.py` が検査）。`verify_top_page.py` の目印（id・class・「○件」のid・日付・%禁止・ナビのリンク先）はそのまま。
- **問いの文言の正典を直した**: 10テーマの冒頭から `<p class="question-line">` が無くなっており、`refresh_featured_slots.py` は main でも止まっていた（`question-line が見つかりません`）。無いときは `configs/top-page.json` の entries の疑問文を使うようにした。
- **見た目は `docs/top-page.css`** に分離（これまではHTML内のstyle）。`home-story.css` は折りたたみの中の4ステップとフッターの背景で引き続き使う。スクロール連動の視差は外した。
- **課題82（テーマカードのラベルの食い違い）**は、ラベルを設定の1か所（`format_label`）にしたことで解消。

## 検査

- `python3 scripts/build_top_page.py --check` OK
- `python3 scripts/verify_top_page.py --allow-overdue-collect` NG 0
- `python3 scripts/sync_portal_stats.py --dry-run` / `refresh_featured_slots.py --dry-run` 変更なし
- `python3 -m unittest tests.test_top_page_build tests.test_portal_stats tests.test_portal_overwrite_safety tests.test_brand_assets tests.test_reaction_map_design tests.test_domain_migration` OK
- `review_with_yomiyasu.py --medium website --strict docs/index.html` 判定OK（絵文字の見出しと「GROWTH.yaml」の語を外した）
- `verify_ai_tone.py` 問題なし

## 未確認・残っていること

- title と meta description を変えた（指名検索の受け皿のまま、「意見が分かれる社会の話題」「検索した疑問」を入れた）。検索結果の表示が変わるまで数日〜数週間。
- 本番ホストでの GA4・AdSense の発火、X埋め込みなし、実機（iPhone）の表示は未確認。
- 計測の基準値（リニューアル前90日）: GA4 トップのセッション 直接56・X 49・AI 5・検索4、Search Console トップ表示7・クリック2。公開後30日でトップ→テーマページの遷移を比べる。
