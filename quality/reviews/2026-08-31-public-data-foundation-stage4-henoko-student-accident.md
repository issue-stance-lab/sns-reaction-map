# 課題57 段階4：辺野古学生事故を公開データJSONへ接続

作成日: 2026-08-31
状態: 接続完了。一般公開は未実施

## 結果

- 論点カードの出所を `data/public/themes/henoko-student-accident.json` に変更した。
- ヒーロー、反応マップ見出し、論点別本文、注目ポイント、詳細の論点別・立場別・クロス・強度別集計を、候補公開JSONから貼り直す後工程を追加した。
- アリーナの点と投稿要約は候補正典から生成し、同じ候補正典から作った公開JSONで集計表示を確定する構成にした。
- 公開JSONが0件の論点を明示し、仮名化検証データがその行を省略する場合は、双方を同じ0件として照合するよう検査を修正した。

## 検査

- 公開候補の実地生成: 公開JSONとページの意見341件が一致
- 承認用マニフェスト: ページとアリーナデータを含む22ファイルを固定
- `verify_public_registry.py --public-only`: OK
- `verify_theme_page.py henoko-student-accident`: NG 0件
- `verify_number_provenance.py henoko-student-accident`: NG 0件
- 全unittest: 342件成功

公開候補の作成までで止めており、公開ページへの反映、push、デプロイは行っていない。
