#!/usr/bin/env python3
"""各テーマHTMLに「世論の潮目」tide widgetを挿入するスクリプト。"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SS = ROOT / "social-samples"

# --- テーマ設定 ---
THEMES = [
    {
        "slug": "takaichi",
        "html": "docs/takaichi-reaction-map-standard.html",
        "widget_id": "takaichi-tide-widget",
        "prev_file": "takaichi_hermes_prev_20260712.json",
        "cur_file": "takaichi_hermes_cur_20260726.json",
        "prev_label": "7月12日",
        "cur_label": "7月26日",
        "use_relevance_filter": True,
        "stance_labels": ["批判・追及", "擁護・懐疑", "慎重・保留"],
        "issue_labels": ["中傷動画・説明責任", "文春報道の真偽", "サナエトークン疑惑", "比較・政治倫理", "松井健氏・工作の実態"],
        "note": "比較対象：7月12日収集分のうち意見投稿／7月26日収集分のうち意見投稿。同じ検索語セットで取得した投稿をAIで再分類しています。サンプルの構成比の変化であり、同じ人の意見が移動したことや世論全体の変化を示すものではありません。",
    },
    {
        # adapter（scripts/refresh_adapters/nickname.py）が更新回どうしの比較で作り直すので、
        # prev_file / cur_file は持たない。固定ファイル名を書いておくと、このスクリプトを
        # 単体で流したときに、あとから増えた更新回を無視して古いデータへ巻き戻る（課題38）。
        "slug": "school-nickname-ban",
        "html": "docs/school-nickname-ban-reaction-map.html",
        "widget_id": "school-nickname-ban-tide-widget",
        "prev_file": None,
        "cur_file": None,
        "prev_label": "",
        "cur_label": "",
        "use_relevance_filter": True,
        "stance_labels": ["一律禁止に反対", "禁止支持", "条件付き・個別対応"],
        "issue_labels": ["一律禁止の実効性", "いじめ・心理的安全", "学校運用・現場体験", "親しさ・呼称文化", "本人意思・柔軟運用"],
        "note": "比較対象：7月12日収集分のうち意見投稿／7月26日収集分のうち意見投稿。サンプル数が少ないため傾向の参考程度にご覧ください。",
    },
    {
        # adapter（scripts/refresh_adapters/bike.py）が更新回どうしの比較で作り直すので、
        # prev_file / cur_file は持たない。固定ファイル名を書いておくと、このスクリプトを
        # 単体で流したときに、あとから増えた更新回を無視して古いデータへ巻き戻る（課題38）。
        "slug": "bike-blue-ticket",
        "html": "docs/bike-blue-ticket-reaction-map.html",
        "widget_id": "bike-blue-ticket-tide-widget",
        "prev_file": None,
        "cur_file": None,
        "prev_label": "",
        "cur_label": "",
        "use_relevance_filter": False,
        "exclude_stances": {"どちらでもない", "中立・情報"},
        "exclude_issues": {"その他"},
        "stance_labels": ["賛成（取締り強化支持）", "反対（インフラ・制度優先）"],
        "issue_labels": ["取締り強化賛成", "インフラ整備優先", "ルール曖昧・不信", "車道走行への不安", "免許制要求"],
        # 注記は adapter が毎回組み立てる（署名定型文の件数を数えて書き足すため）。
        "note": "",
    },
    {
        "slug": "henoko",
        "html": "docs/henoko-student-accident-reaction-map.html",
        "widget_id": "henoko-tide-widget",
        "prev_file": "henoko_hermes_prev_20260712.json",
        "cur_file": "henoko_hermes_cur_20260726.json",
        "prev_label": "7月12日",
        "cur_label": "7月26日",
        "use_relevance_filter": False,
        "exclude_stances": {"論点を切り分ける"},
        "exclude_issues": {"その他"},
        "stance_labels": ["文科省判断を支持", "文科省判断に反発", "中立・情報共有"],
        "issue_labels": ["報道・行政対応", "政治的中立性", "安全管理・事故原因", "平和教育の萎縮", "追悼・被害者の尊厳"],
        "note": "比較対象：7月12日収集分／7月26日収集分。辺野古高校生事故は6月発生のため7月末時点で投稿が少ない。少数サンプルの傾向としてご参照ください。",
    },
    {
        "slug": "elderly-license-revocation",
        "html": "docs/elderly-license-revocation-reaction-map.html",
        "widget_id": "elderly-license-revocation-tide-widget",
        "prev_file": "elderly-license-revocation_hermes_prev_20260712.json",
        "cur_file": "elderly-license-revocation_hermes_cur_20260726.json",
        "prev_label": "7月12日",
        "cur_label": "7月26日",
        "use_relevance_filter": True,
        "stance_labels": ["義務化賛成", "条件付き賛成", "義務化反対"],
        "issue_labels": ["義務化・事故防止", "適性検査強化", "地方の足・移動権", "自主返納支援"],
        "note": "比較対象：7月12日収集分のうち意見投稿／7月26日収集分のうち意見投稿。同じ検索語セットで取得した投稿をAIで再分類しています。",
    },
    {
        "slug": "ai-copyright",
        "html": "docs/ai-copyright-reaction-map.html",
        "widget_id": "ai-copyright-tide-widget",
        "prev_file": "ai-copyright_hermes_prev_20260712.json",
        "cur_file": "ai-copyright_hermes_cur_20260726.json",
        "prev_label": "7月12日",
        "cur_label": "7月26日",
        "use_relevance_filter": True,
        "stance_labels": ["規制・制限強化支持", "推進・活用支持"],
        # 論点は scripts/ai_copyright_taxonomy.py の定義（公開ページと同じ7論点から「その他」を除く）
        "issue_labels": ["学習データ・無断利用", "クリエイター保護・権利", "法制度・規制整備", "技術競争・推進", "利用者モラル・倫理", "AI生成物の権利・創作性"],
        "note": "比較対象：7月12日収集分のうち意見投稿／7月26日収集分のうち意見投稿。同じ検索語セットで取得した投稿をAIで再分類しています。サンプルの構成比の変化であり、同じ人の意見が移動したことや世論全体の変化を示すものではありません。",
    },
    {
        "slug": "fukushuto",
        "html": "docs/fukushuto-reaction-map.html",
        "widget_id": "fukushuto-tide-widget",
        # 2026-08-08: 旧5論点で分類した更新回ファイルから、公開ページと同じ7論点で
        # 分類し直した _v2 へ切り替えた。更新回ファイル自体は記録なので改変しない。
        "prev_file": "fukushuto_hermes_prev_20260714_v2.json",
        "cur_file": "fukushuto_hermes_cur_20260726_v2.json",
        "prev_label": "7月14日",
        "cur_label": "7月26日",
        "use_relevance_filter": True,
        "stance_labels": ["法案反対", "法案賛成・推進"],
        # 論点は scripts/fukushuto_taxonomy.py の定義（公開ページと同じ7論点から「その他」を除く）
        "issue_labels": ["定義・中身", "候補地", "都構想・維新", "防災・災害", "費用・財源", "優先順位"],
        "note": "比較対象：7月14日収集分292件のうち意見投稿／7月26日収集分308件のうち意見投稿。同じ検索語セットで取得した投稿を、公開ページと同じ論点でAIが再分類しています。サンプルの構成比の変化であり、同じ人の意見が移動したことや世論全体の変化を示すものではありません。",
    },
    {
        "slug": "koshitsu-tenpakai",
        "html": "docs/koshitsu-tenpakai-reaction-map.html",
        "widget_id": "koshitsu-tenpakai-tide-widget",
        "prev_file": "koshitsu-tenpakai_hermes_prev_synthetic.json",
        "cur_file": "koshitsu-tenpakai_hermes_cur_20260726.json",
        "prev_label": "7月17日",
        "cur_label": "7月26日",
        "use_relevance_filter": False,
        "stance_labels": ["改正反対（男系維持）", "改正賛成（女系容認）", "中立・情報"],
        "issue_labels": ["男系vs女系", "旧宮家養子縁組", "立法手続き・民主主義", "女性天皇・女系天皇", "愛子さま・皇族の地位"],
        "note": "比較対象：7月17日収集分の2Dスタンス統計（改正成立直後326件）と7月26日収集分のAI分類（347件）。前回は2D分類データを再構成した参考値です。同じ人の意見が移動したことや世論全体の変化を示すものではありません。",
    },
    {
        # 潮目ウィジェットの原型がこのページで、汎用JSとCSSは _load_generic_js /
        # _load_tide_css がここから読み出している。adapter（refresh_adapters/
        # constitutional.py）が更新回どうしの比較で作り直すので、prev_file / cur_file は
        # 使わない（前回・今回は social-samples/updates/ の実データから決まる）。
        "slug": "constitutional-amendment",
        "html": "docs/constitutional-amendment-reaction-map.html",
        "widget_id": "constitutional-tide-widget",
        "prev_file": None,
        "cur_file": None,
        "prev_label": "",
        "cur_label": "",
        "use_relevance_filter": True,
        # 立場・論点は scripts/build_constitutional_arena.py の定義と同じ順。
        # 「その他」は投票にもカードにも出さないので潮目からも外す。
        "stance_labels": ["慎重・反対", "中立", "手続き重視", "改正推進"],
        "issue_labels": [
            "改憲全般",
            "9条・自衛隊",
            "緊急事態条項",
            "国民投票・広告",
            "政党・発議手続き",
            "情報・議論の質",
        ],
        "note": "",
    },
    {
        # adapter（refresh_adapters/consumption_tax.py）が更新回どうしの比較で作り直すので、
        # prev_file / cur_file は使わない（前回・今回は social-samples/updates/ の実データ）。
        "slug": "consumption-tax-cut",
        "html": "docs/consumption-tax-cut-reaction-map.html",
        "widget_id": "consumption-tax-cut-tide-widget",
        "prev_file": None,
        "cur_file": None,
        "prev_label": "",
        "cur_label": "",
        "use_relevance_filter": True,
        # 立場・論点は scripts/build_consumption_tax_arena.py の定義と同じ順。
        # 「その他」は論点カードにも投票にも出さないので潮目からも外す。
        "stance_labels": ["減税推進", "条件付き賛成・政府案に不満", "減税反対・慎重", "中立・情報"],
        "issue_labels": [
            "減税の対象範囲",
            "財源と社会保障",
            "減税の効果",
            "給付など他策との比較",
            "事業者の実務負担",
            "公約と政治不信",
        ],
        "note": "",
    },
]


def load_classified(path: Path, use_relevance: bool, exclude_stances: set | None = None, exclude_issues: set | None = None) -> list[dict]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    result = []
    for r in rows:
        c = r.get("classification", {})
        if use_relevance:
            if not c.get("is_relevant") or not c.get("is_opinion"):
                continue
        else:
            stance = c.get("stance", "")
            issue = c.get("main_issue", "")
            if exclude_stances and stance in exclude_stances:
                continue
            if exclude_issues and issue in exclude_issues:
                continue
        result.append(c)
    return result


def calc_pcts(data: list[dict], labels: list[str], field: str) -> tuple[dict[str, float], int]:
    counts = Counter(r.get(field, "その他") for r in data)
    total = sum(counts[l] for l in labels if l in counts)
    if total == 0:
        return {l: 0.0 for l in labels}, 0
    pcts = {}
    for label in labels:
        pcts[label] = round(counts[label] / total * 100, 1)
    return pcts, total


def biggest_change(labels: list[str], prev: dict, cur: dict) -> str:
    diffs = [(abs(cur.get(l, 0) - prev.get(l, 0)), l, cur.get(l, 0) - prev.get(l, 0)) for l in labels]
    diffs.sort(reverse=True)
    if not diffs:
        return "変化を計算中"
    biggest = diffs[0]
    diff = biggest[2]
    label = biggest[1]
    direction = "増加" if diff > 0 else "減少"
    return f"「{label}」が{abs(diff):.1f}ポイント{direction}"


def generate_tide_section(theme: dict, prev_data: list, cur_data: list) -> str:
    """tide widget HTML+CSS+JSを生成"""
    # パーセント計算
    s_prev, s_prev_n = calc_pcts(prev_data, theme["stance_labels"], "stance")
    s_cur, s_cur_n = calc_pcts(cur_data, theme["stance_labels"], "stance")
    i_prev, i_prev_n = calc_pcts(prev_data, theme["issue_labels"], "main_issue")
    i_cur, i_cur_n = calc_pcts(cur_data, theme["issue_labels"], "main_issue")

    stance_headline = biggest_change(theme["stance_labels"], s_prev, s_cur)
    issue_headline = biggest_change(theme["issue_labels"], i_prev, i_cur)

    # stance max (表示用スケール)
    all_stance_vals = list(s_prev.values()) + list(s_cur.values())
    stance_max = max(10, round(max(all_stance_vals) / 10 + 0.5) * 10) if all_stance_vals else 80

    all_issue_vals = list(i_prev.values()) + list(i_cur.values())
    issue_max = max(10, round(max(all_issue_vals) / 10 + 0.5) * 10) if all_issue_vals else 60

    stance_rows = [{"label": l, "previous": s_prev.get(l, 0.0), "current": s_cur.get(l, 0.0)} for l in theme["stance_labels"]]
    issue_rows = [{"label": l, "previous": i_prev.get(l, 0.0), "current": i_cur.get(l, 0.0)} for l in theme["issue_labels"]]

    datasets = {
        "stance": {"max": stance_max, "headline": stance_headline, "rows": stance_rows},
        "issue": {"max": issue_max, "headline": issue_headline, "rows": issue_rows},
    }

    wid = theme["widget_id"]
    prev_lbl = theme["prev_label"]
    cur_lbl = theme["cur_label"]
    note = theme["note"]

    # 汎用JS (constitutional から流用)
    generic_js = _load_generic_js()

    html = f"""<section class="update-dashboard" aria-label="世論の潮目"><!-- TIDE_CARD_START -->
<section class="tide-card" id="{wid}" aria-label="世論の潮目 前回収集と今回収集の比較">
  <div class="tide-widget-controls" aria-label="潮目の表示切り替え">
    <div class="tide-widget-tabs">
      <button type="button" class="tide-widget-btn" data-tide-mode="stance" aria-pressed="true">立場の変化</button>
      <button type="button" class="tide-widget-btn" data-tide-mode="issue" aria-pressed="false">論点の変化</button>
    </div>
    <button type="button" class="tide-widget-btn tide-replay" data-tide-replay><span class="tide-replay-icon" aria-hidden="true">▶</span>変化を再生</button>
  </div>
  <div class="tide-widget-summary" aria-live="polite">
    <span class="tide-widget-period">{prev_lbl} → {cur_lbl}</span>
    <strong data-tide-headline>{stance_headline}</strong>
  </div>
  <div class="tide-slope-wrap">
    <svg class="tide-slope-svg" viewBox="0 0 720 340" role="img" aria-labelledby="{wid}-slope-title {wid}-slope-desc">
      <title id="{wid}-slope-title">前回と今回の構成比を結ぶグラフ</title>
      <desc id="{wid}-slope-desc">前回収集分{s_prev_n}件と今回収集分{s_cur_n}件の構成比を比較します。</desc>
      <text class="tide-slope-date" x="160" y="28" text-anchor="middle">前回 {prev_lbl}</text>
      <text class="tide-slope-date" x="560" y="28" text-anchor="middle">今回 {cur_lbl}</text>
      <line class="tide-slope-axis" x1="160" y1="48" x2="160" y2="320"></line>
      <line class="tide-slope-axis" x1="560" y1="48" x2="560" y2="320"></line>
      <g data-tide-series></g>
    </svg>
  </div>
  <div class="tide-mobile-rows" data-tide-mobile aria-label="前回と今回の構成比"></div>
  <p class="tide-widget-note">{note}</p>
</section>
<script>
(() => {{
  const root = document.getElementById("{wid}");
  if (!root) return;
  const datasets = {json.dumps(datasets, ensure_ascii=False)};
  {generic_js}
}})();
</script>
<!-- TIDE_CARD_END --></section>"""

    return html


def _load_generic_js() -> str:
    with open(ROOT / "docs" / "constitutional-amendment-reaction-map.html", encoding="utf-8") as f:
        html = f.read()
    start = html.find("<!-- TIDE_CARD_START -->")
    end = html.find("<!-- TIDE_CARD_END -->")
    section = html[start:end]
    sm = re.search(r"<script>(.*?)</script>", section, re.DOTALL)
    if not sm:
        raise RuntimeError("tide JS not found in constitutional HTML")
    js = sm.group(1)
    ds_end = js.find("};", js.find("const datasets"))
    body = js[ds_end + 2:].strip()
    # constitutional の IIFE クローズ })(); を除去（外側の IIFE は generate_tide_section が追加）
    if body.endswith("})();"):
        body = body[:-5].rstrip()
    return body


def _load_tide_css() -> str:
    with open(ROOT / "docs" / "constitutional-amendment-reaction-map.html", encoding="utf-8") as f:
        html = f.read()
    css_m = re.search(r"/\* TIDE_CARD_START \*/(.*?)/\* TIDE_CARD_END \*/", html, re.DOTALL)
    return css_m.group(1).strip() if css_m else ""


def inject_into_html(html_path: Path, tide_html: str, tide_css: str) -> str:
    with open(html_path, encoding="utf-8") as f:
        html = f.read()

    # 既存の tide widget セクションを丸ごと置換
    if "<!-- TIDE_CARD_START -->" in html and "<!-- TIDE_CARD_END -->" in html:
        # <section class="update-dashboard" ...><!-- TIDE_CARD_START -->...<!-- TIDE_CARD_END --></section> を除去
        old_m = re.search(
            r'<section[^>]*><!-- TIDE_CARD_START -->.*?<!-- TIDE_CARD_END --></section>',
            html, re.DOTALL
        )
        if old_m:
            html = html[:old_m.start()] + tide_html + html[old_m.end():]
            return html

    # CSS注入: </style> の直前に追加（既に tide CSS がない場合）
    if "tide-card" not in html:
        css_block = f"\n/* TIDE_CARD_START */\n{tide_css}\n/* TIDE_CARD_END */\n"
        html = html.replace("</style>", css_block + "</style>", 1)

    # HTML注入: <section class="panel" id="explainer-section"> の直前
    insert_markers = [
        '<section class="panel" id="explainer-section">',
        '<section id="explainer-section"',
        '<section class="panel explainer-section"',
    ]
    inserted = False
    for marker in insert_markers:
        if marker in html:
            html = html.replace(marker, tide_html + "\n\n" + marker, 1)
            inserted = True
            break

    if not inserted:
        # fallback: </main> の直前
        html = html.replace("</main>", tide_html + "\n</main>", 1)

    return html


def main() -> None:
    tide_css = _load_tide_css()

    for theme in THEMES:
        print(f"\n=== {theme['slug']} ===")
        if not theme.get("prev_file") or not theme.get("cur_file"):
            # adapter が更新回どうしを比較して作り直すテーマ。固定ファイルを持たない。
            print("  SKIP: adapter が更新回から生成する（固定の比較ファイルなし）")
            continue
        prev_path = SS / theme["prev_file"]
        cur_path = SS / theme["cur_file"]

        if not prev_path.exists():
            print(f"  SKIP: {prev_path} not found")
            continue
        if not cur_path.exists():
            print(f"  SKIP: {cur_path} not found")
            continue

        exclude_stances = theme.get("exclude_stances")
        exclude_issues = theme.get("exclude_issues")
        prev_data = load_classified(prev_path, theme["use_relevance_filter"], exclude_stances, exclude_issues)
        cur_data = load_classified(cur_path, theme["use_relevance_filter"], exclude_stances, exclude_issues)

        print(f"  前回: {len(prev_data)}件, 今回: {len(cur_data)}件")

        if len(prev_data) == 0 and len(cur_data) == 0:
            print("  SKIP: データが0件")
            continue

        tide_html = generate_tide_section(theme, prev_data, cur_data)

        html_path = ROOT / theme["html"]
        new_html = inject_into_html(html_path, tide_html, tide_css)
        html_path.write_text(new_html, encoding="utf-8")
        print(f"  → {theme['html']} 更新完了")


if __name__ == "__main__":
    main()
