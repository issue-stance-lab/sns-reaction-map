# 憲法改正（constitutional-amendment）データ補充＋意見判定の追加 — 2026-08-08

このファイルをそのまま新しいセッションに貼って実行する。

> **このプロンプトは `20260808_constitutional-amendment-refresh.md` を置き換える。**
> 収集の手順は同じだが、分類器の更新と既存データの再分類が加わる。古い方は実行しないこと。

---

## コンテキスト

あなたは「SNS反応まっぷ」プロジェクトのハブAI（Claude Code）です。

- リポジトリ: `/Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator`
- 正典: `DATA_REFRESH.md`（データ更新の手順）/ `LOOP.md` ⓪（作業場所の確保）
- テーマ台帳: `THEMES.yaml` / データ台帳: `DATA_SHEET.md`

## なぜこの作業をするか

11テーマのうち、**憲法改正と辺野古の2本だけ「意見かどうかの判定」を持っていない**。
他の9テーマは「収集した中から意見だけを抜いて数える」形だが、この2本は収集した全件を
そのまま数えている。そのため同じ土俵で比較できず、ニュースのURL共有が「中立」に
混ざったまま賛否の比率になっている。

憲法改正は賛否のラベル（改正推進 / 慎重・反対 / 手続き重視 / 中立）が他テーマと同じ形で
すでに機能しているので、**足りないのは意見判定だけ**。今日が収集期限なので、
新規収集と既存データの作り直しを1回でまとめる。

## タスク（3つ）

1. 分類器に「その他」論点と `is_relevant` / `is_opinion` を追加する
2. 予定どおり収集する（`--promote` は付けない）
3. 既存の正典646件を新しい分類器で分類し直し、データ台帳で3つの合計が一致することを確認する

**必ずこの順番で行う。** 分類器を先に直さないと、新規分だけ新しい形・既存分は古い形という
混ざったファイルができる。

## 前提条件（着手前に確認）

- [ ] 外付けディスク `/Volumes/HD-LE-B` が接続されている（未接続だとバックアップ地点で必ず止まる）
- [ ] 専用の作業ツリーを作る（共有ツリーで作業しない）

---

## 手順

### 1. 作業ツリーを用意する

何をするか: 他セッションとファイルを取り合わないよう、専用の作業用コピーを作る。

```bash
cd /Volumes/M2-WorkSpace/Projects/副業/issue-stance-aggregator && git worktree add ../isa-wt-constitutional -b task/constitutional-opinion-20260808
```

成功の形: `Preparing worktree` と `Switched to a new branch` が出て、`../isa-wt-constitutional` ができている。

### 2. 非公開の正典データを復元する

何をするか: Git管理外（gitignore対象）の本文付きデータを、バックアップから作業ツリーへ展開する。
**これをしないと収集は走っても検査で落ちる。** 不足していても `git status` には出ない。

```bash
cd ../isa-wt-constitutional && tar xzf "$(ls -t /Volumes/HD-LE-B/issue-stance-private-backups/private-data-*.tar.gz | head -1)" -C . --exclude=manifest.json && python3 -c "import yaml,os; th=yaml.safe_load(open('THEMES.yaml'))['themes']; print('欠落:', [v['sample_file'] for v in th.values() if not os.path.exists(v['sample_file'])])"
```

成功の形: `欠落: []`（空のリスト）。1本でも名前が出たら先に進まない。

### 3. 収集ツールを動かせるようにする

何をするか: `node_modules`（収集に使う Playwright 一式）も gitignore 対象で作業ツリーに入らないので複製する。

```bash
cp -R ../issue-stance-aggregator/node_modules .
```

成功の形: 無言で終わる。省くと収集が最初の疎通確認で `Cannot find package 'playwright'` で止まる。

### 4. 分類器を更新する（本作業の中心）

対象ファイル: `scripts/classify_constitutional_arena_hermes.py`

**手本にするファイル**: `scripts/classify_bukatsu_arena_hermes.py`
部活動テーマは同じ Hermes 方式で意見判定を持っている。プロンプト文・出力例・
`parse_response()` の後処理を、このファイルの構造に合わせる。

#### 4-1. `ISSUES` に「その他」を追加する

```python
ISSUES = {
    "改憲全般",
    "9条・自衛隊",
    "緊急事態条項",
    "国民投票・広告",
    "政党・発議手続き",
    "情報・議論の質",
    "その他",          # 追加
}
```

**なぜ**: 現在は逃げ道がなく、分類できない投稿が既存6論点のどれかに押し込まれている。
なお `STANCES`（4つ）は**変えない**。選択肢の数が変わると読者投票の選択肢とずれる。

#### 4-2. プロンプトに判定ルールを足す

現在のプロンプトは「情報共有だけ、文脈不足、論点判定不能は『情報・議論の質』『中立』」と
指示している。**これが問題の原因**で、「議論の質を論じている意見」と「ただのニュース共有」が
同じ箱に入っている。次のように分ける。

- `is_relevant`: 憲法改正、9条、緊急事態条項、国民投票、改憲発議、政党の改憲姿勢に
  関係すれば `true`
- `is_opinion`: 投稿者自身の評価・主張・懸念・提案が読み取れる場合だけ `true`
- ニュース共有・見出しの転載・告知だけなら `is_relevant=true` / `is_opinion=false` /
  `stance` は「中立」
- 無関係なら `is_relevant=false` / `is_opinion=false` / `main_issue` は「その他」/
  `stance` は「中立」
- 「情報・議論の質」は、**議論のされ方そのものを論じている意見**にだけ使う
  （例: 「報道が争点を伝えていない」「印象論ばかりで中身がない」）。
  単なる情報共有をここに入れない

出力例（JSON）にも `is_relevant` と `is_opinion` を含めること。

#### 4-3. `parse_response()` に後処理を足す

`classify_bukatsu_arena_hermes.py` の 87〜95行目と同じ整合処理を入れる。

- `is_relevant` / `is_opinion` を `bool()` で正規化する
- `is_relevant` が false なら `is_opinion` も強制的に false にする
- `is_opinion` が false なら `stance` を「中立」に寄せる

#### 4-4. 集計出力に意見件数を出す

`write_markdown()` で、関連件数と意見件数を出すようにする（部活動と同じ）。

**成功の形**: `python3 -c "import runpy; v=runpy.run_path('scripts/classify_constitutional_arena_hermes.py'); print(sorted(v['ISSUES']), sorted(v['STANCES']))"` が
7論点・4スタンスを表示する。

### 5. 収集・分類・更新回保存を実行する

何をするか: 疎通確認 → 全検索語で収集 → 重複判定 → 試験分類10件 → 全件分類 → 検査 →
更新回保存 → バックアップ＋復元検査、までを1コマンドで行う。
手順4を先に済ませてあるので、新規分は最初から新しい形で分類される。

```bash
python3 scripts/refresh_topic.py --topic constitutional-amendment --date 2026-08-08 --backup-dest /Volumes/HD-LE-B/issue-stance-private-backups
```

成功の形: `social-samples/updates/constitutional-amendment/2026-08-08/` が作られ、
`data/verification/updates/` に仮名化サマリが保存され、`THEMES.yaml` の
`last_refresh_attempt_at` と次回 `collect_at` が更新される。

**`--date` には実際に収集した日を渡す。** この文書に書かれた予定日をそのまま渡さない。
日付がずれたまま進めると検査に掛からず、次回更新の期限計算が狂う。

失敗した場合: バックアップが失敗したら更新回は確定せず `collect_at` も進まない。
**期限を手で進めない。** 失敗のまま残し、`verify_top_page.py` の期限超過NGを残す。

> **想定される警告**: 手順4-1で「その他」を足したため、既存正典のラベル集合は
> 新しい分類器の集合に収まる（広げる方向の変更）。`taxonomy_continuity` は通るはず。
> ここで止まったら、ラベル名の綴りが違っている可能性が高いので、エラーメッセージの
> `unknown_issues` / `unknown_stances` を読んで直す。

### 6. 既存の正典646件を分類し直す

何をするか: 既存データにも `is_relevant` / `is_opinion` を持たせ、テーマ内で
形をそろえる。**ここまでやらないと、新規分だけ判定つき・既存分は判定なしの
混ざったファイルになる。**

対象: `social-samples/constitutional_amendment_hermes_arena_classified.json`（646件）

分類スクリプトの引数は `--help` で確認する。実行前に必ずバックアップを取る。

```bash
cp social-samples/constitutional_amendment_hermes_arena_classified.json /tmp/constitutional_before_reclassify.json
```

成功の形: 646件すべてに `classification.is_relevant` と `classification.is_opinion` が入る。

確認コマンド:

```bash
python3 -c "
import json,collections
d=json.load(open('social-samples/constitutional_amendment_hermes_arena_classified.json'))
c=[r.get('classification',{}) for r in d]
print('総数', len(d))
print('判定なし', sum(1 for x in c if x.get('is_opinion') is None))
print('関連', sum(1 for x in c if x.get('is_relevant')), '意見', sum(1 for x in c if x.get('is_opinion')))
print('論点', collections.Counter(x.get('main_issue') for x in c if x.get('is_opinion')).most_common())
print('賛否', collections.Counter(x.get('stance') for x in c if x.get('is_opinion')).most_common())
"
```

成功の形: `判定なし 0`。意見件数は他テーマの実績（意見率67〜92%）から**450〜580件程度**が
見込み。ここから大きく外れたら分類プロンプトを見直す。

**数字が減るのは正常。** ニュース共有が外れるため、母数が646から減り、賛否の比率も動く。
これは劣化ではなく、他テーマと同じ数え方に揃えた結果である。

### 7. 検証データを作り直す

何をするか: 本文を含まない仮名化サマリ（Git管理する側）を、新しい正典から作り直す。

```bash
python3 -c "
from pathlib import Path
from scripts.verification_data import write_verification_file
write_verification_file(Path('social-samples/constitutional_amendment_hermes_arena_classified.json'), Path('data/verification/constitutional-amendment.json'))
print('done')
"
```

成功の形: `done` と出て、`data/verification/constitutional-amendment.json` の差分が出る。

### 8. データ台帳を作り直して一致を確認する

```bash
python3 scripts/build_data_sheet.py && grep 憲法 DATA_SHEET.md
```

成功の形: 憲法改正の行で、**論点の合計・賛否の合計・意見の件数が同じ数**になっている。

> マップの点（422）だけは合わない。これは公開ページ側が旧ページ埋め込みの古いデータを
> 使っているためで、正典からは再現できない（TASK_BOARD 課題29）。
> **この解消は次のセッションで行う。**
> 指示は `configs/prompts/claude-code/20260808_denominator-opinion-only.md` の
> **第4章「憲法改正 — マップ生成スクリプトを新設する」**。
> 第4章はこのセッションの完了（判定なし0件）を前提にしているので、
> 完了報告に**再分類後の意見件数**を必ず書くこと。

### 9. テストを通してコミットする

```bash
python3 -m unittest discover -s tests -q && python3 scripts/verify_top_page.py && python3 scripts/verify_theme_page.py
```

成功の形: unittest が `OK`、2本の検査スクリプトが exit 0。

通ったらコミットして push、main へPRを出す。コミット対象:

- `scripts/classify_constitutional_arena_hermes.py`（分類器）
- `data/verification/constitutional-amendment.json`（仮名化サマリ）
- `DATA_SHEET.md`
- `THEMES.yaml`

`social-samples/` 配下は非公開なのでコミット対象に入らない（gitignore済み）。

### 10. 片付ける

作業ツリーを消す前に、**そのツリーにしかない非公開ファイルを共有ツリーへ複製し、
バックアップを取り直す。**

```bash
git worktree remove ../isa-wt-constitutional
```

---

## 制約・注意

- **`--promote` を付けない。** このテーマは `migration` で、公開ページのadapterが未整備。
  今回の作業で公開ページの数字は変わらない。
- **`STANCES` を変えない。** 選択肢の数が変わると読者投票の `choiceIdx` の意味がずれ、
  Supabase Edge Function の再デプロイが必要になる（皇室典範で実際に発生した）。
- **`scripts/inject_tide_widget.py` を実行しない。** 公開中のページを古いデータへ
  巻き戻す不具合がある（TASK_BOARD 課題38）。
- **`social-samples/` 配下の未追跡ファイルを消さない。** 非公開の正典は gitignore 対象で、
  古いブランチからは不要ファイルに見える（2026-08-07 に正典1,606件が削除されかけた）。
- **`git checkout -- <ディレクトリ>` を使わない。** 戻すなら自分が変更したファイルだけを
  パス指定で。
- 保護タグ（GA4 `G-K10S4YCZFH` / AdSense `ca-pub-2542211932832864` / Supabase / OGP）を壊さない。
- main への直接コミット禁止。

## 参考: このテーマの現状

| 項目 | 値 |
|---|---|
| タイトル | 憲法改正論議 |
| 正典 | `social-samples/constitutional_amendment_hermes_arena_classified.json`（646件） |
| 収集設定 | `configs/topics/constitutional.yaml`（検索語6本） |
| 公開ページ | `docs/constitutional-amendment-reaction-map.html` |
| 前回更新 | 2026-07-26（追加224件） |
| 取得期間 | 2026-06-20〜2026-07-25 |
| 分類体系 | Hermes / kimi-k2.6、6論点・4スタンス（→ 7論点・4スタンス＋意見判定へ） |
| 意見判定 | **なし**（本作業で追加） |
| ページ更新 | `migration`。`data/issue-counts/` 由来の422件を表示中 |

## 完了報告に含めること

1. 収集件数 / 重複除外後の新規件数 / 分類エラー率
2. **再分類後の意見件数と、論点・賛否の内訳**（作業前は646件・6論点）
3. 次回 `collect_at` の日付と、その根拠になった周期ルール
4. 検査で落ちた項目があればその内容（隠さず書く）
5. マップの点（422）が未解消であることの確認
6. オーナーへの依頼事項があれば1つだけ
