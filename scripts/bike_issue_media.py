#!/usr/bin/env python3
"""自転車の青切符 — 「論点ごとのX投稿」セクションの生成。

ai-copyright/koshitsu-tenpakaiと同じ形（代表投稿の埋め込みと立場ラベルのみ、
編集部要約の複製はしない）。埋め込み(widgets.js)がblockquoteをiframeへ
置き換えた後、中身の描画だけ失敗して空白になる既知の不具合があるため
（koshitsu-tenpakaiで確認、2026-09-20 task/x-embed-fallback）、blockquoteの
外側に常設の出典リンク(x-embed-fallback)を最初から添えている。

代表投稿は正典(social-samples/bike-blue-ticket_2d_classified.json)から、
is_opinion かつ classification.article_usable かつ classification.risk=='low'
の候補に絞り、論点ごとに主張の異なる2件を選んだ（社会全体の意見割合ではなく、
編集部が選んだ一例）。ラベルは正典のclassification.summaryをそのまま使う。

    python3 scripts/bike_issue_media.py --write-html
"""
from __future__ import annotations

import argparse
import html as html_mod
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAGE = ROOT / "docs" / "bike-blue-ticket-reaction-map.html"
PUBLIC_THEME = ROOT / "data" / "public" / "themes" / "bike-blue-ticket.json"

START = "<!-- BIKE_ISSUE_MEDIA_START -->"
END = "<!-- BIKE_ISSUE_MEDIA_END -->"
INSERT_BEFORE = '<section class="panel" id="vote-section"'

# (user, tweet_id, label)。labelは正典のclassification.summaryをそのまま使う。
MEDIA: dict[str, list[tuple[str, str, str]]] = {
    "enforcement-support": [
        ("tea_cardamom", "2085293435490300011", "自転車違反マナーへの憤りと取締強化を強く要求"),
        ("bjayway", "2070305605852836233", "一時不停止が多発しているため警察による厳しい取り締まりを要求"),
    ],
    "infrastructure-first": [
        ("suzu_arakawaCR", "2089861510134890702", "道路整備なしで青切符を決行したことに怒りを表明"),
        ("_hand_and_hand_", "2061484624690475293", "青切符より先に歩行者・自転車・車を分離するインフラ整備を主張"),
    ],
    "road-safety": [
        ("sjodziejci", "2080474053211746304", "車道走行の恐怖から、歩道走行を問題無しと明言すべきと主張"),
        ("shun21829767", "2089509943619813770", "道路が狭く車が怖いという自転車利用者の不安を訴える"),
    ],
    "license-requirement": [
        ("gekipachi_ch", "2083330247035064750", "自転車危険運転多し、青切符不十分で簡易免許制を要望"),
        ("ZPlaiFah", "2070308461683130627", "青切符だけでは不十分で、購入前に道路交通法講習を義務化すべき"),
    ],
    "rule-ambiguity": [
        ("_PURPLE_LEON_", "2095302486580244511", "生活道路の速度制限も自転車青切符も、基準が曖昧でいい加減すぎると批判。"),
        ("aminkf_", "2074865044425498902", "警察官の主観的違反判断への懸念とインフラ整備優先を訴える"),
    ],
    "other": [
        ("haruhi_kaigo", "2082484234237927762", "青切符を装った現金詐欺に注意喚起"),
        ("ao_GSS", "2081029929047904596", "自転車青切符は4月施行で免許点数に影響せずと誤情報を訂正"),
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
#issue-cards .x-embed-fallback{margin:6px 0 0;font-size:12px}
#issue-cards .x-embed-fallback a{color:var(--muted)}
#issue-cards blockquote.twitter-tweet a{font-size:12px;color:var(--muted)}
@media(max-width:640px){#issue-cards .hermes-samples{grid-template-columns:1fr}}
</style>"""


def esc(text: str) -> str:
    return html_mod.escape(text, quote=True)


def build_section(public: dict) -> str:
    cards = []
    for issue in public["issues"]:
        iid = issue["id"]
        key = iid.removeprefix("bike-blue-ticket-")
        posts = MEDIA[key]
        samples = "".join(
            f'<div class="hermes-sample"><span class="hermes-sample-meta">{esc(label)}</span>'
            f'<blockquote class="twitter-tweet" data-conversation="none" data-dnt="true">'
            f'<a href="https://x.com/{user}/status/{tweet_id}">@{user} の投稿をXで見る</a></blockquote>'
            f'<div class="x-embed-fallback"><a href="https://x.com/{user}/status/{tweet_id}">@{user} の投稿をXで見る</a></div></div>'
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
        "青切符をめぐって実際にどんな投稿があったか、論点ごとに編集部が2件ずつ選び"
        "ました。全体の意見の割合を示すものではなく、あくまで論点の中身を具体的に"
        "知るための例です。埋め込みが出ないときは、リンク先のXで本文を確認できます。"
    )
    return (
        f'<section class="panel" id="issue-cards">{CSS}'
        '<div class="panel-title"><h2>論点ごとのX投稿</h2></div>'
        f"<p>{lead}</p>" + "".join(cards) + "</section>"
    )


def inject(page_text: str, section_html: str) -> str:
    """BIKE_ISSUE_MEDIA_START/ENDの間だけを差し替える。

    マーカーが無ければ、投票セクション(vote-section)の直前へ新規に挿入する。
    """
    if START in page_text:
        start_index = page_text.index(START)
        end_index = page_text.index(END) + len(END)
        return page_text[:start_index] + f"{START}\n{section_html}\n{END}" + page_text[end_index:]
    if INSERT_BEFORE not in page_text:
        raise SystemExit("挿入位置のマーカー(vote-section)が見つかりません")
    return page_text.replace(INSERT_BEFORE, f"{START}\n{section_html}\n{END}\n{INSERT_BEFORE}", 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-html", action="store_true", help="独立セクションをdocs/へ書き込む")
    parser.add_argument("--page", type=Path, help="--write-html の対象HTML（省略時はdocs/の既定）")
    parser.add_argument("--public-theme", type=Path, help="件数の出所（省略時はdata/public/themes/の既定）")
    args = parser.parse_args()

    public = json.loads((args.public_theme or PUBLIC_THEME).read_text(encoding="utf-8"))
    missing = [it["id"].removeprefix("bike-blue-ticket-") for it in public["issues"]
               if it["id"].removeprefix("bike-blue-ticket-") not in MEDIA]
    if missing:
        raise SystemExit(f"MEDIAに無い論点があります: {missing}")

    section_html = build_section(public)
    if args.write_html:
        page_path = args.page or DEFAULT_PAGE
        original = page_path.read_text(encoding="utf-8")
        updated = inject(original, section_html)
        if updated != original:
            page_path.write_text(updated, encoding="utf-8")
            print(f"OK  {page_path} を更新しました（BIKE_ISSUE_MEDIA セクション）")
        else:
            print(f"OK  {page_path} は差分なし")
    else:
        print(f"OK  論点{len(public['issues'])}件 / 代表投稿{sum(len(v) for v in MEDIA.values())}件")
        print("    --write-html を付けるとdocs/へ書き込みます")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
