# TASK_BOARD — SNS反応まっぷ（テーマ横断課題のみ）

最終更新: 2026-08-08（課題38を追加）

> **テーマ個別の工程状態は `THEMES.yaml` を参照してください。**
> 完了済み課題は `archive/TASK_BOARD_ARCHIVE.md` に移動しました。

---

## 運用ルール

- ハブAI（Claude Code）は毎セッション LOOP.md に従って動く
- ワーカーAIは `configs/prompts/` のプロンプトに従って作業する
- ブランチ運用: `task/{theme}-{工程}` 形式。main直接コミット禁止
- 保護タグ: GA4(`G-K10S4YCZFH`) / AdSense(`ca-pub-2542211932832864`) / Supabase / OGP

---

## アクティブ課題（テーマ横断）

### 課題13: 新規トピック継続追加
**状態**: 未着手（LOOP.md ②の優先順位5に該当）
**概要**: 2日に1本ペースで新テーマ追加。賛否が出やすいテーマ。戦争関連除外
**手順**: AI_HANDOFF.md §9 参照

### 課題15: AdSense審査対応 & 広告配置設計
**状態**: 2026-08-01 に再審査をリクエスト（審査中）。前回は不承認（2026-07-07、理由: 有用性の低いコンテンツ）
**概要**: 審査結果追跡、通過後の広告ユニット配置設計、プロジェクトアドレスへの管理権限移行
**2026-07-07 対応済み**: 全8テーマページに「この争点の背景」解説セクション追加（configs/*.json の `background` フィールド＋build_reaction_map.py 対応済みのため再ビルドでも保持される）、docs/about.html（運営者情報）新設、全フッターにリンク追加、sitemap更新
**2026-07-30 対応済み**: 問い合わせ窓口をGoogleフォームで開設（メールアドレス非公開・ログイン不要）、about.html の訂正窓口セクションと disclaimer.html の削除依頼導線をフォームにリンク。個別返信は原則行わない旨と、事実誤認の指摘・削除依頼には対応する旨を明記
**2026-08-01 判明した本質的な問題**: AdSenseに登録されているサイトは `issue-stance-lab.github.io`（**ルートのサブドメイン全体**）であり、`/sns-reaction-map/` ではない。7/7以降の対策（背景解説・about・問い合わせ窓口）はすべて `/sns-reaction-map/` 配下で、**審査員が最初に見るルートページは見出し1つ＋リンク1本の947バイトのスタブのままだった**。「有用性の低いコンテンツ」はこれを指していた可能性が高い。所有権確認は完了済み（管理画面で緑チェック）。
**2026-08-01 対応済み**: 別リポジトリ `issue-stance-lab/issue-stance-lab.github.io` の `index.html` を実体のあるトップページに差し替え（プロジェクトの目的、収集→分類→編集の3ステップ、公開中11テーマへのリンク、編集方針5項目、運営者情報と問い合わせフォーム、privacy/disclaimer/usage へのフッターリンク、数字の前にサンプルであり世論調査ではない旨の注意書き）。同リポジトリのルートに `ads.txt` を追加（`docs/ads.txt` と同一内容。従来は `/sns-reaction-map/ads.txt` にしか無く、ルートは404で管理画面のads.txtステータスが「不明」だった）。commit `aa4d05e`
**注意**: ルートページには件数を載せていない。別リポジトリで二重管理すると課題29と同じ数字の食い違いが再発するため、件数と取得期間は各テーマページ側に一本化する方針
**2026-08-01 申請済み**: 管理画面から再審査をリクエスト。お支払いプロフィールは登録済み（住所確認PINは累計$10、支払い方法登録は$100到達後のため現時点では操作不可）
**残作業**: ①審査結果を待つ（数日〜2週間程度）。結果が出たら本欄に記録 ②通過した場合は広告ユニットの配置設計（本課題の後半スコープ）③再度不承認の場合は独自ドメイン移行を優先（github.ioサブドメインは審査上不利）④今後 `/sns-reaction-map/` 側だけを改善しても審査対象のルート（別リポジトリ `issue-stance-lab/issue-stance-lab.github.io`）には反映されない。テーマ追加時はルートの一覧にも追記すること

### 課題17: Googleアカウント・サービスのプロジェクトアドレス統一
**状態**: 未着手
**概要**: AdSense・GitHub Orgの管理権限をプロジェクトアドレスへ移行

### 課題18: サイトデザイン・体験の全面改善
**状態**: 大部分が課題26で実現済み。残りは配色・フォント統一とXブランドトーン統一
**スコープ**: デザインガイドライン策定、全体配色統一、モバイルファースト確認

### 課題19: パイプラインでのステータス自動更新
**状態**: 未着手
**概要**: run_pipeline.py の各Step完了時に site-cases.json の status を自動更新

### 課題27: GitHubトークンを期限付きで作り直す
**状態**: 未着手
**概要**: 現在のGitHubトークン（名前: claude-code）が無期限のためセキュリティリスクあり。90日など期限付きで作り直す
**手順**: https://github.com/settings/tokens で現トークン削除 → 新規作成（repo・workflow・read:orgスコープ、90日期限）→ `gh auth logout` → `gh auth login` でトークン更新

### 課題28: sample_period の unknown を埋める
**状態**: 未着手（`WORK_PLAN_2026-08.md` A-4 で回収）
**概要**: S1 で THEMES.yaml に `sample_period`（収集期間）を追加したが、6テーマが `unknown` のまま。A-4「調査条件の表示」で各テーマの数字の近くに取得期間を出すため、それまでに埋める必要がある
**対象（6件）**: bike-blue-ticket / bukatsu-chiiki / constitutional-amendment / elderly-license-revocation / school-nickname-ban / henoko-student-accident
**手順**: 各テーマの `sample_file` のレコード内タイムスタンプ、または収集時の作業ログ・git log・`social-samples/*.md` から期間を特定する。**特定できない場合は推測で埋めず `unknown` のまま残し、ページ側で「取得期間: 記録なし」と正直に表示する**
**2026-08-02 対応済み（3件）**: `sample_file` の `fetched_at` が全件そろっている constitutional-amendment（2026-06-20〜2026-07-25）/ school-nickname-ban（2026-06-22〜2026-07-12）/ henoko-student-accident（2026-06-14〜2026-06-27）を確定し、ページの「取得期間: 記録なし」も書き換えた。bukatsu-chiiki はパイロットで確定済み。
**全11テーマ再検査**: 同じ基準を既に期間が入っていたテーマにも適用した。takaichi（276件中140件欠損）/ fukushuto（255件全件欠損）も `unknown` へ戻し、koshitsu-tenpakai は正典347件が全て7/26収集なので `2026-07-26` に修正した。現在の `unknown` は ai-copyright / bike-blue-ticket / elderly-license-revocation / takaichi / fukushuto の5件。
**機械検査**: `data/verification/sample-periods.json` に総数・日付あり・欠損・最小日・最大日だけを保存し、`scripts/verify_sample_periods.py` で全11テーマを検査する。個別投稿の取得日は公開しない。
**別件（課題29の一例）**: ai-copyright は `sample_period: "2026-06-10〜2026-07-26"` と書いてあったが、`sample_file` の `fetched_at` は最新が 2026-07-12（339件は欠損）。7/26に収集した452件は `sample_file` に入っておらず別ファイルにあるため、根拠のない期間を公開し続けず `unknown`／「記録なし」へ戻した。次回更新で累積を正典へ統合した時点で確定する。

**注意**: `sample_source` は全11テーマ「Yahooリアルタイム検索」で埋まっている。検索語（クエリ）は未記録なので、A-4 で表示するなら `sample_queries` フィールドの追加も併せて検討する

### 課題29: ページ内件数表示と sample_file の突き合わせ
**状態**: **完了（2026-08-08）**。全11テーマの論点件数を正典 `sample_file` から再現できる状態にし、`data/issue-counts/` を削除した
**概要**: S1 で「分類済み投稿数」をトップに出す根拠を `sample_file` の実レコード数に統一したが、THEMES.yaml のコメント記載や各テーマページ内の件数表示と食い違うテーマがある。トップとテーマページで違う数字が出ると、S1 で解消した矛盾が別の場所で再発する
**乖離の例**:

| テーマ | THEMES.yaml コメント | sample_file 実数 |
|---|---|---|
| bukatsu-chiiki | 旧2D 245件 | 467 |
| constitutional-amendment | 552件 | 646 |
| school-nickname-ban | 134件 | 374 |
| henoko-student-accident | 356件 | 363 |
| consumption-tax-cut | classify2d: n-a | 667 |

**手順**: ①各テーマページが表示している件数がどの数字か（2D分類 / Hermes論点分類 / 収集総数）を特定 ②`sample_file` の数と一致するか確認 ③一致しない場合、どちらが「分類済み投稿」の定義に合うかを決めて統一 ④`verify_top_page.py` に「トップの件数と各テーマページの件数が矛盾しない」検査を追加
**備考**: 2D分類と Hermes 論点分類で対象件数が違うのは妥当な可能性が高い。その場合はページ側の表記を「論点分類 ○件」等に変えて、何を数えた数字かを明示する

**2026-08-02（S8）に判明した、①の調査結果**

課題30の件数併記のために全11テーマの論点別件数の出所を洗ったところ、**7テーマは `sample_file` から再現できたが、4テーマは再現できるファイルがリポジトリに残っていなかった**。

| テーマ | 論点別件数の出所 | `sample_file` から再現できるか |
|---|---|---|
| ai-copyright | sample_file（全件） | ✅ 126/79/73/46/40/31 |
| bukatsu-chiiki / consumption-tax-cut / school-nickname-ban / takaichi | sample_file（`is_opinion` のみ） | ✅ |
| fukushuto | sample_file（全件） | ✅ |
| bike-blue-ticket | sample_file（`classification.main_issue`） | ✅ 2026-08-07に解消（下記） |
| **constitutional-amendment** | ページ内 `const P`（422件） | ❌ sample_file は646件（旧422件の分類が残っている） |
| **henoko-student-accident** | `docs/henoko-arena-data.js`（265件） | ❌ sample_file は363件 |
| **koshitsu-tenpakai** | ページ内 `SM_RAW` + JS の `arenaIssueOf()`（268件） | ❌ sample_file は347件。しかも公開中の h3 件数は `koshitsu-tenpakai_hermes_prev_synthetic.json` 由来 |
| **elderly-license-revocation** | sample_file（`classification.main_issue`） | ✅ 2026-08-07に解消（下記） |

**暫定措置**: 上記4テーマ分を `scripts/extract_arena_issue_assignment.py` でページから1度だけ取り出し、`data/issue-counts/{theme}.json` に固定した。件数併記と検査はこのファイルを読む（ページのHTMLは読まないので、spanを手で書き換えれば検査が落ちる）。

**2026-08-07 対応済み（2テーマ）**: elderly-license-revocation（211件）と bike-blue-ticket（181件）を Hermes で再分類し、結果を正典 `sample_file` の各レコードへ `classification`（main_issue / stance / intensity / summary / reason / confidence / article_usable / risk）として格納した。あわせて次を実施。

- 論点定義を `scripts/elderly_license_taxonomy.py` / `scripts/bike_blue_ticket_taxonomy.py` に切り出し、分類スクリプトと共有（`tests/test_*_taxonomy.py` で固定）
- `configs/{theme}-reaction-map.json` の `issue_counts.source` を削除し、sample_file へ戻した
- 凍結ファイル `data/issue-counts/elderly-license-revocation.json` を削除。bike が依存していた `social-samples/bike_arena_hermes_classified.json` への参照も解消（ファイル自体はGit管理外に残置）
- 再分類前の2D分類のみの正典を `social-samples/{theme}_2d_classified_v1_2d_only.json` として保存
- 再分類でラベルが動いたため、`THEMES.yaml` の `main_issue` 行の内訳も実数へ更新した（elderly 139→95 等）
- 同日に main 側で ai-copyright（7論点・1,606件）と fukushuto も単一ソース化されたため、マージ後は `tests/test_taxonomy_continuity.py` の taxonomy不一致テーマが **0件** になった

**2026-08-07 に判明した未解決点（elderly / bike）**: 論点カードの件数は正典へ揃ったが、**同じページのアリーナ散布データ `SM_RAW` のセクター `i` は旧分類のまま**で、同一ページ内に2つの内訳が並んでいる。

| テーマ | SM_RAW の件数・内訳 | 正典（`classification.main_issue`） |
|---|---|---|
| elderly-license-revocation | 211件 / 139・24・20・9・7・12 | 211件 / 95・14・19・10・9・64 |
| bike-blue-ticket | **268件** / 54・56・16・28・20・94 | 181件 / 38・29・14・14・18・68 |

bike は件数自体も食い違う（SM_RAW は収集総数268件、分類済みは181件）。`verify_theme_page.py` は SM_RAW を検査していないため exit 0 のまま通る。
**発注書**: `configs/prompts/codex/20260807_elderly-bike-arena.md`（`build_elderly_arena.py` / `build_bike_arena.py` の新設と SM_RAW 再注入、検査追加。ブランチ `task/elderly-bike-arena`）

**2026-08-08 対応済み（憲法改正）**: constitutional-amendment は646件を同一条件で再分類し、意見577件に統一した。`scripts/build_constitutional_arena.py` を新設して SM_RAW・論点別の声・スタンス・詳細表を同じ意見集合から再生成し、`issue_counts.source` と凍結ファイルを削除した。

**2026-08-08 対応済み（辺野古）**: henoko-student-accident は363件を意見性付きで再分類し、意見のみをマップと論点件数の母数に統一。`issue_counts.source` と凍結件数ファイルへの依存を解消した。

**残作業なし。** 最後の `data/issue-counts/henoko-student-accident.json` を削除し、`data/issue-counts/` ディレクトリごと不要になった。**課題29は完了。**

**2026-08-08 検査固定**: 全11テーマでマップ・論点・賛否の母数を「意見のみ」に統一。`verify_theme_page.py` に母数一致、ページ全体の管理対象外件数、最大勢力バッジ、昇格順後のビルダ再生成可能性を追加した。差分は config に件数と理由が無ければ許可しない。`DATA_SHEET.md` の再生成忘れも unittest で検出する。
**横展開の完了条件に追加（2026-08-02）**: constitutional / henoko の `data/issue-counts/` 依存は、それぞれのadapter・ビルダー整備と同時に解消する。累積正典またはGit管理する仮名化検証データから論点件数を再現できることをadapter昇格条件とし、暫定ファイルだけを残さない。

### 課題30: 論点カードの解説と実データの乖離
**状態**: 対応案②（件数の併記）を2026-08-02に全11テーマへ適用済み。①③は未着手
**発見**: 2026-08-01、部活動ページの本番確認時

**2026-08-02 対応済み（S8）**
- `configs/{theme}-reaction-map.json` に `issue_counts`（source / basis / cards）を追加。カードと分類結果のラベル対応をここで宣言する
- `scripts/issue_card_counts.py`（件数の計算）と `scripts/sync_issue_counts.py`（HTMLへの注入）を新設。`<span class="explainer-count" id="issue-count-{theme}-{slug}">N件</span>` を全11テーマ・65枚のカードに併記
- `scripts/verify_theme_page.py` に「=== 論点カード ===」3検査を追加（id付きで併記されている / 件数が分類結果と一致する / ハードコードされた件数が残っていない）
- 解説文の中に重複して書かれていた件数（ai-copyright・elderly・henoko・bike・school-nickname・takaichi の計34箇所）を削除。内訳の数字（「うち30件が反対」等）は残した
- `build_bukatsu_arena.py` / `upgrade_constitutional_arena.py` / `build_consumption_tax_page.py` は生成後に `sync_issue_counts.py` を呼ぶようにした。`upgrade_nickname_arena.js` は手動実行が必要な旨をヘッダに明記

**残り（①③、別途判断）**
- 解説文の config への移行
- 件数順の並べ替え、少数論点の「その他」への集約（部活動の地域格差2件は併記で可視化されたが、カードの大きさは他と同じまま）

**概要**: 各テーマページの「このテーマを読み解く、N つの論点」の解説カードが**手書きの固定文言**で、分類結果の件数と連動していない。件数の大小に関わらず全論点が同じ大きさで並ぶため、実データ上ごく少数の論点が主要論点のように見える。

**具体例（部活動の地域移行）**

| 論点カード | 実件数（389件中） | 紙面 |
|---|---|---|
| 教員の働き方 | 114 (29%) | カード1枚 |
| 教育的意義・機会 | 82 (21%) | カード1枚 |
| 制度・移行プロセス | 81 (21%) | カード1枚 |
| 受け皿・指導者 | 61 (16%) | カード1枚 |
| 費用・家庭負担 | 30 (8%) | カード1枚 |
| **地域格差** | **2 (0.5%)** | **カード1枚**（「都市はできるが地方は無理」と1論点として大きく扱われている） |

同じページの「詳細データ」には `地域格差 2` と正しく出ているため、**同一ページ内で扱いの重みが矛盾している**。

**根が深い点: 解説文がPythonスクリプト内にハードコードされている**

config ではなくビルドスクリプトの中に直接埋め込まれている。

```
scripts/build_bukatsu_arena.py:141   <p class="explainer-card-title">地域格差 — 「都市はできるが地方は無理」</p>
scripts/build_consumption_tax_page.py
scripts/upgrade_constitutional_arena.py
scripts/upgrade_nickname_arena.js
```

**影響範囲**: 全11テーマ（論点カードは各テーマ3〜8枚、計70枚以上）

**対応案**（横展開時に決める）
1. 解説文を `configs/*.json` に移す（コードからコンテンツを分離）
2. 各カードに**実件数を併記**する（「地域格差 **2件**」）
3. 件数順に並べる、または一定件数未満は「その他の論点」にまとめる
4. `verify_theme_page.py` に「論点カードの件数が sample_file の分類結果と一致する」検査を追加

**優先度の判断**: 件数表示自体は全て正しいため緊急性は低い。ただし「実態と表示のズレ」はS1〜S6で潰してきた問題と同じ性質のもの。生成AIと著作権への `arguments` 横展開時に、同じ構造の設計判断が必要になるため、そのタイミングで一括対応する。

**2026-08-02 追記**: 「件数の併記」は S8 で全11テーマに実装済み（`issue_counts` + `sync_issue_counts.py` + `verify_theme_page.py` の検査）。残るのは①解説文の config 移行 ②件数順の並べ替え ③少数論点の集約 の3点。いずれも設計判断が必要なため未着手。

### 課題31: 「世論の潮目」ウィジェットの合成データ残存（koshitsu のみ）
**状態**: 未着手
**発見**: 2026-08-02、S8-fix（koshitsu 正典統一）の完了報告時

**概要**: `koshitsu-tenpakai` の「世論の潮目」ウィジェットの**前回値**が、S1 で正典から除外した合成データ `koshitsu-tenpakai_hermes_prev_synthetic.json` 由来のまま残っている。

S8-fix でページ本体（アリーナ・投票・カード・集計・詳細データ）は正典347件から再生成したが、**潮目ウィジェットの比較対象だけは旧データのまま**。

**現在の表示**

```
前回収集分273件と今回収集分347件の構成比を比較します。
比較対象：7月17日収集分の2Dスタンス統計（改正成立直後326件）と
7月26日収集分のAI分類（347件）。前回は2D分類データを再構成した参考値です。
「改正賛成（女系容認）」が9.2ポイント増加
```

**問題点**

1. **合成データが出所** — 前回値は実投稿ではなく、2D分類の集計値から逆算した273件の疑似レコード（`tweet_id: synthetic_*` / `url` 空）。S1 でヒーロー件数から除外した当のデータ
2. **同一ページ内で前回値が2つある** — 本文グラフの説明は「**273件**」、注記は「**326件**」。どちらが前回の母数か読者には分からない
3. **開示が弱い** — 「2D分類データを再構成した参考値」とは書いてあるが、**合成である旨は書かれていない**。読者は実投稿の再分類だと解釈しうる
4. **「9.2ポイント増加」が合成値との比較** — 数字として意味を持たせにくい

**他10テーマは問題なし**（全て実際の収集日を比較対象にしている。確認済み）

**対応案**
1. **koshitsu のみ潮目ウィジェットを非表示にする**（最も安全・実装も軽い）
2. 前回値を実データのある時点（7/12 など）に差し替える。ただし該当データがリポジトリに存在するか要確認
3. ウィジェットは残し、開示文に「前回値は合成データから再構成したものです」と明記したうえで、273/326 の食い違いを解消する

**推奨は案1。** S1〜S8 で「根拠を1行で説明できない数字は載せない」を徹底してきた方針と整合する。ウィジェット自体は他10テーマで正常に機能しているため、機能の削除ではなく1テーマの非表示で足りる。

**該当箇所**: `docs/koshitsu-tenpakai-reaction-map.html` の `TIDE_CARD_START` 〜 `TIDE_CARD_END`

**再発防止**: 対応時に `verify_theme_page.py` へ「潮目ウィジェットの比較対象が合成データでないこと」の検査を追加する

### 課題32: OGP画像とXヘッダー画像に旧コピーとダミー数値が残存
**状態**: **延期**（2026-08-02判断）。画像は生成済み、発注書も準備済み。着手時期は未定
**発見**: 2026-08-02、X固定ポスト差し替え時

**準備済みのもの**
- 生成プロンプト: `manga-prompts/site-ogp-header-prompts.md`（サイトのヒーロー準拠）
- 差し替え発注書: `configs/prompts/codex/20260802_ogp-header-replace.md`
- 新画像: 生成済み（リポジトリ未配置。パスは着手時に確認）

**延期中の状態**: 現行の `default.png` に「42%」等のダミー数値が残ったまま公開されている。
X固定ポストの本文（「世論調査ではありません」）と画像が矛盾している状態が継続する。

**概要**: `docs/ogp/default.png`（2026-06-27作成）に、トップページから削除した旧コピーと根拠のない数値が入ったまま。**サイトのトップURLを共有するたびにこの画像が表示される。**

**画像に含まれている問題のある要素**

| 要素 | 問題 |
|---|---|
| 「その話題、SNSでは実はどっちが多い？」 | S2でトップから削除した旧コピー |
| 賛成42% / 保留18% / 中立20% / 反対20% | **根拠のないダミー値**。S1〜S6で潰した性質の数字 |
| 「トレンド上昇中」「12.5K」「話題沸騰中」 | 実データではない演出値 |

**なぜ緊急度が高いか**

2026-08-02にX固定ポストを「出典は公的資料。**世論調査ではありません**」に差し替えたが、同じ投稿のOGPカードが割合の円グラフを表示しており、**本文と画像が同一投稿内で矛盾している**。

`utm_campaign=profile` / `pinned` を設定して導線を整えた直後であり、**入口の画像だけが最も古い状態**になっている。

**影響範囲**

| 対象 | 現在の画像 |
|---|---|
| `docs/index.html`（トップ） | `ogp/default.png` |
| `docs/usage.html` | `ogp/default.png` |
| X プロフィールのヘッダー画像 | 同じ旧コピー「その話題、SNSでは実はどっちが多い？」入り |

テーマ別OGP（`ogp/ai-copyright.png` 等9枚）は個別テーマ用のため、内容を確認のうえ別途判断する。

**やること**
1. `docs/ogp/default.png` を作り直す（1200×630）
2. X のヘッダー画像を作り直す（1500×500）
3. 差し替え後、X の Card Validator でキャッシュを更新する
4. 余力があればテーマ別OGP9枚の内容も点検する

**画像プロンプト**: `manga-prompts/site-ogp-header-prompts.md` に記載

### 課題33: 非公開の正典データと更新履歴の保全先を確立する
**状態**: 完了（2026-08-02。物理的に別のマシンでの再現のみ未実施）
**発見**: 2026-08-02、部活動パイロットのクリーンクローン検証時

**概要**: 本文・URL・ユーザー識別子を含む5テーマの `sample_file` と、`social-samples/updates/` の更新履歴はGit管理外で、このMacにしか存在しない。Macの故障・紛失時はページ再生成と代表投稿の再選定ができない。

**対応済み**: `data/verification/` に、ソルト無しSHA-256で仮名化した投稿IDと分類5項目だけの検証データを保存した。クリーンクローン／CIで件数・論点・意見数・投稿集合の検査は再現できるが、本文付きデータの復元はできない。

**完了条件**:
1. 公開Gitとは別の、アクセス制御された非公開ストレージを1つ正規の保全先として決める
2. 5テーマの本文付き累積正典と `social-samples/updates/` をバックアップする
3. 更新の昇格完了後に自動または1コマンドでバックアップし、失敗を検知できるようにする
4. 別マシンへの復元テストを行い、正典からページ候補を再生成できることを確認する
5. 保存期間、暗号化、アクセス権、削除手順を運用文書へ記録する

**2026-08-02 対応済み（完了条件3）**: `scripts/backup_private_data.py` を追加。`--dest` で必須の非公開 `sample_file` 5本、`social-samples/updates/`、標準化前のGit管理外raw・分類履歴をアーカイブする。必須ファイル欠落時は作成せず exit 1。同日再実行でも別run-idとなり、作成直後にSHA-256・件数の復元確認を自動実行する。実行確認は25ファイル・5,822,291バイト・復元確認 NG 0件。
**2026-08-02 追加対応**: 共通ランナー `scripts/refresh_topic.py` は、更新回履歴を確定した直後と公開昇格後の2地点でバックアップを必須実行する。バックアップ失敗時は更新回を確定せず、昇格中なら公開側を復元する。`--backup-dest` は必須で、保存先未決定のまま本収集できない。
**注意**: tar.gz自体は暗号化されない。保存先はリポジトリ外とし、暗号化・アクセス範囲はオーナー判断を運用文書へ記録する。
**2026-08-02 保存先決定・初回実行**: 正規保存先を `/Volumes/HD-LE-B/issue-stance-private-backups` に決定。個人サイトとして運用するオーナー判断により暗号化は行わない。25ファイル・5,822,291バイトを初回保存し、別コマンドで全25ファイルを展開してSHA-256・レコード件数を照合、NG 0件。アーカイブSHA-256は `a0414f05679bbb366863cfd32df669f45c80a91bc2457ac53178235bc837f1c1`。
**2026-08-02 復元確認（完了条件4）**: 作業ツリーに依存しないことを示すため、Gitのクリーンクローン（非公開 `sample_file` 5本が欠落した状態）へアーカイブを展開し、次を確認した。

1. 欠落5件 → 0件。ignore対象24ファイルと更新回履歴 `updates/bukatsu-chiiki/2026-08-02/{raw,classified}.json` が復元される
2. 復元した正典から `verification_data.py` で検証データを再生成すると、Git上の `data/verification/*.json` 5本すべてとバイト一致する
3. 復元した正典から `build_bukatsu_arena.py` + `sync_issue_counts.py` でページを再生成すると、公開版と**差分ゼロ**
4. その環境で unittest 45件 OK、全11テーマ NG 0件、`verify_top_page` / `verify_sample_periods` ともに exit 0

**Git ＋ 外付けディスクのアーカイブだけで、公開物と検証を完全に再構成できることが実証された。** 残るのは物理的に別のマシンへディスクを接続する確認のみで、データの十分性としては満たしている。
**保存期間**: 当面は全世代保持。ディスクの共有・譲渡・廃棄時はアーカイブを先に削除する。

### 課題34: ページ更新スクリプトが再実行できないテーマの整備
**状態**: 未着手（課題33のゲート完了後、データ更新の横展開と同時に進める）
**発見**: 2026-08-02、adapter 昇格判定の実測時

**概要**: データ更新を自動化するには「同じ入力で2回実行しても差分が出ない」ページ更新スクリプトが要る。全11テーマで実測し、`THEMES.yaml` の `page_update_mode` に記録した。

| 区分 | テーマ | 状態 |
|---|---|---|
| adapter（2） | bukatsu-chiiki / takaichi | staging候補の入出力に対応。変更候補の2回目実行で差分ゼロ |
| adapter_candidate（2） | henoko-student-accident / koshitsu-tenpakai | 現行入力では冪等だが、staging候補のinput/output指定に未対応 |
| migration（3） | constitutional-amendment / consumption-tax-cut | 生成済みページへ再実行すると `ValueError: substring not found` で落ちる（一度きりの移行用スクリプト） |
| | school-nickname-ban | 実行のたびに空行が1行増える。さらに `upgrade_nickname_arena.js` 内の古い meta description で `configs/theme-seo.json` 由来のSEO文言を巻き戻す |
| manual（4） | ai-copyright / bike-blue-ticket / elderly-license-revocation / fukushuto | 再実行可能な更新スクリプトが存在しない（`inject_tide_widget.py` と検査スクリプトのみ） |

**やること**: ①henoko / koshitsu の候補input/output対応 ②school-nickname-ban の2点を直して adapter へ昇格 ③constitutional-amendment / consumption-tax-cut を再実行可能な形へ書き直す ④manual 4テーマのビルダーを新設する
**注意**: ビルダーを直したら必ず同じ入力で2回実行し、2回目に差分が出ないことを確認してから `page_update_mode` を上げる

**2026-08-02 共通ランナー対応**: `scripts/refresh_topic.py --topic` に、全11テーマ共通の疎通確認・収集・重複排除・10件試験分類・全件分類・集合検査・更新回保存・バックアップを集約した。migration / manual / adapter_candidate も公開せずstaging止まりで予定どおり収集できる。ページ処理は `scripts/refresh_adapters/` に分離し、takaichi は候補ページ・arena data・潮目を2回生成して差分ゼロ、投票topicIdと15選択肢の互換性を検査する。

**横展開のゲート**: 少なくとも保全先の決定、既存データの初回バックアップ、復元確認が終わるまで、他テーマの定期更新を開始しない。

### 課題35: デザインシステム同期の実験が宙に浮いている
**状態**: 判断保留（2026-08-07 の棚卸しで記録。削除も継続も決めていない）
**発見**: 2026-08-07、運用棚卸し

**概要**: `design-system/`（26ファイル、最終更新 2026-06-21）と、その claude.ai/design 同期まわり一式が残っているが、**`docs/` からの参照は0件**。公開サイトは一切使っていない。

| 対象 | 状態 |
|---|---|
| `design-system/` | Git管理下26ファイル。参照元は `.gitignore` と `.design-sync/` のみ |
| `.design-sync/` | 212KB。`config.json` に `projectId: 7a02f1be-4fed-4822-a2f2-4ac155424358` |
| `.ds-sync/` | **45MB**。gitignore済み。同期ツールの実行環境（node_modules含む） |
| `ds-bundle/` | 2.9MB。gitignore済み。生成物 |

**判断が要る点**: claude.ai/design 側にプロジェクトが登録済みのため、消すと同期先との対応が切れる。デザイン刷新（課題18）で使うつもりがあるなら残す、ないなら `archive/` へ移してディスク約48MBを回収する。

**注意**: `.ds-sync/` と `ds-bundle/` はディスク上だけの問題（gitignore済み）。急がないなら先にこの2つだけ消してもよい。

---

### 課題36: 放置された作業ツリー3本
**状態**: 完了（2026-08-08。3本とも削除済み。中間成果物4件は担当ブランチへ保全）
**発見**: 2026-08-07、運用棚卸し

**概要**: `LOOP.md` ⓪ は「作業が終わったら `git worktree remove` で片付ける」と定めているが、3本残っていた。**3本ともブランチは main にマージ済み。**

| ツリー | ブランチ | 未コミット | 処置（2026-08-08） |
|---|---|---|---|
| `.claude/worktrees/agent-ae24789032b473197` | task/henoko-page-v3 | あり。`docs/henoko-student-accident-reaction-map.html` を公開版1,051行 → 142行のスタブに壊す中断状態（投票セクション・シェア・やり直しボタンが全消え）。**採用してはいけない** | 未コミット分を破棄して削除。origin/main の現行版が正 |
| `.claude/worktrees/competent-gates-92d0d7` | detached HEAD | なし | 削除。コミット 5b69733 は `claude/competent-gates-92d0d7`（ローカル・origin 両方）に残存 |
| `.worktrees/fukushuto-tide` | task/fukushuto-tide | 未追跡4件。2026-08-07 に共有ツリーの `social-samples/` へ退避済み（`fukushuto_hermes_prev_20260714_v2.json/.md`、`fukushuto_test_10.json`、`fukushuto_test_10_classified.json`） | 削除。4件は `task/fukushuto-tide` にコミットして push（3b3efef）。詳細は下記 |

**4件の正体（2026-08-08 に中身を確認）**: `configs/prompts/codex/20260807_fukushuto-tide-widget.md` の**手順1・手順2の成果物**であり、破棄してはいけないものだった。

- `fukushuto_test_10.json` / `_classified.json` — 手順2の試験分類10件。入力は旧5論点で全件「副首都法案の是非」、出力は新7論点に分散
- `fukushuto_hermes_prev_20260714_v2.json` / `.md` — 手順1の7/14分292件の再分類。旧版に対し stance が変わったのは29件

**残作業は 2026-08-08 に完了**（`task/fukushuto-tide` の `433d89c`）。7/26分308件を再分類し、対照表でオーナー承認を得たうえで潮目ウィジェットを7論点へ移行した。同一画面での二重表示は解消済み。作業手順は `.claude/skills/taxonomy-migration/` にスキルとして残した。

**なぜ放置が危険だったか**: 2026-08-07 に共有ツリーで事故が2件起きている（分類処理の参照ファイル消失、統合直後の正典1,606件が削除されかけ）。残ったツリーは同じ事故の温床になる。**今回も、未追跡ファイルを中身を見ずに「不要」と判断しかけた。中間成果物は必ず中身を確認してから処置すること。**

---

### 課題37: validate_theme_seo.py が1件落ちている
**状態**: 未着手（2026-08-07 の棚卸しで検出。棚卸し前から存在する既存の不整合）
**発見**: 2026-08-07

```
FAILED: 1 validation error(s)
- ai-copyright-reaction-map.html: dateModified does not match THEMES.yaml updated_at
```

**概要**: `docs/ai-copyright-reaction-map.html` の JSON-LD `dateModified` と `THEMES.yaml` の `updated_at` がずれている。データ更新時にページ側のSEO日付を戻し忘れたと思われる。

**やること**: どちらが正しいか（最後に実際に公開更新した日）を確認して片方へ揃える。ai-copyright は `page_update_mode: adapter` なので、adapter 側で `dateModified` を更新していない可能性も調べる。

---

### 課題38: inject_tide_widget.py が公開中のページを古いデータへ巻き戻す
**状態**: 未着手（2026-08-08 に副首都の作業中に発見。実害は出ていない＝実行直後に戻した）
**発見**: 2026-08-08

**概要**: `scripts/inject_tide_widget.py` は引数を取らず、実行すると `THEMES` の全8テーマの HTML を書き換える。ところが `adapter` 方式のテーマは `refresh_topic.py` 経由で更新されており、スクリプト内の `THEMES` に書かれた更新回のほうが**古い**。そのため実行すると、公開中のページが過去のデータへ戻る。

| テーマ | 公開中 | 実行後（巻き戻り先） |
|---|---|---|
| ai-copyright | 7月26日 → 8月3日 | 7月12日 → 7月26日 |
| takaichi | 7月26日 → 8月7日 | 7月12日 → 7月26日 |

**なぜ危険か**: 1テーマの潮目を直すだけのつもりで実行すると、無関係な2テーマが黙って後退する。`git status` を見て戻さない限り、そのままコミットされて公開される。検査は通ってしまう（日付の新しさを見る検査がない）。

**やること**: 次のいずれか。①`--slug` 引数を足して対象テーマだけ書き換えられるようにする ②`adapter` 方式のテーマを `THEMES` から外し、adapter 側に一本化する ③実行前に「`THEMES` の更新回がページの現状より古くないか」を検査して止める。②が筋が良いが、adapter 側が潮目を生成できるか未確認。

**暫定の回避策**: 実行後に必ず `git status --porcelain` を見て、対象外の `docs/*.html` が出ていたら `git restore` する。この手順は `.claude/skills/taxonomy-migration/SKILL.md` の「落とし穴」に記載済み。
### 課題39: トップページのカウントダウンが毎日ズレる
**状態**: 未着手（2026-08-08 に発生を確認。当日分は手動で直した）
**発見**: 2026-08-08、日付が変わった直後の検査で検出

**概要**: `docs/index.html` の更新バーに「次回更新: 8月9日（あと2日）」のように**残り日数が固定文字列で焼き込まれている**。日付が変わるたびに1日ずつズレ、`scripts/sync_portal_stats.py` を実行するまで公開サイトに誤った日数が出続ける。

`scripts/verify_top_page.py` と `tests/test_portal_stats.py` は毎日この不一致で落ちるため、**「検査が落ちているのが平常」になって本当の異常を見逃す**危険がある。実際 2026-08-08 は、別作業の検証中にこれが混ざって原因切り分けが必要になった。

**取りうる対応（どれか1つ）**:
1. 残り日数の計算をページ内のJSに寄せ、HTMLには日付だけ焼き込む（表示は毎回正しくなる。既に `update-bar-days` という id はあるので差し替えやすい）
2. 「あと◯日」の表示自体をやめ、日付だけ出す（いちばん単純）
3. 毎日 `sync_portal_stats.py` を実行する運用にする（人手が増えるので非推奨）

**推奨**: 1。既存の id をそのまま使えて、検査も安定する。

---


### 課題40: 2026-07-26 の一斉収集が5テーマで正典に統合されていない

**状態**: 進行中（6テーマ中1テーマ完了。2026-08-08 に副首都を実施）
**発見**: 2026-08-08

**概要**: 2026-07-26 に全テーマで一斉収集した分が、**「世論の潮目」ウィジェットを作るためだけに使われ、累積正典に統合されないまま**残っている。THEMES.yaml の `collect_delta` には記録されているため、台帳では「追加済み」に見える。公開ページの収集件数は、この分を数えていない。

| テーマ | 7/26に収集 | 正典に未統合 | 現在の正典 | 実際に持っているデータ |
|---|---|---|---|---|
| 副首都 | 308 | ~~308~~ → 0 | 897 | 統合済み（2026-08-08） |
| 高市 | 178 | **140** | 447 | 587 |
| 自転車の青切符 | 72 | **72** | 181 | 253 |
| 高齢者免許 | 61 | **61** | 211 | 272 |
| あだ名禁止 | 45 | **45** | 374 | 419 |
| 辺野古 | 39 | **39** | 363 | 402 |
| 生成AIと著作権 | 452 | 0 | 1,606 | 統合済み |
| 皇室典範 | 347 | 0 | 347 | 統合済み |

**当初の未統合は合計665件。副首都の308件を統合したので、残りは357件。** 対象テーマの notes には「◯件を追加収集しHermes分類し『世論の潮目』ウィジェットを追加」と書かれており、当時から潮目専用だった。

**なぜ問題か**: ①公開ページの収集件数が実際より少ない ②潮目ウィジェットが、正典に入っていないデータを比較対象にしている ③台帳（collect_delta）とページの数字が食い違う。読者から見えるのは①だけだが、③は今後の集計をずっと狂わせる。

**やること**: 各テーマの `collect_at` のタイミングで、収集と同時に正典へ統合する。7/26分は現行のHermes方式（`is_relevant` / `is_opinion` / `main_issue` / `stance`）で分類済みなので、論点体系が一致していれば再分類は不要。

**対象外（取り残しではないもの）**:
- `koshitsu-tenpakai_hermes_prev_synthetic.json`（273件）… **合成データ**。取得日が無く実投稿ではない。潮目の前回値として注釈付きで開示済み（課題31）
- `ai-copyright_classified_added.json` / `school-nickname-ban_classified_v2_redesign*.json` など … 2026-06 の旧スキーマ（`category` / `policy_attitude`）。現行方式と互換が無く、統合には再分類が必要。別課題として扱う

**着手順**: ~~副首都（2026-08-08 に完了）~~ → 自転車(8/11) → 高齢者(8/13) → 高市(8/14) → あだ名(8/16) → 辺野古(8/18)。各テーマの収集セッションに組み込む。

**副首都でやったこと（残り5テーマの雛形）**:

1. 収集の**前に**正典を入れ替える。7/14分と7/26分（いずれも公開側の論点で再分類済みのv2）を投稿IDで重複排除して結合し、`{theme}_hermes_classified.json` として `sample_file` を差し替える。旧2D正典は消さず `_v1_2d_only.json` に改名して残す。**先に入れ替えると、収集の重複判定が統合後の全件に対して行われる**（後回しにすると、すでに持っている投稿を新規として数え直す）
2. そのうえで `refresh_topic.py` を実行し、更新回の分類結果を正典へ足す
3. `scripts/build_{theme}_arena.py` を作り、ページの件数・論点・賛否・マップの点を正典1本から生成する。`scripts/verify_builder_rebuildability.py` の `BUILDERS` に登録する
4. `configs/{theme}-reaction-map.json` の `denominator_exceptions` を削除する（賛否が入るので不要になる）
5. **新しい正典を `.gitignore` に足す**（本文を含むため。`social-samples/` は全体が除外されているわけではない）
6. **ページ本文に残っている順位の主張（「最多論点」「感情温度が最も高い」など）を外す。** 件数が変わると最大論点が入れ替わり、見出しと数字が食い違う（副首都では「議論の中心」が定義・中身の見出しのまま件数だけ都構想・維新の180件になった）

## 連絡メモ（AI間の申し送り）

| 日付 | 発信AI | 宛先AI | 内容 |
|------|--------|--------|------|
| 2026-06-27 | Antigravity | 全員 | AdSense審査通過後にプロジェクト用アドレスを「管理者」として招待し権限移行すること |
| 2026-07-01 | Antigravity | 全員 | 課題16 OGP対応完了。build_reaction_map.pyにOGP自動挿入機能を追加済み |
| 2026-08-01 | Claude | 全員 | `WORK_PLAN_2026-08.md` と `WORK_PLAN_2026-08_SESSIONS.md` を追加。8月はこの計画に従い、S1〜S5 のセッション単位で進める。発注書は `configs/prompts/codex/` に置く |
| 2026-08-01 | Claude | 全員 | S1完了。トップの数値は `THEMES.yaml` の `sample_file` の実レコード数から生成される。**数値をHTMLに直接書かないこと。** 変更後は必ず `python3 scripts/verify_top_page.py` を実行し、NG（exit 1）がないことを確認する |
