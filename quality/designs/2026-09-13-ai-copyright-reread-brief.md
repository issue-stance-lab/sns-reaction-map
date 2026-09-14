# 課題54: 生成AIと著作権「編集再読」の読む作業（別AI用の指示文）

この1枚だけで作業できる。**他の文書を読む必要はない。**
これは**読む作業と、その結果を仕組みへつなぐところまで**の指示。
つないだ後、山なみページを本番へ出す作業（生成・標準検査・`release`スキルでの反映）は別途行う。

## 何のための作業か

「生成AIと著作権」（theme_id: `ai-copyright`）を旧2D形式から新しい形（山なみ）へ出すには、
生成器 `scripts/build_planet_data.py` の**独自性の検査**（`independence_gate`、同ファイル637行目）
を通す必要がある。検査は「中身が薄いテーマの公開ページを出さない」ためのもので、
**投稿を人（編集部）が1件ずつ本文で読み直した割合**を見る。条件は実質2つ
（コード上の該当行も示す。数字だけ見て古い前提で進めないこと）:

1. **論点全体の50%以上**：`sub_issues`（＝下で選ぶ論点）に設定した論点の件数合計が、
   テーマ全体の意見数の50%以上（655行目付近 `if share < 50`）
2. **論点ごとに読み飛ばし＋増分が4割まで**：`sub_issues`を設定した論点は、その論点の中で
   「読んでいない分（読み飛ばし＋読了後に増えた投稿）」が4割を超えてはいけない
   （677行目付近 `if unread_total > 0.4 * i["count"]`）

**`tasks/task-54.md`の2026-09-13の記録に「1,300件・782件で足りる」という試算があるが、
これは以下の理由でそのまま使わない（下の「選ぶ論点」で理由と代替案を説明する）。**

## 現状（2026-09-13 実測。この文書のために新たに数え直した数字）

`social-samples/ai-copyright_hermes_classified.json`（3,812件、うち意見と判定されたものが
**2,593件**）を実際に集計した結果:

| main_issue | 件数 |
|---|---:|
| 学習データ・無断利用 | 657 |
| 利用者モラル・倫理 | 657 |
| 法制度・規制整備 | 471 |
| クリエイター保護・権利 | 303 |
| その他 | 223 |
| AI生成物の権利・創作性 | 165 |
| 技術競争・推進 | 117 |
| **合計（意見数）** | **2,593** |

`configs/planet/ai-copyright.yaml` はまだ存在しない（このテーマは今回が初めての作成）。
`data/verification/reread/ai-copyright.json`（共通台帳）も無い。無くても検査は通る
（`reread_registry`をfalseにしておけば省略される仕組み。他テーマとの体裁を揃えたい場合のみ後日作る）。

## 選ぶ論点（`sub_issues`にする4〜5論点）

### 「1,300件・782件」をそのまま使わない理由

1. **50%条件のギリギリ狙いは危険。** `tasks/task-54.md`の試算は
   学習データ・無断利用(657)＋その他(223)＋クリエイター保護(303)＋技術競争(117)＝**1,300件
   （50.13%）**——50%ラインの**0.13ポイント上**しかない。この4論点には、まだ独立確認が
   終わっていない分類修正候補が多数ある（`data/verification/editorial-adoption-current.json`の
   `topic=="ai-copyright"`で`independently_checked==false`かつ`current != proposed`が149件あり、
   そのうち88件がこの4論点の**現在の**main_issueに属し、別70件がこの4論点へ**移ってくる**提案に
   なっている）。この149件の分類確認がどちらに転んでも、合計は簡単に50%を割り得る。
   **fukushutoのブリーフが「その他を足して56.7%まで余白を作った」のと同じ理由**で、
   最初から余白を持たせる。
2. **各論点60%だけ読むのは、このテーマでは特に危険。** `THEMES.yaml`のai-copyrightは
   `collect_mode: scheduled`＝**収集が今も続いている**。60%だけ読んで残り40%を「読み飛ばし」の
   まま登録すると、条件2の4割の枠を**開始時点で使い切る**ことになり、次の定期収集で1件でも
   新しい投稿が届いた瞬間に不合格になる（`scripts/verify_reread_headroom.py`が検知する事態その
   もの。bukatsu-chiikiの2論点が実際に上限目前まで来ている前例が[[reference_planetpage_rollout]]
   にある）。**収集が止まっている副首都と違い、ai-copyrightは60%読了では足りない。**

### 推奨: 5論点・全件読了

| 論点 | 件数 | 読む量 |
|---|---:|---|
| 学習データ・無断利用 | 657 | **全件** |
| クリエイター保護・権利 | 303 | **全件** |
| その他 | 223 | **全件** |
| AI生成物の権利・創作性 | 165 | **全件** |
| 技術競争・推進 | 117 | **全件** |
| **合計** | **1,465（意見全体の56.5%）** | |

法制度・規制整備(471)と利用者モラル・倫理(657)は選ばない
（合計を最小にしつつ50%に十分な余白を残す組み合わせを総当たりで確認した）。
**全件読了にする**ことで、条件2の「読み飛ばし」は最初から0件になり、今後の定期収集で
増える分（`grown_count`）だけが4割の枠を消費する形になる。

もし時間の制約でどうしても縮小したい場合の最小構成は上の表と同じ5論点のまま
「各60%」（合計881件）だが、**上記の理由でお勧めしない**。実施者の判断で変える場合は、
この文書の代わりに理由と実際の件数を`tasks/task-54.md`へ書き残すこと。

## 作業ツリー

既に用意済みのものがある: `/Volumes/M2-WorkSpace/Projects/副業/isa-wt-ai-copyright-planet`
（ブランチ`task/ai-copyright-planet`。`social-samples/ai-copyright_hermes_classified.json`は
コピー済み、`node_modules`も複製済み）。**別マシン・別セッションでこれが無ければ**新規に作る:

```bash
git worktree add ../isa-wt-ai-copyright-planet -b task/ai-copyright-planet
cd ../isa-wt-ai-copyright-planet
mkdir -p social-samples
cp ../issue-stance-aggregator/social-samples/ai-copyright_hermes_classified.json social-samples/
cp -R ../issue-stance-aggregator/node_modules .
```

**共有ツリー（`issue-stance-aggregator`本体）では作業しない。** 複数セッションが同じ
作業ツリーを使うと、片方の`git checkout`がもう片方のファイルを消す。

## 対象を手元に出すコマンド

```bash
python3 - <<'PY'
import json

TARGET = ['学習データ・無断利用', 'クリエイター保護・権利', 'その他',
          'AI生成物の権利・創作性', '技術競争・推進']

canon = json.load(open('social-samples/ai-copyright_hermes_classified.json'))
by_issue = {k: [] for k in TARGET}
for rec in canon:
    c = rec.get('classification') or {}
    if c.get('is_opinion') is True and c.get('is_relevant') is True and c.get('main_issue') in TARGET:
        by_issue[c['main_issue']].append({
            'tweet_id': str(rec['tweet_id']), 'url': rec.get('url'), 'text': rec.get('text'),
            'main_issue': c['main_issue'], 'stance': c.get('stance'), 'risk': c.get('risk'),
            'summary': c.get('summary'),
        })

for k, rows in by_issue.items():
    print(f'{k}: {len(rows)}件')
    json.dump(rows, open(f'/tmp/ai-copyright-{TARGET.index(k)}.json', 'w'), ensure_ascii=False, indent=1)
PY
```

成功の形: `学習データ・無断利用: 657件` / `クリエイター保護・権利: 303件` / `その他: 223件` /
`AI生成物の権利・創作性: 165件` / `技術競争・推進: 117件`（**件数が違ったら、着手前に
このブリーフの前提が古くなっている。作業を止めて件数のずれを報告すること**）。

## やること

### 1. 論点ごとに全件の `text`（投稿本文）を読む

- **1件ずつ本文を読む。** `classification.summary`/`reason`等のAI要約は参考にしてよいが、
  最終的な区分（バケット）の判断根拠は本文そのものにする。キーワード自動抽出や
  スクリプトだけでの機械的分類は不可
- 論点ごとに、内容の論拠・主張のパターンでバケットへ分ける。いくつに分けるかは決めうちに
  しない（目安: 学習データ8〜14 / クリエイター保護6〜12 / その他5〜10 / AI生成物4〜8 /
  技術競争4〜8。読んだ結果と違えば読んだほうを採る）
- **stance（規制・制限強化支持／中立・情報／推進・活用支持）を跨いで同じ論拠のバケットに
  なってよい。** バケットは"論拠の種類"であり、stance自体の再判定ではない
  （stanceは既存の`classification.stance`をそのまま使う）
- 各論点**全件**をどこかのバケットに割り当てる（受け皿バケットを1つ用意してよいが、
  読まずに飛ばすことは不可）
- 効率のため、Pythonで一覧を出してまとめて読み、バケットを割り振る進め方でよい
  （1件ずつツールを呼ぶ必要はない）

### 2. 出力ファイルを1本にまとめる

`data/ai-copyright_issues-reread.json` を新規作成する（bukatsu-chiikiの
`cost-receiver-reread.json`、fukushutoの`fukushuto_5issues-reread.json`と同じ、
複数論点1ファイル形式）:

```jsonc
{
  "theme": "ai-copyright",
  "scope": "学習データ・無断利用／クリエイター保護・権利／その他／AI生成物の権利・創作性／技術競争・推進の5論点、意見1,465件全件",
  "population": { "意見全体": 2593, "5論点合計": 1465 },
  "read_at": "（実際に読み終えた日）",
  "method": "編集部（AI）が本文を1件ずつ読み、区分へ分類した。キーワード抽出による機械的分類は使っていない",
  "learning_data": {
    "buckets": { "A": { "label": "…", "count": 0 } },
    "items": [
      { "tweet_id": "…", "main_issue": "学習データ・無断利用", "stance": "…",
        "bucket": "A", "bucket_label": "…", "summary": "…", "text_sha256": "…" }
    ]
  },
  "creator_rights": { "buckets": {}, "items": [] },
  "other": { "buckets": {}, "items": [] },
  "generated_work_rights": { "buckets": {}, "items": [] },
  "tech_promotion": { "buckets": {}, "items": [] }
}
```

- 論点1つ＝1つの上位キー（`learning_data`=学習データ・無断利用 / `creator_rights`=クリエイター
  保護・権利 / `other`=その他 / `generated_work_rights`=AI生成物の権利・創作性 /
  `tech_promotion`=技術競争・推進）
- 各論点内で**`buckets`の合計 = `items`の件数 = その論点の全件数**（657/303/223/165/117と
  一致すること。ずれていると次の検査で止まる）
- `items[].tweet_id`は論点内で重複禁止。`text_sha256`は`text`のsha256（後で本文が変わったら
  検出するため。任意だが推奨）
- `items[]`に`body_reviewed: false`や`review_kind: "automated_classification"`のような
  フィールドを**入れない**こと（`build_planet_data.py`の`validate_reread_records`が
  「本文再読ではない自動分類」として弾く）

## 仕組みへつなぐ（`configs/planet/ai-copyright.yaml`を新規作成）

このテーマは初めての山なみ化なので、yamlファイル自体が無い。以下をそのまま保存する
（`stances`/`issues`の並び・アイコンは**現行の本番ページ`docs/ai-copyright-reaction-map.html`の
投票UI（`VOTE_ISSUES`/`STANCES`、1273〜1287行目付近）と完全に一致させてある**。ここを
変えると過去の投票の意味がずれる。[[reference_pinned_issue_order]]参照）:

```yaml
reread_registry: false
theme_id: ai-copyright
title: 生成AIと著作権
question: 生成AIによる著作物の利用・学習をどこまで認めるべきか
source_label: Yahoo!リアルタイム検索
show_unreviewed_note: true

stances:
  - key: 規制・制限強化支持
    id: ai-copyright-regulation-support
    label: 規制・制限強化支持
    color: "#ff5426"
    pattern: plain
  - key: 中立・情報
    id: ai-copyright-neutral
    label: 中立・情報
    color: "#64748b"
    pattern: dots
  - key: 推進・活用支持
    id: ai-copyright-promotion-support
    label: 推進・活用支持
    color: "#075ef2"
    pattern: diagonal

issues:
  - key: 学習データ・無断利用
    id: ai-copyright-learning-data
    icon: "📚"
  - key: 法制度・規制整備
    id: ai-copyright-legal-framework
    icon: "⚖️"
  - key: 利用者モラル・倫理
    id: ai-copyright-user-ethics
    icon: "💬"
  - key: クリエイター保護・権利
    id: ai-copyright-creator-rights
    icon: "🎨"
  - key: 技術競争・推進
    id: ai-copyright-tech-promotion
    icon: "🚀"
  - key: AI生成物の権利・創作性
    id: ai-copyright-generated-work-rights
    icon: "✨"
  - key: その他
    id: ai-copyright-other
    icon: "🤔"

# 現行の本番ページの投票（choiceIdx = issueIdx*3 + stanceIdx）の並びをそのまま保持。
# 過去の投票が保存されているため、この順序を並べ替えない。
vote_issue_order:
  - 学習データ・無断利用
  - 法制度・規制整備
  - 利用者モラル・倫理
  - クリエイター保護・権利
  - 技術競争・推進
  - AI生成物の権利・創作性
  - その他

sub_issues:
  学習データ・無断利用:
    file: data/ai-copyright_issues-reread.json
    path: [learning_data, buckets]
    items_path: [learning_data, items]
    item_issue_field: main_issue
    coverage: full
    coverage_note: この論点の全件をAIが本文再読した
  クリエイター保護・権利:
    file: data/ai-copyright_issues-reread.json
    path: [creator_rights, buckets]
    items_path: [creator_rights, items]
    item_issue_field: main_issue
    coverage: full
    coverage_note: この論点の全件をAIが本文再読した
  その他:
    file: data/ai-copyright_issues-reread.json
    path: [other, buckets]
    items_path: [other, items]
    item_issue_field: main_issue
    coverage: full
    coverage_note: この論点の全件をAIが本文再読した
  AI生成物の権利・創作性:
    file: data/ai-copyright_issues-reread.json
    path: [generated_work_rights, buckets]
    items_path: [generated_work_rights, items]
    item_issue_field: main_issue
    coverage: full
    coverage_note: この論点の全件をAIが本文再読した
  技術競争・推進:
    file: data/ai-copyright_issues-reread.json
    path: [tech_promotion, buckets]
    items_path: [tech_promotion, items]
    item_issue_field: main_issue
    coverage: full
    coverage_note: この論点の全件をAIが本文再読した

geometry:
  min_area_pct: 2.5
  elevation_k: 50
  elevation_max: 4.0
  fit_points: 30000
  fit_iters: 400
```

**`question`の文言は仮案。** オーナー確認が必要な項目ではない（段階9で共通仕様は承認済み）が、
違和感があれば実施者の判断で変えてよい。`show_unreviewed_note`は法制度・規制整備と
利用者モラル・倫理の2論点が「まだ読み直していない」ことを示す注記の要否
（他テーマの慣例に合わせ`true`にした。不要なら`false`）。

## 完了の確かめ方

**本物の検査をそのまま使う。**

```bash
python3 - <<'PY'
import sys, yaml
sys.path.insert(0, 'scripts')
import build_planet_data as bpd
data = bpd.build('ai-copyright')
cfg = yaml.safe_load(open('configs/planet/ai-copyright.yaml').read())
failures = bpd.independence_gate(data, cfg)
if failures:
    for f in failures: print('NG:', f)
else:
    print('判定: 通る')
PY
```

成功の形: **`判定: 通る`**。着手前に実行すると
`一次資料との突き合わせが無い（data/ai-copyright_claim_posts.json が未作成）` と
`編集部が読み直した論点が意見の0%しかない（50%以上必要）` の2つがNGとして出るはずで、
それが作業前の姿（一次資料との突き合わせ＝「沈んだ大陸・地下水脈」は本ブリーフの対象外。
下記「この文書の対象外」参照）。

エラーが出たら典型的な原因はこれ:
- `「◯◯」の正典ID集合と公開JSONの件数が一致しません` → その論点の`items`件数が
  上の表の件数と違う（読み漏れ・重複・対象外main_issueの混入。数え直しコマンドを再実行して照合）
- `「◯◯」の区分件数が再読IDの実数と一致しません` → `buckets`の`count`と`items`の実数がずれている
- `「◯◯」に読み飛ばしがN件あります` → 全件読了のはずが漏れている

## この文書の対象外（別の作業）

1. **一次資料との突き合わせ（「沈んだ大陸」「地下水脈」）**。
   `quality/research/ai-copyright-primary-sources.md`（12資料、2026-09-07時点）を土台に
   `data/ai-copyright_claim_posts.json`を作る作業。本ブリーフの読む作業とは別物で、
   読む量ははるかに少ない（数件の代表投稿を選ぶだけ）
2. **`data/verification/editorial-adoption-current.json`の149件の分類確認**
   （`topic=="ai-copyright"`・`independently_checked==false`・`current != proposed`）。
   これは`quality/designs/body-review/OPERATING_METHOD.md`と
   `quality/designs/body-review/CYCLE_2000_RUNBOOK.md`が定める、編集担当＋独立監査担当の
   2役・暗号学的な独立性検証つきの別工程で、本ブリーフの「読んでバケットへ分ける」作業とは
   別の仕組み（`prepare_editorial_review_packet.py`等の専用スクリプト群を使う）。
   **本ブリーフの完了に必須ではない**（`independence_gate`はこのファイルを見ない）が、
   放置すると分類の正確さが下がったままになる。着手する場合はこの2文書を先に読むこと
3. **山なみページの実際の生成・標準検査・本番反映**。上の「判定: 通る」が出たら:
   ```bash
   python3 scripts/build_planet_page_preview.py --topic ai-copyright --for-docs \
     --out docs/ai-copyright-reaction-map.html
   ```
   のあと、標準4検査（`verify_theme_page.py`／`verify_number_provenance.py`／
   `verify_top_page.py`／`python3 -m unittest discover -s tests`）と
   `build_public_registry.py --topic ai-copyright`、そして`release`スキルでの反映が必要。
   [[reference_planetpage_rollout]]の「展開1テーマごとに必要な作業」を先に読むこと
   （旧2Dページ固有の削除コード追加など、このテーマならではの落とし穴がある可能性が高い）

## やってはいけないこと

- **キーワード抽出や機械分類の要約だけで区分を決めない。** 本文を読む
- **`vote_issue_order`・`stances`・`issues`の並びやkeyの文字列を、現行ページの投票UIと
  違う形に変えない。** 過去の投票が別の論点として集計されてしまう
- **共有ツリー（`issue-stance-aggregator`本体）で作業しない**
- **`docs/ai-copyright-reaction-map.html`を直接編集しない。** 生成器が書き換える
- **このブリーフの範囲外（一次資料突き合わせ・149件の分類確認・本番反映）まで
  一気にやろうとしない。** それぞれ別の完了確認が要る

## 終わったら

1. `tasks/task-54.md`に、読んだ件数・所要・完了確認の結果を追記する
   （「1,300件・782件」という2026-09-13時点の試算は本ブリーフの実測で更新されたことを明記する）
2. 判定が「通る」になったら、上の「この文書の対象外」3を担当AIへ引き継ぐ
