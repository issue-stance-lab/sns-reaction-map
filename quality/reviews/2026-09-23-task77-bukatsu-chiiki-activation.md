# 課題77 — bukatsu-chiiki連動表示・工程6準備（実ページ有効化と検査の欠落修正）

記録日: 2026-09-23。[6工程計画](../../configs/prompts/20260922_growth-bukatsu-chiiki-connected-layout.md)の工程6。
[工程5の記録](2026-09-23-task77-bukatsu-chiiki-quality.md)の続き。

## 結論（先に）

工程2〜5は候補（一時ファイル）だけで検証しており、`docs/bukatsu-chiiki-reaction-map.html`自体は
まだ無効化のままだった。実際に有効化したところ、公開判断の前提となる検査が3件とも通らず、
いずれも「消費税だけを名指しした処理が残っていて、bukatsu-chiikiが対象に一度も入っていなかった」
という、工程5で見つけた`refresh_planet_section.py`と同型の欠落だった。3件とも修正し、実際の
ページで全検査が通ることを確認した。マージ・pushはまだ行っていない。

## 見つけて直したこと

1. **`verify_theme_page.py`**: `<template>`（JSが選んだ論点だけをcloneする読書面）の中身を
   可視テキストとして数え、`#ocean`側と読書面側の両方に出る同じ注記（沈んだ大陸の断り書き）を
   二重に拾って「同じ数字は1回だけ」を誤検知していた。`<template>`の中身を除外する一般的な
   修正（テーマを問わない、ブラウザの実際の描画と同じ扱いにする）。
2. **`verify_number_provenance.py`**: 再読理由・共通の心配・語られていない争点の件数照合が
   `consumption_tax_count_provenance.py`の無条件呼び出しに決め打ちされていた。
   `scripts/bukatsu_count_provenance.py`を新設（`configs/planet/bukatsu-chiiki.yaml`の
   `sub_issues`を辿って元記録と1件ずつ突き合わせる、consumption_tax版の移植）し、テーマ別の
   対応表で呼び分けるよう一般化。実装中に2件のbukatsu-chiiki固有の差分を発見・対応: 地下水脈が
   複数論点にまたがり同じidが読書面テンプレートごとに複数回現れる（消費税には無い形）、
   沈んだ大陸4件中1件しか`issue_bucket`が付いていない（他3件は未タグのまま、編集部推定なし）。
3. **`configs/page-originality.json`**: 読書面の画面文言はtaxのschema referenceに合わせて
   意図的に揃えたため、消費税の読書面と一致する箇所が生まれた（事故ではない）。
   `--suggest-allow`で生成した7件をallowへ登録し解消。

## 検証

山なみ全10テーマで`verify_theme_page.py`・`verify_number_provenance.py`を再実行しNG0件、
`verify_top_page.py`もOK、全体テスト1103件・`run_public_checks.py`もOK。実際に有効化した
`docs/bukatsu-chiiki-reaction-map.html`をローカルhttp.serverで配信し実機確認（初期表示・
年表2件表示・コンソールエラーなし、スクリーンショットで見た目も確認）。

## 次にすること

オーナーへ完成版の提示・公開判断（工程6の本体）。承認後は`.claude/skills/release/SKILL.md`の
手順（マージ→マージ後mainでの検査→push→CI確認→公開サイト確認→片付け→台帳更新）に進む。
消費税の前例（`quality/reviews/2026-09-22-task77-tax-publication.md`）どおり、表示・レイアウトの
変更でありデータ更新ではないため、`THEMES.yaml`の`updated_at`・`docs/sitemap.xml`は進めない。
