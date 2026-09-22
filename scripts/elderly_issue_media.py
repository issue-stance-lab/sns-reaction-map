#!/usr/bin/env python3
"""高齢者免許返納 — 「論点ごとのX投稿」セクションの生成。

ai-copyright/koshitsu-tenpakaiの現行版（画像・編集部要約は無し、代表投稿の埋め込みと
立場ラベルのみ）と同じ形。elderly-license-revocationは論点画像を山なみパネルへ既に
インライン表示済み（refresh_planet_section.pyの_inject_elderly_landing_images）なので、
ここでは画像を重ねない。代表投稿は正典(social-samples/elderly-license_2d_classified.json)
から、classification.is_opinion かつ classification.article_usable かつ
classification.risk=='low' の候補に絞り、論点ごとに主張の異なる2件を選んだ
（社会全体の意見割合ではなく、編集部が選んだ一例。自社アカウント@sns_hannou_maの
投稿は候補から除外した）。

    python3 scripts/elderly_issue_media.py --write-html
"""
from __future__ import annotations

import argparse
import html as html_mod
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAGE = ROOT / "docs" / "elderly-license-revocation-reaction-map.html"
PUBLIC_THEME = ROOT / "data" / "public" / "themes" / "elderly-license-revocation.json"

START = "<!-- ELDERLY_ISSUE_MEDIA_START -->"
END = "<!-- ELDERLY_ISSUE_MEDIA_END -->"

# (user, tweet_id, label)。labelは正典のclassification.summaryを元に短く整えた。
# 2026-09-22選定、他セクション（象限別の代表的な声）は本対応で削除するため重複確認は不要。
MEDIA: dict[str, list[tuple[str, str, str]]] = {
    "safety": [
        ("snowfff_", "2100868503956034020", "高齢者の免許返納義務化を求める"),
        ("raska921", "2084643731245031786", "返納を求めるなら高齢議員も辞職すべき"),
    ],
    "assessment": [
        ("edo_ein", "2099317516350939144", "適性検査で不適格なら交付自体を拒否すべき"),
        ("YaX7bwxtGy8442", "2091694212609950057", "ETCや生体認証など安全対策を先に義務化すべき"),
    ],
    "voluntary-return": [
        ("Heitarou011", "2095091428057817596", "自主返納を実際に行った体験を報告"),
        ("VVHg6wh2MnQ761i", "2085686153286664398", "強制保険にすれば自主返納も増えるのでは"),
    ],
    "mobility-rights": [
        ("3c1mj1t7pONBDMu", "2098305491663466818", "一律の返納は地方の生活を壊すと反対"),
        ("LIU83414453", "2100393624018321755", "地方は車が必須で返納後の生活が心配"),
    ],
    "alternative-transport": [
        ("Alien_Yaga", "2097996565269143699", "過疎地こそ自動運転の整備を優先すべき"),
        ("yuhki_earlyrt", "2085365880914059334", "代替手段がないまま返納は求められない"),
    ],
    "other": [
        ("IMtzGZPfAKPKSMF", "2093553448533045737", "運転には資格と資質が要ると主張"),
        ("nucomass", "2074146431301251572", "高齢者に求めるなら政治家にも年齢制限を"),
    ],
}

CSS = """<style>
#issue-cards .ic{border-top:2px solid #0F1A3D;padding:22px 0 30px;scroll-margin-top:64px}
#issue-cards .ic:first-of-type{border-top:none;padding-top:0}
#issue-cards .ic+.ic{border-top-color:#DCE3EF}
#issue-cards .ic:target .ic-head h3{color:var(--accent)}
#issue-cards .ic-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:10px}
#issue-cards .ic-head h3{margin:0;font-size:21px;font-weight:900;line-height:1.4;letter-spacing:.01em}
#issue-cards .ic-head .cnt{margin-left:auto;font-weight:900;font-size:26px;line-height:1;font-variant-numeric:tabular-nums;color:#0F1A3D}
#issue-cards .ic-head .cnt small{font-size:13px;font-weight:700;color:var(--muted);margin-left:2px}
#issue-cards .ic-back{display:inline-block;margin-top:16px;font-size:13px;font-weight:700}
#issue-cards .hermes-samples{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;margin-top:6px}
#issue-cards .hermes-sample{min-width:0}
#issue-cards .hermes-sample-meta{font-weight:800;display:block;margin-bottom:8px;font-size:14.5px}
@media(max-width:640px){#issue-cards .hermes-samples{grid-template-columns:1fr}}
</style>"""


def esc(text: str) -> str:
    return html_mod.escape(text, quote=True)


def build_section(public: dict) -> str:
    cards = []
    for issue in public["issues"]:
        iid = issue["id"]
        key = iid.removeprefix("elderly-license-revocation-")
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
        "論点ごとに、実際にあった投稿を編集部が2件ずつ選んで紹介します。"
        "ここに並ぶ投稿はあくまで一例で、その論点における賛成・反対それぞれの多さを示すものではありません。"
        "表示が崩れる場合は、投稿内のリンクからX本体で内容を確認してください。"
    )
    return (
        f'<section class="panel" id="issue-cards">{CSS}'
        '<div class="panel-title"><h2>論点ごとのX投稿</h2></div>'
        f"<p>{lead}</p>" + "".join(cards) + "</section>"
    )


def inject(page_text: str, section_html: str) -> str:
    """ELDERLY_ISSUE_MEDIA_START/ENDの間だけを差し替える。

    マーカーが無ければ、PLANET_SECTION_ENDの直後（一次資料クイズの後・投票の前）へ
    新規に挿入する。
    """
    if START in page_text:
        start_index = page_text.index(START)
        end_index = page_text.index(END) + len(END)
        return page_text[:start_index] + f"{START}\n{section_html}\n{END}" + page_text[end_index:]
    anchor = "<!-- PLANET_SECTION_END -->"
    if anchor not in page_text:
        raise SystemExit("挿入位置のマーカー(PLANET_SECTION_END)が見つかりません")
    return page_text.replace(anchor, f"{anchor}\n{START}\n{section_html}\n{END}", 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-html", action="store_true", help="独立セクションをdocs/へ書き込む")
    parser.add_argument("--page", type=Path, help="--write-html の対象HTML（省略時はdocs/の既定）")
    parser.add_argument("--public-theme", type=Path, help="件数の出所（省略時はdata/public/themes/の既定）")
    args = parser.parse_args()

    import json

    public = json.loads((args.public_theme or PUBLIC_THEME).read_text(encoding="utf-8"))
    missing = [it["id"].removeprefix("elderly-license-revocation-") for it in public["issues"]
               if it["id"].removeprefix("elderly-license-revocation-") not in MEDIA]
    if missing:
        raise SystemExit(f"MEDIAに無い論点があります: {missing}")

    section_html = build_section(public)
    if args.write_html:
        page_path = args.page or DEFAULT_PAGE
        original = page_path.read_text(encoding="utf-8")
        updated = inject(original, section_html)
        if updated != original:
            page_path.write_text(updated, encoding="utf-8")
            print(f"OK  {page_path} を更新しました（ELDERLY_ISSUE_MEDIA セクション）")
        else:
            print(f"OK  {page_path} は差分なし")
    else:
        print(f"OK  論点{len(public['issues'])}件 / 代表投稿{sum(len(v) for v in MEDIA.values())}件")
        print("    --write-html を付けるとdocs/へ書き込みます")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
