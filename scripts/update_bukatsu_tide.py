#!/usr/bin/env python3
"""Update the bukatsu page with Hermes data and a previous/current tide card."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

try:
    from .bukatsu_taxonomy import ISSUES, STANCES, STANCE_BY_LABEL
except ImportError:
    from bukatsu_taxonomy import ISSUES, STANCES, STANCE_BY_LABEL  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parent.parent
STANCE_SHORT = {label: item["short_label"] for label, item in STANCE_BY_LABEL.items()}
STANCE_EXPLANATION = {
    "移行支持": "地域移行を支持する意見",
    "条件付き・改善要求": "地域移行には条件・改善が必要という意見",
    "慎重・反対": "地域移行に慎重・反対する意見",
    "中立・情報": "中立・情報提供の投稿",
}
STANCE_CARD_LABEL = {
    "移行支持": "移行支持",
    "条件付き・改善要求": "条件・改善要求",
    "慎重・反対": "慎重・反対",
    "中立・情報": "中立・情報",
}
STANCE_CLASS = {
    "移行支持": "pro",
    "条件付き・改善要求": "conditional",
    "慎重・反対": "con",
    "中立・情報": "neutral",
}
STANCE_X = {label: float(item["x"]) for label, item in STANCE_BY_LABEL.items()}
INTENSITY_E = {"low": 0.5, "medium": 1.0, "high": 2.0}

# 編集確認済みの代表投稿。直近追加分（status が 208... の投稿）も含め、
# 各論点で具体的な条件・経験・制度設計を説明しているものを優先する。
# データ更新でURLが欠けた場合は、下の confidence 順の候補に安全に戻る。
REPRESENTATIVE_POSTS = {
    "費用・家庭負担": [
        ("https://x.com/TheMirageof0/status/2070621781757726855", "家計にのしかかる会費"),
        ("https://x.com/774nyannyan/status/2086731858579263880", "公費が足りないと縮小・負担増"),
    ],
    "受け皿・指導者": [
        ("https://x.com/maru_moneyy/status/2084392638506274876", "受け皿の人手・送迎が足りない"),
        ("https://x.com/kohei_okada_pt/status/2084608274377437341", "地域資源に合わせた再構築を求める"),
    ],
    "教員の働き方": [
        ("https://x.com/AtelierClutch/status/2082217044611834122", "授業に専念できる環境を求める"),
        ("https://x.com/Namenotblanko/status/2082969614196093400", "善意に頼らない仕組みを求める"),
    ],
    "教育的意義・機会": [
        ("https://x.com/ikuji_takuto/status/2083492685223215132", "学校教育としての部活を残したい"),
        ("https://x.com/39Md8/status/2082487864135393452", "生涯スポーツ・音楽につながる場にしたい"),
    ],
    "地域格差": [
        ("https://x.com/Davestaragues/status/2085511206278939102", "地方で施設が取れない"),
        ("https://x.com/mamamam4949/status/2069589990011818183", "都市部への環境偏在を懸念"),
    ],
    "制度・移行プロセス": [
        ("https://x.com/4ZYVNjQOkWBSoU8/status/2085954870243426355", "公費と負担金の仕組みが必要"),
        ("https://x.com/Goshiki2023/status/2078663825013031272", "費用・場所・責任の設計が未解決"),
    ],
    "その他": [
        ("https://x.com/m727243023/status/2085525452777795616", "吹奏楽は移行しにくいという経験"),
        ("https://x.com/mamimami_koro/status/2087383840331608316", "マネージャーの役割にある性別規範を問う"),
    ],
}

ISSUE_STANCE_LABEL = {
    "移行支持": "地域で担う形を進めたい",
    "条件付き・改善要求": "条件を整えて進めたい",
    "慎重・反対": "今のままでは進めにくい",
    "中立・情報": "経験・情報を共有",
}

TIDE_CSS = """
/* TIDE_CARD_START */
.update-dashboard{padding:18px min(4vw,40px) 34px;background:var(--bg)}
.update-dashboard>.stats{max-width:1180px;margin:0 auto 14px;gap:10px;background:transparent}
.update-dashboard>.stats::before{display:none}
.update-dashboard>.stats .stat{padding:14px 16px;border:1px solid var(--line);border-radius:14px;background:#fff;color:var(--ink);box-shadow:0 8px 24px rgba(18,35,64,.06)}
.update-dashboard>.stats .stat span{font-size:12px;color:var(--muted)}
.update-dashboard>.stats .stat strong{font-size:21px;color:var(--ink)}
.tide-card{max-width:1180px;margin:0 auto;padding:26px 28px;border:1px solid #d9e2ef;border-radius:20px;background:#fff;box-shadow:0 16px 40px rgba(18,35,64,.09);color:var(--ink)}
.tide-head{display:flex;justify-content:space-between;align-items:center;gap:18px;margin-bottom:22px}
.tide-title-wrap{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.tide-kicker{display:inline-flex;padding:5px 10px;border-radius:999px;background:#eaf1ff;color:#315bd8;font-size:13px;font-weight:900}
.tide-head h2{margin:0;font-size:28px;letter-spacing:-.02em}
.tide-period{display:flex;align-items:center;gap:10px;padding:10px 14px;border-radius:12px;background:#f3f6fb;color:#26364f;font-size:16px;font-weight:900;white-space:nowrap}
.tide-period b{color:#315bd8;font-size:18px}
.tide-lead{margin-bottom:8px;font-size:22px;font-weight:900;line-height:1.55}
.tide-delta{color:#b45309;font-size:31px;white-space:nowrap}
.tide-explain{margin:0 0 18px;color:var(--muted);font-size:15px;line-height:1.75}
.tide-movements{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-bottom:20px}
.tide-movement{padding:14px 16px;border:1px solid #e1e7f0;border-radius:14px;background:#f9fbfe}
.tide-movement-label{display:flex;align-items:center;gap:8px;margin-bottom:5px;font-size:14px;font-weight:900}
.tide-dot{width:10px;height:10px;border-radius:50%}.tide-dot.pro{background:#059669}.tide-dot.conditional{background:#d97706}.tide-dot.con{background:#dc2626}
.tide-values{font-size:17px;font-weight:900}.tide-values small{color:var(--muted);font-size:13px;font-weight:800}
.tide-change{display:block;margin-top:3px;font-size:15px;font-weight:900}.tide-change.up{color:#047857}.tide-change.down{color:#b45309}.tide-change.con{color:#b91c1c}
.tide-grid{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(310px,.75fr);gap:22px;align-items:stretch}
.tide-bars{display:grid;gap:14px;padding:18px;border-radius:16px;background:#f3f6fb}
.tide-row{display:grid;grid-template-columns:148px 1fr 74px;gap:12px;align-items:center;font-size:14px;font-weight:900}
.tide-row-label small{display:block;color:var(--muted);font-size:12px}
.tide-track{display:flex;height:18px;border-radius:999px;overflow:hidden;background:#dfe5ee}.tide-seg{height:100%}.tide-seg.pro{background:#34d399}.tide-seg.conditional{background:#fbbf24}.tide-seg.con{background:#fb7185}.tide-seg.neutral{background:#94a3b8}
.tide-legend{display:flex;flex-wrap:wrap;gap:8px 14px;margin-top:2px;color:#4b5c74;font-size:12px;font-weight:800}.tide-legend span{display:inline-flex;align-items:center;gap:5px}.tide-legend i{width:8px;height:8px;border-radius:50%}
.tide-side{display:grid;gap:10px}.tide-fact{padding:14px 16px;border-radius:14px;background:#13223d;color:#dbe6f5;font-size:13px;line-height:1.55}.tide-fact strong{display:block;margin-top:3px;color:#fff;font-size:16px;line-height:1.55}
.tide-note{margin:16px 0 0;padding-top:14px;border-top:1px solid #e4e9f1;color:#66758b;font-size:12px;line-height:1.7}
.tide-widget-controls{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-bottom:18px}
.tide-widget-tabs{display:flex;gap:6px;padding:4px;border-radius:12px;background:#eef3f9}
.tide-widget-btn{min-height:38px;padding:8px 14px;border:0;border-radius:9px;background:transparent;color:#53647c;font:inherit;font-size:13px;font-weight:900;cursor:pointer}
.tide-widget-btn[aria-pressed="true"]{background:#13223d;color:#fff;box-shadow:0 4px 12px rgba(18,35,64,.15)}
.tide-replay{display:inline-flex;align-items:center;gap:6px;border:1px solid #d9e2ef;background:#fff;color:#20314d}
.tide-replay:hover{background:#f3f6fb}.tide-replay-icon{font-size:11px}
.tide-widget-summary{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.tide-widget-period{display:inline-flex;padding:6px 11px;border-radius:999px;background:#eaf1ff;color:#315bd8;font-size:13px;font-weight:900}
.tide-widget-summary strong{font-size:18px;font-weight:900}
.tide-slope-wrap{margin-top:12px}.tide-slope-svg{display:block;width:100%;height:auto;overflow:visible}
.tide-slope-axis{stroke:#d7e0eb;stroke-width:2}.tide-slope-date{fill:#34445e;font-size:16px;font-weight:900}
.tide-slope-label{fill:#0b1d3a;font-size:15px;font-weight:900}.tide-slope-value{fill:#66758b;font-size:13px;font-weight:800}
.tide-slope-line{fill:none;stroke-width:5;stroke-linecap:round}.tide-slope-point{stroke:#fff;stroke-width:3}
.tide-slope-line.series-0{stroke:#10b981}.tide-slope-line.series-1{stroke:#f59e0b}.tide-slope-line.series-2{stroke:#ef476f}.tide-slope-line.series-3{stroke:#64748b}
.tide-slope-point.series-0{fill:#10b981}.tide-slope-point.series-1{fill:#f59e0b}.tide-slope-point.series-2{fill:#ef476f}.tide-slope-point.series-3{fill:#64748b}
.tide-mobile-rows{display:none}.tide-widget-note{margin:4px 0 0;padding-top:14px;border-top:1px solid #e4e9f1;color:#66758b;font-size:12px;line-height:1.7}
.tide-mobile-row{padding:14px 0;border-bottom:1px solid #e4e9f1}.tide-mobile-row:last-child{border-bottom:0}.tide-mobile-head{display:flex;justify-content:space-between;gap:10px;font-size:14px;font-weight:900}
.tide-mobile-values{margin-top:5px;color:#465873;font-size:13px;font-weight:800}.tide-mobile-bars{display:grid;gap:5px;margin-top:9px}.tide-mobile-bar{height:8px;border-radius:999px;background:#e5eaf1;overflow:hidden}.tide-mobile-bar span{display:block;height:100%;border-radius:inherit}.tide-mobile-bar.previous span{background:#a8b4c5}.tide-mobile-bar.current span{background:#315bd8}
.hermes-summary-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.hermes-summary-card{border:1px solid var(--line);border-radius:12px;background:#fff;padding:16px}.hermes-summary-card .axis-count{font-size:28px}
.hermes-issue-list{display:grid;gap:14px}.hermes-issue-card{border:1px solid var(--line);border-radius:12px;background:#fff;padding:18px}.hermes-issue-head{display:flex;justify-content:space-between;gap:12px;align-items:baseline}.hermes-issue-head h3{margin:0;font-size:18px}.hermes-issue-count{font-weight:900;color:var(--accent);white-space:nowrap}
.hermes-stance-bar{display:flex;height:12px;border-radius:999px;overflow:hidden;background:#eef2f6;margin:12px 0 8px}.hermes-stance-bar span.pro{background:#059669}.hermes-stance-bar span.conditional{background:#d97706}.hermes-stance-bar span.con{background:#dc2626}.hermes-stance-bar span.neutral{background:#94a3b8}
.hermes-legend{display:flex;gap:10px;flex-wrap:wrap;color:var(--muted);font-size:11px}.hermes-samples{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:14px}.hermes-sample{min-width:0;overflow:hidden;border:1px solid var(--line);border-radius:10px;padding:12px;background:var(--accent-soft);font-size:12px;line-height:1.55}.hermes-sample-meta{display:block;color:var(--accent);font-size:11px;font-weight:900}.hermes-sample-summary{margin:5px 0 8px;color:var(--ink);font-weight:700}.hermes-sample .twitter-tweet,.hermes-sample .twitter-tweet-rendered{max-width:100%!important;margin:0 auto!important}.hermes-sample .twitter-tweet iframe{max-width:100%!important}
@media(max-width:720px){
  .update-dashboard{padding:10px 10px 24px}.update-dashboard>.stats{grid-template-columns:repeat(2,1fr);gap:8px}.update-dashboard>.stats .stat{padding:12px}.update-dashboard>.stats .stat strong{font-size:18px}
  .tide-card{padding:20px 16px;border-radius:16px}.tide-head{display:block;margin-bottom:18px}.tide-title-wrap{margin-bottom:12px}.tide-head h2{font-size:25px}.tide-kicker{font-size:12px}.tide-period{justify-content:center;width:100%;font-size:14px;white-space:normal}.tide-period b{font-size:16px}
  .tide-lead{font-size:19px}.tide-delta{display:block;margin-top:2px;font-size:27px;white-space:normal}.tide-explain{font-size:14px}.tide-movements,.tide-grid,.hermes-summary-grid,.hermes-samples{grid-template-columns:1fr}
  .tide-movements{gap:8px}.tide-movement{padding:12px 14px}.tide-row{grid-template-columns:92px 1fr 50px;gap:8px;font-size:12px}.tide-row-label small{font-size:10px}.tide-track{height:16px}.tide-bars{padding:14px}.tide-fact strong{font-size:15px}.tide-note{font-size:12px}
  .hermes-issue-head{display:block}.hermes-issue-count{display:block;margin-top:4px}
}
@media(max-width:430px){
  .tide-widget-controls{align-items:stretch}.tide-widget-tabs{width:100%}.tide-widget-tabs .tide-widget-btn{flex:1}.tide-replay{justify-content:center;width:100%}
  .tide-widget-summary{align-items:flex-start;flex-direction:column}.tide-widget-summary strong{font-size:17px}
  .tide-slope-wrap{display:none}.tide-mobile-rows{display:block;margin-top:12px}
}
/* TIDE_CARD_END */
"""

TIDE_WIDGET_JS = r"""
<script>
(() => {
  const root = document.getElementById("bukatsu-tide-widget");
  if (!root) return;
  const datasets = __TIDE_DATA__;
  const svgGroup = root.querySelector("[data-tide-series]");
  const mobileRows = root.querySelector("[data-tide-mobile]");
  const headline = root.querySelector("[data-tide-headline]");
  const modeButtons = [...root.querySelectorAll("[data-tide-mode]")];
  const replayButton = root.querySelector("[data-tide-replay]");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let mode = "stance";
  let animationFrame = 0;
  let hasAutoPlayed = false;

  const yFor = (value, max) => 310 - (value / max) * 235;
  const signed = value => `${value >= 0 ? "+" : "−"}${Math.abs(value).toFixed(1)}ポイント`;
  const svgElement = (name, attrs, text) => {
    const el = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, String(value)));
    if (text !== undefined) el.textContent = text;
    return el;
  };

  function draw(progress = 1) {
    const data = datasets[mode];
    svgGroup.replaceChildren();
    mobileRows.replaceChildren();

    data.rows.forEach((row, index) => {
      const y1 = yFor(row.previous, data.max);
      const y2Target = yFor(row.current, data.max);
      const y2 = y1 + (y2Target - y1) * progress;
      const shown = row.previous + (row.current - row.previous) * progress;
      const shownDelta = shown - row.previous;
      const seriesClass = `series-${index}`;

      svgGroup.appendChild(svgElement("line", {x1:160, y1, x2:560, y2, class:`tide-slope-line ${seriesClass}`}));
      svgGroup.appendChild(svgElement("circle", {cx:160, cy:y1, r:7, class:`tide-slope-point ${seriesClass}`}));
      svgGroup.appendChild(svgElement("circle", {cx:560, cy:y2, r:7, class:`tide-slope-point ${seriesClass}`}));
      svgGroup.appendChild(svgElement("text", {x:145, y:y1-5, "text-anchor":"end", class:"tide-slope-label"}, row.label));
      svgGroup.appendChild(svgElement("text", {x:145, y:y1+17, "text-anchor":"end", class:"tide-slope-value"}, `${row.previous.toFixed(1)}%`));
      svgGroup.appendChild(svgElement("text", {x:575, y:y2-5, class:"tide-slope-label"}, `${shown.toFixed(1)}%`));
      svgGroup.appendChild(svgElement("text", {x:575, y:y2+17, class:"tide-slope-value"}, signed(shownDelta)));

      const mobile = document.createElement("article");
      mobile.className = "tide-mobile-row";
      mobile.innerHTML =
        `<div class="tide-mobile-head"><span>${row.label}</span><strong>${signed(shownDelta)}</strong></div>` +
        `<div class="tide-mobile-values">前回 ${row.previous.toFixed(1)}% → 今回 ${shown.toFixed(1)}%</div>` +
        `<div class="tide-mobile-bars" aria-hidden="true">` +
          `<div class="tide-mobile-bar previous"><span style="width:${row.previous / data.max * 100}%"></span></div>` +
          `<div class="tide-mobile-bar current"><span style="width:${shown / data.max * 100}%"></span></div>` +
        `</div>`;
      mobileRows.appendChild(mobile);
    });
  }

  function animate() {
    cancelAnimationFrame(animationFrame);
    if (reducedMotion) {
      draw(1);
      return;
    }
    const startedAt = performance.now();
    const duration = 900;
    const step = now => {
      const raw = Math.min(1, (now - startedAt) / duration);
      draw(1 - Math.pow(1 - raw, 3));
      if (raw < 1) animationFrame = requestAnimationFrame(step);
    };
    animationFrame = requestAnimationFrame(step);
  }

  function setMode(nextMode) {
    mode = nextMode;
    modeButtons.forEach(button => {
      const selected = button.dataset.tideMode === mode;
      button.setAttribute("aria-pressed", String(selected));
    });
    headline.textContent = datasets[mode].headline;
    animate();
  }

  modeButtons.forEach(button => button.addEventListener("click", () => setMode(button.dataset.tideMode)));
  replayButton.addEventListener("click", animate);
  draw(1);

  if ("IntersectionObserver" in window && !reducedMotion) {
    const observer = new IntersectionObserver(entries => {
      if (!hasAutoPlayed && entries.some(entry => entry.isIntersecting)) {
        hasAutoPlayed = true;
        animate();
        observer.disconnect();
      }
    }, {threshold: 0.35});
    observer.observe(root);
  }
})();
</script>
"""


def load(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list")
    return data


def key(row: dict[str, Any]) -> str:
    return str(row.get("tweet_id") or row.get("url") or row.get("text") or "").strip()


def classification(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("classification")
    return value if isinstance(value, dict) else {}


def opinions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if classification(row).get("is_relevant") and classification(row).get("is_opinion")]


def share(rows: list[dict[str, Any]], field: str, value: str) -> float:
    if not rows:
        return 0.0
    return sum(classification(row).get(field) == value for row in rows) * 100 / len(rows)


def signed(value: float) -> str:
    return f"{value:+.1f}"


def signed_points(value: float) -> str:
    sign = "＋" if value >= 0 else "−"
    return f"{sign}{abs(value):.1f}ポイント"


def stacked_bar(rows: list[dict[str, Any]]) -> str:
    parts = []
    for stance in STANCES:
        width = share(rows, "stance", stance)
        if width:
            parts.append(f'<span class="tide-seg {STANCE_CLASS[stance]}" style="width:{width:.2f}%"></span>')
    return "".join(parts)


def js(value: Any) -> str:
    return json.dumps(str(value or ""), ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e")


def replace_once(source: str, pattern: str, replacement: str, label: str, flags: int = 0) -> str:
    updated, count = re.subn(pattern, lambda _match: replacement, source, count=1, flags=flags)
    if count != 1:
        raise ValueError(f"{label}: expected 1 match, found {count}")
    return updated


def japanese_date(value: str) -> str:
    parsed = date.fromisoformat(value)
    return f"{parsed.month}月{parsed.day}日"


def tide_card(previous: list[dict[str, Any]], current: list[dict[str, Any]], previous_date: str, current_date: str) -> tuple[str, dict[str, Any]]:
    deltas = {stance: share(current, "stance", stance) - share(previous, "stance", stance) for stance in STANCES[:3]}
    focus = max(deltas, key=lambda stance: abs(deltas[stance]))
    issue_deltas = {
        issue: share(current, "main_issue", issue) - share(previous, "main_issue", issue)
        for issue in ISSUES
    }
    rising_issue = max(ISSUES[:-1], key=lambda issue: issue_deltas[issue])
    high_delta = share(current, "intensity", "high") - share(previous, "intensity", "high")
    direction = "増加" if deltas[focus] >= 0 else "減少"
    headline = STANCE_EXPLANATION[focus]
    issue_rows = sorted(ISSUES, key=lambda issue: abs(issue_deltas[issue]), reverse=True)[:4]
    widget_data = {
        "stance": {
            "max": 50,
            "headline": f"{STANCE_CARD_LABEL[focus]}の割合が{abs(deltas[focus]):.1f}ポイント{direction}",
            "rows": [
                {
                    "label": STANCE_CARD_LABEL[stance],
                    "previous": round(share(previous, "stance", stance), 1),
                    "current": round(share(current, "stance", stance), 1),
                }
                for stance in STANCES[:3]
            ],
        },
        "issue": {
            "max": 30,
            "headline": f"{rising_issue}が{abs(issue_deltas[rising_issue]):.1f}ポイント増加",
            "rows": [
                {
                    "label": issue,
                    "previous": round(share(previous, "main_issue", issue), 1),
                    "current": round(share(current, "main_issue", issue), 1),
                }
                for issue in issue_rows
            ],
        },
    }
    widget_script = TIDE_WIDGET_JS.replace(
        "__TIDE_DATA__",
        json.dumps(widget_data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c"),
    )
    previous_label = japanese_date(previous_date)
    current_label = japanese_date(current_date)
    card = f"""<!-- TIDE_CARD_START -->
<section class="tide-card" id="bukatsu-tide-widget" aria-label="世論の潮目 前回更新と今回更新の比較">
  <div class="tide-widget-controls" aria-label="潮目の表示切り替え">
    <div class="tide-widget-tabs">
      <button type="button" class="tide-widget-btn" data-tide-mode="stance" aria-pressed="true">立場の変化</button>
      <button type="button" class="tide-widget-btn" data-tide-mode="issue" aria-pressed="false">論点の変化</button>
    </div>
    <button type="button" class="tide-widget-btn tide-replay" data-tide-replay><span class="tide-replay-icon" aria-hidden="true">▶</span>変化を再生</button>
  </div>
  <div class="tide-widget-summary" aria-live="polite">
    <span class="tide-widget-period">{previous_label} → {current_label}</span>
    <strong data-tide-headline>{widget_data["stance"]["headline"]}</strong>
  </div>
  <div class="tide-slope-wrap">
    <svg class="tide-slope-svg" viewBox="0 0 720 340" role="img" aria-labelledby="tide-slope-title tide-slope-desc">
      <title id="tide-slope-title">前回と今回の構成比を結ぶグラフ</title>
      <desc id="tide-slope-desc">前回追加分{len(previous)}件と今回追加分{len(current)}件の構成比を比較します。</desc>
      <text class="tide-slope-date" x="160" y="28" text-anchor="middle">前回 {previous_label}</text>
      <text class="tide-slope-date" x="560" y="28" text-anchor="middle">今回 {current_label}</text>
      <line class="tide-slope-axis" x1="160" y1="48" x2="160" y2="320"></line>
      <line class="tide-slope-axis" x1="560" y1="48" x2="560" y2="320"></line>
      <g data-tide-series></g>
    </svg>
  </div>
  <div class="tide-mobile-rows" data-tide-mobile aria-label="前回と今回の構成比"></div>
  <p class="tide-widget-note">比較対象：前回追加分 {len(previous)}件／今回追加分 {len(current)}件。同じ検索語セットで取得した意見投稿をAIで再分類しています。投稿サンプルの構成比の変化であり、同じ人の意見が移動したことや世論全体の変化を示すものではありません。</p>
</section>
{widget_script}
<!-- TIDE_CARD_END -->"""
    return card, {
        "focus_stance": focus,
        "focus_delta": deltas[focus],
        "rising_issue": rising_issue,
        "rising_issue_delta": issue_deltas[rising_issue],
        "high_delta": high_delta,
    }


def sm_raw(rows: list[dict[str, Any]]) -> str:
    lines = ["const SM_RAW = ["]
    for row in rows:
        c = classification(row)
        issue = c.get("main_issue") if c.get("main_issue") in ISSUES else "その他"
        lines.append(
            "{" +
            f"x:{STANCE_X.get(str(c.get('stance')), 0):.1f}," +
            f"e:{INTENSITY_E.get(str(c.get('intensity')), 0.5):.1f}," +
            f"c:{float(c.get('confidence', 0.5)):.2f}," +
            f"i:{ISSUES.index(issue)}," +
            f"s:{js(c.get('summary'))}," +
            f"u:{js(row.get('url'))}" +
            "},"
        )
    lines.append("];")
    return "\n".join(lines)


def issue_panel(rows: list[dict[str, Any]]) -> str:
    blocks = []
    for issue in ISSUES:
        group = [row for row in rows if classification(row).get("main_issue") == issue]
        counts = Counter(classification(row).get("stance") for row in group)
        total = len(group)
        bar = "".join(
            f'<span class="{STANCE_CLASS[stance]}" style="width:{counts[stance] * 100 / total:.2f}%"></span>'
            for stance in STANCES if total and counts[stance]
        )
        legend = " ".join(
            f"<span>{html.escape(ISSUE_STANCE_LABEL[stance])} {counts[stance]}</span>"
            for stance in STANCES if counts[stance]
        )
        usable = [row for row in group if classification(row).get("article_usable") and row.get("url")]
        candidates_by_url = {str(row["url"]): row for row in usable}
        candidates = [
            (candidates_by_url[url], label)
            for url, label in REPRESENTATIVE_POSTS.get(issue, [])
            if url in candidates_by_url
        ]
        fallback = sorted(
            [row for row in usable if row not in [candidate[0] for candidate in candidates]],
            key=lambda row: float(classification(row).get("confidence", 0)),
            reverse=True,
        )
        fallback_samples = [
            (row, ISSUE_STANCE_LABEL.get(str(classification(row).get("stance")), "投稿の視点"))
            for row in fallback
        ]
        candidates = (candidates + fallback_samples)[:2]
        samples = "".join(tweet_sample(row, label) for row, label in candidates)
        blocks.append(
            '<article class="hermes-issue-card">'
            f'<div class="hermes-issue-head"><h3>{html.escape(issue)}</h3><span class="hermes-issue-count">{total}件</span></div>'
            f'<div class="hermes-stance-bar">{bar}</div><div class="hermes-legend">{legend}</div>'
            f'<div class="hermes-samples">{samples}</div>'
            "</article>"
        )
    return (
        '<section class="panel conflict-panel"><div class="panel-title"><h2>7つの論点とXの声</h2>'
        '<span>公開投稿を論点・立場・主張の強さで配置</span></div>'
        '<div class="hermes-issue-list">' + "".join(blocks) + "</div></section>"
    )


def tweet_sample(row: dict[str, Any], detail_label: str) -> str:
    """Render the same X embed used for representative posts on other themes."""
    url = html.escape(str(row.get("url") or ""), quote=True)
    handle = re.search(r"x\.com/([^/]+)/status/", str(row.get("url") or ""))
    account = f"@{handle.group(1)}" if handle else "この投稿"
    detail_label = html.escape(detail_label)
    summary = html.escape(str(classification(row).get("summary") or ""))
    return (
        '<div class="hermes-sample">'
        f'<span class="hermes-sample-meta">{detail_label}</span>'
        f'<p class="hermes-sample-summary">{summary}</p>'
        '<blockquote class="twitter-tweet" data-conversation="none" data-dnt="true">'
        f'<a href="{url}">{account} の投稿をXで見る</a></blockquote>'
        "</div>"
    )


def summary_panel(rows: list[dict[str, Any]]) -> str:
    stance_counts = Counter(classification(row).get("stance") for row in rows)
    issue_counts = Counter(classification(row).get("main_issue") for row in rows)
    intensity_counts = Counter(classification(row).get("intensity") for row in rows)
    top_issue, top_count = issue_counts.most_common(1)[0]
    top_stance, stance_count = stance_counts.most_common(1)[0]
    return f"""<section class="panel conflict-panel"><div class="panel-title"><h2>投稿の分類結果</h2><span>意見投稿のみ</span></div>
<div class="hermes-summary-grid">
<article class="hermes-summary-card"><div class="axis-kicker">最多スタンス</div><h3>{html.escape(STANCE_SHORT.get(str(top_stance), str(top_stance)))}</h3><div class="axis-count">{stance_count}</div><p>支持・条件付き・慎重反対を分けて集計しています。</p></article>
<article class="hermes-summary-card"><div class="axis-kicker">最多論点</div><h3>{html.escape(str(top_issue))}</h3><div class="axis-count">{top_count}</div><p>投稿の主眼となる論点を1つに分類しています。</p></article>
<article class="hermes-summary-card"><div class="axis-kicker">感情強度 high</div><h3>強い訴え・批判</h3><div class="axis-count">{intensity_counts["high"]}</div><p>表現の強さであり、意見の正しさを示す値ではありません。</p></article>
</div></section>"""


def details_panel(all_rows: list[dict[str, Any]], opinion_rows: list[dict[str, Any]]) -> str:
    relevant_count = sum(bool(classification(row).get("is_relevant")) for row in all_rows)
    issue_counts = Counter(classification(row).get("main_issue") for row in opinion_rows)
    stance_counts = Counter(classification(row).get("stance") for row in opinion_rows)
    issue_table = "".join(f"<tr><th>{html.escape(issue)}</th><td>{issue_counts[issue]}</td></tr>" for issue in ISSUES)
    stance_table = "".join(f"<tr><th>{html.escape(stance)}</th><td>{stance_counts[stance]}</td></tr>" for stance in STANCES)
    return f"""<section class="panel details-panel" id="detail-data"><div class="panel-title"><h2>詳細データ</h2><span>必要な人向けに折りたたみ</span></div>
<details><summary>収集・分類件数</summary><div class="table-wrap"><table><tbody>
<tr><th>累計収集投稿</th><td>{len(all_rows)}</td></tr><tr><th>テーマ関連投稿</th><td>{relevant_count}</td></tr><tr><th>意見投稿</th><td>{len(opinion_rows)}</td></tr>
</tbody></table></div></details>
<details><summary>論点別件数</summary><div class="table-wrap"><table><tbody>{issue_table}</tbody></table></div></details>
<details><summary>スタンス別件数</summary><div class="table-wrap"><table><tbody>{stance_table}</tbody></table></div></details>
<details><summary>注意</summary><ul><li>Yahooリアルタイム検索で取得したSNS投稿サンプルであり、世論調査ではありません。</li><li>Hermesが論点・スタンス・強度を自動分類しました。</li></ul></details>
</section>"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--classified", type=Path, required=True)
    parser.add_argument("--previous-batch", type=Path, required=True)
    parser.add_argument("--current-batch", type=Path, required=True)
    parser.add_argument("--previous-date", required=True)
    parser.add_argument("--current-date", required=True)
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--output-html", type=Path)
    args = parser.parse_args()

    all_rows = load(args.classified)
    previous_keys = {key(row) for row in load(args.previous_batch)}
    current_keys = {key(row) for row in load(args.current_batch)}
    all_opinions = opinions(all_rows)
    previous = [row for row in all_opinions if key(row) in previous_keys]
    current = [row for row in all_opinions if key(row) in current_keys]
    if not previous or not current:
        raise ValueError(f"comparison batches are empty: previous={len(previous)} current={len(current)}")

    issue_counts = Counter(classification(row).get("main_issue") for row in all_opinions)
    top_issue, top_count = issue_counts.most_common(1)[0]
    relevant_count = sum(bool(classification(row).get("is_relevant")) for row in all_rows)
    card, tide = tide_card(previous, current, args.previous_date, args.current_date)

    page = args.html.read_text(encoding="utf-8")
    if "/* TIDE_CARD_START */" in page:
        page = re.sub(r"/\* TIDE_CARD_START \*/.*?/\* TIDE_CARD_END \*/", TIDE_CSS.strip(), page, count=1, flags=re.DOTALL)
    else:
        page = replace_once(page, r"</style>", TIDE_CSS + "\n</style>", "tide CSS")
    stance_counts = Counter(classification(row).get("stance") for row in all_opinions)
    if top_issue == "教員の働き方":
        focus_title = "教員の負担を減らしながら、活動を誰が支えるのか"
        focus_detail = "教員の働き方を論点とする投稿が最も多く、学校だけに担わせない必要性と、地域で費用・指導者・責任をどう確保するかが同時に問われています。"
    else:
        focus_title = f"「{html.escape(str(top_issue))}」を、どう支えるのか"
        focus_detail = "この論点を中心に、地域展開の進め方と必要な条件が議論されています。"
    summary = (
        '<div class="thirty-summary" aria-label="議論の中心">'
        '<header class="thirty-summary-title"><h2>議論の中心</h2></header><ul>'
        f'<li class="conclusion-focus"><span class="conclusion-count"><b>{top_count}</b>件</span>'
        f'<strong>{focus_title}</strong><span class="conclusion-detail">{focus_detail}</span></li></ul></div>'
    )
    page = replace_once(page, r'<div class="thirty-summary".*?</div>', summary, "30 second summary", flags=re.DOTALL)
    dashboard = f'<section class="update-dashboard" aria-label="更新データと世論の潮目">{card}</section>'
    if '<section class="update-dashboard"' in page:
        page = replace_once(
            page,
            r'<section class="update-dashboard".*?<!-- TIDE_CARD_END --></section>',
            dashboard,
            "update dashboard",
            flags=re.DOTALL,
        )
    else:
        page = re.sub(r"\s*<!-- TIDE_CARD_START -->.*?<!-- TIDE_CARD_END -->\s*", "\n", page, count=1, flags=re.DOTALL)
        page = replace_once(page, r'<section class="stats">.*?</section>', dashboard, "stats dashboard", flags=re.DOTALL)
    page = replace_once(
        page,
        r'<div class="panel-title"><h2>(?:論点アリーナ|SNS反応マップ)</h2><span>.*?</span></div>',
        f'<div class="panel-title"><h2>SNS反応マップ</h2><span>意見{len(all_opinions)}件 | セクター=論点 / 中心に近いほど冷静 / 色=立場</span></div>',
        "arena heading",
    )
    page = replace_once(page, r"const SM_RAW = \[.*?\n\];", sm_raw(all_opinions), "SM_RAW", flags=re.DOTALL)
    issue_js = "const ISSUES=[\n" + ",\n".join(
        f"    {{k:{js(issue)},n:{issue_counts[issue]}}}" for issue in ISSUES
    ) + "\n  ];"
    arena_pos = page.index("<h2>SNS反応マップ</h2>")
    before, after = page[:arena_pos], page[arena_pos:]
    after = replace_once(after, r"const ISSUES=\[.*?\n  \];", issue_js, "arena issues", flags=re.DOTALL)
    page = before + after

    page = replace_once(
        page,
        r'<section class="panel conflict-panel"><div class="panel-title"><h2>7つの論点とXの声</h2>.*?(?=<section class="panel explainer-section">)',
        issue_panel(all_opinions),
        "issue panel",
        flags=re.DOTALL,
    )
    page = replace_once(
        page,
        r'<section class="panel conflict-panel"><div class="panel-title"><h2>(?:スタンス集計|Hermes分類サマリー|投稿の分類結果)</h2>.*?(?=<section class="panel" id="related-topics">)',
        summary_panel(all_opinions),
        "summary panel",
        flags=re.DOTALL,
    )
    page = replace_once(
        page,
        r'<section class="panel details-panel" id="detail-data">.*?</section>(?=\s*</main>)',
        details_panel(all_rows, all_opinions),
        "details panel",
        flags=re.DOTALL,
    )
    page = page.replace(
        "<strong>データの集め方:</strong> Yahooリアルタイム検索からSNS投稿を取得し、AIが自動分類しました。",
        f"<strong>データの集め方:</strong> Yahooリアルタイム検索からSNS投稿を取得し、Hermesが論点・スタンス・強度を分類しました。最終更新: {args.current_date}。",
    )
    page = re.sub(
        r"(<strong>データの集め方:</strong> Yahooリアルタイム検索からSNS投稿を取得し、Hermesが論点・スタンス・強度を分類しました。最終更新: )\d{4}-\d{2}-\d{2}(。)",
        rf"\g<1>{args.current_date}\g<2>",
        page,
        count=1,
    )
    page = page.replace(
        "function colorOf(p){return p.x>=0.5?'#059669':(p.x<=-0.5?'#dc2626':'#64748b');}",
        "function colorOf(p){return p.x>=1?'#059669':(p.x>0?'#d97706':(p.x<=-0.5?'#dc2626':'#64748b'));}",
    )
    page = page.replace(
        '<span><i style="background:#059669"></i>移行支持</span>\n'
        '    <span><i style="background:#dc2626"></i>移行反対</span>\n'
        '    <span><i style="background:#64748b"></i>中立</span>',
        '<span><i style="background:#059669"></i>移行支持</span>\n'
        '    <span><i style="background:#d97706"></i>条件付き</span>\n'
        '    <span><i style="background:#dc2626"></i>慎重・反対</span>\n'
        '    <span><i style="background:#64748b"></i>中立</span>',
    )
    page = page.replace("Powered by Yahooリアルタイム検索 + AI分類", "公開投稿を収集・分類して整理")
    page = page.replace("Powered by Yahooリアルタイム検索 + Hermes分類", "公開投稿を収集・分類して整理")

    output = args.output_html or args.html
    output.write_text(page, encoding="utf-8")
    print(json.dumps({
        "collected": len(all_rows),
        "relevant": relevant_count,
        "opinions": len(all_opinions),
        "previous_opinions": len(previous),
        "current_opinions": len(current),
        "top_issue": top_issue,
        "top_issue_count": top_count,
        "tide": tide,
        "output": str(output),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
