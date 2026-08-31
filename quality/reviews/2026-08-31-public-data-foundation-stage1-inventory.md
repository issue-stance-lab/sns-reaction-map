# 課題57 段階1：公開値の入力・重複棚卸し

実施日: 2026-08-31  
対象: `published: done` の公開10テーマ（高市テーマは対象外）  
結論: 段階2で確定する公開データ契約の入力・出力・廃止対象を特定した。公開物は変更していない。

## 1. 現在の経路

```
非公開正典 social-samples/ ─┐
THEMES.yaml ────────────────┼→ テーマ別生成器／論点件数同期 → docs/各テーマページ
テーマ設定 configs/ ─────────┘                              ↘ docs/index.html
                                                                  ↘ docs/sitemap.xml
```

| 値 | 現在の主な入力 | 現在の表示・生成器 | 段階2以降の扱い |
|---|---|---|---|
| 公開対象・ページパス・更新日・収集期間 | `THEMES.yaml` | `sync_portal_stats.py`、SEO生成器、更新器 | **正典として残す** |
| 質問・説明文・論点の表示名・立場の表示名 | `configs/*-reaction-map.json`、`configs/theme-seo.json` | テーマ別生成器 | **正典として残す**。段階2で安定IDを明示追加する |
| 収集した投稿数・分析対象の意見数・論点別／立場別／強度別件数 | `social-samples/` の分類済み累積正典 | テーマ別生成器、`sync_issue_counts.py`、`verify_number_provenance.py` | **公開JSONから生成**。公開HTMLを入力にしない |
| トップのテーマ数・合計・最終更新日・テーマカード数 | `THEMES.yaml` と、`verification_file` があれば `data/verification/`、なければ `sample_file` | `sync_portal_stats.py` → `docs/index.html` | **catalogから生成**。現行の検証データ優先読込は廃止する |
| sitemap対象・`lastmod` | `configs/site-cases.json` と `configs/theme-seo.json` | `scripts/seo/generate_seo_assets.py` → `docs/sitemap.xml` | **catalogとテーマ台帳から生成**。旧ルートは対象外 |
| 一次資料の件数など、投稿分類から導けない数字 | `number_provenance.sources` / `allow` に理由付きで登録したファイル・一次資料 | テーマ本文 | **出所付き固定値として残す**。公開JSONの投稿集計値に混ぜない |

## 2. 表示場所の完全抽出

`verify_number_provenance.py` の抽出器は、テーマHTMLと同じディレクトリから読むローカルJSの
`N件` とアリーナの `{k: ..., n: N}` を全件抽出する。公開10テーマで **1,306か所** を抽出し、
出所不明は0件だった。

| テーマ | 数値表示数 |
|---|---:|
| 生成AIと著作権 | 170 |
| 自転車青切符 | 211 |
| 部活動の地域移行 | 37 |
| 憲法改正 | 339 |
| 高齢者の免許返納 | 181 |
| 学校のあだ名禁止 | 79 |
| 辺野古高校生死亡事故 | 52 |
| 副首都 | 67 |
| 皇室典範 | 67 |
| 消費税減税 | 103 |

各テーマでは、HTMLに加えて共通の `topic-modern.js`、`vote-config.js`、`vote-store.js`、
`share-x-btn.js` と、必要なテーマ専用アリーナJSを検査した。トップは `sync_portal_stats.py`
の置換対象を調べ、合計、公開テーマ数、投票テーマ数、最終更新日、更新予定、注目カード4件、
テーマカード10件を抽出した。

## 3. `data/verification/` の判断

これは本文を含まない**検査用サマリ**であり、CIとクリーンクローンで投稿集合・分類結果を
照合するためのもの。レコード単位の `record_id_hash` と `confidence` を含む。

- 公開データ契約はレコード単位ハッシュと信頼度を含めないため、`data/verification/` を新しい公開正典にはしない。
- 現在 `verification_file` を持つテーマでは、トップ・一部検査がこのサマリを読み、持たない3テーマでは非公開正典を読む。この分岐は段階3〜4で公開JSON／catalogへ置換する。
- `updates/` は更新回の検査履歴として維持する。公開JSONの入力にも、公開ページの数値の正典にも使わない。
- `*-claims.json` と自転車の再読サマリは、一次資料と投稿を対応付ける検査専用の追加根拠であり、投稿集計とは分けて維持する。

## 4. 旧SQLiteと参考実装

`data/reaction_map.sqlite3` の参照は `data/README.md` と、明示指定で書き込む
`scripts/import_reactions_to_sqlite.py` だけだった。公開生成器・トップ・sitemap・検査は読んでいない。
削除・変更はせず、課題57の入力から除外する。

参考ブランチ `769ba3f` は一括マージしない。再利用するのは次の考え方だけとする。

- `published: done` による公開10テーマ選択
- 収集数、意見数、論点数、更新日を同時に検査する不変条件
- 自転車・消費税の古い数字を検査する観点

同ブランチの `sync_publication_contract.py`、`build_root_index.py`、旧ルート用テスト／
同期処理は、旧ルートまたはHTMLを中間入力にしており、再利用しない。`build_planet_data.py` は
課題54の範囲であり、段階2の契約確定前には取り込まない。

## 5. 段階2への確定事項

1. 公開JSONは非公開正典からのみ集計し、HTML、検証用サマリ、SQLite、旧ルートを入力にしない。
2. `THEMES.yaml` は公開対象・更新予定・ページ位置の正典として残す。
3. テーマ設定は質問・説明文・安定ID・読者向け表示名の正典として残す。
4. 投稿から導けない外部数値は理由付き固定値として隔離し、投稿集計JSONへ混ぜない。
5. 公開HTMLは出力のみとする。トップとsitemapはcatalogを読む経路へ置換する。

## 実行記録

```sh
python3 scripts/verify_number_provenance.py -v
# 公開10テーマを含む全11テーマで NG 0件
```

非公開正典の復元後、公開10テーマの `sample_file` 欠落は0件だった。
