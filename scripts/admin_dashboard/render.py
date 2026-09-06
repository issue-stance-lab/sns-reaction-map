"""集めた材料を1枚の HTML にする。

外部CDNは使わない（オフラインでも開けること）。グラフは自前の inline SVG。
"""

from __future__ import annotations

import datetime as dt
import html
from pathlib import Path
from typing import Iterable

from . import actions
from .collect import ROOT, STAGES

WEEKDAY_JA = "月火水木金土日"

# 公開先。README.md の「公開URL」と揃えること
PUBLIC_BASE = "https://sns-reaction-map.jp/"


def esc(value) -> str:
    return html.escape("" if value is None else str(value))


def fmt_date(value: dt.date | None) -> str:
    if not value:
        return "—"
    return f"{value.month}/{value.day}（{WEEKDAY_JA[value.weekday()]}）"


def fmt_full_date(value: dt.date | None) -> str:
    if not value:
        return "—"
    return f"{value.year}-{value.month:02d}-{value.day:02d}"


def fmt_week_window(end_date: dt.date) -> str:
    """GA4「直近7日」のウィンドウを表示用文字列で返す。end_date が計測日（当日含む7日間）。"""
    start = end_date - dt.timedelta(days=6)
    if start.month == end_date.month:
        return f"{start.month}/{start.day}〜{end_date.month}/{end_date.day}（7日間）"
    return f"{start.month}/{start.day}〜{end_date.month}/{end_date.day}（7日間）"


def fmt_num(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:,.2f}".rstrip("0").rstrip(".")
    return f"{value:,}"


def fmt_views(value) -> str:
    if value is None:
        return "—"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def days_label(days: int | None) -> tuple[str, str]:
    """残り日数を「あと3日」「2日超過」などにし、危険度クラスを添える。"""
    if days is None:
        return "予定なし", "muted"
    if days < 0:
        return f"{-days}日 超過", "danger"
    if days == 0:
        return "今日", "danger"
    if days <= 3:
        return f"あと{days}日", "warn"
    if days <= 7:
        return f"あと{days}日", "soon"
    return f"あと{days}日", "ok"


# ------------------------------------------------------------------ グラフ


def line_chart(points: list[tuple[dt.date, float | None]], *, color: str, height: int = 120, width: int = 520) -> str:
    """日付つきの折れ線。値が無い回（null）は線を切らずに飛ばす。"""
    usable = [(d, v) for d, v in points if v is not None]
    if len(usable) < 2:
        return '<p class="muted small">グラフを描くには2回以上の記録が必要です</p>'

    pad_l, pad_r, pad_t, pad_b = 34, 8, 10, 20
    xs = [d.toordinal() for d, _ in usable]
    ys = [float(v) for _, v in usable]
    x_min, x_max = min(xs), max(xs)
    y_max = max(ys) or 1
    y_min = 0

    def px(x: int) -> float:
        span = (x_max - x_min) or 1
        return pad_l + (x - x_min) / span * (width - pad_l - pad_r)

    def py(y: float) -> float:
        span = (y_max - y_min) or 1
        return height - pad_b - (y - y_min) / span * (height - pad_t - pad_b)

    path = " ".join(f"{'M' if i == 0 else 'L'}{px(x):.1f},{py(y):.1f}" for i, (x, y) in enumerate(zip(xs, ys)))
    area = f"M{px(xs[0]):.1f},{height - pad_b} " + " ".join(f"L{px(x):.1f},{py(y):.1f}" for x, y in zip(xs, ys)) + f" L{px(xs[-1]):.1f},{height - pad_b} Z"

    dots = "".join(
        f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="3" fill="{color}"><title>{fmt_full_date(d)}: {fmt_num(v)}</title></circle>'
        for (d, v), x, y in zip(usable, xs, ys)
    )
    labels = "".join(
        f'<text x="{px(x):.1f}" y="{height - 6}" class="axis" text-anchor="middle">{d.month}/{d.day}</text>'
        for (d, _), x in zip(usable, xs)
    )
    grid = "".join(
        f'<line x1="{pad_l}" y1="{py(y_max * frac):.1f}" x2="{width - pad_r}" y2="{py(y_max * frac):.1f}" class="grid"/>'
        f'<text x="{pad_l - 6}" y="{py(y_max * frac) + 4:.1f}" class="axis" text-anchor="end">{fmt_num(round(y_max * frac))}</text>'
        for frac in (0, 0.5, 1)
    )

    return (
        f'<svg viewBox="0 0 {width} {height}" class="chart" preserveAspectRatio="xMidYMid meet" role="img">'
        f"{grid}"
        f'<path d="{area}" fill="{color}" opacity="0.12"/>'
        f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>'
        f"{dots}{labels}</svg>"
    )


def bar_chart(points: list[tuple[str, float]], *, color: str, height: int = 120, width: int = 520) -> str:
    if not points:
        return '<p class="muted small">記録がありません</p>'
    pad_l, pad_r, pad_t, pad_b = 46, 8, 10, 20
    y_max = max(v for _, v in points) or 1
    inner_w = width - pad_l - pad_r
    slot = inner_w / len(points)
    bar_w = max(2.0, min(18.0, slot * 0.65))

    bars = []
    for i, (label, value) in enumerate(points):
        x = pad_l + slot * (i + 0.5) - bar_w / 2
        h = (value / y_max) * (height - pad_t - pad_b)
        bars.append(
            f'<rect x="{x:.1f}" y="{height - pad_b - h:.1f}" width="{bar_w:.1f}" height="{max(h, 0.8):.1f}" '
            f'fill="{color}" rx="2"><title>{esc(label)}: {fmt_views(int(value))}</title></rect>'
        )

    step = max(1, len(points) // 8)
    labels = "".join(
        f'<text x="{pad_l + slot * (i + 0.5):.1f}" y="{height - 6}" class="axis" text-anchor="middle">{esc(label)}</text>'
        for i, (label, _) in enumerate(points)
        if i % step == 0
    )
    grid = "".join(
        f'<line x1="{pad_l}" y1="{height - pad_b - (height - pad_t - pad_b) * frac:.1f}" x2="{width - pad_r}" '
        f'y2="{height - pad_b - (height - pad_t - pad_b) * frac:.1f}" class="grid"/>'
        f'<text x="{pad_l - 6}" y="{height - pad_b - (height - pad_t - pad_b) * frac + 4:.1f}" class="axis" text-anchor="end">{fmt_views(int(y_max * frac))}</text>'
        for frac in (0, 0.5, 1)
    )
    return f'<svg viewBox="0 0 {width} {height}" class="chart" preserveAspectRatio="xMidYMid meet" role="img">{grid}{"".join(bars)}{labels}</svg>'


# ------------------------------------------------------------------ 部品


def card(label: str, value: str, sub: str = "", tone: str = "") -> str:
    tone_class = f" {tone}" if tone else ""
    sub_html = f'<div class="stat-sub">{sub}</div>' if sub else ""
    return f'<div class="stat{tone_class}"><div class="stat-label">{esc(label)}</div><div class="stat-value">{value}</div>{sub_html}</div>'


def table(headers: Iterable[str], rows: Iterable[Iterable[str]], *, cls: str = "", tools: str = "") -> str:
    """表。tools を渡すと、絞り込み欄と列見出しの並べ替えが付く。

    スマホでは横長の表をカードに組み替えるため、各セルに列名を data-label で持たせる。
    """
    headers = list(headers)
    head = "".join(f'<th scope="col">{esc(h)}</th>' for h in headers)
    body = "".join(
        "<tr>"
        + "".join(f'<td data-label="{esc(headers[i]) if i < len(headers) else ""}">{cell}</td>' for i, cell in enumerate(row))
        + "</tr>"
        for row in rows
    )
    if not body:
        body = f'<tr><td colspan="{len(headers)}" class="muted">データがありません</td></tr>'

    classes = " ".join(part for part in (cls, "sortable" if tools else "") if part)
    grid = f'<div class="scroll"><table class="{classes}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
    if not tools:
        return grid
    return (
        f'<div class="tablebox">'
        f'<div class="tabletools"><input type="search" class="filter" placeholder="{esc(tools)}" '
        f'aria-label="{esc(tools)}"><span class="filter-count"></span>'
        f'<span class="muted small">列見出しをクリックすると並べ替えできます</span></div>'
        f"{grid}</div>"
    )


# GROWTH.yaml の status を、オーナー向けの日本語と危険度に置き換える
EXPERIMENT_STATUS = {
    "measuring": ("計測中", "warn"),
    "closed_undecided": ("判定不能で終了", "muted"),
    "adopted": ("採用", "ok"),
    "rejected": ("不採用", "danger"),
    "blocked": ("止まっている", "danger"),
    "built": ("実装済み・計測待ち", "soon"),
    "building": ("作成中", "soon"),
    "idea": ("案のみ", "muted"),
}

STAGE_MARK = {
    "done": ("●", "ok"),
    "partial": ("◐", "warn"),
    "todo": ("○", "muted"),
    "blocked": ("×", "danger"),
    "n-a": ("–", "muted"),
    None: ("·", "muted"),
}
STAGE_TEXT = {"done": "済み", "partial": "途中", "todo": "未着手", "blocked": "止まっている", "n-a": "対象外", None: "記載なし"}


def theme_name(theme: dict, *, with_key: bool = False) -> str:
    """テーマ名を、公開ページと手元のページへのリンクにする。

    更新したあと現物を見に行く導線がなく、画面と実物を往復できなかったため。
    手元のページは file:// で開く（ブラウザで直接見られる）。
    """
    title = f'<strong>{esc(theme["title"])}</strong>'
    page = theme.get("html")
    if not page:
        return title
    public = PUBLIC_BASE + Path(page).name
    local = f"file://{ROOT / page}"
    links = (
        f'<span class="links"><a href="{esc(public)}" target="_blank" rel="noopener">公開ページ</a>'
        f'<a href="{esc(local)}">手元</a></span>'
    )
    key = f'<div class="muted small">{esc(theme["key"])}</div>' if with_key else ""
    return f"{title}{links}{key}"


def stage_dots(stages: dict) -> str:
    out = []
    for key, label in STAGES:
        value = stages.get(key)
        mark, tone = STAGE_MARK.get(value, ("?", "muted"))
        out.append(f'<span class="dot {tone}" title="{esc(label)}: {esc(STAGE_TEXT.get(value, value))}">{mark}</span>')
    return '<span class="dots">' + "".join(out) + "</span>"


# ------------------------------------------------------------------ 各セクション


def _signal(check: dict) -> str:
    tone = "ok" if check["ok"] else ("danger" if check["ok"] is False else "warn")
    mark = "✓" if check["ok"] else ("✕" if check["ok"] is False else "?")
    return (
        f'<li class="signal {tone}"><span class="signal-mark">{mark}</span>'
        f'<span class="signal-name">{esc(check["name"])}</span>'
        f'<span class="signal-detail">{esc(check["detail"])}</span></li>'
    )


def _command_block(block: dict, *, ready: bool, index: int) -> str:
    steps = "".join(
        f'<div class="step"><div class="step-note">{esc(step["note"])}</div>'
        f'<code class="step-cmd">{esc(step["command"])}</code></div>'
        for step in block["steps"]
    )
    blocked = "" if ready else '<div class="cmd-blocked">上の準備が済むまで実行しないでください。最初の数行がその準備です。</div>'
    impact_tone = "warn" if block["impact"].endswith("更新します") else "muted"
    recommended = '<span class="pill ok">今日はこちら</span>' if block.get("recommended") else ""
    return f"""<div class="cmdbox{'' if ready else ' not-ready'}{' recommended' if block.get('recommended') else ''}">
<div class="cmd-head"><strong>{esc(block["label"])}</strong>{recommended}
<span class="pill {impact_tone}">{esc(block["impact"])}</span>
<button type="button" class="copy" data-copy="cmd{index}">まとめてコピー</button></div>
{blocked}
<div class="steps" id="cmd{index}">{steps}</div>
<div class="cmd-foot"><strong>成功の見え方</strong>: {esc(block["success"])}<br>
<strong>終わったら</strong>: <code>{esc(block["verify"])}</code> — {esc(block["verify_note"])}</div>
</div>"""


def _anomalies(found: list[dict]) -> str:
    """いつもと違うところ。良い変化（伸びた投稿）も同じ場所に出す。"""
    if not found:
        return ""
    items = "".join(
        f'<li class="{esc(item["tone"])}"><strong>{esc(item["title"])}</strong>'
        f'<span>{esc(item["detail"])}</span></li>'
        for item in found
    )
    return (
        f'<h3>気になる変化 {len(found)} 件</h3>'
        '<p class="muted small">履歴を見に行かなくても気づけるよう、いつもと違うところだけを拾っています。'
        "期限切れはここには出しません（上の「次の一手」と重なるため）。</p>"
        f'<ul class="alerts">{items}</ul>'
    )


# --------------------------------------------------------------- CEO経営画面


DEPARTMENT_LABELS = {
    "executive": "経営統括",
    "editorial": "編集部",
    "business": "事業部",
    "engineering-data": "開発・データ部",
    "corporate": "経営管理",
    "quality": "品質監査",
}

HANDOFF_STATUS = {
    "completed": ("完了", "ok"),
    "cancelled": ("中止", "calm"),
    "withdrawn": ("取り下げ", "calm"),
    "in_progress": ("進行中", "soon"),
    "scheduled": ("予定済み", "calm"),
    "recurring": ("継続中", "ok"),
    "awaiting_ceo_approval": ("CEO承認待ち", "warn"),
    "ready_for_drafting": ("執筆可能", "soon"),
    "planned": ("企画済み", "calm"),
    "waiting_external_result": ("外部結果待ち", "calm"),
}


def _goal_value(goal: dict) -> str:
    key, value = goal["key"], goal["value"]
    if "revenue_yen" in key:
        return f"{int(value):,}円"
    if key == "adsense_status" and value == "approved":
        return "承認"
    if key == "company_form" and value == "consider_incorporation":
        return "法人化を検討"
    return fmt_num(value)


def section_ceo(data: dict) -> str:
    company = data.get("company") or {}
    brief = data.get("executive_brief") or []
    constraints = company.get("constraints") or {}
    report = "".join(
        f'<article class="brief-card {esc(item["tone"])}"><div class="brief-label">{esc(item["label"])}</div>'
        f'<div class="brief-text">{esc(item["text"])}</div></article>'
        for item in brief
    )
    owner_hours = constraints.get("owner_hours_per_week_max")
    cost_limit = constraints.get("monthly_operating_cost_yen_max_until_revenue")
    return f"""<section id="ceo" class="ceo-home">
<div class="north-star">
  <div class="north-star-mark" aria-hidden="true"><span></span><i></i><b></b></div>
  <div><div class="eyebrow">会社の北極星</div><h2>{esc(company.get("north_star") or "目的が未記入です")}</h2></div>
</div>
<div class="operating-rule"><span>CEO <strong>週{fmt_num(owner_hours)}時間以内</strong></span>
<span>収益化前の運営費 <strong>月{fmt_num(cost_limit)}円以内</strong></span>
<span><strong>AI中心</strong> ・公開はCEO承認</span></div>
<div class="section-kicker"><span>TODAY</span><h3>今日の経営報告</h3><p>下の4行だけ読めば、今日の判断を始められます。</p></div>
<div class="brief-grid">{report}</div>
</section>"""


def section_operations(data: dict) -> str:
    """Interactive control room. It is emitted only by the loopback server."""
    if not data.get("interactive"):
        return ""
    themes = data["themes"]
    theme_cards = []
    for theme in themes:
        mode_ok = theme["update_mode"] == "adapter"
        due, due_tone = days_label(theme["collect_in"])
        disabled_note = "" if mode_ok else f'<p class="ops-disabled">{esc(theme["update_mode_note"])}</p>'
        theme_cards.append(
            f'<article class="ops-theme" data-theme="{esc(theme["key"])}">'
            f'<label class="ops-select"><input type="checkbox" value="{esc(theme["key"])}">'
            f'<span><strong>{esc(theme["title"])}</strong><small>{esc(theme["key"])}</small></span></label>'
            f'<div class="ops-theme-state"><span class="pill {due_tone}">収集 {esc(due)}</span>'
            f'<span class="pill {"ok" if mode_ok else "warn"}">{esc(theme["update_mode_label"])}</span></div>'
            f'<div class="ops-theme-actions"><button type="button" class="ops-btn" data-action="theme.collect" data-theme="{esc(theme["key"])}">収集・分類</button>'
            f'<button type="button" class="ops-btn secondary" data-action="theme.prepare_release" data-theme="{esc(theme["key"])}" {"" if mode_ok else "disabled"}>公開候補を確認</button></div>'
            f'{disabled_note}</article>'
        )
    return f"""<section id="operations" class="operations" data-token="{esc(data.get('dashboard_token') or '')}">
<div class="ops-heading"><div><div class="eyebrow">OPERATIONS DESK</div><h2>今日の運用をここから進める</h2>
<p>ボタンを押すと専用のCodexセッションが始まります。通常は問題が起きるまで自動で進みます。</p></div>
<div class="ops-server"><span class="ops-live"></span><strong>このMacだけ</strong><small>Codex model <span id="ops-model">—</span></small></div></div>
<div id="ops-dirty" class="ops-warning" hidden></div>
<div class="ops-layout">
  <div class="ops-left">
    <div class="ops-toolbar"><strong>テーマ</strong><button type="button" class="ops-link" id="select-due">予定が近いものを選択</button>
    <button type="button" class="ops-btn primary" id="collect-selected">選んだテーマを順番に収集</button></div>
    <div class="ops-themes">{"".join(theme_cards)}</div>
    <div class="ops-channel-grid">
      <article class="ops-channel x"><span class="ops-channel-mark">X</span><h3>X運用</h3><p>候補作成から投稿画面の準備、24〜48時間後の計測まで。</p>
      <div class="ops-x-usage" id="x-api-usage"><strong>API換算を集計中</strong><span>候補作成後に自動記録します</span></div>
      <div class="ops-channel-actions"><button class="ops-btn primary" data-action="x.prepare">今日のX候補</button><button class="ops-btn" id="open-x">この案で投稿準備</button><button class="ops-btn" data-action="x.measure">結果を計測</button></div>
      <div class="ops-inline"><input id="x-post-url" type="url" placeholder="投稿後の https://x.com/.../status/..."><button class="ops-btn" id="record-x">投稿済みにする</button></div></article>
      <article class="ops-channel metrics"><span class="ops-channel-mark">↗</span><h3>流入データ</h3><p>実測の取得は決められた処理、変化の説明はCodexが担当します。</p>
      <div class="ops-inline"><input id="x-followers" type="number" min="0" inputmode="numeric" placeholder="Xフォロワー数（手入力）"></div>
      <div class="ops-channel-actions"><button class="ops-btn primary" id="refresh-metrics">最新値を取得</button><button class="ops-btn" data-action="metrics.explain">Codexに解説させる</button></div></article>
    </div>
  </div>
  <aside class="ops-console">
    <div class="ops-console-head"><div><div class="eyebrow">CODEX SESSION</div><h3 id="job-title">作業を選んでください</h3></div><button class="ops-link" id="shutdown-dashboard">管理画面を終了</button></div>
    <div id="job-empty" class="ops-empty">左のボタンから作業を始めると、工程とCodexの回答がここに表示されます。</div>
    <div id="job-detail" hidden>
      <div class="ops-session-meta"><span id="job-status" class="pill">—</span><span id="job-owner" class="pill">管理画面で操作</span><code id="job-thread">—</code></div>
      <div class="ops-x-run" id="job-x-usage" hidden></div>
      <ol class="ops-rail" id="job-progress"></ol>
      <div class="ops-approval" id="job-approval" hidden></div>
      <div class="ops-chat" id="job-chat"></div>
      <div class="ops-chat-form"><textarea id="job-message" rows="3" placeholder="この作業についてCodexへ追加で伝える"></textarea><button class="ops-btn primary" id="send-job-message">送る</button></div>
      <div class="ops-console-actions"><button class="ops-btn" id="handoff-job">Codexアプリへ引き継ぐ</button><button class="ops-btn danger" id="cancel-job">中止</button></div>
    </div>
    <div class="ops-history"><div class="ops-history-head"><strong>最近の作業</strong><span id="job-count"></span></div><div id="job-list"></div></div>
  </aside>
</div>
</section>"""


def section_company(data: dict) -> str:
    company = data.get("company") or {}
    today = data["today"]

    pending = company.get("pending_approvals") or []
    approval_cards = []
    for item in pending:
        risks = "".join(f"<li>{esc(risk)}</li>" for risk in item.get("risks") or [])
        approval_cards.append(
            f'<article class="approval-card"><div class="approval-top"><span class="pill warn">CEO判断</span>'
            f'<span class="muted small">依頼 {fmt_full_date(item.get("requested_at"))}</span></div>'
            f'<h4>{esc(item.get("summary"))}</h4><p>{esc(item.get("reason"))}</p>'
            f'<div class="recommendation">推奨 <strong>{esc(item.get("recommendation") or "未記入")}</strong></div>'
            f'{f"<ul>{risks}</ul>" if risks else ""}</article>'
        )
    approvals_html = "".join(approval_cards) or '<p class="empty-state">現在、CEOの承認待ちはありません。</p>'

    work_rows = []
    active_handoffs = [
        item for item in (company.get("handoffs") or [])
        if item.get("status") not in {"completed", "cancelled", "withdrawn"}
    ]
    for item in active_handoffs[:8]:
        status_label, tone = HANDOFF_STATUS.get(item.get("status"), (item.get("status") or "不明", "calm"))
        due_text, due_tone = days_label(item.get("due_in"))
        work_rows.append(
            f'<article class="work-item"><div class="work-meta"><span>{esc(DEPARTMENT_LABELS.get(item.get("department"), item.get("department")))}</span>'
            f'<span class="pill {tone}">{esc(status_label)}</span><span class="pill {due_tone}">{esc(due_text)}</span></div>'
            f'<h4>{esc(item.get("current_state"))}</h4><p><strong>次:</strong> {esc(item.get("next_action"))}</p>'
            f'<div class="work-id">{esc(item.get("id"))} ・ 期日 {fmt_full_date(item.get("due_at"))}</div></article>'
        )

    milestone_cards = []
    for milestone in company.get("milestones") or []:
        due_text, due_tone = days_label(milestone.get("due_in"))
        goals = "".join(
            f'<li><span>{esc(goal["label"])}</span><strong>{esc(_goal_value(goal))}</strong></li>'
            for goal in milestone.get("goals") or []
        )
        milestone_cards.append(
            f'<article class="milestone"><div class="milestone-head"><div><div class="milestone-name">{esc(milestone["label"])}</div>'
            f'<div class="muted small">期日 {fmt_full_date(milestone.get("due_at"))}</div></div>'
            f'<span class="pill {due_tone}">{esc(due_text)}</span></div><ul>{goals}</ul></article>'
        )

    finance = company.get("current_finance")
    if finance:
        profit = "未確定" if finance["profit"] is None else f'{finance["profit"]:,}円'
        unknown = finance["unknown_revenue"] + finance["unknown_costs"]
        unknown_note = (
            f'<div class="finance-note warn-banner">未確認の費目: {esc(", ".join(unknown))}。未確認を0円とは扱いません。</div>'
            if unknown else ""
        )
        finance_html = f"""<div class="finance-panel">
<div class="finance-month">{esc(finance['month'])}</div>
<div class="finance-numbers">
  <div><span>収益</span><strong>{finance['revenue_total']:,}円</strong></div>
  <div><span>費用（確定分）</span><strong>{finance['cost_total']:,}円</strong></div>
  <div><span>利益</span><strong>{esc(profit)}</strong></div>
  <div><span>費用上限</span><strong>{finance['cost_limit']:,}円</strong></div>
</div>{unknown_note}<p>{esc(finance['notes'])}</p></div>"""
    else:
        finance_html = '<p class="empty-state">月次収支の記録がありません。</p>'

    alert_items = "".join(
        f'<li class="{esc(item["tone"])}"><strong>{esc(item["title"])}</strong><span>{esc(item["detail"])}</span></li>'
        for item in company.get("alerts") or []
    )
    ledger_alerts = f'<ul class="alerts ledger-alerts">{alert_items}</ul>' if alert_items else '<p class="ok-banner">会社台帳に記録漏れ・期限超過・費用超過はありません。</p>'

    org_cards = "".join(
        f'<article class="org-card"><div class="org-key">{index:02d}</div><h4>{esc(item["title"])}</h4><p>{esc(item["mission"])}</p></article>'
        for index, item in enumerate(company.get("departments") or [], 1)
    )

    return f"""<section id="company" class="company-board">
<div class="section-kicker"><span>DECIDE</span><h2>CEOの判断と会社の現在地</h2><p>{fmt_full_date(today)} 時点。各台帳から自動で集約しています。</p></div>
<div class="company-split"><div><h3>承認待ち <span class="count">{len(pending)}</span></h3><div class="approval-list">{approvals_html}</div></div>
<div><h3>台帳アラート <span class="count">{len(company.get("alerts") or [])}</span></h3>{ledger_alerts}</div></div>
<h3 class="board-heading">進行中の業務</h3><div class="work-list">{"".join(work_rows)}</div>
<h3 class="board-heading">目標までの距離</h3><div class="milestone-grid">{"".join(milestone_cards)}</div>
<div class="company-split lower"><div><h3>月次収支</h3>{finance_html}</div>
<div><h3>組織と責任</h3><div class="org-grid">{org_cards}</div></div></div>
</section>"""


def section_next(data: dict) -> str:
    action = data.get("next")
    if not action:
        return (
            '<section id="next"><h2>1. 今日の次の一手</h2>'
            '<p class="ok-banner">いま急いでやることはありません。'
            '予定は「3. 更新スケジュール」で確認できます。</p>'
            f'{_anomalies(data.get("anomalies") or [])}</section>'
        )

    checks = action["readiness"]
    ready = bool(checks) and all(check["ok"] for check in checks)
    signals = f'<ul class="signals">{"".join(_signal(c) for c in checks)}</ul>' if checks else ""
    ready_head = ""
    if checks:
        ready_head = "<h3>実行できる状態か</h3>" + (
            '<p class="muted small">すべて通っています。下の手順を実行できます。</p>'
            if ready
            else '<p class="muted small">通っていない項目があります。下の手順の最初の数行が、その準備そのものです。</p>'
        )

    blocks = "".join(_command_block(block, ready=ready, index=i) for i, block in enumerate(action["blocks"]))

    minutes = f'<span class="meta">目安 約{action["minutes"]}分</span>' if action["minutes"] else ""
    last = action.get("last")
    last_html = ""
    if last:
        last_html = (
            f'<p class="muted small">前回このテーマを更新したのは {fmt_full_date(last["date"])}。'
            f'取得 {fmt_num(last["raw"])}件 / 新規 {fmt_num(last["new"])}件 / 意見 {fmt_num(last["opinions"])}件、'
            f'結果は「{esc(last["status"])}」でした。</p>'
        )

    pending = action.get("pending")
    pending_html = ""
    if pending:
        rows = [
            [fmt_full_date(p["date"]), esc(p["kind"]), esc(p["target"] or p["theme"]), esc(p["type"])]
            for p in pending
        ]
        pending_html = (
            '<p class="lead">Xの管理画面で表示回数を見て、<code>content/x/posts.md</code> の該当行に書き足してください。'
            "投稿直後の値は当てにならないので、1〜2日後のいまが測りどきです。</p>"
            + table(["投稿日", "種別", "リプライ先 / テーマ", "型"], rows)
        )

    rest = action.get("rest") or []
    rest_html = ""
    if rest:
        rest_rows = []
        for item in rest:
            text, tone = days_label(item["days"])
            rest_rows.append(
                [
                    esc(item["theme"]["title"]),
                    esc(item["kind"]),
                    fmt_date(item["date"]),
                    f'<span class="pill {tone}">{esc(text)}</span>',
                ]
            )
        rest_html = (
            f'<details class="rest"><summary>このあと7日以内に控えている予定 {len(rest)} 件</summary>'
            + table(["テーマ", "種類", "予定日", "残り"], rest_rows)
            + "</details>"
        )

    return f"""<section id="next"><h2>1. 今日の次の一手</h2>
<div class="next-head {esc(action["tone"])}">
<div class="next-title">{esc(action["title"])}</div>
<div class="next-why">{esc(action["why"])}{minutes}</div>
</div>
{last_html}
{ready_head}{signals}
{blocks}
{pending_html}
{rest_html}
{_anomalies(data.get("anomalies") or [])}
</section>"""


def section_alerts(data: dict) -> str:
    today = data["today"]
    alerts: list[tuple[str, str, str]] = []  # (深刻度, 見出し, 説明)

    # 会社台帳の期限・承認・収支・訂正を、従来の運用警告と同じ場所で見る。
    for item in (data.get("company") or {}).get("alerts") or []:
        alerts.append((item.get("tone") or "warn", item.get("title") or "会社台帳の確認", item.get("detail") or ""))

    for theme in data["themes"]:
        for kind, field, action in (("収集", "collect_in", "データを集める日"), ("公開更新", "refresh_in", "ページを更新して公開する日")):
            days = theme[field]
            if days is None:
                continue
            if days < 0:
                alerts.append(("danger", f"{theme['title']} の{kind}予定が {-days} 日過ぎています", f"{action}は {fmt_full_date(theme['collect_at'] if field == 'collect_in' else theme['refresh_at'])} でした"))
            elif days <= 2:
                alerts.append(("warn", f"{theme['title']} の{kind}予定が {'今日' if days == 0 else f'{days}日後'}です", action))

    snapshots = data["kpi"]["snapshots"]
    if snapshots:
        age = (today - snapshots[-1]["date"]).days
        if age > 10:
            alerts.append(("warn", f"流入の記録（週次KPI）が {age} 日前で止まっています", "GROWTH.yaml の kpi.snapshots に1行追加する運用。週1回が想定"))

    measurement = data.get("x_measurement") or {}
    if measurement.get("error"):
        alerts.append((
            "warn",
            "X の計測状況を集計できませんでした",
            measurement["error"],
        ))
    else:
        overdue = measurement.get("overdue") or []
        if overdue:
            oldest = overdue[0]
            alerts.append((
                "danger" if oldest["age_hours"] >= 48 else "warn",
                f"X投稿の表示回数が {len(overdue)} 件未計測です（最長 {oldest['age_hours']:.0f} 時間経過）",
                f"最も古いのは {oldest['target']} への{oldest['kind']}。"
                "毎日20時の定期タスク x-daily-measure が動いていれば溜まりません。"
                "溜まっているなら、そのタスクが止まっているか失敗しています",
            ))

        review_latest = measurement.get("review_latest")
        if review_latest is None:
            alerts.append((
                "warn",
                "X週次レビューがまだ1件も記録されていません",
                "content/x/weekly-reviews.md に記入する運用。日曜20:30の定期タスク x-weekly-review が担当",
            ))
        else:
            age = (today - review_latest).days
            if age > 10:
                alerts.append((
                    "warn",
                    f"X週次レビューが {age} 日前で止まっています",
                    f"最後の記録は {fmt_full_date(review_latest)} まで。週1回が想定",
                ))

    x_posting = next(
        (item for item in data["kpi"].get("recurring", []) if item["key"] == "x-posting"),
        None,
    )
    if x_posting:
        last_run = x_posting.get("last_run")
        if last_run is None:
            alerts.append(("warn", "X の候補確認日が記録されていません", "GROWTH.yaml の recurring.x-posting.last_run を更新してください"))
        else:
            age = (today - last_run).days
            if age > 3:
                alerts.append((
                    "warn",
                    f"X の候補確認が {age} 日前で止まっています",
                    "投稿本数のノルマはありません。関連ポストを確認し、有効な候補がある場合のみ返信する運用です",
                ))

    primary_research = data.get("primary_research") or {}
    for item in primary_research.get("themes") or []:
        if item.get("last_verified") is None:
            alerts.append((
                "warn",
                f"{item['title']} の一次資料メモがまだ確認されていません",
                ".claude/skills/primary-research/SKILL.md の手順で一次資料を調べる",
            ))
            continue
        overdue_by = item.get("overdue_by")
        if overdue_by is None or overdue_by <= 0:
            continue
        alerts.append((
            "danger" if overdue_by > 30 else "warn",
            f"{item['title']} の一次資料メモが再確認予定を {overdue_by} 日過ぎています",
            f"最終確認 {fmt_full_date(item['last_verified'])}（{item['cadence_days']}日ごとが目安）。"
            ".claude/skills/primary-research/SKILL.md の手順で見直す",
        ))

    for check in data["health"]:
        if check["ok"] is False:
            alerts.append(("danger", f"{check['name']} が使えません", check["detail"]))

    live = data.get("live")
    if live:
        for label, key in (("GA4（アクセス解析）", "ga4"), ("Search Console（検索）", "gsc"), ("Supabase（投票）", "votes")):
            if live.get(f"{key}_error"):
                alerts.append(("danger", f"{label} の自動取得に失敗しました", live[f"{key}_error"]))

    order = {"danger": 0, "warn": 1}
    alerts.sort(key=lambda a: order.get(a[0], 2))

    if not alerts:
        body = '<p class="ok-banner">期限切れ・停止しているものはありません。</p>'
    else:
        body = '<ul class="alerts">' + "".join(
            f'<li class="{level}"><strong>{esc(title)}</strong><span>{esc(detail)}</span></li>' for level, title, detail in alerts
        ) + "</ul>"

    counts = {"danger": sum(1 for a in alerts if a[0] == "danger"), "warn": sum(1 for a in alerts if a[0] == "warn")}
    summary = f'<p class="muted small">対応が要るもの {counts["danger"]} 件 / 近づいているもの {counts["warn"]} 件</p>'
    return f'<section id="alerts"><h2>2. いま対応が要ること</h2>{summary}{body}</section>'


def section_schedule(data: dict) -> str:
    today = data["today"]
    themes = data["themes"]
    handoffs = data.get("company", {}).get("handoffs") or []

    rows = []
    for theme in themes:
        collect_text, collect_tone = days_label(theme["collect_in"])
        refresh_text, refresh_tone = days_label(theme["refresh_in"])
        mode_tone = "ok" if theme["update_mode"] == "adapter" else "warn"
        rows.append(
            [
                theme_name(theme, with_key=True),
                f'{fmt_date(theme["collect_at"])}<div class="pill {collect_tone}">{esc(collect_text)}</div>',
                f'{fmt_date(theme["refresh_at"])}<div class="pill {refresh_tone}">{esc(refresh_text)}</div>',
                f'<span class="pill {mode_tone}" title="{esc(theme["update_mode_note"])}">{esc(theme["update_mode_label"])}</span>',
                fmt_full_date(theme["updated_at"]),
                fmt_num(theme["collect_delta"]),
            ]
        )

    calendar = _calendar(themes, handoffs, today)
    auto = sum(1 for t in themes if t["update_mode"] == "adapter")
    stats = (
        '<div class="stats">'
        + card("テーマ数", str(len(themes)))
        + card("1コマンドで更新できる", f"{auto} / {len(themes)}", "残りは手作業が要る", "warn" if auto < len(themes) else "ok")
        + card("今後7日の予定", str(sum(1 for t in themes for d in (t["collect_in"], t["refresh_in"]) if d is not None and 0 <= d <= 7)))
        + card("期限超過", str(sum(1 for t in themes for d in (t["collect_in"], t["refresh_in"]) if d is not None and d < 0)), tone="danger" if any(d is not None and d < 0 for t in themes for d in (t["collect_in"], t["refresh_in"])) else "")
        + "</div>"
    )

    return f"""<section id="schedule"><h2>3. 更新スケジュール</h2>
<p class="lead">「収集」は投稿データを集めるだけの作業、「公開更新」は集めたデータをページに反映して公開するところまで。テーマの予定日は <code>THEMES.yaml</code>、個別の確認予定は <code>company/HANDOFFS.yaml</code> が正です。</p>
{stats}
<h3>これから5週間</h3>
{calendar}
<h3>テーマ別</h3>
{table(["テーマ", "次の収集", "次の公開更新", "更新のしかた", "最終公開更新", "前回追加"], rows)}
</section>"""


def _calendar(themes: list[dict], handoffs: list[dict], today: dt.date) -> str:
    events: dict[dt.date, list[tuple[str, str]]] = {}
    for theme in themes:
        if theme["collect_at"]:
            events.setdefault(theme["collect_at"], []).append(("収集", theme["title"]))
        if theme["refresh_at"]:
            events.setdefault(theme["refresh_at"], []).append(("公開", theme["title"]))
    for handoff in handoffs:
        for event in handoff.get("schedule") or []:
            events.setdefault(event["date"], []).append(("確認", event["title"]))

    start = today - dt.timedelta(days=today.weekday())
    cells = []
    for offset in range(35):
        day = start + dt.timedelta(days=offset)
        classes = ["cal-day"]
        if day == today:
            classes.append("today")
        if day < today:
            classes.append("past")
        items = "".join(
            f'<div class="cal-item {"collect" if kind == "収集" else "refresh" if kind == "公開" else "check"}">{esc(kind)}・{esc(title)}</div>'
            for kind, title in events.get(day, [])
        )
        cells.append(f'<div class="{" ".join(classes)}"><div class="cal-date">{day.month}/{day.day}</div>{items}</div>')

    head = "".join(f'<div class="cal-head">{ch}</div>' for ch in WEEKDAY_JA)
    return f'<div class="calendar">{head}{"".join(cells)}</div>'


def section_traffic(data: dict) -> str:
    kpi = data["kpi"]
    snapshots = kpi["snapshots"]
    live = data.get("live")

    if not snapshots:
        return '<section id="traffic"><h2>4. 流入</h2><p class="muted">GROWTH.yaml に記録がありません。</p></section>'

    latest = snapshots[-1]
    prev = snapshots[-2] if len(snapshots) > 1 else None

    def delta(field: str) -> str:
        if not prev or latest.get(field) is None or prev.get(field) is None:
            return ""
        diff = latest[field] - prev[field]
        if diff == 0:
            return "前回から横ばい"
        return f"前回から {'+' if diff > 0 else ''}{fmt_num(diff)}"

    age = (data["today"] - latest["date"]).days
    win = fmt_week_window(latest["date"])
    stats = (
        f'<p class="muted small">計測ウィンドウ: {win}</p>'
        '<div class="stats">'
        + card("週の訪問者", fmt_num(latest["weekly_users"]), delta("weekly_users"))
        + card("週のページ閲覧", fmt_num(latest["pageviews"]), delta("pageviews"))
        + card("1人あたり閲覧ページ", fmt_num(latest["pages_per_session"]), delta("pages_per_session"))
        + card("投票（累計）", fmt_num(latest["votes_total"]), delta("votes_total"))
        + card("検索での表示（28日）", fmt_num(latest["gsc_impressions"]), delta("gsc_impressions"))
        + card("検索からのクリック（28日）", fmt_num(latest["gsc_clicks"]), delta("gsc_clicks"))
        + "</div>"
    )

    follower_points = [(s["date"], s["x_followers"]) for s in snapshots if s.get("x_followers") is not None]
    follower_chart = (
        f'<div class="panel"><h4>X フォロワー</h4>{line_chart(follower_points, color="var(--c5)")}</div>'
        if follower_points
        else '<div class="panel"><h4>X フォロワー</h4><p class="muted small" style="padding:16px 0">まだデータがありません。下のフォームで記録してください。</p></div>'
    )
    charts = (
        '<div class="grid2">'
        f'<div class="panel"><h4>週の訪問者</h4>{line_chart([(s["date"], s["weekly_users"]) for s in snapshots], color="var(--c1)")}</div>'
        f'<div class="panel"><h4>週のページ閲覧</h4>{line_chart([(s["date"], s["pageviews"]) for s in snapshots], color="var(--c2)")}</div>'
        f'<div class="panel"><h4>投票（累計）</h4>{line_chart([(s["date"], s["votes_total"]) for s in snapshots], color="var(--c3)")}</div>'
        f'<div class="panel"><h4>検索での表示回数（28日）</h4>{line_chart([(s["date"], s["gsc_impressions"]) for s in snapshots], color="var(--c4)")}</div>'
        + follower_chart
        + "</div>"
    )

    goal = kpi["phase_goal"]
    goal_rows = []
    goal_map = {"weekly_users": ("週の訪問者", latest["weekly_users"]), "votes_total": ("投票（累計）", latest["votes_total"]), "x_followers": ("Xフォロワー", latest["x_followers"])}
    for key, target in goal.items():
        label, current = goal_map.get(key, (key, None))
        pct = min(100, round((current or 0) / target * 100)) if isinstance(target, (int, float)) and target else 0
        goal_rows.append(
            f'<div class="goal"><div class="goal-label">{esc(label)}<span class="muted">{fmt_num(current)} / {fmt_num(target)}</span></div>'
            f'<div class="bar"><span style="width:{pct}%"></span></div></div>'
        )

    history_rows = [
        [
            fmt_full_date(s["date"]),
            fmt_week_window(s["date"]),
            fmt_num(s["weekly_users"]),
            fmt_num(s["pageviews"]),
            fmt_num(s["pages_per_session"]),
            fmt_num(s["votes_total"]),
            fmt_num(s["gsc_impressions"]),
            fmt_num(s["gsc_clicks"]),
        ]
        for s in reversed(snapshots)
    ]

    live_html = ""
    if live:
        live_html = _live_block(live, latest)

    freshness = f'<p class="{"warn-banner" if age > 10 else "muted small"}">この数字は {fmt_full_date(latest["date"])}（{age}日前）に記録したものです。'
    freshness += "画面を開いた時点の実測ではありません。</p>" if not live else "最新の実測は下の「取り直した実測値」を見てください。</p>"

    experiment_rows = []
    for experiment in kpi["experiments"]:
        label, tone = EXPERIMENT_STATUS.get(experiment["status"], (experiment["status"], "muted"))
        experiment_rows.append(
            [
                esc(experiment["bucket"]),
                esc(experiment["title"]),
                f'<span class="pill {tone}">{esc(label)}</span>',
                esc(experiment["metric"]),
                fmt_full_date(experiment["judge_at"]),
            ]
        )
    experiments = table(["区分", "施策", "状態", "見る指標", "判定予定日"], experiment_rows)
    measuring = sum(1 for e in kpi["experiments"] if e["status"] == "measuring")
    experiments_lead = (
        f'<p class="lead">計測中は {measuring} 件。'
        + ("計測中が0件のときは、数字で効果を追っている施策が無いという意味です。" if measuring == 0 else "")
        + "「判定不能で終了」は、効果が無かったのではなく<strong>読み手の数が足りなくて判定できなかった</strong>もので、"
        + "機能はサイトに残っています。</p>"
    )

    return f"""<section id="traffic"><h2>4. 流入（どれだけ読まれているか）</h2>
{freshness}
{stats}
{live_html}
{charts}
<h3>いまのフェーズの卒業条件</h3>
<p class="muted small">現在: {esc(kpi["phase"])}</p>
<div class="goals">{"".join(goal_rows)}</div>
<h3>週次の記録</h3>
{table(["記録日", "計測ウィンドウ（7日間）", "訪問者", "ページ閲覧", "1人あたり", "投票累計", "検索表示", "検索クリック"], history_rows)}
<h3>施策の状態</h3>
{experiments_lead}
{experiments}
</section>"""


def _live_block(live: dict, prev_snapshot: dict | None = None) -> str:
    parts = []

    def live_delta(live_val: int | None, prev_val) -> str:
        if live_val is None or prev_val is None:
            return ""
        diff = live_val - int(prev_val)
        if diff == 0:
            return "前回比 横ばい"
        return f"前回比 {'+' if diff > 0 else ''}{diff:,}"

    ga4 = live.get("ga4")
    ga4_users = ga4_views = None
    if ga4:
        ga4_users = int(float(ga4.get("activeUsers", 0) or 0))
        ga4_views = int(float(ga4.get("screenPageViews", 0) or 0))
        parts.append(card("訪問者（直近7日・実測）", fmt_num(ga4_users),
                          live_delta(ga4_users, prev_snapshot.get("weekly_users") if prev_snapshot else None)))
        parts.append(card("ページ閲覧（直近7日・実測）", fmt_num(ga4_views),
                          live_delta(ga4_views, prev_snapshot.get("pageviews") if prev_snapshot else None)))
    gsc = live.get("gsc")
    if gsc and isinstance(gsc.get("summary"), dict):
        imp = int(float(gsc["summary"].get("impressions", 0) or 0))
        clk = int(float(gsc["summary"].get("clicks", 0) or 0))
        parts.append(card("検索表示（28日・実測）", fmt_num(imp),
                          live_delta(imp, prev_snapshot.get("gsc_impressions") if prev_snapshot else None)))
        parts.append(card("検索クリック（28日・実測）", fmt_num(clk),
                          live_delta(clk, prev_snapshot.get("gsc_clicks") if prev_snapshot else None)))
    votes = live.get("votes")
    if isinstance(votes, dict):
        total = sum(sum(int(v) for v in choices.values()) for topic, choices in votes.items() if not topic.lower().startswith("test"))
        parts.append(card("投票累計（実測）", fmt_num(total),
                          live_delta(total, prev_snapshot.get("votes_total") if prev_snapshot else None)))

    errors = [
        f'<li class="danger"><strong>{esc(label)}</strong><span>{esc(live[key])}</span></li>'
        for label, key in (("GA4（アクセス解析）", "ga4_error"), ("Search Console（検索）", "gsc_error"), ("Supabase（投票）", "votes_error"))
        if live.get(key)
    ]
    error_html = f'<ul class="alerts">{"".join(errors)}</ul>' if errors else ""
    stats_html = f'<div class="stats">{"".join(parts)}</div>' if parts else ""
    stamp = live["fetched_at"].strftime("%Y-%m-%d %H:%M")
    win = fmt_week_window(live["fetched_at"].date())
    prev_date = fmt_full_date(prev_snapshot["date"]) if prev_snapshot else "—"

    follower_form = f"""<h3>X フォロワー数を記録する</h3>
<div class="cmdbox">
  <div class="cmd-head">
    <span>今日のフォロワー数</span>
    <input type="number" id="x-followers-input" min="0" placeholder="例: 5"
      style="font:inherit;font-size:14px;padding:4px 10px;border-radius:6px;border:1px solid var(--line);background:var(--bg);color:var(--fg);width:120px"
      oninput="(function(){{
        var n=document.getElementById('x-followers-input').value;
        var d=new Date().toISOString().slice(0,10);
        var cmd=n?'python3 scripts/record_x_followers.py --count '+n+' --date '+d:'数字を入力してください';
        document.getElementById('x-followers-cmd').textContent=cmd;
      }})()">
    <button class="copy" onclick="(function(){{
      var t=document.getElementById('x-followers-cmd').textContent;
      if(t==='数字を入力してください')return;
      navigator.clipboard.writeText(t).then(function(){{
        var b=event.target;b.textContent='コピーしました';b.classList.add('done');
        setTimeout(function(){{b.textContent='コピー';b.classList.remove('done')}},2000);
      }});
    }})()">コピー</button>
  </div>
  <div class="step-cmd" id="x-followers-cmd">数字を入力してください</div>
  <div class="cmd-foot">実行すると GROWTH.yaml の最新スナップショットに記録されます。実行後は <code>python3 scripts/build_admin_dashboard.py</code> で画面を更新してください。</div>
</div>"""

    compare_note = f'<p class="muted small">前回の週次記録（{prev_date}）との比較。「前回比」はその時点からの変化です。</p>' if prev_snapshot else ""

    return f'<h3>取り直した実測値（{stamp} 時点 / {win}）</h3>{compare_note}{stats_html}{error_html}{follower_form}'


def _pct(value) -> str:
    return "—" if value is None else f"{value:.2f}%"


def _range(low, high, formatter) -> str:
    if low is None or high is None:
        return "—"
    if low == high:
        return formatter(low)
    return f"{formatter(low)} 〜 {formatter(high)}"


def _post_breakdown(axes: list[dict]) -> str:
    """型ごとの実績。中央値だけを見て選ばないよう、件数と幅を必ず並べる。"""
    if not axes:
        return ""

    blocks = []
    for axis in axes:
        rows = []
        for row in axis["rows"]:
            note = '<span class="pill muted">参考値</span>' if row["reference_only"] else ""
            rows.append(
                [
                    f'{esc(row["group"])} {note}',
                    str(row["posts"]),
                    str(row["measured"]),
                    fmt_views(int(row["views_median"])) if row["views_median"] is not None else "—",
                    _range(row["views_min"], row["views_max"], lambda v: fmt_views(int(v))),
                    _pct(row["reach_median"]),
                    _range(row["reach_min"], row["reach_max"], _pct),
                ]
            )
        blocks.append(
            f'<h4>{esc(axis["axis"])}</h4>'
            + table(
                ["区分", "投稿数", "実測できた数", "表示回数の中央値", "表示回数の幅", "到達率の中央値", "到達率の幅"],
                rows,
                cls="breakdown",
            )
        )

    return f"""<h3>型ごとの実績（直近60日）</h3>
<p class="lead">どのリプライ先を選ぶかで到達が大きく変わるため、投稿を3つの軸で束ねたもの。
<strong>「到達率」と「表示回数」は必ず一緒に見てください。</strong>到達率5.8%でも表示回数が5回なら、
読まれた人数はほとんどいません。実測が{esc(str(actions.MIN_SAMPLES))}件に満たない区分は「参考値」と表示しています
（1〜2件の結果はたまたまで動くため、判断の根拠にはできません）。暫定値は集計から外しています。</p>
<div class="breakdowns">{"".join(blocks)}</div>"""


def section_x(data: dict) -> str:
    posts = data["x_posts"]
    themes = data["themes"]
    today = data["today"]

    if not posts:
        return '<section id="x"><h2>5. X（旧Twitter）投稿</h2><p class="muted">content/x/posts.md に実績の記録がありません。</p></section>'

    recent = [p for p in posts if (today - p["date"]).days <= 30]

    def is_measured(post: dict) -> bool:
        return post["own_views_status"] == "measured" and post["own_views"] is not None

    # グラフ・主指標は「自分の投稿が読まれた回数」のうち本計測できたものだけ。
    # 暫定値（投稿直後の値）は入れない。8/8は4→51、2→37と10倍以上動いた
    own_by_day: dict[dt.date, int] = {}
    for post in posts:
        if is_measured(post):
            own_by_day[post["date"]] = own_by_day.get(post["date"], 0) + post["own_views"]
    ordered_days = sorted(own_by_day)[-30:]

    measured = [p for p in recent if is_measured(p)]
    total_own_30 = sum(p["own_views"] for p in measured)
    total_parent_30 = sum(p["parent_views"] or 0 for p in recent)
    with_url = sum(1 for p in recent if p["has_url"])

    stats = (
        '<div class="stats">'
        + card("直近30日の投稿数", str(len(recent)))
        + card(
            "自分の投稿が読まれた回数",
            fmt_views(total_own_30),
            f"実測できた {len(measured)} 本の合計（30日の総量ではない）",
            tone="ok" if measured else "warn",
        )
        + card(
            "返信先の投稿の規模（参考）",
            fmt_views(total_parent_30),
            "自分への到達ではない。相手の投稿が読まれた数",
            tone="muted",
        )
        + card("うちURL付き", str(with_url), "リンクを踏ませる枠は週1〜2本が上限")
        + card("最後の投稿", f'{(today - posts[0]["date"]).days}日前', fmt_full_date(posts[0]["date"]), tone="warn" if (today - posts[0]["date"]).days > 3 else "ok")
        + "</div>"
    )

    chart = bar_chart([(f"{d.month}/{d.day}", float(own_by_day[d])) for d in ordered_days], color="var(--c5)")

    status_label = {"measured": "実測", "provisional": "暫定", "missing": "未計測"}
    rows = []
    for post in posts[:80]:
        text = post["text"] or post["target"]
        status = post["own_views_status"]
        reach = ""
        if is_measured(post) and post["parent_views"]:
            reach = f'{post["own_views"] / post["parent_views"] * 100:.2f}%'
        rows.append(
            [
                fmt_full_date(post["date"]),
                esc(post["kind"]),
                esc(post["theme"]),
                esc(post["type"]),
                f'<span class="{"strong" if (post["own_views"] or 0) >= 300 else ""}">{fmt_views(post["own_views"])}</span>',
                f'<span class="pill {"ok" if status == "measured" else "warn" if status == "provisional" else "muted"}">{status_label[status]}</span>',
                fmt_views(post["parent_views"]),
                reach or "—",
                f'<span class="clamp" title="{esc(text)}">{esc(text[:90])}</span>',
            ]
        )

    theme_rows = []
    for theme in sorted(themes, key=lambda t: (t["x_posted_at"] is not None, t["x_posted_at"] or dt.date.min)):
        age = (today - theme["x_posted_at"]).days if theme["x_posted_at"] else None
        tone = "muted" if age is None else ("danger" if age > 21 else "warn" if age > 10 else "ok")
        theme_rows.append([esc(theme["title"]), fmt_full_date(theme["x_posted_at"]), f'<span class="pill {tone}">{"記録なし" if age is None else f"{age}日前"}</span>'])

    breakdown_html = _post_breakdown(data.get("post_breakdown") or [])

    return f"""<section id="x"><h2>5. X（旧Twitter）投稿</h2>
<p class="lead">記録元は <code>content/x/posts.md</code>。X の管理画面から自動では取れないので、投稿したら手で書き足す運用。ここに出ていない投稿は記録漏れ。</p>
{stats}
<h3>日ごとに自分の投稿が読まれた回数（本計測ぶんのみ・直近30日）</h3>
{chart}
<p class="muted small"><strong>「返信先の投稿の規模」は自分への到達ではありません。</strong>相手の投稿が何人に読まれたかで、そこから自分のリプライに届くのは実測で0.007%〜5.8%（約800倍の開き）。この2つを足し合わせたり、サイトのPVと比べたりはできません。表示回数はXの管理画面から自動で取れないので、投稿の1〜2日後に手で書き足す運用です。投稿直後の値は「暫定」として集計から外しています。</p>
{breakdown_html}
<h3>テーマごとの最終投稿</h3>
{table(["テーマ", "最終投稿日", "経過"], theme_rows)}
<h3>投稿の記録（新しい順・最大80件）</h3>
{table(["日付", "種別", "テーマ", "型・タイプ", "自分の表示回数", "計測", "返信先の規模", "到達率", "内容 / リプライ先"], rows, cls="posts", tools="テーマ・リプライ先・本文で絞り込む")}
</section>"""


def section_themes(data: dict) -> str:
    themes = data["themes"]
    legend = " ".join(f'<span class="legend"><span class="dot ok">●</span>{esc(label)}</span>' for _, label in STAGES)
    rows = []
    for theme in themes:
        period = f'{theme["sample_min"]} 〜 {theme["sample_max"]}' if theme["sample_min"] else "—"
        rows.append(
            [
                theme_name(theme),
                stage_dots(theme["stages"]),
                fmt_num(theme["records"]),
                esc(period),
                fmt_full_date(theme["published_at"]),
                f'<span class="pill {"ok" if theme["update_mode"] == "adapter" else "warn"}">{esc(theme["update_mode_label"])}</span>',
            ]
        )
    return f"""<section id="themes"><h2>6. テーマの状態</h2>
<p class="lead">丸印は左から {esc("・".join(label for _, label in STAGES))} の8工程。<span class="dot ok">●</span>済み <span class="dot warn">◐</span>途中 <span class="dot muted">○</span>未着手 <span class="dot danger">×</span>止まっている <span class="dot muted">–</span>対象外 <span class="dot muted">·</span>台帳に記載なし（丸印にカーソルを載せると工程名が出ます）</p>
{table(["テーマ", "工程", "件数", "収集した期間", "公開日", "更新のしかた"], rows)}
</section>"""


def section_data_assets(data: dict) -> str:
    assets = data.get("data_assets") or {}
    rows = []
    for row in assets.get("themes", []):
        rows.append([esc(row["title"]) + ('<br><span class="muted">公開対象</span>' if row["published"] else '<br><span class="muted">非掲載</span>'),
                     *[esc(fmt_num(row[key])) for key in ("canonical", "saved", "pending", "unknown", "unresolved", "excluded")],
                     esc(fmt_num(row["active"])) + ' / ' + esc(fmt_num(row["reread_excluded"])) + ' / ' + esc(fmt_num(row["unreviewed"])),
                     esc(row["reread_status"])])
    backup = assets.get("backup", {})
    inventory = assets.get("inventory", {})
    inventory_counts = " / ".join(esc(k) + ": " + esc(fmt_num(v)) for k, v in inventory.get("summary", {}).items())
    coverage_rows = [[esc(k), esc({"verified": "照合済み", "missing": "欠落あり", "stale": "変更あり"}[v["status"]]), esc(v["missing"]), esc(v["changed"])] for k, v in inventory.get("coverage", {}).items()]
    operations = [[esc(op["title"]), esc(op["owner"]), esc(op["due_at"]),
                   '完了' if op["status"] == 'done' else ('期限超過' if op["overdue"] else '予定'),
                   esc(op["task"]), esc(op["next_action"])] for op in assets.get("operations", [])]
    return f'''<section id="data-assets"><h2>データの品質と保全</h2>
<p class="lead">全11テーマ（公開対象10・非掲載1）の管理。保存IDは指定した保存回の範囲です。正典外は採用漏れと断定せず、判断状態を分けています。</p>
<p>{esc(assets.get("adoption_status", "未確認"))}<br>照合日時: {esc(assets.get("snapshot_at") or "未確認")}</p>
{table(["テーマ", "正典", "保存ID", "確認待ち", "判断不明", "記録なし", "除外確認", "再読: 意見 / 意見外 / 未読意見", "再読台帳の状態"], rows)}
<p class="small muted">「—」は未確認です。共通台帳未管理は再読0件を意味しません。再読件数には旧記録の継承を含み、人による確認率ではありません。意見外の再読記録も正典に残っています。</p>
<h3>保管境界と保全照合</h3><p>{esc(inventory.get("status", "未確認"))}<br>{inventory_counts}</p>
{table(["保存区分", "照合記録", "欠落数", "変更数"], coverage_rows)}
<h3>バックアップと復元</h3><p>{esc(backup.get("status", "記録なし・未確認"))}<br>
確認日時: {esc(backup.get("verified_at", "未確認"))} / ファイル数: {esc(fmt_num(backup.get("file_count")))}<br>
保存物: {esc(backup.get("archive_name", "未確認"))} / 対象コミット: {esc(backup.get("git_commit", "未確認"))}</p>
<p class="small muted">復元確認の記録を表示しています。現在の外付け接続状態は検査していません。別マシンでの復元は未実施（課題33・50）です。</p>
<h3>継続作業の担当と期日</h3><p>{esc(assets.get("operations_status", "予定未確認"))}</p>
{table(["作業", "担当", "期日", "状態", "課題", "次にすること"], operations)}</section>'''


def section_data_updates(data: dict) -> str:
    updates = data["data_updates"]
    rows = []
    for update in updates:
        ok = update["checks_ok"]
        tone = "ok" if ok else ("danger" if ok is False else "muted")
        rows.append(
            [
                fmt_full_date(update["date"]),
                esc(update["theme"]),
                fmt_num(update["raw"]),
                fmt_num(update["duplicates"]),
                f'<strong>{fmt_num(update["new"])}</strong>',
                fmt_num(update["opinions"]),
                fmt_num(update["errors"]),
                f'<span class="pill {tone}">{esc(update["status"])}</span>',
                f'{update["minutes"]}分' if update["minutes"] else "—",
            ]
        )
    note = '<p class="lead">1回の収集で何件取れて、何件が重複で落ちて、何件が新しく残ったか。<code>data/verification/updates/</code> にある検査結果そのままです。ここに出るのは検査つきで回した回だけで、それ以前の手作業の回は記録が残っていません。</p>'
    return f'<section id="data"><h2>7. データ更新の履歴</h2>{note}{table(["日付", "テーマ", "取得", "重複", "新規", "意見", "分類エラー", "検査", "所要"], rows, cls="updates")}</section>'


def section_history(data: dict) -> str:
    commits = data["commits"]
    by_date: dict[dt.date, list[dict]] = {}
    for commit in commits:
        by_date.setdefault(commit["date"], []).append(commit)

    blocks = []
    for date in sorted(by_date, reverse=True):
        entries = []
        for commit in by_date[date]:
            scope = f'<span class="scope">{esc(commit["scope"])}</span>' if commit["scope"] else ""
            entries.append(
                f'<li><span class="tag {esc(commit["kind"] or "other")}">{esc(commit["kind_label"])}</span>'
                f'{scope}<span>{esc(commit["message"])}</span>'
                f'<code class="muted">{esc(commit["sha"])}</code></li>'
            )
        items = "".join(entries)
        blocks.append(f'<div class="day"><div class="day-date">{fmt_full_date(date)}<span class="muted small">{len(by_date[date])}件</span></div><ul class="commits">{items}</ul></div>')

    return f"""<section id="history"><h2>8. 変更履歴</h2>
<p class="lead">直近 {len(commits)} 件の変更（合流だけの記録は除外）。「機能追加」は新しくできるようになったこと、「不具合修正」は壊れていたものを直したことです。</p>
<div class="timeline">{"".join(blocks)}</div>
</section>"""


def _task_phase(status: str) -> tuple[str, str]:
    """状態の書き出しから、進み具合をざっくり3段階に分ける。"""
    head = status.replace("*", "").strip()
    if head.startswith("完了"):
        return "完了", "ok"
    if head.startswith(("進行中", "対応中", "一部", "大部分", "実装済", "対応案")):
        return "進行中", "warn"
    if head.startswith(("判断保留", "保留", "待ち")):
        return "保留", "muted"
    return "未着手", "danger"


PRIORITY_TONE = {"高": "danger", "中": "warn", "低": "muted"}


def section_tasks(data: dict) -> str:
    tasks = data["tasks"]
    rows = []
    counts = {"未着手": 0, "進行中": 0, "完了": 0, "保留": 0}
    waiting = 0
    for task in tasks:
        phase, tone = _task_phase(task["status"])
        counts[phase] = counts.get(phase, 0) + 1
        owner_decision = task["waiting_on"] and "なし" not in task["waiting_on"]
        if owner_decision and phase != "完了":
            waiting += 1
        priority = task["priority"]
        rows.append(
            [
                f'課題{task["id"]}',
                f'<strong>{esc(task["title"])}</strong>'
                + (f'<div class="muted small">関連: {esc(task["related"])}</div>' if task["related"] else ""),
                f'<span class="pill {PRIORITY_TONE.get(priority, "muted")}">{esc(priority or "—")}</span>',
                f'<span class="pill {tone}">{phase}</span>'
                + (f'<div class="pill danger">判断待ち: {esc(task["waiting_on"])}</div>' if owner_decision else ""),
                esc(task["deadline"]) or '<span class="muted">—</span>',
                esc(task["next_step"]) or '<span class="muted">未記入</span>',
                esc(task["status"][:200]),
            ]
        )

    summary = " / ".join(f"{key} {value}件" for key, value in counts.items() if value)
    headline = (
        f'<div class="stats">{card("あなたの判断待ち", str(waiting), "止まっている理由が判断なら、ここが動かないと先へ進みません", tone="danger" if waiting else "ok")}'
        + card("課題の総数", str(len(tasks)), esc(summary))
        + "</div>"
    )
    filled = sum(1 for task in tasks if task["next_step"])
    return f"""<section id="tasks"><h2>9. 抱えている課題</h2>
<p class="lead"><code>TASK_BOARD.md</code> に載っている {len(tasks)} 件。「完了」と書かれたまま残っているものは、
まだ <code>archive/TASK_BOARD_ARCHIVE.md</code> へ移していないだけです。区分は状態欄の書き出しから機械的に判定しています。</p>
{headline}
<p class="muted small">「優先度」「期限」「次にすること」「判断待ち」は <code>TASK_BOARD.md</code> の任意の欄です
（<code>**優先度**: 高</code> のように書くと、ここに出ます）。いま {filled} / {len(tasks)} 件に記入があります。</p>
{table(["番号", "課題", "優先度", "区分", "期限", "次にすること", "状態"], rows, cls="tasks", tools="課題名・状態で絞り込む")}
</section>"""


def section_health(data: dict) -> str:
    rows = []
    for check in data["health"]:
        tone = "ok" if check["ok"] else ("danger" if check["ok"] is False else "warn")
        mark = "使える" if check["ok"] else ("使えない" if check["ok"] is False else "未確認")
        rows.append([esc(check["name"]), f'<span class="pill {tone}">{mark}</span>', esc(check["detail"])])
    return f"""<section id="health"><h2>10. 数字の取得元の状態</h2>
<p class="lead">流入や投票の数字を自動で取ってくる仕組みが生きているかどうか。ここが赤いと、上の数字が古いまま更新されません。</p>
{table(["取得元", "状態", "詳細"], rows)}
</section>"""


# ------------------------------------------------------------------ 全体


CSS = """
:root{--bg:#edf2f6;--fg:#172235;--muted:#637184;--line:#d4dde5;--panel:#fbfcfe;
--ink:#173c5a;--water:#2f7e83;--sun:#c98b24;--paper:#f7fafc;
--ok:#24775b;--warn:#9b6712;--danger:#ad3d35;--soon:#276c9b;
--c1:#276c9b;--c2:#6467a8;--c3:#24775b;--c4:#b37720;--c5:#2f7e83;}
@media (prefers-color-scheme:dark){:root{--bg:#101820;--fg:#e7edf2;--muted:#9aaaba;--line:#2b3a47;--panel:#16222c;
--ink:#9dc5df;--water:#64b7b7;--sun:#e0a94b;--paper:#15212a;
--ok:#5bc798;--warn:#e4b45c;--danger:#f08479;--soon:#70afe0;
--c1:#70afe0;--c2:#a5a8e7;--c3:#5bc798;--c4:#e4b45c;--c5:#64b7b7;}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font-family:"Hiragino Sans","Yu Gothic UI","Noto Sans JP",-apple-system,BlinkMacSystemFont,sans-serif;
line-height:1.7;font-size:15px;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px 96px}
header.top{padding:30px 0 14px;border-bottom:1px solid var(--line);margin-bottom:8px;position:relative}
header.top::after{content:"";position:absolute;left:0;bottom:-1px;width:116px;height:3px;background:linear-gradient(90deg,var(--ink) 0 46%,var(--sun) 46% 54%,var(--water) 54%)}
header.top h1{margin:0 0 4px;font:700 28px/1.25 "Avenir Next","Hiragino Sans",sans-serif;letter-spacing:.015em}
.product-name{font:700 11px/1 "Avenir Next",sans-serif;letter-spacing:.2em;color:var(--water);text-transform:uppercase;margin-bottom:8px}
.built{color:var(--muted);font-size:13px}
.local-note{margin-top:12px;padding:10px 14px;border-radius:8px;background:color-mix(in srgb,var(--soon) 12%,transparent);
border:1px solid color-mix(in srgb,var(--soon) 35%,transparent);font-size:13px}
nav.toc{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 92%,transparent);
backdrop-filter:blur(8px);border-bottom:1px solid var(--line);margin-bottom:24px}
nav.toc ul{display:flex;gap:4px;list-style:none;margin:0;padding:8px 0;overflow-x:auto}
nav.toc a{display:block;white-space:nowrap;padding:5px 11px;border-radius:999px;text-decoration:none;
color:var(--muted);font-size:13px}
nav.toc a:hover{background:var(--panel);color:var(--fg)}
nav.toc a:focus-visible,.copy:focus-visible,.filter:focus-visible{outline:3px solid color-mix(in srgb,var(--soon) 38%,transparent);outline-offset:2px}
section{margin:0 0 52px;scroll-margin-top:56px}
h2{font-size:20px;margin:0 0 6px;padding-bottom:8px;border-bottom:2px solid var(--line)}
h3{font-size:15px;margin:28px 0 10px;color:var(--fg)}
h4{font-size:13px;margin:0 0 8px;color:var(--muted);font-weight:600}
.lead{color:var(--muted);font-size:13.5px;margin:8px 0 16px}
.muted{color:var(--muted)}.small{font-size:12.5px}.strong{font-weight:700}
.eyebrow{font:700 11px/1.2 "Avenir Next",sans-serif;letter-spacing:.18em;color:var(--water);text-transform:uppercase;margin-bottom:9px}
.north-star{display:grid;grid-template-columns:88px 1fr;gap:24px;align-items:center;margin:10px 0 0;padding:26px 28px;
background:linear-gradient(120deg,color-mix(in srgb,var(--ink) 10%,var(--panel)),var(--panel) 62%,color-mix(in srgb,var(--water) 10%,var(--panel)));
border:1px solid var(--line);border-radius:18px;box-shadow:0 16px 42px color-mix(in srgb,var(--ink) 9%,transparent)}
.north-star h2{max-width:850px;margin:0;padding:0;border:0;font-size:clamp(22px,3vw,35px);line-height:1.5;letter-spacing:.015em;color:var(--ink)}
.north-star-mark{width:76px;height:76px;position:relative;border-radius:50%;border:1px solid color-mix(in srgb,var(--ink) 24%,transparent)}
.north-star-mark::before,.north-star-mark::after{content:"";position:absolute;top:15px;width:32px;height:46px;border:2px solid var(--ink)}
.north-star-mark::before{left:8px;border-right:0;border-radius:32px 0 0 32px;transform:rotate(18deg)}
.north-star-mark::after{right:8px;border-left:0;border-radius:0 32px 32px 0;transform:rotate(-18deg)}
.north-star-mark span{position:absolute;width:8px;height:8px;border-radius:50%;background:var(--sun);left:33px;top:33px;z-index:2}
.north-star-mark i,.north-star-mark b{position:absolute;width:22px;height:2px;background:var(--water);top:36px}.north-star-mark i{left:3px}.north-star-mark b{right:3px}
.operating-rule{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0 30px}
.operating-rule span{padding:6px 11px;border:1px solid var(--line);border-radius:999px;background:color-mix(in srgb,var(--panel) 78%,transparent);font-size:12px;color:var(--muted)}
.operating-rule strong{color:var(--fg)}
.section-kicker{display:grid;grid-template-columns:80px minmax(240px,1fr) auto;gap:14px;align-items:end;margin:26px 0 12px;border-bottom:1px solid var(--line);padding-bottom:8px}
.section-kicker>span{font:700 10px/1 "Avenir Next",sans-serif;letter-spacing:.18em;color:var(--water)}
.section-kicker h2,.section-kicker h3{font-size:19px;margin:0;padding:0;border:0}.section-kicker p{margin:0;color:var(--muted);font-size:12px;text-align:right}
.brief-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:14px;overflow:hidden}
.brief-card{min-height:140px;background:var(--panel);padding:16px 17px;border-top:4px solid transparent}
.brief-card.focus{border-top-color:var(--water)}.brief-card.warn{border-top-color:var(--sun)}.brief-card.danger{border-top-color:var(--danger)}
.brief-label{font:700 11px/1.2 "Avenir Next","Hiragino Sans",sans-serif;letter-spacing:.08em;color:var(--muted);margin-bottom:12px}
.brief-text{font-weight:650;line-height:1.65}
.company-split{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:22px}.company-split.lower{margin-top:30px;align-items:start}
.company-split h3,.board-heading{font-size:15px;margin:0 0 10px}.count{display:inline-grid;place-items:center;min-width:22px;height:22px;margin-left:5px;border-radius:50%;background:var(--ink);color:var(--panel);font:700 11px/1 "Avenir Next",sans-serif}
.approval-list,.work-list{display:grid;gap:9px}.approval-card,.work-item,.milestone,.finance-panel,.org-card{background:var(--panel);border:1px solid var(--line);border-radius:12px}
.approval-card{padding:15px;border-left:4px solid var(--sun)}.approval-top,.work-meta,.milestone-head{display:flex;align-items:center;justify-content:space-between;gap:7px;flex-wrap:wrap}
.approval-card h4,.work-item h4{font-size:14px;color:var(--fg);margin:10px 0 4px}.approval-card p,.work-item p,.finance-panel p,.org-card p{font-size:12.5px;color:var(--muted);margin:3px 0;line-height:1.6}
.approval-card ul{margin:8px 0 0;padding-left:18px;color:var(--muted);font-size:11.5px}.recommendation{font-size:12px;color:var(--muted);margin-top:8px}.recommendation strong{color:var(--water)}
.ledger-alerts{margin-top:0}.empty-state{padding:18px;border:1px dashed var(--line);border-radius:12px;color:var(--muted);background:color-mix(in srgb,var(--panel) 70%,transparent)}
.board-heading{margin-top:30px}.work-list{grid-template-columns:repeat(2,minmax(0,1fr))}.work-item{padding:14px 15px}.work-meta{justify-content:flex-start;color:var(--water);font-size:11.5px}.work-item h4{font-weight:650}.work-id{font:500 10px/1.4 "Avenir Next",sans-serif;color:var(--muted);margin-top:10px;letter-spacing:.02em}
.milestone-grid{display:grid;grid-template-columns:1.35fr 1fr 1fr;gap:10px}.milestone{padding:14px}.milestone-name{font-weight:750;color:var(--ink)}.milestone ul{list-style:none;margin:12px 0 0;padding:0;border-top:1px solid var(--line)}
.milestone li{display:flex;justify-content:space-between;gap:10px;padding:6px 0;border-bottom:1px solid color-mix(in srgb,var(--line) 66%,transparent);font-size:12px}.milestone li span{color:var(--muted)}.milestone li strong{font-variant-numeric:tabular-nums;text-align:right}
.finance-panel{padding:16px}.finance-month{font:750 13px/1.2 "Avenir Next",sans-serif;color:var(--water);letter-spacing:.08em}.finance-numbers{display:grid;grid-template-columns:repeat(2,1fr);gap:1px;background:var(--line);margin:12px 0;border:1px solid var(--line)}
.finance-numbers div{background:var(--panel);padding:10px}.finance-numbers span{display:block;font-size:10.5px;color:var(--muted)}.finance-numbers strong{font:750 18px/1.4 "Avenir Next","Hiragino Sans",sans-serif}.finance-note{font-size:11.5px}
.org-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.org-card{padding:12px;position:relative;overflow:hidden}.org-key{position:absolute;right:8px;top:5px;font:800 28px/1 "Avenir Next",sans-serif;color:color-mix(in srgb,var(--ink) 9%,transparent)}.org-card h4{position:relative;margin:0 0 4px;color:var(--ink)}
code{background:color-mix(in srgb,var(--fg) 8%,transparent);padding:1px 5px;border-radius:4px;font-size:12.5px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(158px,1fr));gap:10px;margin:14px 0}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.stat-label{font-size:12px;color:var(--muted)}
.stat-value{font-size:24px;font-weight:700;line-height:1.25;font-variant-numeric:tabular-nums}
.stat-sub{font-size:11.5px;color:var(--muted);margin-top:2px}
.stat.danger .stat-value{color:var(--danger)}.stat.warn .stat-value{color:var(--warn)}.stat.ok .stat-value{color:var(--ok)}
.next-head{border-radius:10px;padding:14px 16px;margin:12px 0;border:1px solid var(--line);background:var(--panel)}
.next-head.danger{border-left:5px solid var(--danger)}
.next-head.warn{border-left:5px solid var(--warn)}
.next-title{font-size:20px;font-weight:700;line-height:1.4}
.next-why{color:var(--muted);font-size:13px;margin-top:2px}
.next-why .meta{margin-left:10px;padding:1px 8px;border-radius:999px;font-size:11.5px;
background:color-mix(in srgb,var(--muted) 15%,transparent)}
.signals{list-style:none;margin:8px 0 16px;padding:0;display:grid;
grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:6px}
.signal{display:flex;gap:8px;align-items:baseline;background:var(--panel);border:1px solid var(--line);
border-radius:8px;padding:7px 11px;font-size:12.5px}
.signal-mark{flex:none;font-weight:700}
.signal.ok .signal-mark{color:var(--ok)}
.signal.danger .signal-mark{color:var(--danger)}
.signal.warn .signal-mark{color:var(--warn)}
.signal-name{flex:none;font-weight:600}
.signal-detail{color:var(--muted);font-size:11.5px}
.cmdbox{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:12px 0}
.cmdbox.not-ready{opacity:.72}
.cmdbox.recommended{border-color:color-mix(in srgb,var(--ok) 50%,var(--line))}
.cmd-head{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:8px}
.cmd-blocked{font-size:12px;color:var(--warn);background:color-mix(in srgb,var(--warn) 12%,transparent);
border-radius:6px;padding:6px 10px;margin-bottom:8px}
.copy{margin-left:auto;font:inherit;font-size:12px;padding:3px 12px;border-radius:999px;cursor:pointer;
border:1px solid var(--line);background:color-mix(in srgb,var(--fg) 5%,transparent);color:var(--fg)}
.copy:hover{background:color-mix(in srgb,var(--fg) 10%,transparent)}
.copy.done{border-color:var(--ok);color:var(--ok)}
.copy-area{width:100%;min-height:96px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;
line-height:1.6;padding:8px 10px;margin-bottom:8px;border-radius:6px;border:2px solid var(--soon);
background:var(--bg);color:var(--fg);white-space:pre}
.step{margin-bottom:7px}
.step-note{font-size:11.5px;color:var(--muted);margin-bottom:2px}
.step-cmd{display:block;white-space:pre-wrap;word-break:break-all;font-size:12px;line-height:1.6;
padding:6px 10px;border-radius:6px;background:color-mix(in srgb,var(--fg) 7%,transparent)}
.cmd-foot{margin-top:10px;padding-top:9px;border-top:1px solid var(--line);font-size:12px;color:var(--muted);line-height:1.8}
.links{display:inline-flex;gap:8px;margin-left:8px;font-size:11px;font-weight:400}
.links a{color:var(--soon);text-decoration:none;border-bottom:1px dotted currentColor}
.links a:hover{border-bottom-style:solid}
.breakdowns h4{margin-top:14px}
table.breakdown{min-width:640px}
table.breakdown td{white-space:nowrap}
.rest{margin-top:14px}
.rest summary{cursor:pointer;font-size:13px;color:var(--muted);padding:6px 0}
.stale{position:sticky;top:0;z-index:9;background:var(--danger);color:#fff;padding:10px 16px;font-size:13.5px;line-height:1.6}
.stale code{background:rgba(255,255,255,.22);color:#fff}
.alerts{list-style:none;margin:12px 0;padding:0;display:flex;flex-direction:column;gap:8px}
.alerts li{border-left:4px solid var(--line);background:var(--panel);border-radius:0 8px 8px 0;padding:10px 14px}
.alerts li.danger{border-left-color:var(--danger)}
.alerts li.warn{border-left-color:var(--warn)}
.alerts li strong{display:block;font-size:14px}
.alerts li span{display:block;color:var(--muted);font-size:12.5px}
.ok-banner{background:color-mix(in srgb,var(--ok) 12%,transparent);border:1px solid color-mix(in srgb,var(--ok) 32%,transparent);
border-radius:8px;padding:12px 14px;margin:12px 0}
.warn-banner{background:color-mix(in srgb,var(--warn) 12%,transparent);border:1px solid color-mix(in srgb,var(--warn) 32%,transparent);
border-radius:8px;padding:10px 14px;margin:12px 0;font-size:13px}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--panel)}
table{width:100%;border-collapse:collapse;font-size:13px;min-width:520px}
th{text-align:left;font-weight:600;font-size:12px;color:var(--muted);padding:9px 12px;
border-bottom:1px solid var(--line);white-space:nowrap;background:color-mix(in srgb,var(--fg) 3%,transparent)}
td{padding:9px 12px;border-bottom:1px solid color-mix(in srgb,var(--line) 60%,transparent);vertical-align:top}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover{background:color-mix(in srgb,var(--fg) 3%,transparent)}
table.posts{min-width:900px}
table.posts td{white-space:nowrap}
table.updates{min-width:700px}
table.updates td{white-space:nowrap}
.pill{display:inline-block;padding:1px 8px;border-radius:999px;font-size:11.5px;font-weight:600;white-space:nowrap;
background:color-mix(in srgb,var(--muted) 15%,transparent);color:var(--muted)}
.pill.ok{background:color-mix(in srgb,var(--ok) 16%,transparent);color:var(--ok)}
.pill.warn{background:color-mix(in srgb,var(--warn) 18%,transparent);color:var(--warn)}
.pill.danger{background:color-mix(in srgb,var(--danger) 16%,transparent);color:var(--danger)}
.pill.soon{background:color-mix(in srgb,var(--soon) 16%,transparent);color:var(--soon)}
.dots{display:inline-flex;gap:3px}
.dot{font-size:13px;line-height:1}
.dot.ok{color:var(--ok)}.dot.warn{color:var(--warn)}.dot.danger{color:var(--danger)}.dot.muted{color:var(--muted)}
.calendar{display:grid;grid-template-columns:repeat(7,1fr);gap:4px;margin:12px 0}
.cal-head{text-align:center;font-size:11.5px;color:var(--muted);padding:2px 0}
.cal-day{min-height:62px;background:var(--panel);border:1px solid var(--line);border-radius:7px;padding:5px 6px}
.cal-day.past{opacity:.45}
.cal-day.today{border-color:var(--soon);box-shadow:0 0 0 1px var(--soon) inset}
.cal-date{font-size:11px;color:var(--muted);font-variant-numeric:tabular-nums}
.cal-item{font-size:10.5px;line-height:1.35;margin-top:3px;padding:2px 4px;border-radius:4px;
overflow:hidden;text-overflow:ellipsis}
.cal-item.collect{background:color-mix(in srgb,var(--c5) 20%,transparent);color:var(--fg)}
.cal-item.refresh{background:color-mix(in srgb,var(--c2) 22%,transparent);color:var(--fg)}
.cal-item.check{background:color-mix(in srgb,var(--soon) 21%,transparent);color:var(--fg)}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px;margin:14px 0}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.chart{width:100%;height:auto;display:block}
.chart .grid{stroke:var(--line);stroke-width:1}
.chart .axis{fill:var(--muted);font-size:9px}
.goals{display:flex;flex-direction:column;gap:10px;margin:12px 0}
.goal-label{display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px}
.bar{height:8px;border-radius:999px;background:color-mix(in srgb,var(--muted) 20%,transparent);overflow:hidden}
.bar span{display:block;height:100%;background:var(--c1);border-radius:999px}
.timeline{display:flex;flex-direction:column;gap:6px}
.day{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 14px}
.day-date{display:flex;gap:10px;align-items:baseline;font-size:12.5px;font-weight:600;color:var(--muted);
font-variant-numeric:tabular-nums}
.commits{list-style:none;margin:6px 0 0;padding:0;display:flex;flex-direction:column;gap:5px}
.commits li{display:flex;gap:8px;align-items:baseline;font-size:13px;flex-wrap:wrap}
.tag{flex:none;font-size:10.5px;font-weight:700;padding:1px 7px;border-radius:4px;
background:color-mix(in srgb,var(--muted) 16%,transparent);color:var(--muted)}
.tag.feat{background:color-mix(in srgb,var(--ok) 16%,transparent);color:var(--ok)}
.tag.fix{background:color-mix(in srgb,var(--danger) 15%,transparent);color:var(--danger)}
.tag.docs{background:color-mix(in srgb,var(--soon) 15%,transparent);color:var(--soon)}
.scope{font-size:11.5px;color:var(--muted)}
.clamp{display:inline-block;max-width:38ch;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;vertical-align:bottom}
.legend{margin-right:10px;font-size:12px;color:var(--muted)}
footer{border-top:1px solid var(--line);padding-top:16px;color:var(--muted);font-size:12.5px}
.tablebox{margin:12px 0}
.tabletools{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:8px}
.filter{font:inherit;font-size:13px;padding:5px 12px;border-radius:999px;min-width:240px;
border:1px solid var(--line);background:var(--panel);color:var(--fg)}
.filter-count{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}
th.sortcol{cursor:pointer;user-select:none}
th.sortcol:hover{color:var(--fg)}
th.sortcol::after{content:"";opacity:.35;margin-left:4px}
th.sortcol[data-dir="asc"]::after{content:"▲";opacity:1}
th.sortcol[data-dir="desc"]::after{content:"▼";opacity:1}
.ops-x-usage{display:grid;grid-template-columns:1fr 1fr;gap:2px 8px;margin:0 0 10px;padding:8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);font-size:10.5px}.ops-x-usage strong,.ops-x-usage span{display:block}.ops-x-usage span{color:var(--muted)}
.ops-x-run{margin:9px 14px 0;padding:9px;border:1px solid var(--line);border-radius:8px;background:var(--bg);font-size:10.5px;line-height:1.6}.ops-x-run strong{display:block}.ops-x-run span{color:var(--muted)}
.operations{margin-top:18px}.ops-heading{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;margin-bottom:16px}.ops-heading h2{border:0;padding:0;font-size:25px;color:var(--ink)}.ops-heading p{margin:5px 0;color:var(--muted);font-size:13px}.ops-server{display:grid;grid-template-columns:auto auto;align-items:center;gap:1px 8px;flex:none;padding:9px 12px;border:1px solid var(--line);border-radius:10px;background:var(--panel);font-size:12px}.ops-server small{grid-column:2;color:var(--muted)}.ops-live{width:9px;height:9px;border-radius:50%;background:var(--ok);box-shadow:0 0 0 4px color-mix(in srgb,var(--ok) 15%,transparent);grid-row:1/3}.ops-warning{padding:10px 13px;margin-bottom:12px;border-left:4px solid var(--danger);background:color-mix(in srgb,var(--danger) 10%,var(--panel));font-size:12.5px}.ops-layout{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(340px,.72fr);gap:14px;align-items:start}.ops-left,.ops-console{min-width:0}.ops-toolbar{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin-bottom:9px}.ops-toolbar .primary{margin-left:auto}.ops-link{border:0;background:none;color:var(--soon);font:inherit;font-size:12px;cursor:pointer;padding:4px}.ops-link:hover{text-decoration:underline}.ops-themes{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;max-height:480px;overflow:auto;padding-right:3px}.ops-theme{border:1px solid var(--line);background:var(--panel);border-radius:10px;padding:10px}.ops-theme:has(input:checked){border-color:var(--water);box-shadow:0 0 0 1px var(--water) inset;background:color-mix(in srgb,var(--water) 6%,var(--panel))}.ops-select{display:flex;gap:8px;align-items:flex-start;cursor:pointer}.ops-select input{accent-color:var(--water);margin-top:4px}.ops-select span{min-width:0}.ops-select strong,.ops-select small{display:block}.ops-select strong{font-size:13px;line-height:1.45}.ops-select small{font:500 9.5px/1.4 "Avenir Next",sans-serif;color:var(--muted);overflow:hidden;text-overflow:ellipsis}.ops-theme-state{display:flex;gap:5px;margin:8px 0}.ops-theme-actions,.ops-channel-actions,.ops-console-actions{display:flex;gap:6px;flex-wrap:wrap}.ops-btn{appearance:none;border:1px solid var(--line);border-radius:7px;background:color-mix(in srgb,var(--fg) 4%,var(--panel));color:var(--fg);font:650 11.5px/1.25 "Hiragino Sans","Yu Gothic UI",sans-serif;padding:7px 9px;cursor:pointer}.ops-btn:hover:not(:disabled){border-color:var(--water);background:color-mix(in srgb,var(--water) 9%,var(--panel))}.ops-btn:focus-visible,.ops-link:focus-visible,.ops-select input:focus-visible,.ops-chat-form textarea:focus-visible,.ops-inline input:focus-visible{outline:3px solid color-mix(in srgb,var(--soon) 35%,transparent);outline-offset:2px}.ops-btn.primary{background:var(--ink);border-color:var(--ink);color:var(--panel)}.ops-btn.danger{color:var(--danger)}.ops-btn:disabled{opacity:.42;cursor:not-allowed}.ops-disabled{margin:7px 0 0;color:var(--warn);font-size:10.5px;line-height:1.45}.ops-channel-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}.ops-channel{position:relative;overflow:hidden;border:1px solid var(--line);border-radius:12px;background:var(--panel);padding:13px}.ops-channel h3{margin:0 0 3px;font-size:14px}.ops-channel p{margin:0 0 11px;color:var(--muted);font-size:11.5px;max-width:44ch}.ops-channel-mark{position:absolute;right:10px;top:5px;font:800 32px/1 "Avenir Next",sans-serif;color:color-mix(in srgb,var(--water) 14%,transparent)}.ops-inline{display:flex;gap:6px;margin-top:8px}.ops-inline input,.ops-chat-form textarea{min-width:0;width:100%;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:var(--fg);font:inherit;font-size:11.5px;padding:7px 9px}.ops-console{position:sticky;top:58px;border:1px solid var(--line);border-radius:14px;background:var(--panel);box-shadow:0 16px 38px color-mix(in srgb,var(--ink) 8%,transparent);max-height:calc(100vh - 76px);overflow:auto}.ops-console-head{display:flex;justify-content:space-between;gap:10px;padding:14px 15px 11px;border-bottom:1px solid var(--line)}.ops-console-head h3{margin:0;font-size:15px}.ops-empty{padding:34px 20px;color:var(--muted);font-size:12.5px;text-align:center}.ops-session-meta{display:flex;gap:5px;align-items:center;flex-wrap:wrap;padding:10px 14px;border-bottom:1px solid var(--line)}.ops-session-meta code{margin-left:auto;max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:9px}.ops-rail{list-style:none;margin:0;padding:10px 14px 5px}.ops-rail li{position:relative;padding:0 0 13px 24px;font-size:11.5px}.ops-rail li::before{content:"";position:absolute;left:4px;top:3px;width:9px;height:9px;border-radius:50%;background:var(--line);box-shadow:0 0 0 3px var(--panel),0 0 0 4px var(--line)}.ops-rail li::after{content:"";position:absolute;left:8px;top:16px;bottom:0;width:1px;background:var(--line)}.ops-rail li:last-child::after{display:none}.ops-rail li.active::before{background:var(--water);box-shadow:0 0 0 3px var(--panel),0 0 0 4px var(--water)}.ops-rail time{display:block;color:var(--muted);font-size:9.5px}.ops-approval{margin:6px 14px;padding:10px;border:1px solid color-mix(in srgb,var(--sun) 45%,var(--line));border-radius:9px;background:color-mix(in srgb,var(--sun) 9%,var(--panel));font-size:11.5px}.ops-chat{border-top:1px solid var(--line);padding:12px 14px;max-height:260px;overflow:auto}.ops-message{padding:9px 10px;margin:0 0 7px;border-radius:9px;background:var(--bg);white-space:pre-wrap;font-size:11.5px;line-height:1.6}.ops-message.user{margin-left:24px;background:color-mix(in srgb,var(--soon) 11%,var(--panel))}.ops-live-summary{color:var(--muted);font-size:11px;padding:7px;border-left:2px solid var(--water)}.ops-chat-form{display:grid;grid-template-columns:1fr auto;gap:6px;padding:0 14px 10px}.ops-console-actions{padding:0 14px 12px}.ops-history{border-top:1px solid var(--line);padding:11px 14px}.ops-history-head{display:flex;justify-content:space-between;font-size:11.5px;margin-bottom:6px}.ops-job{display:grid;grid-template-columns:auto 1fr auto;gap:7px;align-items:center;width:100%;border:0;border-top:1px solid color-mix(in srgb,var(--line) 65%,transparent);background:none;color:var(--fg);text-align:left;padding:7px 0;cursor:pointer}.ops-job:hover strong{color:var(--water)}.ops-job strong{font-size:11.5px}.ops-job small{display:block;color:var(--muted);font-size:9.5px}.ops-job-state{width:7px;height:7px;border-radius:50%;background:var(--muted)}.ops-job-state.running,.ops-job-state.preflight,.ops-job-state.reviewing,.ops-job-state.applying,.ops-job-state.verifying{background:var(--water)}.ops-job-state.completed{background:var(--ok)}.ops-job-state.failed,.ops-job-state.cancelled{background:var(--danger)}.ops-job-state.needs_input,.ops-job-state.awaiting_approval{background:var(--sun)}
@media(max-width:640px){
.wrap{padding:0 12px 64px}
.north-star{grid-template-columns:54px 1fr;gap:13px;padding:18px 15px}.north-star-mark{width:50px;height:50px}.north-star-mark::before,.north-star-mark::after{top:9px;width:22px;height:31px}.north-star-mark::before{left:4px}.north-star-mark::after{right:4px}.north-star-mark span{left:21px;top:21px}.north-star-mark i,.north-star-mark b{width:14px;top:24px}.north-star h2{font-size:19px;line-height:1.55}
.section-kicker{grid-template-columns:62px 1fr}.section-kicker p{grid-column:1/-1;text-align:left}.brief-grid{grid-template-columns:1fr}.brief-card{min-height:0}.company-split,.company-split.lower,.work-list,.milestone-grid,.org-grid{grid-template-columns:1fr}.operating-rule{gap:5px}.finance-numbers{grid-template-columns:1fr 1fr}
.calendar{grid-template-columns:repeat(7,1fr);gap:2px}
.cal-day{min-height:48px;padding:3px}
.cal-item{font-size:9px}
h1{font-size:21px}
.filter{min-width:0;flex:1}
.signals{grid-template-columns:1fr}
.step-cmd{font-size:11px}
/* 横長の表は読めないので、1行を1枚のカードに組み替える */
.tablebox .scroll{border:none;background:none;overflow-x:visible}
.tablebox table,.tablebox thead,.tablebox tbody,.tablebox tr,.tablebox td{display:block;min-width:0}
.tablebox thead{display:none}
.tablebox tr{background:var(--panel);border:1px solid var(--line);border-radius:10px;
padding:8px 12px;margin-bottom:8px}
.tablebox td{border:none;padding:3px 0;white-space:normal;display:flex;gap:10px;font-size:12.5px}
.tablebox td::before{content:attr(data-label);flex:none;width:8.5em;color:var(--muted);font-size:11.5px}
.tablebox .clamp{max-width:none;white-space:normal}
.ops-heading{display:block}.ops-server{margin-top:10px;width:max-content}.ops-layout{grid-template-columns:1fr}.ops-themes,.ops-channel-grid{grid-template-columns:1fr;max-height:none}.ops-console{position:static;max-height:none}.ops-toolbar .primary{margin-left:0}.operations{margin-bottom:36px}
}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
"""

# 外部CDNは使わない方針なので、必要な動きだけを素のJSで書く。
# ここでやるのは2つだけ。日数の再計算はしない（Python側と二重管理になるため）。
SCRIPT = r"""
(function () {
  // 1) 作った日と、いま開いた日がずれていたら赤帯を出す。
  //    この画面は静止画なので、古いHTMLを開くと「あと2日」が実は「1日超過」になる。
  var built = document.body.dataset.built;
  var now = new Date();
  var pad = function (n) { return String(n).padStart(2, "0"); };
  var iso = now.getFullYear() + "-" + pad(now.getMonth() + 1) + "-" + pad(now.getDate());
  if (built && built !== iso) {
    var days = Math.round((Date.parse(iso) - Date.parse(built)) / 86400000);
    var bar = document.createElement("div");
    bar.className = "stale";
    bar.innerHTML =
      "<strong>この画面は" + Math.abs(days) + "日" + (days > 0 ? "前" : "先") + "（" + built +
      "）に作ったものです。</strong>「あと◯日」「今日やること」はすべてその時点の計算で、" +
      "いまの状況とは違います。作り直す: <code>python3 scripts/build_admin_dashboard.py --open</code>";
    document.body.insertBefore(bar, document.body.firstChild);
  }

  // 2) コマンドのコピー。file:// では navigator.clipboard が塞がれる環境があるので、
  //    失敗したら選択状態にして、手でコピーできるところまで持っていく。
  var buttons = document.querySelectorAll(".copy");
  Array.prototype.forEach.call(buttons, function (button) {
    button.addEventListener("click", function () {
      var box = document.getElementById(button.getAttribute("data-copy"));
      if (!box) { return; }
      var lines = Array.prototype.map.call(box.querySelectorAll(".step-cmd"), function (el) {
        return el.textContent;
      });
      var reset = function () {
        button.textContent = "まとめてコピー";
        button.classList.remove("done");
      };
      var done = function () {
        button.textContent = "コピーしました";
        button.classList.add("done");
        setTimeout(reset, 2000);
      };
      var text = lines.join("\n");
      // 最後の手段。コマンドだけを入れた入力欄を作って選択させる。
      // 注釈まで選ぶと、貼り付けたときに日本語が混ざって動かない。
      var selectOnly = function () {
        var area = document.createElement("textarea");
        area.value = text;
        area.setAttribute("readonly", "readonly");
        area.className = "copy-area";
        box.parentNode.insertBefore(area, box);
        area.focus();
        area.select();
        var copied = false;
        try { copied = document.execCommand("copy"); } catch (error) { copied = false; }
        if (copied) {
          area.remove();
          done();
          return;
        }
        button.textContent = "この枠を ⌘C でコピーしてください";
        area.addEventListener("blur", function () { area.remove(); reset(); });
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, selectOnly);
      } else {
        selectOnly();
      }
    });
  });

  // 3) 表の絞り込み。入力に含まれる語をすべて含む行だけ残す（空白区切りのAND）。
  Array.prototype.forEach.call(document.querySelectorAll(".tablebox"), function (box) {
    var input = box.querySelector(".filter");
    var counter = box.querySelector(".filter-count");
    var rows = box.querySelectorAll("tbody tr");
    if (!input) { return; }
    input.addEventListener("input", function () {
      var words = input.value.toLowerCase().split(/\s+/).filter(Boolean);
      var shown = 0;
      Array.prototype.forEach.call(rows, function (row) {
        var text = row.textContent.toLowerCase();
        var hit = words.every(function (word) { return text.indexOf(word) !== -1; });
        row.style.display = hit ? "" : "none";
        if (hit) { shown += 1; }
      });
      counter.textContent = words.length ? shown + " / " + rows.length + " 件" : "";
    });
  });

  // 4) 列見出しをクリックして並べ替え。
  //    "1.2K" や "0.30%" のまま文字として並べると桁が壊れるので、数値に直してから比べる。
  var sortValue = function (text) {
    var value = text.trim();
    if (!value || value === "—") { return { empty: true }; }
    if (/^\d{4}-\d{2}-\d{2}$/.test(value)) { return { num: Date.parse(value) }; }
    var match = value.match(/^\*{0,2}(-?[\d,]+(?:\.\d+)?)\s*(万|K|M|%)?/i);
    if (match) {
      var num = parseFloat(match[1].replace(/,/g, ""));
      var unit = (match[2] || "").toUpperCase();
      if (unit === "万") { num *= 10000; }
      else if (unit === "K") { num *= 1000; }
      else if (unit === "M") { num *= 1000000; }
      return { num: num };
    }
    return { str: value };
  };

  Array.prototype.forEach.call(document.querySelectorAll("table.sortable"), function (table) {
    var headers = table.querySelectorAll("thead th");
    Array.prototype.forEach.call(headers, function (header, column) {
      header.classList.add("sortcol");
      header.addEventListener("click", function () {
        var descending = header.getAttribute("data-dir") !== "desc";
        Array.prototype.forEach.call(headers, function (other) {
          other.removeAttribute("data-dir");
        });
        header.setAttribute("data-dir", descending ? "desc" : "asc");
        var body = table.querySelector("tbody");
        var rows = Array.prototype.slice.call(body.querySelectorAll("tr"));
        rows.sort(function (left, right) {
          var a = sortValue((left.children[column] || {}).textContent || "");
          var b = sortValue((right.children[column] || {}).textContent || "");
          if (a.empty && b.empty) { return 0; }
          if (a.empty) { return 1; }   // 値の無い行は常に下
          if (b.empty) { return -1; }
          var result;
          if (a.num !== undefined && b.num !== undefined) { result = a.num - b.num; }
          else { result = String(a.str || a.num).localeCompare(String(b.str || b.num), "ja"); }
          return descending ? -result : result;
        });
        rows.forEach(function (row) { body.appendChild(row); });
      });
    });
  });
})();
"""

INTERACTIVE_SCRIPT = r"""
(function () {
  var root = document.getElementById("operations");
  if (!root) { return; }
  var token = root.getAttribute("data-token");
  var state = { jobs: [], themes: [], dirty: [], x_api_usage: {} };
  var selectedJobId = null;
  var batchRemaining = [];
  var statusLabel = {
    queued:"実行待ち",preflight:"準備確認",running:"実行中",reviewing:"品質監査中",
    awaiting_approval:"CEO承認待ち",applying:"反映中",verifying:"最終検査中",
    completed:"完了",needs_input:"対応待ち",failed:"失敗",cancelled:"中止"
  };
  var actionLabel = {
    "theme.collect":"収集・分類","theme.prepare_release":"公開候補の確認","theme.release":"承認して公開",
    "x.prepare":"今日のX候補","x.record_post":"X投稿の記録","x.measure":"X結果の計測",
    "metrics.refresh":"流入データ取得","metrics.explain":"流入データの解説"
  };
  var warn = function (message) {
    var box = document.getElementById("ops-dirty"); box.hidden = !message; box.textContent = message || "";
  };
  var api = function (path, options) {
    options = options || {};
    options.headers = Object.assign({"X-Dashboard-Token":token}, options.headers || {});
    if (options.body) { options.headers["Content-Type"] = "application/json"; }
    return fetch(path, options).then(function (response) {
      return response.json().then(function (data) {
        if (!response.ok) { throw new Error(data.error || "操作に失敗しました"); }
        return data;
      });
    });
  };
  var post = function (path, payload) { return api(path, {method:"POST",body:JSON.stringify(payload || {})}); };
  var escapeHtml = function (value) {
    var div=document.createElement("div"); div.textContent=value == null ? "" : String(value); return div.innerHTML;
  };
  var latestJob = function (action, theme, statuses) {
    return state.jobs.find(function (job) {
      return job.action === action && (!theme || job.theme === theme) && (!statuses || statuses.indexOf(job.status) !== -1);
    });
  };
  var startJob = function (action, payload) {
    if (state.dirty.length && ["theme.collect","x.record_post","x.measure"].indexOf(action) !== -1) {
      warn("未コミットの変更があるため、変更を伴う作業は開始できません: " + state.dirty.slice(0,3).join(" / "));
      return Promise.reject(new Error("未コミット変更があります"));
    }
    if (action === "theme.prepare_release") {
      var source = latestJob("theme.collect", payload.theme, ["completed"]);
      if (!source) { warn("先に同じテーマの「収集・分類」を完了してください。"); return Promise.reject(new Error("収集結果がありません")); }
      payload.source_job_id = source.id;
    }
    warn("");
    return post("/api/v1/jobs", {action:action,payload:payload || {}}).then(function (job) {
      selectedJobId = job.id; return refresh();
    }).catch(function (error) { warn(error.message); throw error; });
  };
  var renderJobs = function () {
    var list=document.getElementById("job-list");
    document.getElementById("job-count").textContent=state.jobs.length+"件";
    list.innerHTML=state.jobs.slice(0,16).map(function (job) {
      return '<button class="ops-job" data-job="'+job.id+'"><span class="ops-job-state '+job.status+'"></span><span><strong>'+escapeHtml(actionLabel[job.action] || job.action)+'</strong><small>'+escapeHtml(job.theme || (job.created_at || "").slice(0,16))+'</small></span><span class="pill">'+escapeHtml(statusLabel[job.status] || job.status)+'</span></button>';
    }).join("") || '<div class="muted small">まだ作業履歴がありません</div>';
    Array.prototype.forEach.call(list.querySelectorAll("[data-job]"),function(button){button.onclick=function(){selectedJobId=button.getAttribute("data-job");renderDetail();};});
  };
  var renderXUsage = function () {
    var box=document.getElementById("x-api-usage");if(!box){return;}
    var usage=(state.x_api_usage||{}).days_30||{};
    if(!usage.runs){box.innerHTML='<strong>API換算は未記録</strong><span>次回の「今日のX候補」から記録</span>';return;}
    box.innerHTML='<strong>30日: '+escapeHtml(usage.unique_posts_read)+'投稿を確認</strong><span>'+escapeHtml(usage.runs)+'回中 '+escapeHtml(usage.complete_runs)+'回が完全記録</span><strong>投稿だけ $'+escapeHtml(Number(usage.posts_only_usd||0).toFixed(2))+'</strong><span>投稿者情報込み $'+escapeHtml(Number(usage.posts_and_users_usd||0).toFixed(2))+'</span>';
  };
  var renderDetail = function () {
    var job=state.jobs.find(function(item){return item.id===selectedJobId;});
    document.getElementById("job-empty").hidden=!!job; document.getElementById("job-detail").hidden=!job;
    if(!job){return;}
    document.getElementById("job-title").textContent=(actionLabel[job.action]||job.action)+(job.theme?" / "+job.theme:"");
    var status=document.getElementById("job-status");status.textContent=statusLabel[job.status]||job.status;status.className="pill "+(["completed"].indexOf(job.status)>=0?"ok":["failed","cancelled"].indexOf(job.status)>=0?"danger":["needs_input","awaiting_approval"].indexOf(job.status)>=0?"warn":"soon");
    document.getElementById("job-owner").textContent=job.control_owner==="codex_app"?"Codexアプリで操作":"管理画面で操作";
    document.getElementById("job-thread").textContent=job.thread_id||"セッション準備中";
    var runBox=document.getElementById("job-x-usage"),runUsage=(job.result||{}).x_api_usage;
    runBox.hidden=!runUsage;
    if(runUsage){var cost=runUsage.estimated_cost_usd||{};runBox.innerHTML='<strong>この検索: '+escapeHtml(runUsage.unique_posts_read==null?"件数不明":runUsage.unique_posts_read+"投稿")+' / 候補 '+escapeHtml(runUsage.candidates_shortlisted==null?"不明":runUsage.candidates_shortlisted+"件")+'</strong><span>検索 '+escapeHtml(runUsage.queries_count==null?"不明":runUsage.queries_count+"回")+'・個別確認 '+escapeHtml(runUsage.post_detail_reads==null?"不明":runUsage.post_detail_reads+"件")+'・API換算 $'+escapeHtml(cost.posts_only==null?"—":Number(cost.posts_only).toFixed(2))+'〜$'+escapeHtml(cost.posts_and_users==null?"—":Number(cost.posts_and_users).toFixed(2))+(runUsage.counts_complete?"":"（一部未計測）")+'</span>';}
    var progress=(job.progress||[]).slice(-8);document.getElementById("job-progress").innerHTML=progress.map(function(item,index){return '<li class="'+(index===progress.length-1?"active":"")+'"><span>'+escapeHtml(item.text)+'</span><time>'+escapeHtml((item.at||"").replace("T"," ").slice(0,16))+'</time></li>';}).join("");
    var approval=document.getElementById("job-approval"); approval.hidden=true; approval.innerHTML="";
    if(job.pending_request&&job.pending_request.kind==="runtime"){
      approval.hidden=false;approval.innerHTML='<strong>Codexの操作許可</strong><p>'+escapeHtml(job.pending_request.reason||"")+'</p><div class="ops-channel-actions"><button class="ops-btn primary" data-decision="accept">今回だけ許可</button><button class="ops-btn" data-decision="acceptForSession">この作業中は許可</button><button class="ops-btn danger" data-decision="decline">許可しない</button></div>';
    } else if(job.status==="awaiting_approval"&&job.action==="theme.prepare_release"){
      var artifacts=((job.result||{}).artifacts||[]).map(function(item){return '<a class="ops-btn" target="_blank" rel="noopener" href="/api/v1/jobs/'+job.id+'/artifact?path='+encodeURIComponent(item.path)+'">'+escapeHtml(item.label)+' をプレビュー</a>';}).join("");
      approval.hidden=false;approval.innerHTML='<strong>公開してよいか確認してください</strong><p>品質監査: '+escapeHtml((job.quality||{}).verdict||"—")+'。承認後はmainへの統合、検査、push、本番の現物確認、バックアップまで自動で進みます。</p><div class="ops-channel-actions">'+artifacts+'<button class="ops-btn primary" id="approve-release">承認して公開</button></div>';
      approval.querySelector("#approve-release").onclick=function(){startJob("theme.release",{theme:job.theme,source_job_id:job.id});};
    }
    Array.prototype.forEach.call(approval.querySelectorAll("[data-decision]"),function(button){button.onclick=function(){post("/api/v1/jobs/"+job.id+"/decision",{decision:button.getAttribute("data-decision")}).then(refresh).catch(function(error){warn(error.message);});};});
    var chat=document.getElementById("job-chat");chat.innerHTML=(job.messages||[]).map(function(message){return '<div class="ops-message '+escapeHtml(message.role||"assistant")+'">'+escapeHtml(message.text||"")+'</div>';}).join("")+(job.live_summary?'<div class="ops-live-summary">'+escapeHtml(job.live_summary)+'</div>':"");chat.scrollTop=chat.scrollHeight;
    var handoff=document.getElementById("handoff-job");handoff.textContent=job.control_owner==="codex_app"?"管理画面へ戻す":"Codexアプリへ引き継ぐ";handoff.disabled=["running","preflight","reviewing","applying","verifying"].indexOf(job.status)>=0;
    document.getElementById("send-job-message").disabled=job.control_owner!=="dashboard"||["running","preflight","reviewing","applying","verifying"].indexOf(job.status)>=0;
  };
  var maybeContinueBatch = function () {
    if(!batchRemaining.length){return;}
    var current=state.jobs.find(function(job){return job.id===selectedJobId;});
    if(current&&current.action==="theme.collect"&&current.status==="completed"){
      var next=batchRemaining.shift();startJob("theme.collect",{theme:next});
    } else if(current&&["failed","needs_input","cancelled"].indexOf(current.status)>=0){
      warn("連続収集を停止しました。現在のテーマを確認してから、残りを再度選択してください。");batchRemaining=[];
    }
  };
  var refresh = function () {return api("/api/v1/state").then(function(data){state=data;document.getElementById("ops-model").textContent=data.model;if(!selectedJobId&&data.jobs.length){selectedJobId=data.jobs[0].id;}if(data.dirty.length){warn("未コミット変更を保護しています: "+data.dirty.slice(0,3).join(" / "));}renderXUsage();renderJobs();renderDetail();maybeContinueBatch();});};
  Array.prototype.forEach.call(root.querySelectorAll("[data-action]"),function(button){button.addEventListener("click",function(){var action=button.getAttribute("data-action");var payload={};if(button.getAttribute("data-theme")){payload.theme=button.getAttribute("data-theme");}startJob(action,payload);});});
  document.getElementById("collect-selected").onclick=function(){var selected=Array.prototype.map.call(root.querySelectorAll(".ops-theme input:checked"),function(input){return input.value;});if(!selected.length){warn("収集するテーマを一つ以上選んでください。");return;}batchRemaining=selected.slice(1);startJob("theme.collect",{theme:selected[0]});};
  document.getElementById("select-due").onclick=function(){var due=state.themes.filter(function(theme){if(!theme.collect_at){return false;}return Date.parse(theme.collect_at)<=Date.now()+7*86400000;}).map(function(theme){return theme.key;});Array.prototype.forEach.call(root.querySelectorAll(".ops-theme input"),function(input){input.checked=due.indexOf(input.value)>=0;});};
  document.getElementById("record-x").onclick=function(){startJob("x.record_post",{url:document.getElementById("x-post-url").value});};
  document.getElementById("refresh-metrics").onclick=function(){startJob("metrics.refresh",{x_followers:document.getElementById("x-followers").value});};
  document.getElementById("open-x").onclick=function(){var jobs=state.jobs.filter(function(job){return job.action==="x.prepare"&&job.status==="completed";});var messages=jobs.length?(jobs[0].messages||[]):[];var text=messages.map(function(item){return item.text||"";}).join("\n");var match=text.match(/POST_TEXT_BEGIN\s*([\s\S]*?)\s*POST_TEXT_END/);if(!match){warn("先に「今日のX候補」を作り、推奨案を確認してください。");return;}window.open("https://x.com/intent/post?text="+encodeURIComponent(match[1].trim()),"_blank","noopener");};
  document.getElementById("send-job-message").onclick=function(){var text=document.getElementById("job-message").value;if(!selectedJobId||!text.trim()){return;}post("/api/v1/jobs/"+selectedJobId+"/messages",{text:text}).then(function(){document.getElementById("job-message").value="";refresh();}).catch(function(error){warn(error.message);});};
  document.getElementById("cancel-job").onclick=function(){if(selectedJobId){post("/api/v1/jobs/"+selectedJobId+"/cancel",{}).then(refresh).catch(function(error){warn(error.message);});}};
  document.getElementById("handoff-job").onclick=function(){var job=state.jobs.find(function(item){return item.id===selectedJobId;});if(!job){return;}post("/api/v1/jobs/"+job.id+"/control",{owner:job.control_owner==="codex_app"?"dashboard":"codex_app"}).then(refresh).catch(function(error){warn(error.message);});};
  document.getElementById("shutdown-dashboard").onclick=function(){post("/api/v1/shutdown",{}).then(function(){document.body.innerHTML='<main style="max-width:520px;margin:15vh auto;font-family:sans-serif"><h1>管理画面を終了しました</h1><p>このタブは閉じてかまいません。</p></main>';}).catch(function(error){warn(error.message);});};
  refresh().catch(function(error){warn(error.message);});setInterval(refresh,2000);setInterval(function(){post("/api/v1/heartbeat",{});},30000);
})();
"""

NAV = [
    ("ceo", "CEOホーム"),
    ("company", "承認・目標・収支"),
    ("next", "次の一手"),
    ("alerts", "対応が要ること"),
    ("schedule", "スケジュール"),
    ("traffic", "流入"),
    ("x", "X投稿"),
    ("themes", "テーマ"),
    ("data", "データ更新"),
    ("data-assets", "データ品質・保全"),
    ("history", "変更履歴"),
    ("tasks", "課題"),
    ("health", "取得元"),
]


def render(data: dict) -> str:
    navigation = ([('operations', '運用する')] if data.get("interactive") else []) + NAV
    nav = "".join(f'<li><a href="#{key}">{esc(label)}</a></li>' for key, label in navigation)
    built = data["built_at"].strftime("%Y-%m-%d %H:%M")
    # 古いHTMLを開いたときに赤帯を出すため、作成日をブラウザ側から読める形で置く
    built_date = data["today"].isoformat()
    sections = "".join(
        [
            section_ceo(data),
            section_operations(data),
            section_company(data),
            section_next(data),
            section_alerts(data),
            section_schedule(data),
            section_traffic(data),
            section_x(data),
            section_themes(data),
            section_data_updates(data),
            section_data_assets(data),
            section_history(data),
            section_tasks(data),
            section_health(data),
        ]
    )
    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>SNS反応まっぷ 管理画面</title>
<style>{CSS}</style></head>
<body data-built="{built_date}"><div class="wrap">
<header class="top">
<div class="product-name">SNS Reaction Map / Executive Office</div>
<h1>CEO 経営管理画面</h1>
<div class="built">{built} 時点のリポジトリの中身から作成</div>
<div class="local-note"><strong>このファイルは公開されません。</strong>手元の Mac の中だけにあり、
GitHub にも上がりません（<code>company/dashboard/</code> は Git の管理対象外）。数字を新しくするには作り直すコマンドを実行します。</div>
</header>
<nav class="toc"><ul>{nav}</ul></nav>
{sections}
<footer>
生成元: THEMES.yaml / GROWTH.yaml / content/x/posts.md / TASK_BOARD.md / data/verification/ / git log<br>
作り直すコマンド: <code>python3 scripts/build_admin_dashboard.py --open</code>（実測値も取り直す場合は <code>--fetch</code> を足す）
</footer>
</div><script>{SCRIPT}{INTERACTIVE_SCRIPT if data.get('interactive') else ''}</script></body></html>
"""
