# 検証用データ

このディレクトリは、Git管理外の `sample_file` から生成した公開可能な派生データです。
クリーンクローンとCIでは、件数・論点件数・意見数・投稿集合の包含関係をこのデータで検証します。

各レコードに残すのは次だけです。

- 投稿識別子をソルト無しで決定的に SHA-256 化した `record_id_hash`
- `main_issue`
- `stance`
- `is_opinion`
- `is_relevant`
- `confidence`

本文、URL、ユーザーID、tweet_id、要約は含めません。生成は
`scripts/verification_data.py` を使い、手編集しません。

`record_id_hash` は別マシンやCIでも同じ投稿を照合できる仮名化識別子です。
候補のtweet_idを知る第三者は収集対象だったか照合できるため、匿名化データではありません。

`updates/<theme>/<date>/` は更新回ごとの仮名化（ハッシュ化）履歴です。これは検査を再現するための
履歴であり、本文付きの `raw.json` / `classified.json` を復元するバックアップではありません。
本文付き正典と履歴は、公開Gitとは別の非公開ストレージで保全する必要があります。
