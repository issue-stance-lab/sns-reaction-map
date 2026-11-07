"""Render the photo and diagram guide from the checked constitutional reading data."""
from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

from constitutional_reading import (
    esc, fmt, issue_name, jp_date, ordered_issues, ordered_reasons, pct1, reason_label,
)

PREFIX = "constitutional-amendment-"
ASSETS = Path("scripts/constitutional_redesign")


def render(root: Path, data: dict, body: BeautifulSoup) -> str:
    guide = BeautifulSoup((root / ASSETS / "visual-guide.html").read_text(encoding="utf-8"), "html.parser")
    public = data["public"]
    issues = ordered_issues(data)
    by_id = {issue["id"].removeprefix(PREFIX): issue for issue in issues}
    reasons = {
        issue["id"]: dict(ordered_reasons(data, issue, data["cfg"]["issues"][issue["id"]]))
        for issue in issues
    }
    counts = {
        **{key: issue["count"] for key, issue in by_id.items()},
        "collected": public["collected_count"],
        "opinions": public["opinion_count"],
        "issues": len(issues),
        "reasons": sum(map(len, reasons.values())),
    }
    for field in guide.select("[data-cav-count]"):
        field.string = fmt(counts[field["data-cav-count"]])

    def destination(key: str) -> str:
        name, _, reason = key.partition("/")
        issue = by_id[name]["id"]
        target = f"fr-r-{issue}-{reason}"
        return target if reason and body.find(id=target) else f"issue-{issue}"

    for link in guide.select("[data-cav-target]"):
        link["href"] = "#" + destination(link["data-cav-target"])
    for node in guide.select("[data-cav-reason]"):
        name, reason = node["data-cav-reason"].split("/")
        issue = by_id[name]
        iid = issue["id"]
        bucket = reasons[iid].get(reason)
        cfg = data["cfg"]["issues"][iid]
        if bucket:
            voice = cfg.get("reasons", {}).get(reason, {}).get("voice")
            node.append(BeautifulSoup(
                f'<h4>{esc(reason_label(data, cfg, reason, bucket))}</h4>'
                f'<p>{fmt(bucket["count"])}件・この論点の{pct1(bucket["count"], issue["count"])}％</p>'
                + (f'<p>{esc(voice)}</p>' if voice else ""), "html.parser",
            ))
        node.append(BeautifulSoup(
            f'<a href="#{esc(destination(node["data-cav-reason"]))}">SNSの理由と内訳を読む →</a>',
            "html.parser",
        ))

    chart = ['<h4>論点ごとの意見件数</h4>', '<ul class="cav-bars">']
    for issue in issues:
        count = issue["count"]
        chart.append(
            f'<li><a href="#issue-{esc(issue["id"])}">{esc(issue_name(data, issue))}</a>'
            f'<span class="cav-bar" aria-hidden="true"><i style="width:{pct1(count, counts["opinions"])}%"></i></span>'
            f'<b>{fmt(count)}件</b></li>'
        )
    chart.append("</ul>")
    guide.select_one("[data-cav-issues]").append(BeautifulSoup("".join(chart), "html.parser"))

    for table in guide.select("table"):
        headings = [th.get_text(" ", strip=True) for th in table.select("thead th")]
        for row in table.select("tbody tr"):
            for index, cell in enumerate(row.find_all(["td", "th"], recursive=False)):
                if cell.name == "td" and index < len(headings):
                    cell["data-label"] = headings[index]

    targets = {tag["id"] for tag in body.select("[id]")} | {"cap-method"}
    for tag in guide.select("[id]"):
        if tag["id"] in targets:
            raise ValueError(f"図解ガイドのIDが重複しています: {tag['id']}")
        targets.add(tag["id"])
    for link in guide.select('a[href^="#"]'):
        if link["href"][1:] not in targets:
            raise ValueError(f"図解ガイドのリンク先がありません: {link['href']}")
    for img in guide.select("img"):
        if not (root / "docs" / img["src"]).is_file():
            raise ValueError(f"図解ガイドの写真がありません: {img['src']}")

    nav = []
    for section in guide.select(".cav-content > [data-readpoint]"):
        title = section.get("data-format-title", section["data-readpoint"])
        kind = section.get("data-format", "article")
        if section.name == "section":
            heading = section.find(["h2", "h3", "h4"])
            if heading:
                heading.name = "h3"
        nav.append(f'<li data-kind="{esc(kind)}"><a href="#{esc(section["id"])}">{esc(title)}</a></li>')
    nav.extend(
        f'<li data-kind="article"><a href="#issue-{esc(issue["id"])}">'
        f'{esc(issue_name(data, issue))}・{fmt(issue["count"])}件</a></li>'
        for issue in issues
    )
    for issue in issues:
        iid = issue["id"]
        cfg = data["cfg"]["issues"][iid]
        for reason, bucket in reasons[iid].items():
            label = reason_label(data, cfg, reason, bucket)
            target = destination(iid.removeprefix(PREFIX) + "/" + reason)
            nav.append(
                f'<li data-kind="reason" hidden><a href="#{esc(target)}">'
                f'{esc(issue_name(data, issue))} ／ {esc(label)}</a></li>'
            )
    return (
        '<section class="cav" id="constitutional-visual-guide" aria-labelledby="cav-title">'
        '<header><p class="eyebrow">憲法改正を読み解く</p>'
        '<h2 id="cav-title">写真・図解・比較表で読む憲法改正</h2>'
        f'<p>SNSの集計は{jp_date(public["updated_on"])}更新。制度の確認日は、各資料の記録を参照してください。</p>'
        '<p><a href="#constitutional-amendment-reading">SNSの反応マップへ ↓</a></p></header>'
        '<div class="cav-layout"><details class="cav-nav" open><summary>目次・図表・検索</summary>'
        '<div class="cav-tabs" role="group" aria-label="目次の表示">'
        '<button type="button" data-cav-mode="all" aria-pressed="true">目次</button>'
        '<button type="button" data-cav-mode="visual" aria-pressed="false">図・表</button>'
        '<button type="button" data-cav-mode="search" aria-pressed="false">検索</button></div>'
        '<label class="cav-search" hidden>本文の項目・SNSの理由を探す<input type="search"></label>'
        '<p class="cav-empty" role="status" hidden>見つかりませんでした。</p>'
        f'<ul>{"".join(nav)}</ul></details>{guide}</div></section>'
    )
