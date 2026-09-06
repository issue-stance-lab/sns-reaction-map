# 課題63 段階C：再読記録の共通管理

## 目的と保存先

本文を読んだ証拠を投稿単位で引き継ぎ、追加・本文変更・論点変更・意見判定変更を見つける。
台帳は `data/verification/reread/{テーマ}.json`、共通処理は `scripts/reread_registry.py`、
操作は `scripts/manage_reread_registry.py`。既存の区分・読了成果は変更しない。

初回移行は部活動・自転車・高齢者の3テーマ。全1,684件（現行意見1,587、除外97）を保持した。
残りテーマにも同じコマンドを使えるが、他テーマの既存成果を未確認のまま移行済みとは扱わない。
初回AI分類や限定確認を、本文再読として自動登録しない。

## 何を区別するか

- `snapshot_at` と `baseline_text_sha256`：共通管理へ移した時点の日時・本文版。読了の日時・本文版ではない。
- `review.evidence_quality=legacy`：従来の本文再読の記録。個別の読了日時・確認者・本文版の不明はnull。
- `review.evidence_quality=verified`：読了日時・確認者・読んだ本文の指紋・手順の識別・根拠の指紋がある記録。
- 自転車262件は既存の証拠を継承。手順は元台帳に記載されたmethodの指紋で識別し、別の手順を作ったことにしない。
- `source_date_labels`：旧資料の日付表記をそのまま保存した参照情報。複数の日付から最新日を選んで全件へ割り当てない。
- 台帳の投稿キーは投稿IDのSHA-256。新台帳へ本文・URL・投稿ID・要約・根拠本文を入れない。

`canonical_sha256` は初回スナップショットの原本全体の指紋。差分再読の登録では選んだ投稿の
基準だけを更新するため、現在の原本全体の指紋を表す欄として扱わない。
過去の台帳版と、固定対象・提出証拠を保存して更新経緯を追えるようにする。

## 日常の入口

現行原本と台帳を比較する。成功すると2種類の集計が出る。
`all_records` は意見以外も含む全投稿、`current_opinions` は現行の意見だけ。
区分の変化と読了状態は別軸なので、表示されたすべての件数を足さない。

```bash
python3 scripts/manage_reread_registry.py status --topic bukatsu-chiiki
```

`reviewed_legacy` は旧記録、`reviewed_verified` は証拠がそろった記録、`unreviewed` は未読または本文版が変わった分。
`added` / `removed` / `body_changed` / `issue_changed` / `opinion_changed` が差分。
これは人間の確認率・理解率ではない。論点が変わった場合も、旧区分を黙って新論点へ移さない。

## 差分を読む作業

1. 未読・追加・変更分のうち現行意見を固定する。必要なら `--issue` で論点を絞る。
2. 本文付き入力は外付け等の非公開保存先へ出す。対象固定では台帳の読了数は増えない。
3. 担当AIまたは人が実際に本文を読み、対象にある全件の証拠を提出する。
4. 次版台帳を作り、独立確認後に正式台帳へ採用する。原本の意見判定変更とページ公開は別工程。

以下は部活動の差分を固定する例。既存のファイル名は再使用しない。

```bash
python3 scripts/manage_reread_registry.py prepare --topic bukatsu-chiiki \
  --out /Volumes/HD-LE-B/issue-stance-private-backups/stagec-bukatsu-target.json \
  --private-input /Volumes/HD-LE-B/issue-stance-private-backups/stagec-bukatsu-input.json
```

成功すると「読む対象を固定しました: N件」と出る。0件なら新しい読了対象は作らない。
本文の入力・固定対象・提出結果は同じ作業回の証拠として一緒に保全する。

提出JSONは配列で、各要素を `post_key` と `review` にする。`review` の必須項目は
`kind=editorial_body_reread`、`evidence_quality=verified`、時差付きISO日時の`read_at`、
`reviewer_type=editorial_ai`または`human`、`reviewer`、`method_version`、読んだ本文の`text_sha256`、
根拠の`reason_sha256`、証拠の`source_file`と`source_sha256`、編集区分`bucket`。
根拠本文は非公開証拠へ保存する。値が埋まっただけでは実際に読んだことの独立証明にはならないため、
採用前に担当外の確認者が本文・根拠を照合する。

```bash
python3 scripts/manage_reread_registry.py record --topic bukatsu-chiiki \
  --target /Volumes/HD-LE-B/issue-stance-private-backups/stagec-bukatsu-target.json \
  --reviews /Volumes/HD-LE-B/issue-stance-private-backups/stagec-bukatsu-reviews.json \
  --out /Volumes/HD-LE-B/issue-stance-private-backups/stagec-bukatsu-next.json
```

成功すると次版台帳ができる。欠落・重複・対象外・本文不一致・対象固定後の台帳変更は停止する。
このコマンドは正式台帳を置換せず、ページも公開しない。新しい区分の表示は、採用時に
テーマの区分元と共通台帳を同じ証拠へ結び付け、生成検査で確かめる。

## 検査と既存ページへの接続

```bash
python3 scripts/verify_reread_registry.py --against-private
```

成功は `NG 0件`。GitHubの自動検査は本文を使わず、台帳の形式と継承元の指紋を検査する。
新ページ生成では共通台帳を読み、再読済みの本文・論点・意見判定・集合が変わっていれば停止する。
既存の課題62の読み飛ばし／増分／時期不明の基準は維持する。
固定対象での差分再読と、既存ページの過去日付に基づく未読内訳は区別する。

元の再読資料を更新した場合も指紋不一致で止まる。確認を省くために初回移行をやり直して
現在の本文を「過去に読んだ本文」と見せない。`initialize` は既存台帳の上書きを拒否する。

今回、新規の本文再読・分類変更・未採用投稿の追加・一般公開は実施していない。
段階Dは保存回と正典の採用状態、段階Eは保全・管理画面への接続を担当する。
