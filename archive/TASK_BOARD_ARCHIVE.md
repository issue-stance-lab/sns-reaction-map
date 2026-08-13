# TASK_BOARD アーカイブ — 完了済み・移管済み課題

移動日: 2026-07-05
元ファイル: TASK_BOARD.md（git履歴で全文参照可能）

---

## 完了済み課題

| 課題 | 担当 | 完了日 | 概要 |
|------|------|--------|------|
| 課題1: 公開準備 | Hermes | 2026-06-27 | ポータル・トピックページの品質を公開レベルに |
| 課題2: 投票バックエンド | Antigravity2 | 2026-06-24 | Supabaseバックエンド導入 |
| 課題3: 集客基盤 | Codex | 2026-06-27 | SEO・GA4・Search Console導入 |
| 課題4: パイプライン効率化 | Claude Code | 2026-06-24 | run_pipeline.py ワンコマンド化 |
| 課題5: 収益化 | Hermes→Claude/Antigravity | 2026-06-27 | Buy Me a Coffee・AdSense申請・ads.txt |
| 課題7: データ補充 | Codex/Claude Code | 2026-06-28 | 5テーマの追加収集・再分類。継続はLOOP.md④で管理 |
| 課題8: UI/UX改善 | Claude Code | 2026-06-27 | マガジン風UI・ツイート埋め込み・AI画像 |
| 課題9: テーマ別分類設計 | Claude Code | 2026-06-28 | school/henoko再設計完了 |
| 課題10: 投票導線改善 | Hermes | 2026-06-27 | 投票ガイドライン策定・全テーマ文言刷新 |
| 課題11: 投票エラー修正 | Claude Code | 2026-06-27 | スクリプト断片化+23505判定漏れ修正 |
| 課題12: 正式公開 | Claude Code | 2026-06-28 | GitHub Pages・SEO・GA4・OGP全適用 |
| 課題16: OGP画像 | Antigravity | 2026-07-01 | 8テーマOGP画像作成・適用 |
| 課題21: データ再分類 | Hermes | 2026-07-02 | school・elderly両テーマの保留率改善 |
| 課題22: BMC URL修正 | Claude Code | 2026-07-02 | 全ページのBuy Me a Coffee URL統一 |
| 課題25: スタンスマップ統一 | Claude Code | 2026-07-04 | 半円図→2Dマップ一括移行 |
| 課題26: v3構成改革 | ワーカーAI/Claude Code | 2026-07-05 | Phase A〜F全完了 |

---

## グロース課題（GROWTH.yaml へ移管）

以下の課題はグロースループで管理する。詳細は `GROWTH.yaml` / `GROWTH_LOOP.md` を参照。

| 旧課題 | 対応する GROWTH.yaml 項目 |
|--------|--------------------------|
| 課題6: X初期フォロワー獲得・集客強化（@sns_hannou_ma 0→100） | recurring.x-posting |
| 課題14: ページ表示速度最適化（Lighthouse計測・Twitter widgets.js遅延読み込み） | capabilities（未起票、必要時に追加） |
| 課題20: テーマ別問題提起LP | capabilities（未起票、必要時に追加） |

---

## テーマ個別課題（THEMES.yaml へ移管）

以下の課題はテーマ工程として THEMES.yaml で管理する。

| 旧課題 | 対応する THEMES.yaml 工程 |
|--------|--------------------------|
| 課題23: ai-copyright 2D分類 | classify2d（done） |
| 課題24: 漫画コンテンツ追加 | manga_data / manga_img |
| 課題27: bukatsu-chiiki 画像生成 | manga_img（blocked） |
| 課題28: 旧3テーマ v3化 | classify2d → page_v3 |
| 課題46: 運用メモの公開停止 | Claude Code | 2026-08-13 | `docs/` 直下の運用メモ10件を `docs-internal/` へ移動。verify_top_page.py に再発防止の検査を追加 |

---

## 旧チーム構成（参考）

| AI | 役割 | 得意分野 |
|----|------|---------|
| Claude Code | ハブ（司令塔） | 対話的設計・既存コード改善・git統合・ローカル実行 |
| Codex (GPT-5.5) | ワーカー | PR作成・テスト・長期実行タスク |
| Antigravity2 (Gemini 3.5 Flash) | ワーカー | フルスタックアプリ生成・バックエンド |
| Hermes (Kimi K2.6) | ワーカー | フロントエンド生成・UI品質 |

---

## 旧連絡メモ（完了済み）

| 日付 | 発信AI | 宛先AI | 内容 |
|------|--------|--------|------|
| 2026-06-24 | Codex | Hermes/Claude Code | SEOツール追加。docs/seo-setup.mdの手順で適用 |
| 2026-06-24 | Codex | Claude Code | 課題4クロスレビュー。P1対応依頼 |
| 2026-06-24 | Claude Code | Codex | レビュー全6項目対応完了 |
| 2026-06-24 | Codex | Claude Code | 再レビュー。P3指摘 |
| 2026-06-24 | Claude Code | Codex | P3対応完了（try/finally化） |


---

## 課題46 の詳細（2026-08-13 完了）
### 課題46: 運用メモ9件が公開サイトから配信されている
**状態**: 未着手（2026-08-10 記録）
**きっかけ**: 課題45で `x-posts.md` をサイト配信から外した際、`docs/` 直下に
運用メモの `.md` が残っていることに気づいた。**9件すべて HTTP 200 で配信中**
（`https://issue-stance-lab.github.io/sns-reaction-map/<ファイル名>` で誰でも読める）。

| ファイル | 行数 | 内容 |
|---|---|---|
| `ga4-automation.md` | 334 | GA4の自動取得手順（OAuth設定を含む） |
| `gsc-automation.md` | 258 | Search Console の自動取得手順 |
| `voting_design_guideline.md` | 135 | 投票設問・選択肢の設計方針 |
| `growth-kpi-automation.md` | 107 | KPI取得の自動化メモ |
| `seo-setup.md` | 88 | SEO・X共有のセットアップ |
| `adsense-setup.md` | 84 | AdSense導入手順 |
| `supabase-votes-automation.md` | 84 | 投票数の自動取得メモ |
| `kpi-snapshot-request-2026-07-07.md` | 60 | KPI取得依頼（未対応のまま） |
| `substack-takaichi-reaction-table.md` | 43 | Substack貼り付け用の分類表 |

**調査済み（作業前に読むこと）**:
- **鍵・トークンは無い。** `client_secret` / `refresh_token` / APIキーはいずれも不在。
  `adsense-setup.md` の `ca-pub-1234567890123456` はプレースホルダで実IDではない。
  `ga4-automation.md` の `G-K10S4YCZFH` はページに埋まる公開値
- **課題45と同じく「漏洩」ではなく「見え方」の課題。** 運用の手順が読める状態
- **サイト内からリンクされていない**（`docs/*.html` に参照なし）。URL直打ちでのみ到達する
- 相互参照は `docs/` 内で閉じている（`ga4-automation` を2件、`gsc-automation` と
  `growth-kpi-automation` を各1件が参照）。**リポジトリ外からの参照は無い**
- `docs/images/README.md` はサブディレクトリなので別途判断（画像素材の説明）

**取るべき方法**: 課題45と同じ `git rm --cached` ＋ `.gitignore`。
ただし**それだけではサイト配信は止まらない**。デプロイは `docs/` を丸ごと
アップロードするため、**追跡を外してもローカルにファイルが残っていれば配信され続ける**
（課題45の `x-posts.md` はリポジトリ直下へ「移動」したので止まった）。

→ **この課題では「`docs/` の外へ移す」方が確実。** 移動先の候補は `docs-internal/` など。
   相互参照が `docs/` 内で閉じているので、まとめて移せばリンクは壊れない。

**判断が要る点**: `substack-takaichi-reaction-table.md` は外部貼り付け用に作ったもので、
公開前提だった可能性がある。移す前にオーナーに確認すること。

**完了**: 2026-08-13。`git mv` で10件（9件＋`docs/images/README.md`）を `docs-internal/` へ移動。
相互参照の書き換えは5行のみ。`substack-takaichi-reaction-table.md` も移動した（貼り付け元の作業ファイルで
リンク0件、かつ記載183件が現行正典447件と食い違うため）。機密は無かったが、`ga4-automation.md` と
`gsc-automation.md` にオーナーのローカルパスが含まれ、リポジトリが public のため git 履歴には残る。
