# 課題54 段階10-1: 自転車の青切符を新しい形にする（別セッション用の指示文）

**9テーマ展開の1本目。**この1枚で作業できるように書いてある。
全体像は `quality/designs/2026-09-06-nine-theme-rollout-brief.md` にあるが、
**このテーマを進めるだけなら読まなくてよい。**

## 最初に読むこと

**読む作業はほぼ終わっている。**このテーマは過去に編集部が273件＋77件を読み直しており、
独自性の検査に必要な分がすでにそろっている。**残りは最少4件、多く見ても26件。**

したがってこの作業の中身は、**①既存の読み直しデータを新しい形へ変換する
②足りない台帳を書く ③アダプタを自転車でも動くようにする**の3つになる。

（`nine-theme-rollout-brief.md` には「自転車は要読了234件」と書いてあるが、
これは既存の読み直しを数える前の値で、**実測の結果もっと少ない**。こちらを正とする）

---

## いまの状態（2026-09-06 実測）

意見468件／収集468件／一次資料の照合7件（資料どおり2・少しずれる4・裏が取れない1）

### 論点と読み直しの進み具合

生成器は「読み直し済みの論点が意見の50%以上（＝234件以上）」を求め、
さらに**論点ごとに未読が4割以下**であることを求める。

| 論点 | 全体 | 読直済 | 未読 | 未読率 | 4割条件 |
|---|---|---|---|---|---|
| その他 | 213 | 63 | 150 | 70% | × |
| 取締り強化賛成 | 90 | 87 | 3 | 3% | **○** |
| インフラ整備優先 | 58 | 54 | 4 | 7% | **○** |
| ルール曖昧・不信 | 58 | 32 | 26 | 45% | **×（あと4件で○）** |
| 免許制要求 | 29 | 21 | 8 | 28% | **○** |
| 車道走行への不安 | 20 | 16 | 4 | 20% | **○** |

- いま条件を満たす4論点の合計 = **197件**。50%の壁（234件）に**37件足りない**
- **「ルール曖昧・不信」の未読26件のうち4件を読めば**、この論点が条件を満たし、
  合計 197+58 = **255件**となって壁を越える
- **推奨は26件すべて読む**こと。4件だけだと次の収集で1件増えるたびに条件を割る

### 既存の読み直しデータ（形が違うので変換が要る）

| ファイル | 中身 | 形 |
|---|---|---|
| `data/verification/bike-blue-ticket-reread.json` | 273件 | `[{tweet_id, bucket, signature, excerpt}]` の配列。bucket は support / abolish / scope / place / distrust / strict |
| `data/bike-blue-ticket_opposition_reread.json` | 反対77件 | `{buckets: {区分: [tweet_id, …]}}` |

生成器が読む形は**これとは別**で、部活動のものが見本になる
（`data/bukatsu-chiiki_teacher-reread.json`）。

```jsonc
{ "theme": "...", "scope": "...", "population": {...}, "read_at": "...", "method": "...",
  "buckets": { "A": {"label": "…", "count": 12}, … },
  "items": [ {"tweet_id":"…","url":"…","stance":"…","bucket":"A","bucket_label":"…","summary":"…","risk":"low"} ] }
```

**`buckets` の合計＝`items` の件数**になっていること。生成器はこの合計を
「読み直した件数」として使う。

## そろっていないもの

| 要るもの | 状態 |
|---|---|
| `configs/planet/bike-blue-ticket.yaml` | **無い**（`configs/planet/bukatsu-chiiki.yaml` を写して直す） |
| `data/verification/bike-blue-ticket-background.json` | **無い**（`quality/research/bike-blue-ticket-primary-sources.md` 150行から書く） |
| 資料にあるのにSNSにないこと（`-sunk-continents.json` / `-veins.json`） | **無い**（`status: not_started`） |
| 編集部の横断整理（`-editorial.json`） | **無い**（`status: not_started`） |

**この4つのうち、公開の検査で必須なのは前の2つだけ。**あとの2つは無くても検査は通り、
ページでは空欄のまま出る（部活動の設計どおり）。**先に前の2つを終わらせて画面を出し、
残りは後から足すこと。**

## アダプタが自転車では動かない

`scripts/build_planet_page_preview.py` は部活動のページ構造を前提にしている。
差し込み位置に使っている `<!-- BUKATSU_ENTRY_END -->` が自転車には無い。
自転車にあってページ本体を作っている目印は次のとおり。

```
ARGUMENTS / PROCESS_SECTIONS / REREAD_BASIS / RESEARCH_CONDITIONS
＋ 全テーマ共通（ADSENSE_TAG / ARTICLE_JSON_LD / ARTICLE_TRUST / GA_TAG / SEO_META / TIDE_CARD）
```

**直し方は「切り取る」から「残すものを名指しして他を捨てる」へ変える。**
残すのは、全テーマ共通の目印の区間＋投票（`#vote-section`）＋関連テーマ
（`#related-topics`）＋詳細データ＋SNS投稿サンプル。それ以外の `<main>` の中身は捨てて、
新しい部品（第1部・確かめること・SNS反応マップ・論点カード）を組み立て直す。

こうすると設定は「残すものの一覧」だけになり、残り8テーマでも同じコードが動く。
**自転車で通れば、以降のテーマは設定を足すだけになる。**

## 手順

1. 専用の作業ツリーを作る
   `git worktree add ../isa-wt-<名前> -b task/<名前> main`
2. 非公開の正典を同期する（gitに入らない）
   `rsync -a ../issue-stance-aggregator/social-samples/ social-samples/`
3. **「ルール曖昧・不信」の未読26件を読む**（下のコマンドで出す）
4. 既存の350件＋今回の分を、生成器が読む形の
   `data/bike-blue-ticket_issues-reread.json` へまとめる
5. `configs/planet/bike-blue-ticket.yaml` を書く（**件数は書かない**。
   `sub_issues` に、条件を満たす5論点を登録する）
6. `data/verification/bike-blue-ticket-background.json` を書く
   （定義1文・なぜ始まったか・経緯の年表・確かめること。**すべて出典URL付き**）
7. アダプタを「残すものを名指しする」形へ作り替え、自転車で組み立てる
8. 実画面で見て、検査を通す

### 未読26件を出すコマンド

```bash
python3 - <<'PY'
import json
rows = json.load(open('social-samples/bike-blue-ticket_2d_classified.json'))
a = json.load(open('data/verification/bike-blue-ticket-reread.json'))
b = json.load(open('data/bike-blue-ticket_opposition_reread.json'))
read = {x['tweet_id'] for x in a} | {t for v in b['buckets'].values() for t in v}
t = [r for r in rows
     if (r.get('classification') or {}).get('main_issue') == 'ルール曖昧・不信'
     and r.get('tweet_id') not in read]
json.dump(t, open('/tmp/bike-unread.json', 'w'), ensure_ascii=False, indent=1)
print(len(t), '件を /tmp/bike-unread.json へ出した')
PY
```

成功の形: `26 件を /tmp/bike-unread.json へ出した`

## 通す検査

```bash
python3 scripts/build_planet_data.py --topic bike-blue-ticket   # --prototype を付けない
python3 -m unittest discover -s tests
python3 scripts/verify_theme_page.py
python3 scripts/verify_number_provenance.py
python3 scripts/verify_top_page.py
```

成功の形: 「独自性の検査に不合格」が出ず `wrote …` まで進む／`OK`／`NG 0件`。
**同じ入力で2回生成して差分が出ないこと**も確かめる（課題34）。

## やってはいけないこと

- **`--prototype` で独自性の検査を迂回しない。**公開できないページができるだけ
- **設定ファイルに件数を書かない。**件数は必ず正典から数え直す
- **既存の読み直し350件を作り直さない。**読んだ日も方法も違うものが混ざる
- **AIの `summary` だけで分類しない。**本文（`text`）を読む
- **手書きのHTMLを `docs/` へ置かない。**`verify_builder_rebuildability.py` が落ちる
- **共有ツリーで作業しない。**専用の作業ツリーを作る
- **「その他」213件を読もうとしない。**区分できないものの集まりで、
  読んでも論点にならない。50%の壁は名前のある論点だけで越える

## 参考

- 見本のページ: `quality/prototypes/bukatsu-chiiki-page-preview.html`
- 見本の設定: `configs/planet/bukatsu-chiiki.yaml`
- 見本の経緯台帳: `data/verification/bukatsu-chiiki-background.json`
- 組み立ての記録と残っている宿題: `quality/reviews/2026-09-05-task54-page-assembly.md`
- 一次資料メモ: `quality/research/bike-blue-ticket-primary-sources.md`
