# 課題93: 山なみテーマの「後付け処理」スクリプトが再生成パイプラインから漏れていないか、他5テーマも確認する

**登録日**: 2026-09-25
**状態**: 未着手（fukushutoの定期更新作業中に発見）
**優先度**: 中（fukushutoは対応済み。他テーマで実際に古い数字が公開されているかは未確認）
**関連**: 80（副首都の画像脱落。同根の問題パターン）

## 何が起きたか

fukushutoの2026-09-24定期収集分（新規271件・意見231件）を反映する際、`build_fukushuto_arena.py`の
`apply_public_counts()`（`--public-counts-only`、`refresh_topic.py --apply-promotion`のfinalize
相当）が「論点ごとのX投稿」（`#issue-cards`、件数バッジは`fukushuto_issue_media.py`の
`build_section()`が担当する後付け区間）を再生成対象に含めておらず、`verify_number_provenance.py`
が「説明できない数字7件」でNGを出して発覚した。`fukushuto_issue_media.py`自体は
`build_fukushuto_arena.py`から一度もimport・呼び出しされておらず、初回導入時（9月下旬、
コミット`7e0f4cee`）に一度だけ手動実行され、その後の定期更新では二度と実行されない設計に
なっていた。`apply_public_counts()`内に同期処理を追加して解消した（コミット`7ecc55f1`）。

課題80（副首都の論点画像7枚が本番から消えた）と全く同じ構造的原因——**builder本体が作らない、
テーマ固有の後付け差し込み処理は、再生成のたびに古いまま取り残されるか消える**——の再発である。
DATA_REFRESH.mdの「テーマ固有の追加処理が要る場合がある」節にはこの種の見落としへの注意書きは
あるが、`#issue-cards`（「論点ごとのX投稿」機能）は同節の記述時点ではまだ存在しなかった。

## 横展開が必要な理由

同種の独立スクリプト（`grep -rln "hermes-samples" scripts/*.py`で該当）が他5テーマにも存在する。
いずれも対応する`build_*_arena.py`・`refresh_adapters/*.py`から呼ばれているかを
`grep -n "issue_media" scripts/refresh_adapters/*.py scripts/build_*_arena.py`で確認したところ
0件で、fukushutoと同じ「独立スクリプトのまま」に見える。

- `scripts/ai_copyright_issue_media.py`
- `scripts/bike_issue_media.py`
- `scripts/elderly_issue_media.py`
- `scripts/koshitsu_issue_media.py`
- `scripts/nickname_issue_media.py`

ただし、**これらのテーマで実際に本番ページの件数バッジが古いままになっているかは未確認**。
fukushutoで発覚したのは、たまたま今回`verify_number_provenance.py`が「論点ごとのX投稿」の
件数を新たに検出対象にしたため（または今回初めてこの機能を持つ状態で定期更新が回ったため）で、
他テーマでは該当機能を持つテーマ自体がまだ「初回導入後、一度も定期更新していない」可能性もある
（その場合はまだ実害が出ていない）。

## やること

1. 上記5テーマそれぞれの本番ページ（`docs/{theme}-reaction-map.html`の`#issue-cards`）の
   件数バッジと、`data/public/themes/{theme}.json`の`issues[].count`を突き合わせ、
   ずれているテーマを特定する
2. ずれているテーマがあれば、fukushutoと同じ形（`apply_public_counts()`相当の関数内で
   `{theme}_issue_media.inject()`を呼ぶ）で修正する
3. ずれていなくても、次回定期更新で同じ理由で古くなる可能性があるため、各テーマの
   builder修正は先回りして行ってよい（実害の有無に関わらず、放置すると課題80と同じ
   「気づかれるまで公開版が古いまま」を繰り返す）
