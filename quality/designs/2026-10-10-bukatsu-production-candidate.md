# 部活動の新デザイン：生成処理と公開前候補
2026-10-10。課題54。公開・main統合・投票送信は未実施。

## 実装
- 外部フォルダ14にあった試作の再生成元を scripts/bukatsu_redesign/ に移した。個人PCの絶対パスへの依存を除去。
- scripts/build_bukatsu_redesign.py が既存の検証済み部活動HTMLを読み、別フォルダにページ、授業用ページ、画像、投票クライアント、指紋一覧を生成する。
- scripts/build_bukatsu_arena.py --redesign-output <出力先> で既存生成の後に新デザインを生成できる。既存の標準生成経路は維持。
- preview は本番ホストに置いても投票を送らない。release は sns-reaction-map.jp でだけ既存Supabase設定を有効にする。GAとAdSenseはreleaseにだけ現行の保護タグを継承。
- 投票のtopic_id・7論点の順番・3立場の順番・choice_idxの計算を保持。公開時には既存の投票済み保存キーを使う。
- 本番の読書進捗はテーマ固有v2キーへ。旧isa-seen-bukatsu-chiikiのi:論点IDのみ引き継ぐ。旧クイズ等の別概念は水増ししない。確認画面は試作専用キー。
- 公開用データ契約PLANET_DATAを維持。UIの集計用JSONとの一致、各理由ボタンの件数、合計を検査する。公開検査は新デザインの理由ボタンも照合する。
- 調査条件・代表投稿の確認表示を現行から継承。「その他」は分類項目として残し、総数表記を「6つの論点＋その他」に整理。
- 説明等の参照本文・理由分類と集計データに変更があれば出力前に停止。既存候補を保持する。
- スマホの詳細推移表を表内スクロールへ修正。HTMLのdescription重複解消、旧アンカーの接続、図解・授業リンクも維持。

## 確認結果
- Python 43テスト（新デザイン13、既存テーマ・投票18、数字検査12）、投票クライアント3テスト成功。
- build_bukatsu_arena.py --redesign-output 経由で生成成功。元ページに差分なし。
- 同一入力の再生成一致、本文変更時の停止、docsへの直接出力拒否、各スクリプトの構文検査。
- 公開候補に対する verify_theme_page.py はNG0。既存の検査基準を飛ばさず、表示形式が変わった理由件数の照合のみ対応。
- SupabaseのGETを本番Originで実行しHTTP200、CORS一致、既存countsを取得。POSTは送っていない。保存成功・失敗時の挙動はモックテスト。
- ブラウザ375px・1280pxで横はみ出しなし。375pxは詳細推移を開いた状態も確認。
- 投票の選択・再読込での保存・やり直し、詳細グラフ再生、元投稿2件のiframe生成、山を選択してもscrollY同一を確認。
- ブラウザのページエラー0。撮影記録は外部16フォルダ preview/evidence/page-desktop.png。
- verify_ai_tone.py 合格。今回変更した短い公開案内文のよみやす検査は98/100、warn0。
- 継承したeditorial-source.html全体の厳格な文体検査では既存の長文・引用・文末に19警告が残る。今回の移植で原文・引用を保持した箇所で、公開文章全体の文体合格とは扱わない。

## 生成方法
リポジトリルートで実行する。

確認用の生成：
```sh
python3 scripts/build_bukatsu_arena.py --redesign-output /tmp/bukatsu-review
```
成功時は既存生成のOKと、新しいHTMLのBuilt表示が出る。/tmp/bukatsu-review/bukatsu-chiiki-reaction-map.html が確認用ページ。

公開候補の生成（公開操作ではない）：
```sh
python3 scripts/build_bukatsu_redesign.py --mode release --output-dir /tmp/bukatsu-release
```
成功時はBuilt 22 files (release); no deployment performed. と表示される。ファイル指紋はbuild-manifest.json。

## 公開前の残作業
1. オーナーが今回の候補の表示・内容を確認する。
2. 通常の更新・公開運用はまだ現行HTMLを入力にする。docsを新デザインへ置き換える際は、既存生成用HTMLの保存先とrefresh adapterの入出力を同時に切り替える必要がある。新HTMLだけをdocsへコピーして公開しない。
3. 数字の出所の全検査、全体印刷・JavaScript無効時の実機確認、継承した長文の扱いを確認する。
4. 公開時はrelease手順で承認・統合・公開確認。本番の投票POSTは実票を入れるため未実施。

現段階は「再生成できる確認用・公開用候補の準備」であり、通常更新経路の本番切替完了ではない。
