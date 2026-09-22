#!/usr/bin/env python3
"""副首都 — 「論点ごとのX投稿」セクションの生成。

ai-copyright・koshitsu-tenpakaiの現行版と同じ形（画像・編集部要約は無し、
代表投稿の埋め込みと立場ラベルのみ）。挿入位置はFACT_CHECK_ENDの直後
（fukushutoには{THEME}_AUDIT_ENDに当たる一次資料照合セクションが
`id="fact-check"` という別名で存在するため、そちらをアンカーにする）。

    python3 scripts/fukushuto_issue_media.py --write-html
"""
from __future__ import annotations

import argparse
import html as html_mod
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAGE = ROOT / "docs" / "fukushuto-reaction-map.html"
PUBLIC_THEME = ROOT / "data" / "public" / "themes" / "fukushuto.json"

START = "<!-- FUKUSHUTO_ISSUE_MEDIA_START -->"
END = "<!-- FUKUSHUTO_ISSUE_MEDIA_END -->"

# (user, tweet_id, label)。2件とも社会全体の意見割合ではなく、
# 編集部が本文を読んで選んだ一例（考え方が分かれる2件）。
MEDIA: dict[str, list[tuple[str, str, str]]] = {
    "definition": [
        ("jokerk_", "2094367800144150922", "定義が固まらないまま採決したと批判"),
        ("papasan_at_home", "2094371171286593968", "副首都の役割は防災でなく行政代替と指摘"),
    ],
    "location": [
        ("penate3", "2099121459646046603", "南海トラフを理由に大阪でなく岡山を推す"),
        ("subuta123", "2091355693471436876", "大阪を副首都にすべきだと主張"),
    ],
    "osaka-restoration": [
        ("OZTb6JODs20cT4b", "2097329314853433813", "大阪を真の副首都とする具体案を提示"),
        ("caka3636", "2100192282922385701", "都構想と副首都は別物で利権目的と批判"),
    ],
    "disaster-preparedness": [
        ("UuuUuu1036354", "2097456646054392066", "地下空洞と南海トラフで大阪は不適地と主張"),
        ("ronpao01", "2090108122111398130", "防災と経済発展のため副首都は必要"),
    ],
    "finance": [
        ("yoshiwatch204", "2083354928739918289", "通信技術で代替可能で多額費用は不要と主張"),
        ("K1wkZk3gogjOuRk", "2081235627320947153", "医療・介護の財源不足と比べて副首都を批判"),
    ],
    "priority": [
        ("omakihan1016", "2088851608792879210", "老朽化した水道管の整備を優先すべきと主張"),
        ("ichigo_toiimasu", "2098325551870247081", "食料安全保障を優先すべきと主張"),
    ],
    "other": [
        ("tQTGSRa8mF33132", "2091288957669748740", "副首都法案の廃止を求める"),
        ("002t", "2081235897249665390", "一極集中是正のため副首都に賛成"),
    ],
}

CSS = """<style>
#issue-cards .ic{border-top:2px solid #0F1A3D;padding:22px 0 30px;scroll-margin-top:64px}
#issue-cards .ic+.ic{border-top-color:#DCE3EF}
#issue-cards .ic:target .ic-head h3{color:var(--accent)}
#issue-cards .ic-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:10px}
#issue-cards .ic-head h3{margin:0;font-size:21px;font-weight:900;line-height:1.4;letter-spacing:.01em}
#issue-cards .ic-head .cnt{margin-left:auto;font-weight:900;font-size:26px;line-height:1;font-variant-numeric:tabular-nums;color:#0F1A3D}
#issue-cards .ic-head .cnt small{font-size:13px;font-weight:700;color:var(--muted);margin-left:2px}
#issue-cards .ic-back{display:inline-block;margin-top:16px;font-size:13px;font-weight:700}
#issue-cards .hermes-samples{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;margin-top:20px}
#issue-cards .hermes-sample{min-width:0}
#issue-cards .hermes-sample-meta{font-weight:800}
@media(max-width:640px){#issue-cards .hermes-samples{grid-template-columns:1fr}}
</style>"""


def esc(text: str) -> str:
    return html_mod.escape(text, quote=True)


def build_section(public: dict) -> str:
    cards = []
    for issue in public["issues"]:
        iid = issue["id"]
        key = iid.removeprefix("fukushuto-")
        posts = MEDIA[key]
        samples = "".join(
            f'<div class="hermes-sample"><span class="hermes-sample-meta">{esc(label)}</span>'
            f'<blockquote class="twitter-tweet" data-conversation="none" data-dnt="true">'
            f'<a href="https://x.com/{user}/status/{tweet_id}">@{user} の投稿をXで見る</a></blockquote></div>'
            for user, tweet_id, label in posts
        )
        cards.append(
            f'<article class="ic" id="issue-{esc(iid)}">'
            f'<div class="ic-head"><h3>{esc(issue["label"])}</h3>'
            f'<span class="cnt">{issue["count"]}<small>件</small></span></div>'
            f'<div class="hermes-samples">{samples}</div>'
            '<a class="ic-back" href="#planet-block">↑ 地図へ戻る</a></article>'
        )
    lead = (
        "各論点につき2件、実際にあった投稿を編集部が選んでいます。"
        "全体としてどちらが優勢かを示す集計ではなく、論点の中身を具体的に"
        "つかむための例です。表示が崩れるときは、リンクからX上の投稿を直接ご確認ください。"
    )
    return (
        f'<section class="panel" id="issue-cards">{CSS}'
        '<div class="panel-title"><h2>論点ごとのX投稿</h2></div>'
        f"<p>{lead}</p>" + "".join(cards) + "</section>"
    )


def inject(page_text: str, section_html: str) -> str:
    """FUKUSHUTO_ISSUE_MEDIA_START/ENDの間だけを差し替える。

    マーカーが無ければ、副首都の一次資料照合セクション（FACT_CHECK_END）の
    直後、無ければPLANET_SECTION_ENDの直後へ新規に挿入する。
    """
    if START in page_text:
        pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
        return pattern.sub(f"{START}\n{section_html}\n{END}", page_text)
    for anchor in ("<!-- FACT_CHECK_END -->", "<!-- PLANET_SECTION_END -->"):
        if anchor in page_text:
            return page_text.replace(anchor, f"{anchor}\n{START}\n{section_html}\n{END}", 1)
    raise SystemExit("挿入位置のマーカーが見つかりません（まだ山なみ形式ではない）")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-html", action="store_true", help="独立セクションをdocs/へ書き込む")
    parser.add_argument("--page", type=Path, help="--write-html の対象HTML（省略時はdocs/の既定）")
    parser.add_argument("--public-theme", type=Path, help="件数の出所（省略時はdata/public/themes/の既定）")
    args = parser.parse_args()

    public = json.loads((args.public_theme or PUBLIC_THEME).read_text(encoding="utf-8"))
    missing = [it["id"].removeprefix("fukushuto-") for it in public["issues"]
               if it["id"].removeprefix("fukushuto-") not in MEDIA]
    if missing:
        raise SystemExit(f"MEDIAに無い論点があります: {missing}")

    section_html = build_section(public)
    if args.write_html:
        page_path = args.page or DEFAULT_PAGE
        original = page_path.read_text(encoding="utf-8")
        updated = inject(original, section_html)
        if updated != original:
            page_path.write_text(updated, encoding="utf-8")
            print(f"OK  {page_path} を更新しました（FUKUSHUTO_ISSUE_MEDIA セクション）")
        else:
            print(f"OK  {page_path} は差分なし")
    else:
        print(f"OK  論点{len(public['issues'])}件 / 代表投稿{sum(len(v) for v in MEDIA.values())}件")
        print("    --write-html を付けるとdocs/へ書き込みます")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
