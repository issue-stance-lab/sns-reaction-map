# 課題106: トップページのリニューアル（検索した疑問から入る型）

**登録**: 2026-10-15（オーナー指示「個別ページはリニューアルした。今度はトップページ。リサーチ機能でユーザーがどんな検索をして何を求めているかを推察して、どんな入口がベストかを盛り込む」）

## 何をしたか

- 検索の根拠: UIデザイン調査 `61_トップページ_検索根拠_2026-10-15`（ラッコキーワード・Googleサジェスト・Google Trends・Search Console・GA4）
- 設計記録: `quality/designs/2026-10-15-top-page-renewal.md`
- 仕組み: `configs/top-page.json`（手書き文言）→ `scripts/build_top_page.py` → `docs/index.html`。見た目は `docs/top-page.css`
- 検査: `tests/test_top_page_build.py`（生成結果と一致・sync_portal_stats と refresh_featured_slots の差分0・verify_top_page NG0・段階の切替）

## 分かったこと

- サイトの考え方そのもの（SNSの反応まとめ）を探す検索は無い。トップは「来た人を、検索した疑問のテーマへ最短で送る」役
- トップの入口は直接入力・X・ChatGPT（GA4 90日）。検索から来た人はテーマページに直接着地する
- `refresh_featured_slots.py` は10テーマの刷新で `question-line` が無くなり main でも止まっていた。`configs/top-page.json` の疑問文を代わりの正典にした

## 残り

- 公開後30日（2026-11-14ごろ）に、トップ→テーマページの遷移とSearch Consoleの表示をリニューアル前（直接56・X 49・検索4セッション、表示7）と比べる
- 皇室（10/24）・副首都（10/30）の施行後に `enforcement_confirmed_on` を入れて再生成し、並び順（entries の順）を見直す
