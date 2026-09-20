#!/usr/bin/env python3
"""生成AIと著作権 — 「論点ごとのX投稿」セクションの生成。

koshitsu-tenpakaiの現行版（画像・編集部要約は無し、代表投稿の埋め込みと
立場ラベルのみ）と同じ形。ai-copyrightは論点画像を山なみパネルへ既に
インライン表示済み（2026-09-20、_inject_ai_copyright_landing_images）なので、
ここでは画像を重ねない。代表投稿はなるべく直近の投稿を選んだ
（社会全体の意見割合ではなく、編集部が選んだ一例）。

    python3 scripts/ai_copyright_issue_media.py --write-html
"""
from __future__ import annotations

import argparse
import html as html_mod
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAGE = ROOT / "docs" / "ai-copyright-reaction-map.html"
PUBLIC_THEME = ROOT / "data" / "public" / "themes" / "ai-copyright.json"

START = "<!-- AI_COPYRIGHT_ISSUE_MEDIA_START -->"
END = "<!-- AI_COPYRIGHT_ISSUE_MEDIA_END -->"

# (user, tweet_id, label)。2件とも2026-06-22〜2026-09-05の正典から、
# なるべく直近（tweet_id基準）かつ論点の考え方が分かれる2件を選んだ。
MEDIA: dict[str, list[tuple[str, str, str]]] = {
    "learning-data": [
        ("hello_jinsei_11", "2096054163344130472", "AI出力は盗用の集合体と批判"),
        ("Ailnlv2", "2096043249177927793", "AIだけを特別視する理由に疑問"),
    ],
    "user-ethics": [
        ("7u7t7u", "2096030978267664520", "運営サイトに方針の明確化を求める"),
        ("1KGXAHrWKH25965", "2096066224707019044", "AI活用にも発想力が要ると反論"),
    ],
    "legal-framework": [
        ("hito4622", "2096043110921130139", "意図的な模倣への法規制を提案"),
        ("shiroshiromagic", "2096040620083253473", "著作権法30条の4を根拠に反論"),
    ],
    "creator-rights": [
        ("abura_dev", "2096003143779926115", "AI使用で評価は上がらないと断定"),
        ("SakuraVfairy", "2095875011253071879", "技術は肯定しつつ自身の変化を語る"),
    ],
    "tech-promotion": [
        ("emutyworks", "2096046437583008140", "仕事では既に不可欠と指摘"),
        ("Tnohito", "2086213627430990277", "実用性のあるAIへ資源を回すべき"),
    ],
    "generated-work-rights": [
        ("otaku_yaruze", "2095883804791751159", "言語による創作と組み替えは別と主張"),
        ("lady_bebe_rose", "2094392287610696187", "プロンプト作成者に著作権があると主張"),
    ],
    "other": [
        ("calamele_rockey", "2096026110173864395", "両陣営の過激さに疲れたと吐露"),
        ("odanngo_chan", "2094079715388878972", "反対の立場でも実用面は試す"),
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
        key = iid.removeprefix("ai-copyright-")
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
        "各論点でどんな声が上がっているか、編集部が代表的な投稿を選びました。"
        "ここに挙げた投稿は考え方の一例で、全体の賛否の割合を表すものでは"
        "ありません。埋め込みが表示されないときは、投稿へのリンクからXで見られます。"
    )
    return (
        f'<section class="panel" id="issue-cards">{CSS}'
        '<div class="panel-title"><h2>論点ごとのX投稿</h2></div>'
        f"<p>{lead}</p>" + "".join(cards) + "</section>"
    )


def inject(page_text: str, section_html: str) -> str:
    """AI_COPYRIGHT_ISSUE_MEDIA_START/ENDの間だけを差し替える。

    マーカーが無ければ、生成AI著作権の独立セクション（AI_COPYRIGHT_AUDIT_END）
    の直後、無ければPLANET_SECTION_ENDの直後へ新規に挿入する。
    """
    if START in page_text:
        pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
        return pattern.sub(f"{START}\n{section_html}\n{END}", page_text)
    for anchor in ("<!-- AI_COPYRIGHT_AUDIT_END -->", "<!-- PLANET_SECTION_END -->"):
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
    missing = [it["id"].removeprefix("ai-copyright-") for it in public["issues"]
               if it["id"].removeprefix("ai-copyright-") not in MEDIA]
    if missing:
        raise SystemExit(f"MEDIAに無い論点があります: {missing}")

    section_html = build_section(public)
    if args.write_html:
        page_path = args.page or DEFAULT_PAGE
        original = page_path.read_text(encoding="utf-8")
        updated = inject(original, section_html)
        if updated != original:
            page_path.write_text(updated, encoding="utf-8")
            print(f"OK  {page_path} を更新しました（AI_COPYRIGHT_ISSUE_MEDIA セクション）")
        else:
            print(f"OK  {page_path} は差分なし")
    else:
        print(f"OK  論点{len(public['issues'])}件 / 代表投稿{sum(len(v) for v in MEDIA.values())}件")
        print("    --write-html を付けるとdocs/へ書き込みます")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
