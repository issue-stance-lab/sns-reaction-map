# 課題77 — bukatsu-chiiki（部活動の地域移行）連動表示 工程1: 内容確定書

作成: 2026-09-22。[別テーマへの適用手順](2026-09-22-task77-connected-layout-rollout-guide.md)の「次のテーマで進める6工程」の
工程1（内容と配置）にあたる。同梱JSON: [2026-09-22-task77-bukatsu-chiiki-content-contract.json](2026-09-22-task77-bukatsu-chiiki-content-contract.json)。
消費税版の実装構造の詳しい対応表は[スキーマリファレンス](2026-09-22-task77-consumption-tax-schema-reference.md)。
対象: `bukatsu-chiiki`。公開URL・論点ID・投票の保存先と選択肢の意味は変更しない。

## 結論（先に）

**bukatsu-chiikiは連動表示に必要な原材料のほぼ全てを既に持っている。** 沈んだ大陸4件・地下水脈2本・
事実確認7件・論点別X投稿14件・理由の内訳(5論点・43理由)・一次資料クイズ7問・年表6段階・授業節・
編集情報は、すべて公開済みデータとして既に存在する。消費税と違い「新規に集計・照合しないと表示する
中身が無い」という状態ではない。**無いのは「これらを1か所につないで見せる新しい画面」だけ**であり、
工程2以降は主にconsumption_tax_connected.py相当の配線作業になる。

一方、消費税より規模が大きい点が1つある: 理由(reason)ごとにX投稿例を開く機能（tax工程6後の追加機能）に
相当する対象が、taxの25理由に対しbukatsu-chiikiは**最大43理由**（5論点×6〜15）と多い。この機能は
tax本体の6工程には含まれず追加依頼だった。bukatsu-chiikiでも6工程の必須要件にはせず、着手するなら
独立工程として計画することを推奨する（下記open_gaps参照）。

## 論点別接続表（1論点1行、詳細は同梱JSON）

| 論点ID | 名称 | 件数/順位 | 再読状態 | 理由数 | 既存投稿2件 | 資料照合(確認済み) | 沈んだ大陸 | 地下水脈 | 図解 |
|---|---|---|---|---|---|---|---|---|---|
| `bukatsu-chiiki-kyoin` | 🏫教員の働き方 | 401件・1位 | full (323/401読了) | 15 (A〜N,P) | ✓ | kyushokuchoseigaku | なし | vein-2 | kyoin-v2 |
| `bukatsu-chiiki-seido` | 📋制度・移行プロセス | 314件・2位 | full (257/314読了) | 8 (plan-*/child-*/other共有) | ✓ | original-deadline, national-funding | なし | vein-2 | seido-v3 |
| `bukatsu-chiiki-kyoiku` | ⭐教育的意義・機会 | 256件・3位 | full (215/256読了) | 8 (seidoと同一枠組み) | ✓ | chutairen-entry | なし | なし | kyoiku-v2 |
| `bukatsu-chiiki-ukezara` | 👤受け皿・指導者 | 208件・4位 | partial (192/208読了) | 6 (R1〜R6) | ✓ | coach-pay, shidoin-role | sc-3, sc-4 | vein-1, vein-2 | ukesara-v2 |
| `bukatsu-chiiki-hiyo` | 💴費用・家庭負担 | 149件・5位 | partial (136/149読了) | 6 (P1〜P6) | ✓ | national-funding, club-cost-survey | sc-2 | なし | hiyou-v3 |
| `bukatsu-chiiki-sonota` | 💬その他 | 56件・6位 | **未再読** | 0 | ✓ | なし | なし | なし | sonota-v2 |
| `bukatsu-chiiki-kakusa` | 🗾地域格差 | 17件・7位 | **未再読** | 0 | ✓ | なし | sc-1 | vein-2 | kousa-v2 |

**「資料照合(確認済み)」列は`data/public/themes/bukatsu-chiiki.json`の`claim_verification.claims[].issue_ids`から
直接読んだ値（national-fundingはseido/hiyo両方に紐付く）。** 当初`data/verification/bukatsu-chiiki-claims.json`
（無タグ）だけを見て編集部推定としていたが、下流の公開JSONに既に機械可読タグがあることが分かり訂正した。
一方、沈んだ大陸(sunk_continents)は公開JSON上でも本当にsc-1（`nearest_issue_id`=kakusa）以外は無タグ。
bukatsu-check4項目・年表6件も同様に無タグで、これらは真のギャップとして残る（詳細は同梱JSONの`open_gaps`）。

## そのまま維持する既存機能（連動表示化で壊してはいけないもの）

- **STANCE_GLANCE（冒頭の立場バー、表示専用）**・**予想2問**・**山の下の立場フィルター(すべて+4)**・
  **論点パネル内の立場フィルター**の4箇所。taxと同型の「重複していた立場操作」がbukatsu-chiikiにも
  そのまま存在する（4箇所が独立して存在し、選択が連動していない）。連動表示化の主眼はこれを1組に
  集約すること
- 沈んだ大陸4件・地下水脈2本（「資料にあるのに、SNSにないこと」表示、立場で絞っても変わらない）
- 一次資料クイズ7問（`id="quiz"`、claim-auditと同じFACT_CHECKS7件を`window.PLANET_DATA.claims`経由で再利用）
- 編集部の横断整理4項目（2026-09-04時点、日付は表示改修では動かさない）
- 論点一覧7件（順位・件数・%・島数/未再読表示）
- 潮目カード（立場の変化/論点の変化タブ、9/15→9/22比較、再生アニメーション）
- claim-audit「その言い分、原典に当たるとどうなるか」7件（照合日2026-09-02、対象32投稿）
- issue-cards「論点ごとのX投稿」14件（`<blockquote class="twitter-tweet">`形式、`#planet-block`への戻りリンク）
- vote-section（`data-vote-topic="bukatsu-chiiki-issue-stance-v1"`、2段階：論点7択→**投票専用の立場3択**
  （反対・慎重／どちらでもない／賛成・推進。表示用4立場とは別物）、7×3=21通り、シェア・やり直すボタン）
- classroom-section（授業・探究学習、理由3+3・一次資料3・問いの例3・印刷、課題77 Part Bで導入済み）
- article-trust（編集・分析情報）・related-topics（次に見るテーマ）・detail-data（詳細データ折りたたみ）
- explainer-modal（論点パネルの図解クリックで拡大）・progress bar（読んだところ）
- **旧2Dスタンスマップ(SM_RAW)は連動表示で一切参照しない。** 課題73で削除対象として既に追跡中の死んだデータ

## 消費税との構造差分（同じ処理を共通化する前に把握しておくこと）

1. 投票の通り数と手順がtaxと違う。taxは論点(7)×立場(4)=28通りが最初から7×4個のボタン。
   bukatsu-chiikiは「①論点7択タップ→②立場**3**択タップ」の2段階UIで**7×3=21通り**
   （投票専用の3立場は表示用4立場とは別物、下記2の直前の注記参照）。保存番号の変換式は
   `choiceIdx = issueIdx * 3 + stanceIdx`（HTML内で確認済み）、`vote_issue_order`が
   `issueIdx`の並びを固定する点はtaxの`slot`方式と同じ考え方
2. 理由(reason)の再読状況がtaxと逆。taxは7論点中4論点が再読済み（3論点は`not_reviewed`）。
   bukatsu-chiikiは7論点中5論点が再読済み（その他・地域格差の2論点が`not_reviewed`）
3. 理由IDの命名規則が論点ごとにバラバラ（taxは単一英大文字で統一）。P1-P6／R1-R6／A〜N,P／
   plan-*・child-*・other。特にseido(制度)とkyoiku(教育的意義)は**同一の8理由の枠組みを共有**し、
   件数だけが違う（理由IDだけでは一意にならず、必ずissue_id+reason_idの組で扱う必要がある点はtaxと同じ）
4. 沈んだ大陸のissue紐付けがtaxより弱い。taxは`nearest_issue_id`を4件全てに持つが、bukatsu-chiikiは
   公開JSON上でも`nearest_issue_id`がsc-1（kakusa）のみで他3件はnull（無タグ、確認済み）
5. 年表がtaxと違い論点非連動。taxのtimelineは3件それぞれに`issue_ids`が付き論点と連動するが、
   bukatsu-chiikiの年表6件は時系列の通し記事で論点タグが無い。連動させるかは工程3以降の判断事項
6. 「編集部の横断整理」という、taxのcontent-contractには出てこないテーマ全体の総括ブロックが
   bukatsu-chiikiに存在する（4項目、日付2026-09-04）。tax側にも類似機能があるか本調査では未照合
7. 論点直下の投稿2件（issue-cards）は`<blockquote class="twitter-tweet">`で公式X埋め込みマークアップに
   なっている。taxのISSUE_CARDS_POSTSと同じ「理由とは無関係の別系統」という設計は共通
8. 立場の配色が2系統ある。山・立場バー・升目・論点パネルはteal/purple/gold/gray
   （`configs/planet/bukatsu-chiiki.yaml`）、投票ボタン・潮目カード・旧散布図は
   green/orange/red/gray（`configs/bukatsu-chiiki-reaction-map.json`の`arena_taxonomy.stances`）。
   連動表示でどちらに寄せるか工程3で決める。tax同様、見本の色へサイト全体を変えないこと
9. 投票→図の連動フックが死んでいる。`showVote()`が呼ぶ`window.setStanceMapVoteMarker()`は
   現ページのどこにも定義が無い（`#stance-map-section`も存在しない、CSSだけ残存）。
   旧2D散布図時代の連携の残骸で、新しい連動表示を作る際の「ここが元々の連動ポイントだった」
   参考にはなるが、そのまま復活させる対象ではない
10. `drawPanel()`は`#extras-{issue_id}`（クイズ照合・海面下導線）をJSで再構築せず、Pythonが
    生成した静的HTMLをそのままコピーする設計になっている（既存コードに「ここでもう一度
    組み立てると、同じ数字と文言が2通りに分かれる」というコメントがある）。連動表示の新設部分も
    この原則を踏襲すること
11. `configs/topics/bukatsu-chiiki-v2.yaml`は無関係な別物（Ollama初期分類器用の12論点・6立場体系）。
    現行の7論点・4立場Hermes体系と混同して接続表に混ぜないこと

## 変更前の比較基準（同梱JSONの`before_state_baseline`と同一）

- git commit: `6b2de21a66e2b46dff554ed93b8aa8e0b97b122f`
- `docs/bukatsu-chiiki-reaction-map.html` sha256: `d36c533f52e6fe87ce8e1254aee87ead871e6cecace6d46c08e16319e310eaa5`（474,003 bytes）
- 収集1,726件・意見1,401件・取得期間2026-06-27〜2026-09-21・更新2026-09-22
- 図解画像8枚（`docs/images/topics/bukatsu-chiiki/`、うち無印ファイル7枚は現行未参照の旧版とみられる。削除要否は本作業の対象外）

## 不足・要確認事項（工程2着手前に読むこと、詳細は同梱JSONの`open_gaps`）

1. bukatsu-check(制度4項目)・年表(6件)のissue_id対応は今も編集部推定（claim-auditと沈んだ大陸sc-1は
   公開JSONで機械可読タグを確認できたが、この2つは手書き静的HTMLで生成器が見当たらず、タグ自体が
   存在しない）。オーナー確認が要るか実装セッションの判断に委ねるかを工程2着手時に決める
2. 投票専用の立場3択（表示用4立場とは別物）に「条件付き・改善要求」に対応する選択肢が無い。
   連動表示の「選択中の立場」(4種、閲覧用)と「投票」(3種、独立)を混同しないこと
3. 立場の配色が2系統（表示用と投票・潮目用）ある。連動表示でどちらに寄せるか工程3で決める
4. 一次資料クイズ7問はclaim-auditと同じFACT_CHECKS7件の別の見せ方であることを確認済み（未確定事項ではない）
5. 理由からX投稿を開く機能（tax追加機能相当）はbukatsu-chiikiで最大43理由と規模が大きい。
   6工程の必須要件にせず、着手する場合は独立工程として計画すること
6. 予想問題②「強い表現がいちばん多い論点」の正解データ照合（taxのQ1/Q2で見つかった数値誤りの
   ような問題が無いか）は本パスでは未実施
7. `scripts/build_bukatsu_arena.py`のうちSTANCE_GLANCE・bukatsu-background(年表)・bukatsu-check
   パネルをどの関数が組み立てているか、`refresh_adapters/`の専用アダプタの実体、
   `verify_builder_rebuildability.py`のbukatsu-chiiki対象が何かは未確認。工程2で実装前に読むこと
   （論点ボタン・立場ボタン・山の描画・論点本文切替を担うJS関数群`issueTabs()`/`buildModes()`/
   `morphTo()`/`render()`/`drawPanel()`は特定済み、スキーマリファレンスの比較節を参照）

## 完了条件（工程1）

どの論点にも出所と表示先がある：済み（同梱JSON）。確認されていない内容を補っていない：済み
（機械可読タグは公開JSONを直接読んで確認、無タグの項目は`_inferred`のまま残し空欄を捏造していない）。
残す機能の一覧がそろっている：済み（上記「そのまま維持する既存機能」）。

## 次にすること

工程2（更新に耐える土台）着手。まず`scripts/build_bukatsu_arena.py`・`refresh_planet_section.py`・
`update_bukatsu_tide.py`・`build_bukatsu_process_sections.py`を実装前提で読み、
[6工程の実装計画](../../configs/prompts/20260922_growth-bukatsu-chiiki-connected-layout.md)の工程2チェックリストへ進む。
