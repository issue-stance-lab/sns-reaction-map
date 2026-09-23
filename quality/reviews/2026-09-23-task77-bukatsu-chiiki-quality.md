# 課題77 — bukatsu-chiiki連動表示・工程5（表示・既存機能・次回更新の3方向からの検証）実装記録

記録日: 2026-09-23。[6工程計画](../../configs/prompts/20260922_growth-bukatsu-chiiki-connected-layout.md)の工程5。
[工程4の記録](2026-09-23-task77-bukatsu-chiiki-integration.md)の続き。消費税版の同じ位置づけの記録:
`2026-09-22-task77-consumption-tax-quality.md`。

## 結論（先に）

**次回の定期データ更新で連動表示が壊れる重大な欠落を発見し、修正した。** 山なみ全テーマ共通の
`scripts/refresh_planet_section.py`の仕上げ処理が、連動表示の再適用を消費税テーマだけに
決め打ちしており、bukatsu-chiikiを含む他テーマでは（エラーにならないまま）何もしていなかった。
公開判断の前に見つけられたため、公開後の事故を未然に防げた。この修正を含め、計画書の検証表
11項目はすべて確認・合格した。

## 重大な発見と修正: 次回更新で連動表示が再適用されない

### 何が起きていたか

`scripts/refresh_planet_section.py`（「山」の区間を最新データで作り直す、山なみ全10テーマ共通の
スクリプト）の仕上げ処理（旧727〜728行目）:
```python
from consumption_tax_connected import apply as connect_page
new_html = connect_page(new_html, topic=topic)
```
このファイルには本来「テーマごとに違う処理を呼び分ける」対応表（`TOPIC_ENRICH`・
`TOPIC_METHOD_TEXT`）が既にあるが、連動表示の再適用だけはこの仕組みを使わず、消費税の関数を
直接名指ししていた。呼ばれた`consumption_tax_connected.apply()`は「自分のテーマ以外なら
何もしない」という安全装置を内蔵しているため、bukatsu-chiikiでこのスクリプトを実行しても
エラーにはならず、**連動表示側が気づかれないまま素通りされる**状態だった。

一方、`scripts.bukatsu_connected.apply()`を実際に呼べる経路は`refresh_adapters/bukatsu.py`の
`_build_once()`（`refresh_topic.py --prepare-promotion`/`--promote`からのみ到達）だけで、
その出力HTMLは独自性検査の見積り用にしか使われず、`docs/`へ書き込まれる実経路
（`DATA_REFRESH.md`のbukatsu-chiiki定期更新手順、ステップ6・10・11）には含まれていない。
つまり**通常の定期更新経路のどこからも`bukatsu_connected.apply()`が呼ばれない**という、
コード上明確な欠落だった（実機調査で発見。詳細はコミット履歴のsubagent報告を参照）。

### 何が問題だったか

工程1〜4自体（このworktree内の候補生成・検証）は正しく動く。しかし公開後、次にbukatsu-chiikiの
定期更新（課題69で確立した手順）が実行されると、「山」の中身（論点の件数等）は新しくなるのに、
連動表示側（読書面の年表・理由・件数プレースホルダ）は**古いまま取り残される**リスクがあった。

### 修正内容

`scripts/refresh_planet_section.py`に`_apply_connected_display(topic, html)`を新設し、
テーマごとに正しい`apply()`を呼び分ける形にした。
```python
def _apply_connected_display(topic: str, html: str) -> str:
    if topic == "consumption-tax-cut":
        from consumption_tax_connected import apply as connect_page
        return connect_page(html, topic=topic)
    if topic == "bukatsu-chiiki":
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from scripts.bukatsu_connected import apply as connect_page
        return connect_page(html, topic=topic)
    return html
```
`bukatsu_connected.apply()`は内部で`from scripts.bukatsu_connected_content import ...`という
絶対importを使うため、`scripts/`自体（既存の25行目で追加済み）だけでなく**リポジトリ直下**も
sys.pathに無いと`ModuleNotFoundError: No module named 'scripts'`になる。これは実機で
`python3 scripts/refresh_planet_section.py ...`と同じ実行条件を再現して確認した（`cwd`を
リポジトリ外にして`sys.path`の混入を排除するテストと、実際の呼び出し形そのままのテストの
両方で再現・修正を確認）。消費税側のbare importは変更していない。

他テーマ（henoko・bike・constitutional・ai-copyright・nickname・elderly・fukushuto・koshitsu）は
どちらの分岐にも該当せず、修正後も`return html`（無変更）のまま、修正前と同じ挙動を保つ。

### 修正の検証

- `tests/test_bukatsu_connected_refresh.py`（新規、5件）: ①有効化済みページへ再適用しても
  検査が通り冪等であること、②未公開ページを勝手に有効化しないこと、③無関係テーマは無変更のこと、
  ④非公開正典を使わず`bpd.build()`を公開データへ差し替えて実際の`refresh()`経路を通し、
  連動表示が失われないこと、⑤2回連続の`refresh()`が冪等であることを確認。
- 既存の消費税側回帰検査`tests/test_consumption_tax_connected_refresh.py`（6件）を再実行しOK
  （この修正が消費税の挙動を壊していないことを確認）。
- 既存の`tests/test_bike_planet_refresh.py`（7件、bike-blue-ticketの定期更新回帰検査）を
  再実行しOK。
- 山なみ形式の全10テーマで`scripts/verify_theme_page.py {topic}`を再実行し、全てNG 0件。
- プロジェクト全体のテスト（120ファイル・1103件）を再実行しOK（skipped=4）。

## 検証表（計画書の11項目）

| 検証 | 結果 |
|---|---|
| 内容と数字 | `verify_number_provenance.py`OK（拾った161／説明できた161／説明できない0）。`verify_theme_page.py`の件数・母数・同じ数字は1回だけ、いずれもOK |
| 実機 | 320/375/1280pxで7論点×5表示（すべて＋4立場）=35通り×3幅=105通りを実機で一巡し、横はみ出し0件・コンソールエラー0件（Playwright、`tests/test_bukatsu_connected_quality_browser.cjs`） |
| 操作 | キーボード（Enterで選択）・連続切替・動きを減らす設定（`reducedMotion:'reduce'`で即時反映を実測）・論点リンク（授業節・issue-cards）・戻る/進む（`history.back/forward`）を実機で確認 |
| 図解・X投稿 | 7枚の画像をHTTP HEADで200確認、7論点×2件=14件の投稿リンクとフォールバックリンクの対応を確認。埋め込みは`<details>`の外に編集部メタ文が常に見える設計（工程3から変更なし） |
| 投票 | 論点7×投票専用立場3=21通り全部を実クリックし、送信された`choice_idx`（0〜20）・localStorage・画面表示ラベルが期待どおりであることを確認（`tests/test_bukatsu_connected_vote_browser.cjs`）。本番Supabaseへの実送信は0件（`/functions/v1/cast-vote`だけをテスト応答へ差し替え）。投票操作で山なみ側の選択状態が変わらないことも確認 |
| 引用・授業 | 授業節の6論点リンクは新設のhashchange統一で論点選択へつながることを確認済み（工程4）。bukatsu-chiikiには消費税版のような専用の「引用コピー」機能は無く、この項目は該当なし。印刷は全テーマ共通の`topic-modern.js`/`topic-modern.css`（工程4で発見・訂正済み）がそのまま動作し、連動表示の新パネルは印刷対象外（`.classroom-section`以外を隠す既存CSSの対象内） |
| JavaScriptなし | `#fallback`は連動表示の適用前後でバイト単位で完全に同一（`apply()`は読むだけで一切書き換えない）ことを確認。既存のJS無効時の読める状態はそのまま維持されている |
| 次回更新 | 上記「重大な発見と修正」のとおり。修正後は実際の`refresh()`経路で連動表示が失われないことをテストで確認 |
| 入力が変わる場合 | 最多論点(教員の働き方)と最少論点(地域格差)の件数を入れ替えた隔離データで、読書面は7論点分そろって追従し、投票のVOTE_ISSUES/STANCES/choiceIdx式（バイト単位）は変わらないことを確認（`tests/test_bukatsu_connected.py::test_display_adapts_to_changed_counts_while_vote_payload_stays_fixed`） |
| 他テーマ | 今回`refresh_planet_section.py`という共有ファイルに手を入れたため特に重点確認。山なみ全10テーマで`verify_theme_page.py`・既存の消費税/bike回帰検査を再実行しOK。bukatsu-chiiki固有のファイル（`bukatsu_connected*.py`・bridge.js・CSS）は他テーマから一切参照されない |
| 未再読論点 | 地域格差・その他を実機で確認。「まだ編集部が投稿を1件ずつ読み直していません」という断り書きのみが出て、NaN/undefined/Infinity等の不正な値が出ないことを確認（35通りの一括スイープ含む） |

## 新規に追加した回帰検査

- `tests/test_bukatsu_connected.py`: 1件追加（計16件）。件数・順位が変わっても表示が追従し
  投票の保存式は変わらないことを確認。
- `tests/test_bukatsu_connected_refresh.py`（新規、5件）: 上記「重大な発見と修正」参照。
  非公開正典を使わず、公開データだけで`refresh()`の実経路を検証できる。
- `tests/test_bukatsu_connected_vote_browser.cjs`（新規、Playwright）: 投票21通りの実クリック検証。
  `BUKATSU_CONNECTED_URL`環境変数にローカル候補のURLを渡して実行する
  （消費税版`test_consumption_tax_connected_page_browser.cjs`の投票検査部分と同じ手法）。
- `tests/test_bukatsu_connected_quality_browser.cjs`（新規、Playwright）: 実機表示・動きを
  減らす設定・キーボード・未再読論点の回帰検査。同じく`BUKATSU_CONNECTED_URL`が必要。
  いずれもCIには組み込まず（ローカル候補サーバーが要るため）、消費税版の`.cjs`群と同じく
  手元での再実行を前提とする。

## 範囲外・確認できなかったこと

- 潮目カード・claim-auditの「実際の生成スクリプトを走らせての次回更新確認」は、
  `update_bukatsu_tide.py`・`build_bukatsu_process_sections.py`がPLANET_SECTIONの外側だけを
  書き換える設計であることをコードで確認したのみで、実行そのもの（非公開正典と外部書き込みを
  伴うため）は行っていない。次回の実データ更新時に確認する。
- 印刷プレビューの見た目（PDF化してのテキスト抽出・A4に収まるか等）は、消費税版のように
  `pdftotext`/`pdfinfo`を使った内容検証までは行っていない。ボタンを押すと`window.print()`が
  呼ばれ、対象が`.classroom-section`に絞られる既存CSSが適用されること（構造的に正しいこと）の
  確認にとどめた。

## 次にすること

工程6（完成版の確認・公開判断）。オーナーへ実データの完成版と検証結果一式を提示し、公開の判断を
受ける。公開時は`.claude/skills/release/SKILL.md`の手順に従う。
