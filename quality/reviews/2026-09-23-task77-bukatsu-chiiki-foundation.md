# 課題77 — bukatsu-chiiki連動表示・工程2（通常更新で維持できる土台）実装記録

記録日: 2026-09-23。[6工程計画](../../configs/prompts/20260922_growth-bukatsu-chiiki-connected-layout.md)の工程2。
[内容確定書](../designs/2026-09-22-task77-bukatsu-chiiki-content-contract.md)を内容の基準とし、
[消費税版のデータ構造リファレンス](../designs/2026-09-22-task77-consumption-tax-schema-reference.md)を実装の起点にした。

## 工程着手前に確認した未確認事項（計画書「確認済みの実装上の事情」5〜7）

- **`build_bukatsu_arena.py`（1048行）の担当範囲**: STANCE_GLANCE（`stance_glance()`/`apply_bukatsu_stance_glance()`）
  だけを持つ。予想2問・`bukatsu-background`・`bukatsu-check`は別スクリプト`build_planet_page_preview.py`が
  一度だけ変換した静的内容で、この生成器は触らない。`bukatsu-background`/`bukatsu-check`という要素名は
  消費税ページにも同じ文字列で存在する共通の部品名だった（テーマ専用ではない）。
- **`refresh_adapters/bukatsu.py`の実体**: `build()`が`update_bukatsu_tide.py`を2回実行して冪等性を検査、
  `finalize()`が`build_bukatsu_arena.py`を昇格後に実行する。**`refresh_planet_section.py`はどちらからも
  呼ばれていない**（山なみ本体は通常更新で自動的には再生成されない）。連動表示は`build()`側（tax版の
  `_apply_tide()`と同じ位置づけ）へ登録し、STANCE_GLANCEより後（`finalize()`）に上書きされる領域は避けた。
- **`verify_builder_rebuildability.py`の対象**: bukatsu-chiikiの対象は`build_bukatsu_arena.py`で、
  PLANET_SECTIONは検査範囲外。**公開済みの消費税版連動表示も同じ理由でこの検査には入っていない**
  （教室節のときのような専用検査の追加はtax版でも行われていない）。同じ扱いに揃え、この検査への追加は
  今回も行わなかった。冪等性は`bukatsu_connected.py`自身の検査（下記）で見る。

## 実装したもの

- `scripts/bukatsu_connected.py`: `TOPIC="bukatsu-chiiki"`、3段構えのテーマ限定ガード
  （`topic!=TOPIC`／`activate or enabled(source)`／`PLANET_DATA.theme_id`一致）。
  `content_index()`が論点→資料照合ID・語られていない争点ID・共通の心配IDをIDだけで結ぶ。
  年表・制度チェック（`bukatsu-background`/`bukatsu-check`）は接続していない
  （issue_idsを持たないデータ構造のため。工程4で連動させるか判断する、計画書のとおり）。
- **決定事項（工程2で判断が必要だった1点）**: 語られていない争点4件のうち3件（sc-2/3/4）は
  `nearest_issue_id`が無い。編集部推定で論点を割り当てず、**未タグのまま**にした。
  既存の`#ocean`（海面下の表示）はもともと論点非依存でテーマ全体に表示する設計のため、
  未タグでも失われず、特定の論点の読書面にも出さない。編集部推定は行っていない。
- `scripts/templates/bukatsu_connected_bridge.js`: 山の`render/layout/land/morphTo/orbit`等は
  一切上書きしない。STANCE_GLANCE（4ボタン、表示のみで山と無接続だった）と`#modes`
  （山の立場フィルター）の両方に、既存のonclickへ追加する形でlistenerを足し、押下状態を
  常に一致させる。`#modes`は`buildModes()`実行前（`/* ---------- 初期化 ----------`直前）に
  挿し込まれるため、個別ボタンではなく`#modes`自体への委譲にした（直接付与だと空振りする）。
  `#modes`からの変更はSTANCE_GLANCE側の対応ボタンを実際にクリックさせて説明文まで揃える
  （文言を作り直すとPythonの原文と2通りに分かれるため）。`window.BukatsuConnectedMap`
  （`getState`/`selectIssue`/`selectStance`）を新設。投票（3立場・21通り）とクイズ・潮目・
  探査記録（進捗バー）の状態は独立のまま、触っていない。
- `docs/bukatsu-connected.css`: 現時点はほぼ空（押下状態の見た目は既存CSSがすでに持つため）。
  読書面の見た目（工程3以降）はここに追加する。
- `scripts/refresh_adapters/bukatsu.py`: `_build_once()`の末尾で`bukatsu_connected.apply()`を呼ぶ
  よう登録。マーカー未挿入の現行ページでは`enabled()`が偽のため無操作（今回の変更は非公開のまま）。
- **作らなかったもの**: tax版にある`consumption_tax_connected_vote.py`相当は今回は不要と判断した。
  bukatsu-chiikiの投票は`bukatsu_taxonomy.py`＋`configs/bukatsu-chiiki-reaction-map.json`という
  既存の正典を持ち、工程2では投票UIを一切変更しないため、新しいIDを注入する処理を持つ意味が無い
  （計画時点の見込みは外れていたので、当初案のファイルは作らなかった）。

## 検査

- `tests/test_bukatsu_connected.py`（9件、新規）: 他テーマ・未有効化ページへの無操作、同じ入力の
  2回適用で目印が重複しないこと、資料照合IDが論点の埋め込みと自己整合すること、未タグの語られていない
  争点が特定の論点に紐付かないこと、論点の並び替え・表示名変更で接続表が変わらないこと、
  投票（`VOTE_ISSUES`×`STANCES`＝21通り、`choiceIdx`の式）が適用前後で変化しないことを確認。
- `python3 -m unittest discover`: 全体1091件（新規9件を含む）、OK（既存スキップ4件のみ）。
  `scripts/refresh_adapters/bukatsu.py`のimportも確認。
- 実機確認（ローカルhttp.serverでこの作業ツリーの`docs/`を配信し、組み込みブラウザで確認。
  `activate=True`で作った候補を一時的に`docs/`直下へ置いて確認後、削除・コミット対象からも除外）:
  STANCE_GLANCEのボタンを押すと山が実際に動き、`#modes`側の押下状態も揃う。逆に`#modes`を押すと
  STANCE_GLANCE側の押下状態と説明文の両方が揃う（クリックを転送する方式で実現）。山のヒルを直接
  クリックする既存の論点選択（`land()`）は変更の影響を受けず従来どおり動く。コンソールエラーなし。
  この過程で1件バグを発見・修正済み（下記）。

## 見つけて直したバグ

`_bridge()`の挿し込み位置（`buildModes()`実行前）に対して、初版のJSは`#modes`の各ボタンへ
初期化時点で直接`addEventListener`していたため、まだ存在しないボタンへの登録が空振りしていた
（`#modes`を押しても山は動くがSTANCE_GLANCE側の見た目が更新されない）。`#modes`自体（常に存在する
入れ物）へのイベント委譲に直し、実機で双方向の同期を再確認した。

## 残る既知の制約（工程3以降で判断）

STANCE_GLANCEには「すべて」に対応するボタンが無い。`#modes`の「すべて」を押すと押下状態は
正しく全解除されるが、STANCE_GLANCE自身の説明文（直前に押した立場の説明）は消えない
（元々「すべて」の概念を持たない部品のため、クリック転送でも解決しない）。実害はないが、
見た目の一貫性としては工程3で扱うことを勧める。

## 完了条件の確認（計画書の工程2）

「bukatsu-chiikiの候補を同じ入力で2回生成して同じ結果になる」: `bukatsu_connected.py`自身の
冪等性は`test_same_input_does_not_accumulate_assets_or_bridges`・
`test_reapplying_to_an_already_enabled_page_replaces_the_block_in_place`で確認済み。
adapter全体（`update_bukatsu_tide.py`の实行を含む）の2回比較は、現状は無操作（マーカー未挿入）
のため素通りする。有効化後の全体2回比較は、実際に有効化する工程（3以降）で実施する。
「生成器に新しい処理が登録され、他テーマの表示が変わらない」: 登録済み（`refresh_adapters/bukatsu.py`）、
他9テーマ不変は`test_activation_is_explicit_and_other_themes_are_unchanged`で確認。

## 次にすること

工程3（3論点で中心の体験を作り、7論点へ広げる）。計画書が指定する最初の3論点は
教員の働き方(kyoin)・受け皿指導者(ukezara)・その他(sonota)。読書面（理由・投稿例・制度・資料）を
初めて作る工程のため、`consumption_tax_connected_content.py`を実装の起点にする。
