# 課題54 段階11：総合監査（2026-09-15）

オーナーから「10テーマが揃ったので、最後の総合監査」の指示を受け、工程表の段階11
（10テーマ・トップ・sitemapの総合監査 → CEO承認 → 公開）のうち、**監査**を実施した。
一般公開（CEO承認）はこの記録を提示したうえでオーナーに確認する。

## 実施した検査と結果

| 検査 | 結果 | 備考 |
|---|---|---|
| `python3 -m unittest discover -s tests` | OK（970件、4件skip） | |
| `verify_theme_page.py`（全11テーマ、builder_rebuildability込み） | NG 0件 | 「注意」2件（bukatsu-chiiki・elderly-license-revocationの論点数カウント方法。既知の仕様） |
| `verify_number_provenance.py`（全11テーマ） | NG 0件 | 数字の出所すべて説明可能 |
| `verify_public_registry.py --against-private` | OK | 10テーマの公開データが非公開正典と完全一致 |
| `verify_page_originality.py` | OK | 11ページとも使い回しなし |
| `test_domain_migration.py` | OK（10件） | 新ドメイン統一・canonical/OGP/sitemap/robots/CNAME/CORS許可ホストすべて検査対象 |
| `verify_top_page.py` | **NG** | `collect_at` 期限超過8テーマのみ。[project_refresh_waits_for_task5463]の既知の許容状態（収集は課題54・63完了後）で、今回の監査対象外 |
| `verify_adoption_registry.py` | 当初**NG** → 対応し解消 | 下記「課題68の解消」参照 |
| `verify_reread_headroom.py` | 警告4件（exit 0） | bukatsu-chiiki「受け皿・指導者」39%・「費用・家庭負担」38%、consumption-tax-cut「減税の対象範囲」32%・「減税の効果」31%（上限40%）。いずれも現時点は合格域内だが、次回収集前に追い読みが要る |

sitemap.xml・robots.txt・docs/CNAMEを目視確認。10テーマ+about+disclaimer等が新ドメイン
`https://sns-reaction-map.jp/` で統一されており、旧ドメイン文字列の残存なし。

## 本番ブラウザ確認

`https://sns-reaction-map.jp/` トップと `koshitsu-tenpakai-reaction-map.html`（直近公開・9/15反映）を
実機相当で確認。コンソールエラー0件、375px幅で横スクロールなし、進捗バー・ヒーロー・一次資料照合
セクションとも正常表示。他9テーマは機械検査（上表）で担保し、個別のブラウザ確認は割愛した。

投票APIのCORS preflightを本番Supabaseエンドポイントに送り、
`access-control-allow-origin: https://sns-reaction-map.jp` を確認（技術的な疎通はOK）。
**実際に1票投じてやり直しボタンまで動く目視確認は今回も未実施**（課題55の段階0-1から持ち越し）。

## 課題68の解消（ついでに発見・対応）

`verify_adoption_registry.py` がNGだったため`build_adoption_registry.py --check`で調べたところ、
課題68が報告していた **ai-copyright** に加えて、**consumption-tax-cut・koshitsu-tenpakai** も
同種の指紋不一致があると判明した（同スクリプトは`require()`で最初のNGを検出した時点で打ち切る実装のため、
ai-copyright以外はこれまで一度も報告されていなかった）。

3テーマとも `public_sha256` のみの変化（koshitsu-tenpakaiのみ `canonical_file` も変化。ただし
THEMES.yamlの現行`sample_file`と一致しており、9/13の候補統合を正しく反映しているだけと確認）。
`records`件数はいずれも無変化、`decision_seed`・`scope_config`・`cohorts`も無変化。3テーマとも
課題54の正規の山なみ移行手順（一次資料照合・編集部の横断整理→independence_gate通過→標準検査→
本番反映）を経た承認済みの変更であり、`build_adoption_registry.py`（「追加・削除・再分類は行わない」
照合専用ツール）による機械的な指紋再集計だけで解消できると判断した。

`task/task68-adoption-registry` で再生成・`verify_adoption_registry.py`をOK化・
`test_adoption_registry.py` 12件OKを確認し、本番反映した。詳細は
[archive/tasks/task-68.md](../../archive/tasks/task-68.md)。

## Search Console（未達）

段階11の完了条件「Search Consoleで新ドメインの最新版取得を確認」を`scripts/fetch_gsc_metrics.py`で
自動確認しようとしたが、**GSC APIが403（`User does not have sufficient permission for site`）を返し取得できなかった**。
`--site-url`の既定値は新ドメインに正しく向いている（課題55の修正は生きている）ため、コード側の問題ではなく、
OAuth認証がこの新ドメインのSearch Consoleプロパティに対する権限を持っていない状態と見られる。
OAuthの再認証・権限確認はオーナー操作（`OPERATIONS.md`の役割分担）のため、この監査では解消できなかった。

課題55の記録によれば2026-08-31時点でSearch Consoleへのsitemap登録・検出ページ数16件確認は
済んでいる（段階5-1）。「4週間、週1回インデックス状況を見る」（段階5-3）は8/31起点でまだ経過していない。

## 未確認・持ち越し事項（総合監査の限界）

- Search Consoleの最新インデックス状況（上記、API権限エラーで自動取得不可。オーナー操作が必要）
- 投票の実クリック確認（CORS疎通はAPIで確認済みだが、実際に1票入れる目視確認は未実施）
- bukatsu-chiiki・consumption-tax-cutの編集再読の余裕が40%上限に接近（現状は合格域内。次回定期収集の前に追い読みが必要）
- 憲法改正の追加659件の独立確認は別途継続中（課題54本体の記述どおり、段階11の対象外）
