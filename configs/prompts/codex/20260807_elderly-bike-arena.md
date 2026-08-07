## タスク: 高齢者免許返納・自転車青切符のアリーナデータ（SM_RAW）再生成プログラムの構築

### 出典
- `TASK_BOARD.md` 課題34
- `THEMES.yaml` elderly-license-revocation, bike-blue-ticket

---

### 背景・目的
高齢者免許返納および自転車青切符のテーマにおいて、ページの論点カードや統計は正典 `sample_file` に統一されたが、ページ内のアリーナ点データ（`SM_RAW`）は旧分類や別ファイルに由来しており、`main_issue`（セクター `i`）が正典と整合していない。

`build_koshitsu_arena.py` や `build_bukatsu_arena.py` と同様に、正典 `sample_file` のみを読み込み、`main_issue`・座標・感情強度・要約・URL から `SM_RAW` や各種集計データを完全再現・再生成する再実行可能なスクリプトを構築し、HTMLへ再注入する。

---

### やること

1. **`scripts/build_elderly_arena.py` の作成**
   - `social-samples/elderly-license_2d_classified.json` (正典) から `SM_RAW` を再生成
   - `main_issue` を `elderly_license_taxonomy.ISSUE_INDEX` を用いてセクター index `i` に変換
   - `docs/elderly-license-revocation-reaction-map.html` 内の `const SM_RAW = [...]` を更新
   - `--check` フラグ（差分検査モード）の実装

2. **`scripts/build_bike_arena.py` の作成（または共通スクリプト）**
   - 自転車青切符の正典 (`social-samples/bike-blue-ticket_2d_classified.json`) から `SM_RAW` を再生成
   - `bike_blue_ticket_taxonomy` (または該当論点定義) に従い `i` を割り当て
   - `docs/bike-blue-ticket-reaction-map.html` 内の `const SM_RAW = [...]` を更新

3. **`verify_theme_page.py` の検証強化**
   - `SM_RAW` の件数および `i` インデックスが正典 `sample_file` の `main_issue` と完全一致することをアサーション

---

### 制約
- 保護タグを壊さない (`G-K10S4YCZFH`, `ca-pub-2542211932832864`, Supabase, OGP)
- ブランチ: `task/elderly-bike-arena`
- `SM_RAW` の件数・セクター `i` を正典から厳格に再現すること

---

### 完了条件
- [ ] `scripts/build_elderly_arena.py` が作成され、再実行可能である
- [ ] `scripts/build_bike_arena.py` が作成され、再実行可能である
- [ ] `docs/elderly-license-revocation-reaction-map.html` の `SM_RAW` が更新されている
- [ ] `docs/bike-blue-ticket-reaction-map.html` の `SM_RAW` が更新されている
- [ ] `python3 scripts/verify_theme_page.py elderly-license-revocation` が exit 0
- [ ] `python3 scripts/verify_theme_page.py bike-blue-ticket` が exit 0
- [ ] `python3 scripts/verify_top_page.py` が exit 0
