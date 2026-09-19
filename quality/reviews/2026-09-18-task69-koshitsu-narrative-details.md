# 課題69 詳細: 皇室典範（koshitsu-tenpakai）の「議論の中心」追加と起承転結型への再編（2026-09-18）

`tasks/task-69.md` から400行上限のため切り出した（2026-09-19）。

### 2026-09-18 koshitsu-tenpakai: オーナー指摘でヒーロー内「議論の中心」を追加（本番反映済み）

公開後、オーナーが実際の画面を見て「他のテーマにはある『議論の中心』が無い」と指摘
（fukushutoのスクリーンショット添付）。他の山なみテーマ（bukatsu-chiiki・fukushuto・
constitutional-amendment・consumption-tax-cut）はヒーロー直下に最大論点の要約
「議論の中心」を持つが、皇室典範の2026-09-13候補には最初から含まれておらず、
現行ページとの差分比較（both-sides-missing）では気づけなかった項目だった。

`configs/koshitsu-tenpakai-reaction-map.json`のarena.issue_blocks全5件に
conclusion（headline/detail）を追加。文言は各論点の理由内訳（islands）で最も多い
カテゴリを根拠にした。`apply_koshitsu_conclusion()`を新設し、公開JSONの最大論点に
対応するconclusionをヒーローのlead直後へ差し込む（初回挿入・以後の差し替え両対応、
最大論点が入れ替わっても壊れないよう5論点分すべて用意）。

**確認方法**: ローカルの/tmpに直接置くと画像・フォントが読み込めず見た目が壊れて
見えた（[[feedback_artifact_standalone_page_preview]]と同型の罠）。作業ツリーの
`docs/`配下に一時ファイルを置いて自作サーバーで配信し、実際のアセットが読み込まれる
状態でオーナーと一緒にスクリーンショットを確認してから公開した。

標準検査4種・unittest 970件・run_public_checksいずれもNG0件、本番反映後にブラウザで
実ページを確認済み。作業ツリー（`../isa-wt-koshitsu-conclusion`）は削除済み。

**教訓**: 差分ベースの点検（現行ページと再生成結果を比較）は「両方に無い要素」を
検出できない。他テーマとの横並び比較（画面を直接見比べる）でしか見つからない
見落としがある。bike-blue-ticket・constitutional-amendmentの着手前にも、
他4テーマとページ構成を横並びで確認する価値がある。

### 2026-09-18 koshitsu-tenpakai: オーナー指摘「あっちこっち行っていそう」で起承転結型へ再編（本番反映済み）

オーナーが「皇室典範テーマもどうもあっち行ったりこっち行ったりしていそう」と指摘
（fukushuto・consumption-tax-cutで既に直した「構成が行ったり来たりする」問題と同種の
懸念）。fukushutoの現行構成と直接比較し、2つの問題を確認した。

1. 「論点ごとの図解とX投稿」が山（対話パネル）とは別セクションになっており、
   山を押しても図解は出ず、ジャンプリンクで画面下まで飛ばす構造だった
   （fukushutoが再編前に持っていた重複と同型）。
2. 一次資料照合（koshitsu-audit）が資料系セクション群（クイズ・資料にあるのに・
   編集部横断整理）から離れ、投票の後ろに取り残されていた。

対応: ①論点の図解画像を各論点の詳細パネル（`extras-{id}`、山を押したときにJSが
`innerHTML`で読み込む唯一の場所）へ差し戻す`apply_koshitsu_landing_images()`を新設
（6論点中3論点は詳細パネル自体が無かったため新設）。②モーダル拡大表示のクリック
判定を、静的な`querySelectorAll+forEach`からイベント委譲（`closest()`）へ変更
——動的に挿入した画像はページ読み込み時に存在しないため静的判定では反応しない
（fukushutoの同じ修正と同型）。③koshitsu-auditセクションをissue-cardsより前
（`PLANET_SECTION_END`直後）へ移動し、資料系4セクションが連続するよう並べ替えた。
④issue-cardsから重複した画像を削除、見出しを「論点ごとの図解とX投稿」→
「論点ごとのX投稿」に変更（位置は変えていない）。

**作業中の訂正**: セクション移動の際、`#ocean`・`#editorial`もPLANET_SECTION外だと
誤認し、koshitsu-auditを両者の間へ移動しようとしたが、実際はどちらもPLANET_SECTION内
（山なみジェネレータが毎回まるごと作り直す領域）だった。`build_koshitsu_arena.py
--check`の冪等性検査（「landing-panelが6件必要なのに0件」）が本番反映前に検出、
`html.index()`で実位置を確認してから正しい位置（PLANET_SECTION_END直後）へ
やり直した。詳細は[[reference_planet_regen_wipes_hand_edits]]に追記済み。

標準検査4種・unittest 970件・run_public_checksいずれもNG0件、ブラウザで
山クリック→画像表示→モーダル拡大まで実地確認済み。作業は
`task/koshitsu-narrative-restructure`ブランチへコミット済み（`23d453b`）、
mainへのマージ・本番反映はこれから。
