#!/usr/bin/env python3
"""Build a reusable static SNS reaction map from classified reaction JSON."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_STANCE_ORDER = ["批判", "擁護", "賛成", "反対", "比較", "未確認", "保留", "その他"]

TOPIC_THEME_COLORS: dict[str, dict[str, str]] = {
    "政治": {"grad_1": "#dc2626", "grad_2": "#991b1b", "accent": "#dc2626", "accent_soft": "#fef2f2", "bg": "#fffbfb", "section_bg1": "#fef2f2"},
    "教育": {"grad_1": "#0891b2", "grad_2": "#155e75", "accent": "#0891b2", "accent_soft": "#ecfeff", "bg": "#f8fdfe", "section_bg1": "#ecfeff"},
    "テック": {"grad_1": "#7c3aed", "grad_2": "#5b21b6", "accent": "#7c3aed", "accent_soft": "#f5f3ff", "bg": "#faf8ff", "section_bg1": "#f5f3ff"},
    "交通": {"grad_1": "#0d9488", "grad_2": "#115e59", "accent": "#0d9488", "accent_soft": "#f0fdfa", "bg": "#f8fffe", "section_bg1": "#f0fdfa"},
    "スポーツ": {"grad_1": "#ea580c", "grad_2": "#9a3412", "accent": "#ea580c", "accent_soft": "#fff7ed", "bg": "#fffcf8", "section_bg1": "#fff7ed"},
    "default": {"grad_1": "#1769d1", "grad_2": "#0a3d91", "accent": "#1769d1", "accent_soft": "#e7f1ff", "bg": "#f3f5f8", "section_bg1": "#eff6ff"},
}

DEFAULT_CONFIG = {
    "title": "SNS反応まっぷ",
    "subtitle": "投稿サンプルを、論点カテゴリ・検索クエリ・立場で可視化した編集用ビューです。",
    "source_label": "SNS/Yahooリアルタイム検索",
    "category_order": [],
    "stance_order": DEFAULT_STANCE_ORDER,
    "sample_limit_per_category": 3,
    "show_raw_text": True,
    "notes": [
        "これは世論調査ではなく、取得した投稿サンプルの反応整理です。",
        "投稿本文の転載は最小限にし、公開記事では要約中心にしてください。",
        "代表投稿は公開前に人間が確認する前提です。",
    ],
    "conflict_axes": [],
    "category_tones": {},
    "nav_links": [],
    "grad_1": "",
    "grad_2": "",
    "hero_badge": "",
    "hero_image": "",
    "topic_type": "",
}


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def read_json(path: str) -> Any:
    return json.loads(resolve(path).read_text(encoding="utf-8"))


def merge_config(config_path: str | None) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    if config_path:
        user_config = read_json(config_path)
        config.update(user_config)
    return config


def resolve_theme(config: dict[str, Any]) -> dict[str, str]:
    topic_type = str(config.get("topic_type") or "")
    for keyword, colors in TOPIC_THEME_COLORS.items():
        if keyword != "default" and keyword in topic_type:
            return colors
    return TOPIC_THEME_COLORS["default"]


def pct(value: int, max_value: int) -> float:
    if max_value <= 0:
        return 0.0
    return value / max_value


def heat_color(value: int, max_value: int) -> str:
    ratio = pct(value, max_value)
    if value == 0:
        return "#f5f6f8"
    if ratio < 0.2:
        return "#dceeff"
    if ratio < 0.4:
        return "#9fd0ff"
    if ratio < 0.6:
        return "#4da3ff"
    if ratio < 0.8:
        return "#1769d1"
    return "#0a3d91"


def text_color(value: int, max_value: int) -> str:
    return "#ffffff" if pct(value, max_value) >= 0.55 else "#172033"


def classification(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("classification") or {}


def category_of(row: dict[str, Any]) -> str:
    return str(classification(row).get("category") or "未分類")


def stance_of(row: dict[str, Any]) -> str:
    return str(classification(row).get("stance") or classification(row).get("stance_to_target") or "その他")


def summary_of(row: dict[str, Any]) -> str:
    return str(classification(row).get("summary") or "").strip()


def confidence_of(row: dict[str, Any]) -> float:
    try:
        return float(classification(row).get("confidence") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def ordered_values(found: set[str], preferred: list[str]) -> list[str]:
    ordered = [value for value in preferred if value in found]
    ordered.extend(sorted(found - set(ordered)))
    return ordered


def table_html(title: str, first_col: str, rows: list[str], cols: list[str], counts: Counter[tuple[str, str]]) -> str:
    max_value = max(counts.values(), default=0)
    out = [f"<section class=\"panel heat-panel\"><div class=\"panel-title\"><h2>{html.escape(title)}</h2><span>色が濃いほど件数が多い</span></div>", "<div class=\"table-wrap\"><table class=\"heat-table\">"]
    out.append(
        "<thead><tr>"
        f"<th>{html.escape(first_col)}</th>"
        + "".join(f"<th>{html.escape(col)}</th>" for col in cols)
        + "<th>合計</th></tr></thead>"
    )
    out.append("<tbody>")
    for row in rows:
        total = sum(counts.get((row, col), 0) for col in cols)
        out.append(f"<tr data-category=\"{html.escape(row)}\"><th><span class=\"row-dot\"></span>{html.escape(row)}</th>")
        for col in cols:
            value = counts.get((row, col), 0)
            zero_class = " zero" if value == 0 else ""
            out.append(
                f"<td class=\"heat-cell{zero_class}\" "
                f"style=\"background:{heat_color(value, max_value)};color:{text_color(value, max_value)}\" "
                f"title=\"{html.escape(row)} / {html.escape(col)}: {value}件\"><span>{value}</span></td>"
            )
        out.append(f"<td class=\"total\">{total}</td></tr>")
    out.append("</tbody></table></div></section>")
    return "\n".join(out)


def category_counts_html(categories: list[str], counts: Counter[str]) -> str:
    max_value = max(counts.values(), default=0)
    out = ["<section class=\"panel\"><div class=\"panel-title\"><h2>分類別件数</h2><span>論点の量感</span></div>", "<div class=\"bar-list\">"]
    for category in categories:
        value = counts.get(category, 0)
        width = 0 if max_value == 0 else round((value / max_value) * 100)
        out.append(
            f"<div class=\"bar-row\" data-category=\"{html.escape(category)}\">"
            f"<div class=\"bar-meta\"><span>{html.escape(category)}</span><strong>{value}</strong></div>"
            "<div class=\"bar-track\">"
            f"<div class=\"bar-fill\" style=\"width:{width}%\"></div>"
            "</div>"
            "</div>"
        )
    out.append("</div></section>")
    return "\n".join(out)


def _is_x_url(url: str) -> bool:
    return bool(re.match(r"https?://(twitter\.com|x\.com)/\w+/status/\d+", url))


def _slug(text: str) -> str:
    return re.sub(r"[^\w]", "-", text).strip("-")[:60]


def representative_html(rows: list[dict[str, Any]], categories: list[str], config: dict[str, Any]) -> str:
    sample_limit = int(config.get("sample_limit_per_category") or 3)
    show_raw_text = bool(config.get("show_raw_text", True))
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    sorted_rows = sorted(
        rows,
        key=lambda row: (
            not bool(classification(row).get("article_usable", False)),
            -confidence_of(row),
        ),
    )
    for row in sorted_rows:
        category = category_of(row)
        if len(buckets[category]) < sample_limit:
            buckets[category].append(row)

    out = ['<section class="panel"><div class="panel-title"><h2>代表サンプル</h2></div>', '<div class="sample-grid">']
    for category in categories:
        items = buckets.get(category, [])
        if not items:
            continue
        cat_id = _slug(category)
        out.append(f'<article class="sample-card" id="sample-{cat_id}"><h3>{html.escape(category)}</h3><div>')
        for row in items:
            c = classification(row)
            text = str(row.get("text", "")).replace("\n", " ")
            if len(text) > 180:
                text = text[:177] + "..."
            out.append(
                '<div class="sample">'
                f'<div class="meta">{html.escape(stance_of(row))} / 信頼度 {confidence_of(row):.2f}</div>'
                f'<p>{html.escape(summary_of(row) or text)}</p>'
            )
            url = str(row.get("url", "")).strip()
            if url and _is_x_url(url):
                out.append(
                    f'<blockquote class="twitter-tweet" data-conversation="none" data-dnt="true">'
                    f'<a href="{html.escape(url)}"></a></blockquote>'
                )
            elif show_raw_text:
                out.append(f"<blockquote>{html.escape(text)}</blockquote>")
                if url:
                    out.append(f'<a href="{html.escape(url)}">投稿URL</a>')
            elif url:
                out.append(f'<a href="{html.escape(url)}">投稿URL</a>')
            reason = str(c.get("reason") or "").strip()
            if reason:
                out.append(f'<div class="reason">理由: {html.escape(reason)}</div>')
            out.append("</div>")
        out.append("</div></article>")
    out.append("</div></section>")
    return "\n".join(out)


def notes_html(config: dict[str, Any]) -> str:
    notes = [str(note) for note in config.get("notes", []) if str(note).strip()]
    if not notes:
        return ""
    lines = ["<section class=\"note-panel\"><h2>注意</h2><ul>"]
    for note in notes:
        lines.append(f"<li>{html.escape(note)}</li>")
    lines.append("</ul></section>")
    return "\n".join(lines)


def nav_html(config: dict[str, Any]) -> str:
    links = config.get("nav_links") or []
    if not links:
        return ""
    items = []
    for link in links:
        label = str(link.get("label") or "").strip()
        url = str(link.get("url") or "").strip()
        if label and url:
            items.append(f'<a href="{html.escape(url)}">{html.escape(label)}</a>')
    if not items:
        return ""
    return f'<nav class="top-nav">{"".join(items)}</nav>'


TONE_COLORS = {
    "positive": ("#1769d1", "#e7f1ff", "#0f4e9d"),
    "negative": ("#b54708", "#fff1e8", "#8a3206"),
    "safety": ("#16885a", "#e8f7ef", "#0f6845"),
    "neutral": ("#667085", "#f2f4f7", "#344054"),
    "warning": ("#7a4cc2", "#f2ecff", "#55348a"),
    "derived": ("#0f7490", "#e5f7fb", "#0b586d"),
}


def css_attr(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_tone_css(config: dict[str, Any]) -> str:
    category_tones = config.get("category_tones") or {}
    lines = []
    for category, tone in category_tones.items():
        main, soft, text = TONE_COLORS.get(str(tone), TONE_COLORS["neutral"])
        selector = css_attr(str(category))
        lines += [
            f'[data-category="{selector}"] th {{ border-left: 5px solid {main}; }}',
            f'[data-category="{selector}"] .row-dot {{ background: {main}; }}',
            f'[data-category="{selector}"] .bar-fill {{ background: linear-gradient(90deg, {soft}, {main}); }}',
            f'[data-category="{selector}"] .bar-meta span {{ color: {text}; font-weight: 700; }}',
        ]
    for tone, (main, soft, text) in TONE_COLORS.items():
        lines += [
            f'.axis-card[data-tone="{tone}"] {{ border-top: 5px solid {main}; background: linear-gradient(180deg, #fff, {soft}); }}',
            f'.axis-card[data-tone="{tone}"] .axis-kicker {{ color: {text}; }}',
            f'.axis-card[data-tone="{tone}"] .axis-tags span {{ background: {soft}; color: {text}; }}',
        ]
    return "\n".join(lines)


def conflict_axes_html(rows: list[dict[str, Any]], config: dict[str, Any]) -> str:
    axes = config.get("conflict_axes") or []
    if not axes:
        return ""
    counts = Counter(category_of(row) for row in rows)
    cards = []
    for axis in axes:
        categories = list(axis.get("categories") or [])
        count = sum(counts.get(category, 0) for category in categories)
        cards.append(
            f"<article class=\"axis-card\" data-tone=\"{html.escape(str(axis.get('tone') or 'neutral'))}\">"
            f"<div class=\"axis-kicker\">{html.escape(str(axis.get('kicker') or '対立軸'))}</div>"
            f"<h3>{html.escape(str(axis.get('label') or ''))}</h3>"
            f"<div class=\"axis-count\">{count}<span>件</span></div>"
            f"<p>{html.escape(str(axis.get('description') or ''))}</p>"
            f"<div class=\"axis-tags\">{''.join(f'<a href=\"#sample-{_slug(category)}\" style=\"text-decoration:none;color:inherit;\"><span>{html.escape(category)}</span></a>' for category in categories)}</div>"
            "</article>"
        )
    return (
        "<section class=\"panel conflict-panel\">"
        "<div class=\"panel-title\"><h2>対立軸</h2><span>何を評価し、何を問題視しているか</span></div>"
        f"<div class=\"axis-grid\">{''.join(cards)}</div>"
        "</section>"
    )


TONE_TO_SEMICIRCLE_COLOR = {
    "negative": "#e07040",
    "positive": "#4a90d9",
    "derived": "#0f7490",
    "warning": "#7a4cc2",
    "neutral": "#94a3b8",
    "safety": "#16885a",
}


def vote_ui_html(config: dict[str, Any]) -> str:
    axes = config.get("conflict_axes") or []
    if len(axes) < 2:
        return ""
    topic_id = config.get("title", "topic").replace(" ", "_")[:20]
    axes_js = json.dumps(
        [{"kicker": a.get("kicker", ""), "label": a.get("label", ""),
          "tone": a.get("tone", "neutral"), "color": TONE_TO_SEMICIRCLE_COLOR.get(a.get("tone", "neutral"), "#94a3b8")}
         for a in axes],
        ensure_ascii=False,
    )
    title_for_share = config.get("title", "SNS反応まっぷ")
    vote_intro = config.get("vote_intro", "")
    vote_method = config.get("vote_method", "")
    vote_labels = config.get("vote_labels") or []

    supabase_url_js = json.dumps(config.get("supabase_url") or "")
    supabase_anon_key_js = json.dumps(config.get("supabase_anon_key") or "")

    intro_html = ""
    if vote_intro:
        intro_html = f'<p style="font-size:14px;color:var(--ink);line-height:1.75;margin:0 0 12px;">{html.escape(vote_intro)}</p>'
    method_html = ""
    if vote_method:
        method_html = (
            f'<div style="font-size:12px;color:var(--muted);background:var(--accent-soft);border-radius:8px;'
            f'padding:10px 14px;margin:0 0 16px;line-height:1.65;">'
            f'<span style="font-weight:700;">データの集め方:</span> {html.escape(vote_method)}</div>'
        )

    # Build vote_labels into axes_js — override kicker/label with user-friendly labels
    axes_with_labels = []
    for i, a in enumerate(axes):
        label = vote_labels[i] if i < len(vote_labels) else a.get("label", "")
        axes_with_labels.append({
            "kicker": a.get("kicker", ""),
            "label": label,
            "origLabel": a.get("label", ""),
            "tone": a.get("tone", "neutral"),
            "color": TONE_TO_SEMICIRCLE_COLOR.get(a.get("tone", "neutral"), "#94a3b8"),
        })
    axes_js = json.dumps(axes_with_labels, ensure_ascii=False)

    return f"""<section class="panel" id="vote-section">
<div class="panel-title"><h2>この話題、あなたはどう感じる？</h2><span>SNSの声を見る前に</span></div>
{intro_html}
{method_html}
<p style="font-size:13px;color:var(--ink);font-weight:700;margin:0 0 14px;">結果を見る前に — あなたの感覚に近いのは？</p>
<div id="vote-buttons" style="display:flex;flex-wrap:wrap;gap:10px;margin-bottom:8px;"></div>
<p style="font-size:11px;color:var(--muted);margin:0;">※ 世論調査ではありません。投票は集計されサーバーに保存されます。</p>
<div id="vote-result" style="display:none;margin-top:20px;">
  <div style="background:var(--accent-soft);border-radius:10px;padding:16px;margin-bottom:16px;">
    <div style="font-size:13px;font-weight:700;color:var(--accent);margin-bottom:8px;" id="vote-position-label"></div>
    <div style="font-size:12px;color:var(--muted);line-height:1.7;" id="vote-position-text"></div>
  </div>
  <div style="font-size:14px;font-weight:700;margin-bottom:12px;">みんなの感覚（投票集計）</div>
  <div id="vote-bars" style="margin-bottom:16px;"></div>
  <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px;">
    <a id="share-x" href="#" target="_blank" rel="noopener"
       style="display:inline-flex;align-items:center;gap:6px;padding:8px 18px;border-radius:8px;background:#000;color:#fff;text-decoration:none;font-size:13px;font-weight:700;">
      𝕏 でシェア
    </a>
    <button id="vote-redo-btn"
       style="padding:8px 18px;border-radius:8px;border:1px solid var(--line);background:var(--panel);cursor:pointer;font-size:13px;font-weight:600;">
      投票をやり直す
    </button>
  </div>
  <p style="font-size:12px;color:var(--muted);margin:0;">下にスクロールすると、SNS投稿の自動分類結果（勢力図）を確認できます。<br>あなたの感覚と、SNSの声の分布を見比べてみてください。</p>
</div>
</section>
<script>
(function(){{
  var TOPIC="{html.escape(topic_id)}";
  var axes={axes_js};
  var TITLE="{html.escape(title_for_share)}";
  var KEY="sns_vote_"+TOPIC;

  var supabaseUrl={supabase_url_js};
  var supabaseAnonKey={supabase_anon_key_js};
  var supabaseClient=null;

  if(supabaseUrl && supabaseAnonKey && typeof supabase!=="undefined"){{
    supabaseClient=supabase.createClient(supabaseUrl, supabaseAnonKey);
    // Supabase mode: hide the redo button to prevent abuse and desync
    var redoBtn=document.getElementById("vote-redo-btn");
    if(redoBtn) redoBtn.style.display="none";
  }}

  var stored={{}};
  var myVote=localStorage.getItem(KEY+"_my");

  // Blur the semicircle chart until voted (deferred to ensure DOM is ready)
  function applyBlur(){{
    var chartPanel=document.getElementById("semicircle-chart");
    if(chartPanel){{
      var wrap=chartPanel.closest(".panel");
      if(wrap && myVote===null){{
        wrap.id="chart-panel";
        wrap.style.filter="blur(8px)";wrap.style.pointerEvents="none";wrap.style.userSelect="none";
        wrap.style.position="relative";
        var overlay=document.createElement("div");
        overlay.id="chart-overlay";
        overlay.style.cssText="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;z-index:5;background:rgba(255,255,255,.3);border-radius:8px;";
        overlay.innerHTML='<div style="text-align:center;"><div style="font-size:16px;font-weight:800;color:var(--ink);">まず投票してから結果を見よう</div><div style="font-size:12px;color:var(--muted);margin-top:4px;">上の投票ボタンを押すと解除されます</div></div>';
        wrap.appendChild(overlay);
      }}
    }}
  }}
  
  async function fetchVotes(){{
    if(supabaseClient){{
      try{{
        var res=await supabaseClient
          .from("votes")
          .select("choice_idx")
          .eq("topic_id", TOPIC);
        if(res.error) throw res.error;
        stored={{}};
        (res.data||[]).forEach(function(row){{
          var idx=row.choice_idx;
          stored[idx]=(stored[idx]||0)+1;
        }});
      }}catch(err){{
        console.error("Error fetching votes from Supabase:", err);
        stored=JSON.parse(localStorage.getItem(KEY+"_counts")||"{{}}");
      }}
    }}else{{
      stored=JSON.parse(localStorage.getItem(KEY+"_counts")||"{{}}");
    }}
    if(myVote!==null){{
      showResults(parseInt(myVote));
    }}
  }}

  if(document.readyState==="loading"){{
    document.addEventListener("DOMContentLoaded", function(){{ applyBlur(); fetchVotes(); }});
  }}else{{
    setTimeout(function(){{ applyBlur(); fetchVotes(); }},0);
  }}

  var btnWrap=document.getElementById("vote-buttons");
  axes.forEach(function(a,i){{
    var btn=document.createElement("button");
    btn.style.cssText="flex:1;min-width:140px;padding:14px 12px;border-radius:12px;border:2px solid "+a.color+";background:"+a.color+"10;cursor:pointer;transition:all .15s;text-align:center;";
    btn.innerHTML='<div style="font-size:13px;font-weight:700;color:var(--ink);line-height:1.4;">'+a.label+'</div>';
    btn.onmouseenter=function(){{btn.style.background=a.color+"22";btn.style.transform="translateY(-2px)"}};
    btn.onmouseleave=function(){{btn.style.background=a.color+"10";btn.style.transform="none"}};
    btn.onclick=function(){{castVote(i)}};
    btnWrap.appendChild(btn);
  }});

  document.getElementById("vote-redo-btn").onclick=function(){{
    localStorage.removeItem(KEY+"_my");
    location.reload();
  }};

  function revealChart(){{
    var wrap=document.getElementById("chart-panel");
    if(wrap){{
      wrap.style.transition="filter .6s ease";
      wrap.style.filter="none";wrap.style.pointerEvents="auto";wrap.style.userSelect="auto";
      var ov=document.getElementById("chart-overlay");
      if(ov)ov.remove();
    }}
  }}

  async function castVote(idx){{
    if(myVote!==null) return;
    
    var btns=btnWrap.querySelectorAll("button");
    btns.forEach(function(b){{b.disabled=true; b.style.opacity="0.5"}});

    if(supabaseClient){{
      var success=false;
      try{{
        var res=await supabaseClient
          .from("votes")
          .insert([{{ topic_id: TOPIC, choice_idx: idx }}]);
        if(res.error) throw res.error;
        success=true;
      }}catch(err){{
        console.error("Error casting vote to Supabase:", err);
        var msg=err.message||"";
        var details=err.details||"";
        if(msg.indexOf("already voted")!==-1 || details.indexOf("already voted")!==-1){{
          alert("24時間以内に同一IPアドレスからすでに投票されています。集計結果のみ表示します。");
          success=true;
        }}else{{
          alert("投票データの送信中にエラーが発生しました。");
          // Local fallback in case of connection failure
          stored[idx]=(stored[idx]||0)+1;
          localStorage.setItem(KEY+"_counts",JSON.stringify(stored));
        }}
      }}
      if(success){{
        await fetchVotes();
      }}
    }}else{{
      // Pure local fallback
      stored[idx]=(stored[idx]||0)+1;
      localStorage.setItem(KEY+"_counts",JSON.stringify(stored));
    }}

    localStorage.setItem(KEY+"_my",""+idx);
    myVote=""+idx;
    revealChart();
    showResults(idx);
  }}

  function showResults(myIdx){{
    var total=0;
    axes.forEach(function(_,i){{total+=(stored[i]||0)}});
    if(total===0)total=1;

    var myAxis=axes[myIdx];
    var posLabel=document.getElementById("vote-position-label");
    var posText=document.getElementById("vote-position-text");
    posLabel.textContent="あなたの選択: 「"+myAxis.label+"」";
    posLabel.style.color=myAxis.color;
    posText.textContent="下のSNS投稿の自動分類結果と見比べて、SNSの声とあなたの感覚がどれくらい近いか確認してみてください。";

    var barsEl=document.getElementById("vote-bars");
    barsEl.innerHTML="";
    axes.forEach(function(a,i){{
      var c=stored[i]||0;
      var pct=Math.round(c/total*100);
      var isMine=i===myIdx;
      var row=document.createElement("div");
      row.style.cssText="margin-bottom:8px;";
      row.innerHTML='<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
        +'<span style="font-size:12px;font-weight:'+(isMine?'800':'600')+';color:'+(isMine?a.color:'var(--ink)')+';">'
        +(isMine?'✓ ':'')+a.label+'</span>'
        +'<span style="font-size:14px;font-weight:800;color:'+a.color+'">'+pct+'% ('+c+'票)</span></div>'
        +'<div style="height:8px;border-radius:4px;background:var(--line);overflow:hidden;">'
        +'<div style="height:100%;width:'+pct+'%;background:'+a.color+';border-radius:4px;transition:width .4s ease;"></div></div>';
      barsEl.appendChild(row);
    }});

    // Improved X share text with dynamic percentages
    var shareBtn=document.getElementById("share-x");
    var pctList=axes.map(function(a,i){{
      var c=stored[i]||0;
      var pct=Math.round(c/total*100);
      return a.label+" "+pct+"%";
    }}).join(" / ");
    
    var text="【"+TITLE+"】\\nこの話題、私は「"+myAxis.label+"」に投票しました（"+pctList+"）。\\nSNSの声の分布と自分の感覚、あなたも比べてみて。\\n\\n#SNS反応まっぷ";
    shareBtn.href="https://x.com/intent/tweet?text="+encodeURIComponent(text);
    var shortLabel=myAxis.label.length>15?myAxis.label.substring(0,15)+"…":myAxis.label;
    shareBtn.textContent="𝕏 でシェア「"+shortLabel+"」";

    document.getElementById("vote-result").style.display="block";
    document.getElementById("vote-result").scrollIntoView({{behavior:"smooth",block:"nearest"}});
  }}
}})();
</script>"""


def semicircle_html(categories: list[str], counts: Counter[str], config: dict[str, Any] = None) -> str:
    axes = (config or {}).get("conflict_axes") or []
    category_tones = (config or {}).get("category_tones") or {}
    if axes:
        items = []
        for axis in axes:
            label = str(axis.get("label") or "")
            tone = str(axis.get("tone") or "neutral")
            color = TONE_TO_SEMICIRCLE_COLOR.get(tone, "#94a3b8")
            axis_cats = list(axis.get("categories") or [])
            cnt = sum(counts.get(cat, 0) for cat in axis_cats)
            if cnt > 0:
                items.append({"label": label, "count": cnt, "color": color, "cats": axis_cats})
        uncovered = set(categories) - {cat for item in items for cat in item["cats"]}
        uncovered_count = sum(counts.get(cat, 0) for cat in uncovered)
        if uncovered_count > 0:
            items.append({"label": "その他", "count": uncovered_count, "color": "#cbd5e1", "cats": list(uncovered)})
    else:
        items = []
        for i, cat in enumerate(categories):
            cnt = counts.get(cat, 0)
            if cnt > 0:
                tone = category_tones.get(cat, "neutral")
                color = TONE_TO_SEMICIRCLE_COLOR.get(tone, "#94a3b8")
                items.append({"label": cat, "count": cnt, "color": color, "cats": [cat]})
    if not items:
        return ""
    total = sum(item["count"] for item in items)
    data_js = json.dumps(
        [{"label": item["label"], "count": item["count"], "color": item["color"],
          "cats": ", ".join(item["cats"])}
         for item in items],
        ensure_ascii=False,
    )
    # Reorder: left side = first axis, right side = second axis, rest in between
    # This creates a left-vs-right confrontation layout
    if len(items) >= 2:
        left = items[0]
        right = items[1]
        middle = items[2:]
        ordered = [left] + middle + [right]
    else:
        ordered = items
        left = items[0] if items else None
        right = items[1] if len(items) > 1 else None

    ordered_js = json.dumps(
        [{"label": item["label"], "count": item["count"], "color": item["color"],
          "cats": ", ".join(item["cats"])}
         for item in ordered],
        ensure_ascii=False,
    )

    left_html = ""
    right_html = ""
    if left:
        left_html = (
            f'<div style="text-align:center;padding:8px 16px;border-radius:10px;'
            f'background:{left["color"]}12;border:2px solid {left["color"]};">'
            f'<div style="font-size:12px;font-weight:700;color:{left["color"]}">{html.escape(left["label"])}</div>'
            f'<div style="font-size:32px;font-weight:800;color:{left["color"]};line-height:1.2">{left["count"]}</div>'
            f'</div>'
        )
    if right:
        right_html = (
            f'<div style="text-align:center;padding:8px 16px;border-radius:10px;'
            f'background:{right["color"]}12;border:2px solid {right["color"]};">'
            f'<div style="font-size:12px;font-weight:700;color:{right["color"]}">{html.escape(right["label"])}</div>'
            f'<div style="font-size:32px;font-weight:800;color:{right["color"]};line-height:1.2">{right["count"]}</div>'
            f'</div>'
        )

    half = total // 2

    return f"""<section class="panel">
<div class="panel-title"><h2>反応の勢力図</h2><span>対立軸ごとの比率</span></div>
<div style="display:flex;justify-content:space-between;align-items:flex-end;max-width:660px;margin:0 auto 8px;padding:0 10px;">
  {left_html}
  <div style="text-align:center;color:var(--muted);font-size:12px;">
    <div style="font-size:11px;">過半数</div>
    <div style="font-weight:800;font-size:16px;color:var(--ink);">{half + 1}</div>
    <div style="font-size:18px;">▼</div>
  </div>
  {right_html}
</div>
<div style="position:relative;max-width:660px;margin:0 auto;">
  <svg viewBox="0 0 660 350" id="semicircle-chart" style="font-family:-apple-system,BlinkMacSystemFont,'Hiragino Sans',sans-serif;"></svg>
  <div style="position:absolute;bottom:12px;left:50%;transform:translateX(-50%);text-align:center;">
    <div style="font-size:42px;font-weight:800;color:var(--ink);line-height:1;">{total}</div>
    <div style="font-size:14px;color:var(--muted);">サンプル</div>
  </div>
</div>
<div id="semicircle-legend" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px 20px;margin-top:16px;"></div>
<script>
(function(){{
  var data={ordered_js};
  var total=data.reduce(function(s,d){{return s+d.count}},0);
  var cx=330,cy=310,outerR=290,innerR=160,gap=0.008;
  var svg=document.getElementById("semicircle-chart");
  var startAngle=Math.PI;
  data.forEach(function(d,idx){{
    var sweep=(d.count/total)*Math.PI-gap;
    var endAngle=startAngle+sweep;
    var x1o=cx+outerR*Math.cos(startAngle),y1o=cy+outerR*Math.sin(startAngle);
    var x2o=cx+outerR*Math.cos(endAngle),y2o=cy+outerR*Math.sin(endAngle);
    var x1i=cx+innerR*Math.cos(endAngle),y1i=cy+innerR*Math.sin(endAngle);
    var x2i=cx+innerR*Math.cos(startAngle),y2i=cy+innerR*Math.sin(startAngle);
    var la=sweep>Math.PI?1:0;
    var path="M "+x1o+" "+y1o+" A "+outerR+" "+outerR+" 0 "+la+" 1 "+x2o+" "+y2o+" L "+x1i+" "+y1i+" A "+innerR+" "+innerR+" 0 "+la+" 0 "+x2i+" "+y2i+" Z";
    var el=document.createElementNS("http://www.w3.org/2000/svg","path");
    el.setAttribute("d",path);el.setAttribute("fill",d.color);
    el.style.transition="opacity .15s";el.style.cursor="pointer";
    el.onmouseenter=function(){{el.style.opacity="0.75"}};
    el.onmouseleave=function(){{el.style.opacity="1"}};
    var t=document.createElementNS("http://www.w3.org/2000/svg","title");
    t.textContent=d.label+": "+d.count+"件 ("+(d.count/total*100).toFixed(1)+"%)"+"\\n"+d.cats;
    el.appendChild(t);svg.appendChild(el);
    var mid=startAngle+sweep/2,lr=(outerR+innerR)/2;
    if(d.count>=5){{
      var tx=document.createElementNS("http://www.w3.org/2000/svg","text");
      tx.setAttribute("x",cx+lr*Math.cos(mid));
      tx.setAttribute("y",cy+lr*Math.sin(mid)-8);
      tx.setAttribute("text-anchor","middle");tx.setAttribute("dominant-baseline","central");
      tx.setAttribute("font-size","26");tx.setAttribute("font-weight","800");
      tx.setAttribute("fill","#fff");tx.setAttribute("pointer-events","none");
      tx.textContent=d.count;svg.appendChild(tx);
    }}
    if(sweep>0.25){{
      var tx2=document.createElementNS("http://www.w3.org/2000/svg","text");
      var short=d.label.length>12?d.label.substring(0,12)+"…":d.label;
      tx2.setAttribute("x",cx+lr*Math.cos(mid));
      tx2.setAttribute("y",cy+lr*Math.sin(mid)+14);
      tx2.setAttribute("text-anchor","middle");tx2.setAttribute("dominant-baseline","central");
      tx2.setAttribute("font-size","11");tx2.setAttribute("font-weight","600");
      tx2.setAttribute("fill","rgba(255,255,255,.85)");tx2.setAttribute("pointer-events","none");
      tx2.textContent=short;svg.appendChild(tx2);
    }}
    startAngle=endAngle+gap;
  }});
  // Center line (majority marker)
  var lineX=cx;
  var el=document.createElementNS("http://www.w3.org/2000/svg","line");
  el.setAttribute("x1",lineX);el.setAttribute("y1",cy-outerR-5);
  el.setAttribute("x2",lineX);el.setAttribute("y2",cy-innerR+5);
  el.setAttribute("stroke","var(--ink,#172033)");el.setAttribute("stroke-width","2");
  el.setAttribute("stroke-dasharray","4,3");el.setAttribute("opacity","0.4");
  svg.appendChild(el);

  var leg=document.getElementById("semicircle-legend");
  data.forEach(function(d){{
    var item=document.createElement("div");
    item.style.cssText="display:flex;align-items:flex-start;gap:8px;font-size:13px;padding:6px 0;";
    item.innerHTML='<span style="width:14px;height:14px;border-radius:4px;background:'+d.color+';flex-shrink:0;margin-top:2px"></span><div><strong style="font-size:14px">'+d.label+'</strong> <span style="color:var(--accent);font-weight:800;font-size:16px;margin-left:4px">'+d.count+'</span><span style="color:var(--muted);font-size:11px;margin-left:2px">件</span><div style="color:var(--muted);font-size:11px;margin-top:2px">'+d.cats+'</div></div>';
    leg.appendChild(item);
  }});
}})();
</script>
</section>"""


def build(rows: list[dict[str, Any]], config: dict[str, Any]) -> str:
    category_found = {category_of(row) for row in rows}
    stance_found = {stance_of(row) for row in rows}
    query_found = {str(row.get("query", "") or "不明") for row in rows}

    categories = ordered_values(category_found, list(config.get("category_order") or []))
    stances = ordered_values(stance_found, list(config.get("stance_order") or DEFAULT_STANCE_ORDER))
    queries = sorted(query_found)

    by_query = Counter((category_of(row), str(row.get("query", "") or "不明")) for row in rows)
    by_stance = Counter((category_of(row), stance_of(row)) for row in rows)
    by_category = Counter(category_of(row) for row in rows)
    by_stance_total = Counter(stance_of(row) for row in rows)

    total = len(rows)
    top_category = by_category.most_common(1)[0] if by_category else ("", 0)
    top_stance = by_stance_total.most_common(1)[0] if by_stance_total else ("", 0)
    title = str(config.get("title") or "SNS反応まっぷ")
    subtitle = str(config.get("subtitle") or "")
    source_label = str(config.get("source_label") or "SNSサンプル")
    tone_css = build_tone_css(config)

    theme = resolve_theme(config)
    cfg_grad1 = config.get("grad_1") or theme["grad_1"]
    cfg_grad2 = config.get("grad_2") or theme["grad_2"]
    cfg_accent = theme["accent"]
    cfg_accent_soft = theme["accent_soft"]
    cfg_bg = theme["bg"]
    cfg_section_bg1 = theme["section_bg1"]

    hero_image = str(config.get("hero_image") or "")
    hero_image_css = ""
    if hero_image:
        hero_image_css = f"""
    .hero::before {{
      content: '';
      position: absolute;
      inset: 0;
      background: url('{hero_image}') center/cover no-repeat;
      opacity: .18;
      z-index: 0;
    }}"""

    hero_badge = str(config.get("hero_badge") or config.get("topic_type") or "")
    hero_badge_html = ""
    if hero_badge:
        hero_badge_html = f'<span style="display:inline-block;background:rgba(255,255,255,.2);color:#fff;padding:6px 18px;border-radius:999px;font-size:13px;font-weight:800;letter-spacing:.04em;margin-bottom:8px;backdrop-filter:blur(4px);border:1px solid rgba(255,255,255,.15);">{html.escape(hero_badge)}</span>'

    ogp_title = str(config.get("ogp_title") or config.get("title") or title)
    ogp_desc = str(config.get("ogp_description") or config.get("subtitle") or subtitle)
    canonical_url = str(config.get("canonical_url") or "")
    og_image = str(config.get("og_image") or "")

    ogp_meta_html = ""
    if ogp_title or ogp_desc or canonical_url or og_image:
        meta_tags = []
        if ogp_desc:
            meta_tags.append(f'  <meta name="description" content="{html.escape(ogp_desc)}">')
        if canonical_url:
            meta_tags.append(f'  <link rel="canonical" href="{html.escape(canonical_url)}">')
        meta_tags.append('  <meta property="og:site_name" content="SNS反応まっぷ">')
        meta_tags.append('  <meta property="og:type" content="article">')
        if ogp_title:
            meta_tags.append(f'  <meta property="og:title" content="{html.escape(ogp_title)}">')
            meta_tags.append(f'  <meta name="twitter:title" content="{html.escape(ogp_title)}">')
        if ogp_desc:
            meta_tags.append(f'  <meta property="og:description" content="{html.escape(ogp_desc)}">')
            meta_tags.append(f'  <meta name="twitter:description" content="{html.escape(ogp_desc)}">')
        if canonical_url:
            meta_tags.append(f'  <meta property="og:url" content="{html.escape(canonical_url)}">')
        if og_image:
            meta_tags.append(f'  <meta property="og:image" content="{html.escape(og_image)}">')
            meta_tags.append(f'  <meta name="twitter:image" content="{html.escape(og_image)}">')
        meta_tags.append('  <meta name="twitter:card" content="summary_large_image">')
        ogp_meta_html = "\n".join(meta_tags) + "\n"

    supabase_script = ""
    if config.get("supabase_url") and config.get("supabase_anon_key"):
        supabase_script = '  <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>\n'

    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
{ogp_meta_html}{supabase_script}  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
  <style>
    :root {{
      color-scheme: light;
      --bg: {cfg_bg};
      --ink: #172033;
      --muted: #667085;
      --line: #d7dce6;
      --panel: #ffffff;
      --accent: {cfg_accent};
      --accent-soft: {cfg_accent_soft};
      --shadow: 0 10px 28px rgba(16, 24, 40, .06);
      --grad-1: {cfg_grad1};
      --grad-2: {cfg_grad2};
      --section-bg1: {cfg_section_bg1};
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: "Noto Sans JP", -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", sans-serif;
      line-height: 1.65;
    }}
    .hero {{
      position: relative;
      background: linear-gradient(135deg, var(--grad-1), var(--grad-2));
      overflow: hidden;
    }}{hero_image_css}
    .hero-inner {{
      position: relative;
      z-index: 1;
      padding: 48px min(6vw, 72px) 40px;
    }}
    .hero h1 {{
      margin: 0 0 12px;
      font-size: clamp(28px, 5vw, 48px);
      font-weight: 900;
      color: #fff;
      letter-spacing: -.02em;
      line-height: 1.2;
    }}
    .hero .lead {{
      color: rgba(255,255,255,.85);
      font-size: clamp(15px, 2vw, 18px);
      max-width: 720px;
      line-height: 1.8;
    }}
    .wave-divider {{
      display: block;
      width: 100%;
      height: 50px;
      margin-top: -1px;
    }}
    .top-nav {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 20px;
    }}
    .top-nav a {{
      display: inline-flex;
      align-items: center;
      min-height: 32px;
      border: 1px solid rgba(255,255,255,.25);
      border-radius: 8px;
      padding: 5px 10px;
      background: rgba(255,255,255,.12);
      color: #fff;
      text-decoration: none;
      font-weight: 800;
      backdrop-filter: blur(4px);
    }}
    .top-nav a:hover {{ background: rgba(255,255,255,.2); }}
    h1 {{ margin: 0 0 8px; font-size: clamp(26px, 4vw, 42px); letter-spacing: 0; }}
    h2 {{ margin: 0 0 16px; font-size: 20px; }}
    h3 {{ margin: 0 0 12px; font-size: 16px; }}
    .lead {{ margin: 0; color: var(--muted); max-width: 960px; }}
    main {{ padding: 0; max-width: none; margin: 0; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 0;
      margin: 0;
      background: linear-gradient(135deg, var(--grad-1), var(--grad-2));
      position: relative;
    }}
    .stats::before {{
      content: '';
      position: absolute;
      inset: 0;
      background:
        radial-gradient(circle at 10% 50%, rgba(255,255,255,.15) 0%, transparent 50%),
        radial-gradient(circle at 90% 30%, rgba(255,255,255,.1) 0%, transparent 40%);
      pointer-events: none;
    }}
    .stat {{
      position: relative;
      padding: 28px 24px;
      border: none;
      border-radius: 0;
      box-shadow: none;
      background: transparent;
      color: #fff;
      border-right: 1px solid rgba(255,255,255,.15);
      transition: background .2s;
    }}
    .stat:last-child {{ border-right: none; }}
    .stat:hover {{ background: rgba(255,255,255,.08); }}
    .stat span {{
      display: block;
      color: rgba(255,255,255,.85);
      font-size: 13px;
      font-weight: 700;
      letter-spacing: .06em;
      margin-bottom: 6px;
    }}
    .stat strong {{
      display: block;
      font-size: 28px;
      font-weight: 900;
      color: #fff;
      line-height: 1.3;
    }}
    .panel, .note-panel {{
      background: transparent;
      border: none;
      border-radius: 0;
      padding: 48px min(6vw, 72px);
      margin: 0;
      box-shadow: none;
      position: relative;
      max-width: none;
    }}
    .panel:nth-of-type(odd) {{
      background: var(--section-bg1, #f8fafc);
    }}
    .panel:nth-of-type(even) {{
      background: #fff;
    }}
    #vote-section {{
      background: #fff !important;
      border-bottom: 1px solid var(--line);
    }}
    .panel > *,
    .note-panel > * {{
      max-width: 1000px;
      margin-left: auto;
      margin-right: auto;
    }}
    .panel-title {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 32px;
    }}
    .panel-title h2 {{
      margin: 0;
      font-size: 30px;
      font-weight: 900;
      letter-spacing: -.02em;
      display: flex;
      align-items: center;
      gap: 14px;
    }}
    .panel-title h2::before {{
      content: '';
      display: inline-block;
      width: 5px;
      height: 32px;
      background: linear-gradient(180deg, var(--grad-1), var(--grad-2));
      border-radius: 3px;
      flex-shrink: 0;
    }}
    .panel-title span {{
      color: var(--muted);
      font-size: 14px;
      white-space: nowrap;
      background: rgba(0,0,0,.04);
      padding: 6px 16px;
      border-radius: 999px;
      font-weight: 700;
      border: 1px solid rgba(0,0,0,.06);
    }}
    .table-wrap {{
      overflow-x: auto;
      border: none;
      border-radius: 16px;
      background: #fff;
      box-shadow: 0 4px 24px rgba(0,0,0,.06);
    }}
    table {{ width: 100%; border-collapse: separate; border-spacing: 0; min-width: 900px; }}
    table.compact {{ min-width: 420px; max-width: 760px; }}
    th, td {{
      border-right: 1px solid rgba(0,0,0,.04);
      border-bottom: 1px solid rgba(0,0,0,.04);
      padding: 14px;
      text-align: center;
      vertical-align: middle;
      white-space: nowrap;
    }}
    tr:last-child th, tr:last-child td {{ border-bottom: 0; }}
    th:last-child, td:last-child {{ border-right: 0; }}
    th:first-child {{
      text-align: left;
      position: sticky;
      left: 0;
      background: #fff;
      z-index: 1;
      min-width: 240px;
      max-width: 340px;
      white-space: normal;
      line-height: 1.45;
    }}
    .row-dot {{
      display: inline-block;
      width: 9px;
      height: 9px;
      border-radius: 999px;
      margin-right: 8px;
      background: #98a2b3;
      vertical-align: 1px;
    }}
    thead th {{
      position: sticky;
      top: 0;
      z-index: 2;
      background: linear-gradient(180deg, var(--grad-1), var(--grad-2));
      color: #fff;
      font-size: 12px;
      font-weight: 800;
      line-height: 1.35;
      white-space: normal;
      min-width: 112px;
      padding: 16px 14px;
    }}
    thead th:first-child {{ z-index: 3; background: linear-gradient(180deg, var(--grad-1), var(--grad-2)); color: #fff; }}
    td {{ font-weight: 800; font-variant-numeric: tabular-nums; }}
    tbody tr {{ transition: background .12s; }}
    tbody tr:hover {{ background: var(--accent-soft); }}
    .heat-cell {{
      transition: transform .12s ease, box-shadow .12s ease;
    }}
    .heat-cell span {{
      display: inline-flex;
      min-width: 34px;
      height: 34px;
      align-items: center;
      justify-content: center;
      border-radius: 10px;
      background: rgba(255, 255, 255, .2);
      font-size: 14px;
    }}
    .heat-cell:hover {{
      transform: scale(1.08);
      box-shadow: inset 0 0 0 2px rgba(23, 105, 209, .3);
    }}
    .heat-cell.zero {{
      color: #98a2b3 !important;
      font-weight: 600;
    }}
    .heat-cell.zero span {{ background: transparent; }}
    .total {{
      background: rgba(0,0,0,.03);
      font-weight: 900;
      min-width: 72px;
      font-size: 15px;
    }}
    .bar-list {{
      display: grid;
      gap: 4px;
      max-width: 1000px;
    }}
    .bar-row {{
      display: grid;
      gap: 8px;
      padding: 16px 20px;
      background: rgba(255,255,255,.7);
      border-radius: 14px;
      transition: all .2s;
      border: 1px solid rgba(0,0,0,.04);
      backdrop-filter: blur(4px);
    }}
    .bar-row:hover {{
      background: #fff;
      box-shadow: 0 8px 24px rgba(0,0,0,.06);
      transform: translateX(4px);
    }}
    .bar-meta {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      font-size: 14px;
    }}
    .bar-meta span {{ color: var(--ink); font-weight: 700; }}
    .bar-meta strong {{ font-variant-numeric: tabular-nums; font-size: 18px; font-weight: 900; }}
    .bar-track {{
      height: 14px;
      border-radius: 999px;
      overflow: hidden;
      background: rgba(0,0,0,.06);
    }}
    .bar-fill {{
      height: 100%;
      border-radius: inherit;
      transition: width .8s cubic-bezier(.22,1,.36,1);
    }}
    .axis-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 20px;
    }}
    .axis-card {{
      border: none;
      border-radius: 20px;
      padding: 28px;
      min-height: 240px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      transition: transform .25s cubic-bezier(.22,1,.36,1), box-shadow .25s;
      box-shadow: 0 4px 20px rgba(0,0,0,.06);
      position: relative;
      overflow: hidden;
    }}
    .axis-card:hover {{
      transform: translateY(-6px) scale(1.01);
      box-shadow: 0 20px 50px rgba(0,0,0,.12);
    }}
    .axis-kicker {{
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: .06em;
      color: var(--accent);
    }}
    .axis-card h3 {{
      margin: 0;
      font-size: 20px;
      font-weight: 900;
      line-height: 1.35;
    }}
    .axis-count {{
      display: inline-flex;
      align-items: baseline;
      gap: 4px;
      font-size: 44px;
      font-weight: 900;
      font-variant-numeric: tabular-nums;
      color: var(--ink);
    }}
    .axis-count span {{
      color: var(--muted);
      font-size: 14px;
      font-weight: 700;
    }}
    .axis-card p {{
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.7;
    }}
    .axis-tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: auto;
    }}
    .axis-tags span {{
      border-radius: 8px;
      padding: 5px 12px;
      font-size: 11px;
      font-weight: 700;
      background: var(--accent-soft);
      color: var(--accent);
    }}
    {tone_css}
    .legend {{
      display: flex;
      gap: 8px;
      align-items: center;
      color: var(--muted);
      font-size: 12px;
      margin-top: 16px;
      padding: 12px 18px;
      background: rgba(255,255,255,.6);
      border-radius: 12px;
      border: 1px solid rgba(0,0,0,.04);
    }}
    .chip {{ width: 28px; height: 14px; border-radius: 4px; border: 1px solid rgba(0,0,0,.06); }}
    .sample-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
    }}
    .sample-card {{
      border: none;
      border-radius: 20px;
      padding: 0;
      background: #fff;
      overflow: hidden;
      transition: transform .25s cubic-bezier(.22,1,.36,1), box-shadow .25s;
      box-shadow: 0 2px 12px rgba(0,0,0,.05);
    }}
    .sample-card:hover {{
      transform: translateY(-4px);
      box-shadow: 0 16px 40px rgba(0,0,0,.1);
    }}
    .sample-card > h3 {{
      margin: 0;
      padding: 18px 22px 14px;
      font-size: 15px;
      font-weight: 800;
      border-bottom: 1px solid var(--line);
    }}
    .sample-card > div {{
      padding: 16px 22px 20px;
    }}
    .sample {{ border-top: 1px solid var(--line); padding-top: 10px; margin-top: 10px; }}
    .meta {{
      color: var(--accent);
      font-size: 13px;
      font-weight: 800;
      letter-spacing: .04em;
    }}
    blockquote {{
      margin: 0 0 10px;
      padding: 14px 18px;
      border-left: 4px solid var(--accent);
      background: var(--accent-soft);
      border-radius: 0 12px 12px 0;
      font-size: 16px;
      line-height: 1.75;
      color: var(--ink);
    }}
    .reason {{ color: var(--ink); font-size: 14px; margin-top: 8px; line-height: 1.6; }}
    a {{ color: var(--accent); font-size: 13px; }}
    .note-panel {{
      background: linear-gradient(135deg, var(--accent-soft), #fff) !important;
      border-left: 5px solid var(--accent) !important;
      padding: 36px min(6vw, 72px) !important;
    }}
    .note-panel h2 {{ font-size: 22px; color: var(--accent); }}
    .note-panel ul {{ margin: 0; padding-left: 20px; }}
    .note-panel li {{ margin-bottom: 8px; font-size: 15px; line-height: 1.8; }}
    .conflict-panel {{
      border-top: 4px solid transparent !important;
      border-image: linear-gradient(90deg, var(--grad-1), var(--grad-2)) 1 !important;
    }}
    @media (max-width: 720px) {{
      .stats {{ grid-template-columns: repeat(2, 1fr); }}
      .stat {{ padding: 20px 16px; }}
      .stat strong {{ font-size: 18px; }}
      .panel, .note-panel {{ padding: 32px 16px !important; }}
      .axis-card {{ padding: 20px; min-height: auto; }}
      .axis-count {{ font-size: 32px; }}
      .sample-grid {{ grid-template-columns: 1fr; }}
      .bar-row {{ padding: 12px 14px; }}
      .panel-title {{ flex-direction: column; align-items: flex-start; gap: 8px; }}
      .panel-title h2 {{ font-size: 26px; }}
      .hero-inner {{ padding: 36px 16px 32px; }}
      th:first-child {{ min-width: 180px; }}
      table {{ min-width: 760px; }}
    }}
  </style>
</head>
<body>
  <section class="hero">
    <div class="hero-inner">
      {nav_html(config)}
      {hero_badge_html}
      <h1>{html.escape(title)}</h1>
      <p class="lead">{html.escape(subtitle)}</p>
    </div>
  </section>
  <svg class="wave-divider" viewBox="0 0 1440 50" preserveAspectRatio="none" fill="var(--bg)">
    <path d="M0,0 C360,50 1080,50 1440,0 L1440,50 L0,50 Z"/>
  </svg>
  <main>
    <section class="stats">
      <div class="stat"><span>総サンプル</span><strong>{total}</strong></div>
      <div class="stat"><span>ソース</span><strong>{html.escape(source_label)}</strong></div>
      <div class="stat"><span>最多カテゴリ</span><strong>{html.escape(top_category[0])} {top_category[1]}</strong></div>
      <div class="stat"><span>最多スタンス</span><strong>{html.escape(top_stance[0])} {top_stance[1]}</strong></div>
    </section>
    {vote_ui_html(config)}
    {semicircle_html(categories, by_category, config)}
    {conflict_axes_html(rows, config)}
    {category_counts_html(categories, by_category)}
    {table_html("カテゴリ × 検索クエリ", "分類", categories, queries, by_query)}
    <div class="legend">
      <span>少</span>
      <span class="chip" style="background:#f5f6f8"></span>
      <span class="chip" style="background:#dceeff"></span>
      <span class="chip" style="background:#9fd0ff"></span>
      <span class="chip" style="background:#4da3ff"></span>
      <span class="chip" style="background:#1769d1"></span>
      <span class="chip" style="background:#0a3d91"></span>
      <span>多</span>
    </div>
    {table_html("カテゴリ × スタンス", "分類", categories, stances, by_stance)}
    {representative_html(rows, categories, config)}
    {notes_html(config)}
  </main>
  <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
  <footer style="background:linear-gradient(135deg, var(--grad-2), var(--grad-1));border-top:none;padding:48px 24px;text-align:center;color:#fff;font-size:12px;line-height:1.8;">
    <div>Powered by Yahooリアルタイム検索 + AI分類</div>
    <a href="index.html" style="color:rgba(255,255,255,.85);text-decoration:none;font-weight:700;font-size:13px;">← SNS反応まっぷ トップへ</a>
    <div style="margin-top:8px;color:rgba(255,255,255,.6);">
      <a href="privacy.html" style="color:rgba(255,255,255,.7);margin-right:16px;">プライバシーポリシー</a>
      <a href="disclaimer.html" style="color:rgba(255,255,255,.7);">免責事項</a>
    </div>
    <div style="margin-top:10px;">
      <a href="https://www.buymeacoffee.com/sns_hannou_map" target="_blank" rel="noopener"
         style="display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:8px;background:#ffdd00;color:#0d0d0d;text-decoration:none;font-size:13px;font-weight:700;">
        ☕ このプロジェクトを応援
      </a>
    </div>
  </footer>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build static SNS reaction map HTML")
    parser.add_argument("--input", required=True, help="Classified reaction JSON")
    parser.add_argument("--output", required=True, help="Output HTML path")
    parser.add_argument("--config", default="", help="Optional reaction map config JSON")
    args = parser.parse_args()

    rows = read_json(args.input)
    config = merge_config(args.config or None)
    config["supabase_url"] = os.environ.get("SUPABASE_URL", "")
    config["supabase_anon_key"] = os.environ.get("SUPABASE_ANON_KEY", "")
    output = resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build(rows, config), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
