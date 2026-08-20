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
PUBLIC_BASE = "https://issue-stance-lab.github.io/sns-reaction-map/"


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
            '<p class="lead">Xの管理画面で表示回数を見て、<code>x-posts.md</code> の該当行に書き足してください。'
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

    calendar = _calendar(themes, today)
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
<p class="lead">「収集」は投稿データを集めるだけの作業、「公開更新」は集めたデータをページに反映して公開するところまで。予定日は <code>THEMES.yaml</code> が正。</p>
{stats}
<h3>これから4週間</h3>
{calendar}
<h3>テーマ別</h3>
{table(["テーマ", "次の収集", "次の公開更新", "更新のしかた", "最終公開更新", "前回追加"], rows)}
</section>"""


def _calendar(themes: list[dict], today: dt.date) -> str:
    events: dict[dt.date, list[tuple[str, str]]] = {}
    for theme in themes:
        if theme["collect_at"]:
            events.setdefault(theme["collect_at"], []).append(("収集", theme["title"]))
        if theme["refresh_at"]:
            events.setdefault(theme["refresh_at"], []).append(("公開", theme["title"]))

    start = today - dt.timedelta(days=today.weekday())
    cells = []
    for offset in range(28):
        day = start + dt.timedelta(days=offset)
        classes = ["cal-day"]
        if day == today:
            classes.append("today")
        if day < today:
            classes.append("past")
        items = "".join(
            f'<div class="cal-item {"collect" if kind == "収集" else "refresh"}">{esc(kind)}・{esc(title)}</div>'
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
        return '<section id="x"><h2>5. X（旧Twitter）投稿</h2><p class="muted">x-posts.md に実績の記録がありません。</p></section>'

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
<p class="lead">記録元は <code>x-posts.md</code>。X の管理画面から自動では取れないので、投稿したら手で書き足す運用。ここに出ていない投稿は記録漏れ。</p>
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
<p class="muted small">「優先度」「次にすること」「判断待ち」は <code>TASK_BOARD.md</code> の任意の欄です
（<code>**優先度**: 高</code> のように書くと、ここに出ます）。いま {filled} / {len(tasks)} 件に記入があります。</p>
{table(["番号", "課題", "優先度", "区分", "次にすること", "状態"], rows, cls="tasks", tools="課題名・状態で絞り込む")}
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
:root{--bg:#f6f7f9;--fg:#16191d;--muted:#697080;--line:#dfe3e9;--panel:#fff;
--ok:#1a7f4b;--warn:#a86400;--danger:#b3261e;--soon:#1f6feb;
--c1:#1f6feb;--c2:#7b48d6;--c3:#1a7f4b;--c4:#c2740b;--c5:#0e7c86;}
@media (prefers-color-scheme:dark){:root{--bg:#101317;--fg:#e6e9ee;--muted:#98a1b0;--line:#2a3038;--panel:#171b21;
--ok:#4ec98a;--warn:#e0a33c;--danger:#f2776b;--soon:#6ea8fe;
--c1:#6ea8fe;--c2:#b48ef5;--c3:#4ec98a;--c4:#e0a33c;--c5:#3fbfc9;}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Noto Sans JP",sans-serif;
line-height:1.7;font-size:15px;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px 96px}
header.top{padding:28px 0 12px;border-bottom:1px solid var(--line);margin-bottom:8px}
header.top h1{margin:0 0 4px;font-size:26px;letter-spacing:.01em}
.built{color:var(--muted);font-size:13px}
.local-note{margin-top:12px;padding:10px 14px;border-radius:8px;background:color-mix(in srgb,var(--soon) 12%,transparent);
border:1px solid color-mix(in srgb,var(--soon) 35%,transparent);font-size:13px}
nav.toc{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 92%,transparent);
backdrop-filter:blur(8px);border-bottom:1px solid var(--line);margin-bottom:24px}
nav.toc ul{display:flex;gap:4px;list-style:none;margin:0;padding:8px 0;overflow-x:auto}
nav.toc a{display:block;white-space:nowrap;padding:5px 11px;border-radius:999px;text-decoration:none;
color:var(--muted);font-size:13px}
nav.toc a:hover{background:var(--panel);color:var(--fg)}
section{margin:0 0 52px;scroll-margin-top:56px}
h2{font-size:20px;margin:0 0 6px;padding-bottom:8px;border-bottom:2px solid var(--line)}
h3{font-size:15px;margin:28px 0 10px;color:var(--fg)}
h4{font-size:13px;margin:0 0 8px;color:var(--muted);font-weight:600}
.lead{color:var(--muted);font-size:13.5px;margin:8px 0 16px}
.muted{color:var(--muted)}.small{font-size:12.5px}.strong{font-weight:700}
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
@media(max-width:640px){
.wrap{padding:0 12px 64px}
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
}
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

NAV = [
    ("next", "次の一手"),
    ("alerts", "対応が要ること"),
    ("schedule", "スケジュール"),
    ("traffic", "流入"),
    ("x", "X投稿"),
    ("themes", "テーマ"),
    ("data", "データ更新"),
    ("history", "変更履歴"),
    ("tasks", "課題"),
    ("health", "取得元"),
]


def render(data: dict) -> str:
    nav = "".join(f'<li><a href="#{key}">{esc(label)}</a></li>' for key, label in NAV)
    built = data["built_at"].strftime("%Y-%m-%d %H:%M")
    # 古いHTMLを開いたときに赤帯を出すため、作成日をブラウザ側から読める形で置く
    built_date = data["today"].isoformat()
    sections = "".join(
        [
            section_next(data),
            section_alerts(data),
            section_schedule(data),
            section_traffic(data),
            section_x(data),
            section_themes(data),
            section_data_updates(data),
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
<h1>SNS反応まっぷ 管理画面</h1>
<div class="built">{built} 時点のリポジトリの中身から作成</div>
<div class="local-note"><strong>このファイルは公開されません。</strong>手元の Mac の中だけにあり、
GitHub にも上がりません（<code>admin/</code> は Git の管理対象外）。数字を新しくするには作り直すコマンドを実行します。</div>
</header>
<nav class="toc"><ul>{nav}</ul></nav>
{sections}
<footer>
生成元: THEMES.yaml / GROWTH.yaml / x-posts.md / TASK_BOARD.md / data/verification/ / git log<br>
作り直すコマンド: <code>python3 scripts/build_admin_dashboard.py --open</code>（実測値も取り直す場合は <code>--fetch</code> を足す）
</footer>
</div><script>{SCRIPT}</script></body></html>
"""
