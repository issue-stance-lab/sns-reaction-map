# 課題57 段階4：生成AIと著作権を公開データJSONへ接続

作成日: 2026-08-31
状態: 接続完了。一般公開は未実施

## 結果

- 論点カードの出所を `data/public/themes/ai-copyright.json` に変更した。
- ヒーロー、注目ポイント、反応マップの母数・見出し・代替テキスト、論点アトラス、詳細データの論点別・立場別集計を、候補公開JSONから貼り直す後工程を追加した。
- アリーナの点データは個々の投稿の要約とURLが必要なため、候補正典から生成する。その正典から作った同じ候補公開JSONで、ページ上の集計表示を確定する構成にした。

## 検査

- 公開候補の実地生成: 公開JSONとページの意見数1,924件が一致
- 承認用マニフェスト: ページとアリーナデータを含む22ファイルを固定
- `verify_public_registry.py --public-only`: OK
- `verify_theme_page.py ai-copyright`: NG 0件
- `verify_number_provenance.py ai-copyright`: NG 0件
- 全unittest: 335件成功

公開候補の作成までで止めており、公開ページへの反映、push、デプロイは行っていない。
