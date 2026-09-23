# 課題77 — ai-copyright（生成AIと著作権）連動表示 工程1: 内容確定書

作成: 2026-09-23。[別テーマへの適用手順](2026-09-22-task77-connected-layout-rollout-guide.md)の「次のテーマで進める6工程」の
工程1（内容と配置）にあたる。同梱JSON: [2026-09-23-task77-ai-copyright-content-contract.json](2026-09-23-task77-ai-copyright-content-contract.json)。
消費税版の実装構造の詳しい対応表は[スキーマリファレンス](2026-09-22-task77-consumption-tax-schema-reference.md)、
bukatsu-chiiki移植の先例は[bukatsu-chiiki内容確定書](2026-09-22-task77-bukatsu-chiiki-content-contract.md)。
対象: `ai-copyright`。公開URL・論点ID・投票の保存先と選択肢の意味は変更しない。

作業ツリー: `../isa-wt-task77-ai-copyright`（ブランチ`task/task77-ai-copyright-connected-layout`）。
本工程で公開ページ・生成器・集計データは変更していない（`data/public/themes/ai-copyright.json`・
`data/verification/ai-copyright-*.json`・`configs/planet/ai-copyright.yaml`等を直接読んで確認しただけ）。

## 結論（先に）

**ai-copyrightは連動表示に必要な原材料のほぼ全てを既に持っている。** 沈んだ大陸4件・地下水脈2本・
資料照合(claim-audit)6件・論点ごとのX投稿(issue-cards)7論点×2件・編集部の横断整理5件・
一次資料クイズ6問・年表(背景)6段階・授業節(classroom section)・編集分析情報は、すべて公開済み
データとして既に存在する。bukatsu-chiiki・消費税と同じく「無いのは、これらを1か所につないで
見せる新しい画面」だけ。

一方、bukatsu-chiiki・消費税のどちらにも無い**ai-copyright独自の要素が2つ**ある。

1. **`#bukatsu-check`（制度確認4項目、idはテンプレート由来のまま）**: bukatsu-chiikiと同じ
   共有テンプレートだが、ai-copyrightでは「法律」と「任意のルール」を分けて確かめる、という
   このテーマ特有の内容（著作権法・解釈・プリンシプル・コードの混同を防ぐ4問）が入っている。
   bukatsu-chiikiのbukatsu-check同様、**論点idのタグは無い**（`data/verification/ai-copyright-background.json`
   の`checklist.items[]`を直接確認、4件とも`issue_ids`キー自体が無い）。
2. **`#copyright-entry`（「判断の入口」、他9テーマに無い独自セクション）**: 「学習・出力・公開の
   どの場面の話をしているか」を3段階（学習データの収集・学習／生成／公開・販売）で整理する
   ナビゲーション。特定の論点に属さず全論点を横断する内容のため、論点idでのタグ付け対象では
   ないと判断する（下記「ai-copyright固有の未解決事項」参照）。

また、**課題77とは別の既存の不具合を1件発見し、課題90として新規登録した**：`#ai-copyright-tide-widget`
（世論の潮目）が山なみ移行後、通常更新の経路から外れて自動更新されなくなっている
（`build_ai_copyright_arena.py`の`apply_tide()`が旧2D形式向け分岐でしか呼ばれない）。
本移植では「現状のまま位置と機能を維持する」に留め、鮮度の回復は課題90で扱う。

## 論点別接続表（1論点1行、詳細は同梱JSON）

論点IDは`configs/planet/ai-copyright.yaml`・`data/public/themes/ai-copyright.json`を直接読んで確認した値。
件数・順位は2026-09-20更新・2026-06-22〜2026-09-20収集の公開データ（意見2,865件）。

| 論点ID | 名称 | 件数・順位・比率 | 再読状態 | 理由数 | issue-cards | claim-audit | 沈んだ大陸 | 地下水脈 | 図解 |
|---|---|---|---|---|---|---|---|---|---|
| `ai-copyright-learning-data` | 📚学習データ・無断利用 | 730件・1位・25.5% | full（657/730読了、`read_at`2026-09-13） | 12種（島表示13） | ✓2件 | 2件（unauthorized_learning_infringement, data_disclosure_needed） | sc-1, sc-4（2件） | なし | あり |
| `ai-copyright-user-ethics` | 💬利用者モラル・倫理 | 723件・2位・25.2% | **未再読** | 0 | ✓2件 | 0件 | なし | vein-2（1件） | あり |
| `ai-copyright-legal-framework` | ⚖️法制度・規制整備 | 522件・3位・18.2% | **未再読** | 0 | ✓2件 | 2件（data_disclosure_needed, tech_innovation_over_regulation） | sc-3（1件） | vein-1, vein-2（2件） | あり |
| `ai-copyright-creator-rights` | 🎨クリエイター保護・権利 | 334件・4位・11.7% | full（303/334読了、`read_at`2026-09-13） | 10種（島表示11） | ✓2件 | 2件（compensation_required, creator_protection_insufficient） | sc-2（1件） | なし | あり |
| `ai-copyright-other` | 🤔その他 | 238件・5位・8.3% | full（223/238読了） | 7種（島表示8） | ✓2件 | 0件 | なし | なし | あり |
| `ai-copyright-generated-work-rights` | ✨AI生成物の権利・創作性 | 186件・6位・6.5% | full（165/186読了） | 7種（島表示8） | ✓2件 | 1件（ai_output_has_copyright） | なし | なし | あり |
| `ai-copyright-tech-promotion` | 🚀技術競争・推進 | 132件・7位・4.6% | full（117/132読了） | 6種（島表示7） | ✓2件 | 1件（tech_innovation_over_regulation） | なし | vein-1（1件） | あり |

**「claim-audit」「沈んだ大陸」「地下水脈」の列は、いずれも`data/public/themes/ai-copyright.json`の
`claim_verification.claims[].issue_ids`・`ocean_layer.sunk_continents[].nearest_issue_id`・
`ocean_layer.veins[].issue_ids`を直接読んで確認した値（推測ではない）。** bukatsu-chiikiと違い、
沈んだ大陸4件は**全件**`nearest_issue_id`を持ち編集部推定の補完は不要（4件中3件が無タグだった
bukatsu-chiikiより状態が良い）。claim-auditの6件も全件issue_idsを持ち、複数論点にまたがるもの
（`data_disclosure_needed`→学習データ+法制度、`tech_innovation_over_regulation`→法制度+技術競争）がある。

**「理由数」列（`data/ai-copyright_issues-reread.json`）は5論点で存在するが、`__unread__`バケットは
どの論点にも無い**（bukatsu-chiikiと違う点）。「島」表示の件数（ページ実測）は理由の種類数より
常に+1多い（学習データ12種→島13、クリエイター保護10種→島11、その他7種→島8、生成物権利7種→島8、
技術競争6種→島7、5/5で一致）。理由バケットの件数合計が読了件数（例: 学習データ657件）と一致し、
論点件数（730件）との差（73件）が未読分として存在するため、**「+1」は`build_planet_data.py`が
実行時に合成している「未読」を表す島だと推測されるが、同スクリプトのソースまでは本工程では
未確認**（`build_ai_copyright_arena.py`にはreason関連の処理が無いことは確認済み＝grep 0件）。

**再読データの母数（`population.意見全体`=2,593件、`read_at`2026-09-13）が、現在の公開母数
（2,865件、2026-09-20更新）より少ない。** 9/20収集で加わった新規272件は、この5論点の理由再読には
まだ反映されていない。これは通常運用の編集再読の遅れであり課題77の対象外だが、読書面の文言には
「論点全体の内容」に加えて再読基準日（2026-09-13時点）を明記する必要がある。

各論点に対応する図解は7論点とも存在（`scripts/refresh_planet_section.py`の
`AI_COPYRIGHT_LANDING_IMAGE_BY_ISSUE_ID`、7件登録済み。fallback-navの`landing-panel`へ差し込み済み）。

## そのまま維持する既存機能（連動表示化で壊してはいけないもの）

- **STANCE_GLANCE（冒頭の立場バー、表示専用）**・**山の下の立場フィルター（すべて+3）**・
  **論点パネル内の立場フィルター（重複）**の3箇所。bukatsu-chiiki・消費税と同型の「重複していた
  立場操作」がai-copyrightにも存在する（3箇所が独立し、選択が連動していない）。ただし
  **予想2問（guess）に相当するUIはai-copyrightのページには見当たらない**（本工程では確認できず。
  bukatsu-chiiki・消費税にはある「①どちらが多いと思うか②強い表現が一番多い論点は」形式の
  guessesブロックが、ai-copyrightのSNS反応マップ内には存在しない可能性がある。工程2で
  `land()`/`buildGuesses()`相当の有無を実装前提で確認すること）
- 沈んだ大陸4件・地下水脈2本（「資料にあるのに、SNSにないこと」表示、立場で絞っても変わらない。
  全件`nearest_issue_id`/`issue_ids`でタグ済み）
- 一次資料クイズ6問（`id="quiz"`、claim-auditと同じ6件を`window.PLANET_DATA`経由で再利用と推定。
  bukatsu-chiikiの前例（claim-auditと同じFACT_CHECKSを流用）と同型かは工程2で確認）
- 編集部の横断整理5件（`editorial_summary.findings`、`ai-copyright-ed-1`〜`-5`、確認日2026-09-14）
- 論点一覧7件（順位・件数・%・島数/未再読表示、`id="list"`）
- claim-audit「その言い分、一次資料に当たるとどうなるか」6件（`id="ai-copyright-audit"`、
  確認日2026-09-19、対象投稿12件＝1件あたり2投稿）
- issue-cards「論点ごとのX投稿」7論点×2件（`id="issue-cards"`、**7論点全部にあり欠けがない**。
  bukatsu-chiiki・消費税と同じ「理由とは無関係の別系統」の投稿）
- vote-section（`data-vote-topic="ai-copyright-issue-stance-v1"`、`storageKey='sns_vote_ai_copyright_2step'`、
  2段階：論点7択→**立場3択**、保存式`choiceIdx = issueIdx * 3 + stanceIdx`（HTML内`selIssue*STANCES.length+stanceIdx`で確認済み）、
  7×3=21通り、シェア・やり直すボタン）
- classroom-section（授業・探究学習、理由3+3・一次資料3・問いの例3・印刷、課題77 Part Bで
  全10ページへ導入済み。`configs/classroom/ai-copyright.json`）
- article-trust（編集・分析情報）・related-topics（次に見るテーマ）・detail-data（詳細データ折りたたみ、
  分類別件数／カテゴリ×検索クエリ／カテゴリ×スタンス）
- explainer-modal（論点パネルの図解クリックで拡大）・progress bar（読んだところ、0/21）
- **`#bukatsu-background`（背景・経緯、実質的に年表を兼ねる）**: 確認日2026-09-19。
  `timeline`6段階（各`id/when/era/text/sources`、**issue_idsは無い**＝消費税と同じく無タグ。
  bukatsu-chiikiは年表を論点連動させる追加実装をしたが、必須ではない）
- **`#bukatsu-check`（法律と任意ルールを分けて確かめる、4項目）**: 上記「結論」参照。
  **論点idタグは無い**（真のギャップ、下記「未解決事項」で扱う）
- **`#copyright-entry`（判断の入口、3段階）**: ai-copyright独自。上記「結論」参照
- `ai-copyright-arena-data.js`は山なみでは無害・未使用のまま維持（削除は本作業の対象外）
- **旧アリーナ時代の死んだ連動フックが投票JS内に残る**: `window.setArenaVoteMarker`
  （`docs/ai-copyright-reaction-map.html:2574,2578`）は`if(window.setArenaVoteMarker)`で
  安全にガードされているが定義元が無い（grep 0件）。`#issue-arena-section`
  （同2579、投票後のスクロール先）も同様に定義が無い。bukatsu-chiikiの
  `window.setStanceMapVoteMarker()`と同型の「死んだ連動ポイント」で、実害は無いが
  そのまま復活させる対象ではない（新しい連動表示の参考にはなる）

## 消費税・bukatsu-chiikiとの構造差分（同じ処理を共通化する前に把握しておくこと）

1. **立場が3種**（消費税は4種、bukatsu-chiikiは表示4種・投票専用3種の二重体系）。
   ai-copyrightは**表示フィルターも投票も同じ3種**（規制/中立/推進）だが、
   **文言が違う**: 表示フィルターは「規制・制限強化支持／中立・情報／推進・活用支持」、
   投票UIは「規制賛成・著作権保護／どちらでもない／AI活用推進・規制反対」
   （`docs/ai-copyright-reaction-map.html:2549-2551`で確認）。同じ3立場の別ラベルであり、
   bukatsu-chiikiのような「投票専用の別選択肢体系」ではない。連動表示でこの文言差を
   統一するかどうかは範囲外の判断（勝手に変えない）
2. 投票の保存式は`issueIdx*3+stanceIdx`でbukatsu-chiikiと同型（7×3=21）。消費税の
   `issue.slot*4+stance.slot`（7×4=28）とは体系が違う
3. `vote_issue_order`（投票ボタンの順）が件数順（表示順）と異なる。`configs/planet/ai-copyright.yaml`の
   `vote_issue_order`とHTML内`VOTE_ISSUES`配列の並びが一致することを確認済み（学習データ→法制度→
   利用者モラル→クリエイター保護→技術競争→生成物権利→その他）。bukatsu-chiiki・消費税と同じ注意点
4. **理由（reason/bucket）の投稿例つき開閉表示（消費税の追加機能相当）はai-copyrightに無い**。
   `configs/ai-copyright-reason-posts.json`も`scripts/ai_copyright_reason_posts.py`も存在しない
   （grep 0件）。bukatsu-chiikiも同じ機能を6工程の必須要件にせず未実装のまま出荷した前例があり、
   **ai-copyrightも同じ扱い（論点全体のissue-cards 2件を維持し、理由は件数ラベルの静的一覧として
   見せるに留める）を提案する**。着手するなら独立工程とすること
5. 沈んだ大陸・地下水脈の論点タグが**全件揃っている**（bukatsu-chiikiは4件中3件無タグだった）。
   claim-auditも全件タグ済みで、この点はai-copyrightのほうが移植しやすい
6. **年表（background timeline）に論点タグが無い**点は消費税・bukatsu-chiiki(当初)と同じ。
   bukatsu-chiikiは工程4でオーナー確認のうえ論点連動を追加実装した前例があるが、必須ではない
7. **`#bukatsu-check`4項目に論点タグが無い**点はbukatsu-chikiと同じ真のギャップ。
   ただしbukatsu-chiikiは当初タグ付けを見送って公開し、オーナー指摘を受けて後日追加した
   （二度手間だった）。**ai-copyrightでは同じ手戻りを避けるため、下記の案を工程1の時点で提示する**
8. **`#copyright-entry`（判断の入口）はai-copyright独自で、bukatsu-chiiki・消費税に前例が無い**。
   論点非依存のクロスカット内容として扱う（下記参照）
9. **`#ai-copyright-tide-widget`（潮目）が定期更新で自動同期されない**（課題90）。
   bukatsu-chiikiの「連動表示自体が定期更新で消える」不具合（工程5で発見・修正済み）とは別種だが、
   「山なみ移行時のガード分岐に新機能が引っかかって取り残される」という**同じ型**の欠落
10. 予想2問（guesses）に相当するUIの有無が本工程では未確認（上記「維持する機能」参照）。
    bukatsu-chiiki・消費税にはあるが、ai-copyrightのSNS反応マップにこの2問が見当たらない
11. `drawPanel()`/`land()`/`issueTabs()`相当のJS関数群、`refresh_adapters/ai_copyright.py`の
    `adapter_name`実値、`verify_builder_rebuildability.py`のai-copyright対象は未確認。
    bukatsu-chikiと同じく工程2で実装前提で読むこと

## ai-copyright固有の未解決事項（工程2着手前に判断すること）

### 1. `#bukatsu-check`4項目の論点タグ付け案（ドラフト、要確認）

bukatsu-chiikiは「年表と同じ手順（内容提示→タグ付け案確認→オーナー承認）」で後日タグ付けした。
同じ手戻りを避けるため、内容を読んだ時点での対応案を先に示す。

| 項目 | 問い | 提案するタグ付け先 | 根拠 |
|---|---|---|---|
| AI学習と著作権侵害 | 「無断学習」は一律に違法なのか | `ai-copyright-learning-data` | 項目名が論点名と直接対応 |
| 学習データの情報開示 | AI事業者は出所を明かす義務があるのか | `ai-copyright-legal-framework`（+`ai-copyright-learning-data`も候補） | claim-auditの`data_disclosure_needed`が同じ内容を学習データ+法制度の両方へ紐付けている前例と一致させる案 |
| 2026年の著作権法改正 | SNSで話題の「著作権法改正」とAI学習の関係 | `ai-copyright-legal-framework` | 法改正そのものの話題 |
| 声・作風の保護 | 似せて作られた声や画風への対応 | `ai-copyright-creator-rights` | パブリシティ権・実演家保護はクリエイター保護・権利の範疇 |

この案は内容を読んだ上での推測であり、**確定ではない**。工程2または3の着手時に、
bukatsu-chiikiと同じ「内容提示→確認」の手順を踏むことを推奨する。

### 2. `#copyright-entry`（判断の入口）の扱い

3段階（学習データの収集・学習／生成／公開・販売）はいずれも特定の1論点に対応しない
横断的な内容（例えば「学習」段階は学習データ・無断利用だけでなく法制度・規制整備にも関わる）。
**論点への統合は「該当なし」とし、独立した折りたたみブロックとして維持する案を提案する**
（V09表の「該当なし」区分に相当。原材料が無いのではなく、性質上1論点に属さないことが根拠）。
配置は、他テーマの「編集部の横断整理」と同様に山・読書面クラスタの後段、投票の直前を候補とする
（現状の相対位置に近い）。この配置は工程3・4の視覚検証で確定させる。

### 3. 理由（reason）ごとの投稿例表示機能の要否

上記「構造差分4」のとおり、bukatsu-chiikiの前例に倣い**新設しない**（論点全体のissue-cards
2件を維持し、理由は件数ラベルの静的一覧として見せる）ことを提案する。オーナーから追加の
指示があれば独立工程として計画する。

### 4. 年表への論点タグ付け

必須ではない（V01の要件は「年表を山・読書面の後段へ移動して日付で切替」のみ）。
bukatsu-chikiのように論点連動を追加するかは、工程3・4着手時にオーナーへ確認するかを
実装セッションの判断に委ねる。

## 変更前の比較基準（同梱JSONの`before_state_baseline`と同一）

- git commit（このファイル作成時点のHEAD）: `258643bde8f7e90764c70fcfacd06a3a2a0360aa`
- `docs/ai-copyright-reaction-map.html` sha256: `246fd91dbe1468ffb63361b43ba6324fd5b4d9981d0e6012146465e72532c7f9`（315,984 bytes）
- 収集4,280件・意見2,865件・取得期間2026-06-22〜2026-09-20・更新2026-09-20（`THEMES.yaml`）
- 図解画像30枚（`docs/images/topics/ai-copyright/`。うち`ai-copyright-vote-*.webp`4枚は
  投票UIの現行実装（テキストボタン）からは参照されておらず旧デザインの残存と見られる。
  削除要否は本作業の対象外）

## 不足・要確認事項（工程2着手前に読むこと、詳細は同梱JSONの`open_gaps`）

1. 予想2問（guesses）に相当するUIがai-copyrightのSNS反応マップに存在するか本工程では未確認
   （上記「維持する機能」参照）。無ければ「新設しない」のか「他テーマにある機能なので追加する」のか
   工程2着手時に判断すること
2. `land()`/`drawPanel()`相当のJS関数群、`refresh_adapters/ai_copyright.py`の`adapter_name`実値、
   `verify_builder_rebuildability.py`のai-copyright対象は未確認。工程2で実装前提で読むこと
3. `scripts/build_ai_copyright_process_sections.py`（288行）が実際に`#ai-copyright-audit`
   （claim-audit）セクションのHTML文字列を生成しているか未確認（ファイル冒頭のみ確認）
4. `configs/ai-copyright-reaction-map.json`（旧2D設計時代のconfig）が`ai_copyright_taxonomy.py`・
   `scripts/prepare_editorial_candidate_text.py`から今も読まれている件の役割の全容が未確認。
   連動表示の生成器を書く前に、この旧configへの依存関係を確認すること
5. 一次資料クイズ6問（`id="quiz"`）が claim-audit の6件をそのまま再利用しているか
   （bukatsu-chiikiの前例と同型か）は本工程では未確認
6. `#issue-cards`の投稿2件×7論点がどのスクリプト（`ai_copyright_issue_media.py`、156行）で
   どう選定されたか（編集部選定か機械選定か）は未確認
7. 「島」表示（bucket数+1）が本当に「未読」を表す合成島かどうか、`build_planet_data.py`の
   ソースでは未確認（5/5のパターン一致からの推測に留まる）
8. `docs/ai-copyright-vote-*.webp`4枚・`ai-copyright-arena-data.js`など、山なみでは
   未参照と見られるファイルの削除要否（課題73「旧アリーナの死んだデータ」の対象範囲か）は
   本工程では判断しない

## 完了条件（工程1）

どの論点にも出所と表示先がある：済み（上記接続表、公開JSON・reread JSONを直接読んで確認）。
確認されていない内容を補っていない：済み（`#bukatsu-check`・`#copyright-entry`のタグ付け案は
「ドラフト・要確認」と明記、reason-posts機能は「新設しない」提案として明記、架空の理由・投稿・
資料は作っていない）。残す機能の一覧がそろっている：済み（上記「そのまま維持する既存機能」）。

## 次にすること

工程2（更新に耐える土台）着手。まず`scripts/build_ai_copyright_arena.py`・
`scripts/refresh_adapters/ai_copyright.py`・`scripts/refresh_planet_section.py`の
`_sync_ai_copyright_method_text()`・`scripts/build_ai_copyright_process_sections.py`を
実装前提で読み、bukatsu-chiikiの`scripts/bukatsu_connected.py`・`scripts/bukatsu_connected_content.py`
を土台に`scripts/ai_copyright_connected.py`（仮）を新設する。上記「未解決事項」1・2・3を
工程2の冒頭で解消してから配線に入ること。
