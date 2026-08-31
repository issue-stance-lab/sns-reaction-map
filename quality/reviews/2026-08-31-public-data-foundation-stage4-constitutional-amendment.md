# 課題57 段階4：憲法改正を公開データJSONへ接続

作成日: 2026-08-31
状態: 接続完了。一般公開は未実施

## 結果

- 論点カードの出所を `data/public/themes/constitutional-amendment.json` に変更した。
- ヒーロー、調査条件、議論の中心、注目ポイント、マップ見出し、詳細の論点別・立場別・強度別集計を、候補公開JSONから貼り直す後工程を追加した。
- マップの点と代表投稿は個々の投稿の要約・URLが必要なため候補正典から生成し、同じ候補正典から作った公開JSONで集計表示を確定する構成にした。

## 検査

- 公開候補の実地生成: 公開JSONとページの意見966件が一致
- 承認用マニフェスト: ページを含む21ファイルを固定
- `verify_public_registry.py --public-only`: OK
- `verify_theme_page.py constitutional-amendment`: NG 0件
- `verify_number_provenance.py constitutional-amendment`: NG 0件
- 全unittest: 337件成功

公開候補の作成までで止めており、公開ページへの反映、push、デプロイは行っていない。
