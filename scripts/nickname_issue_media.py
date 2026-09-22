#!/usr/bin/env python3
"""学校でのあだ名禁止 — 「論点ごとのX投稿」セクションの生成。

他テーマ（consumption-tax-cut・koshitsu-tenpakai等）の#issue-cardsと同じ形。
要約文（投稿本文の言い換え）は付けず、ラベル＋埋め込みだけにする（同じ文の
反復が「質の低いコンテンツ」の兆候として審査上逆効果になるため）。埋め込みは
scripts/x_embed.py の embed_html() を使い、自前でblockquoteは書かない。

このテーマのページには一次資料クイズ（claim-audit）が無いため、挿入位置は
投票セクション（vote-section）の直前とした（bike-blue-ticketと同じ形）。

代表投稿は正典(social-samples/school-nickname-ban_hermes_arena_classified.json)
から、is_opinion かつ article_usable かつ risk=='low' の候補に絞り、論点ごとに
本文を読んで具体的に違う角度から語っている2件を選んだ（社会全体の意見割合では
なく、編集部が選んだ一例）。ラベルは正典のclassification.summaryをそのまま使う。
「その他」は該当する意見が0件のため対象外。

    python3 scripts/nickname_issue_media.py --write-html
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from x_embed import embed_html  # noqa: E402

DEFAULT_PAGE = ROOT / "docs" / "school-nickname-ban-reaction-map.html"
PUBLIC_THEME = ROOT / "data" / "public" / "themes" / "school-nickname-ban.json"

START = "<!-- NICKNAME_ISSUE_MEDIA_START -->"
END = "<!-- NICKNAME_ISSUE_MEDIA_END -->"
INSERT_BEFORE = '<section class="panel" id="vote-section"'

# (url, label)。labelは正典のclassification.summaryをそのまま使う。
# 表示順は投票セクションのvote_issue_orderと揃えた。2026-09-22選定。
MEDIA: dict[str, list[tuple[str, str]]] = {
    "school-nickname-ban-psychological-safety": [
        ("https://x.com/ibrahim_kh21712/status/2064315852036456507", "いじめ防止や公平性を学校のルール変更の背景として説明"),
        ("https://x.com/accelerator09/status/2097150687641817369", "あだ名がいじめの原因だったため禁止に賛成"),
    ],
    "school-nickname-ban-uniform-rule": [
        ("https://x.com/silentman124/status/2079418693881344176", "あだ名禁止は監視不可能で実効性なく、いじめ防止にならない"),
        ("https://x.com/RM_OFFRoadMania/status/2064148087292236034", "悪い呼称を付ける側への対応が必要で全体廃止には反対"),
    ],
    "school-nickname-ban-naming-culture": [
        ("https://x.com/kinakina35/status/2068167994224824357", "子どもはあだ名の善悪を区別でき親しみある呼称を否定すべきでない"),
        ("https://x.com/pumousuallife/status/2067967272703180860", "親しみを込めたあだ名と貶めるあだ名を区別しあだ名禁止を支持"),
    ],
    "school-nickname-ban-school-practice": [
        ("https://x.com/tategami_lab/status/2075873203034136829", "自宅では呼び捨ても学校ではさん付けを徹底している実態"),
        ("https://x.com/narru957/status/2093910365952438651", "あだ名禁止で教員が過剰に追及される現状を懸念"),
    ],
    "school-nickname-ban-gender-consideration": [
        ("https://x.com/brightestbug/status/2068046556918353969", "学校でのさん付け統一を面白がりつつあだ名の方が個性が出ると支持"),
        ("https://x.com/seiro10/status/2064292094152413689", "あだ名禁止には賛成、全員さん付けには反対"),
    ],
    "school-nickname-ban-individual-choice": [
        ("https://x.com/ikedaosamu/status/2082643827278708864", "あだ名とニックネームの区別し確認を提案"),
        ("https://x.com/DecentTourGuide/status/2097220251301921109", "本人が希望・命名したあだ名のみ認めるべき"),
    ],
}

# vote-section（投票セクション）と同じ並び順。「その他」は意見0件のため対象外。
ISSUE_ORDER = [
    "school-nickname-ban-psychological-safety",
    "school-nickname-ban-uniform-rule",
    "school-nickname-ban-naming-culture",
    "school-nickname-ban-school-practice",
    "school-nickname-ban-gender-consideration",
    "school-nickname-ban-individual-choice",
]

CSS = """<style>
#issue-cards .ic{border-top:2px solid #0F1A3D;padding:22px 0 30px;scroll-margin-top:64px}
#issue-cards .ic:first-of-type{border-top:none;padding-top:0}
#issue-cards .ic:target .ic-head h3{color:var(--accent)}
#issue-cards .ic-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:10px}
#issue-cards .ic-head h3{margin:0;font-size:21px;font-weight:900;line-height:1.4;letter-spacing:.01em}
#issue-cards .ic-head .cnt{margin-left:auto;font-weight:900;font-size:26px;line-height:1;
  font-variant-numeric:tabular-nums;color:#0F1A3D}
#issue-cards .ic-head .cnt small{font-size:13px;font-weight:700;color:var(--muted);margin-left:2px}
#issue-cards .ic-back{display:inline-block;margin-top:16px;font-size:13px;font-weight:700}
#issue-cards .hermes-samples{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;margin-top:6px}
#issue-cards .hermes-sample{min-width:0}
#issue-cards .hermes-sample-meta{font-weight:800;display:block;margin-bottom:8px;font-size:14.5px}
@media (max-width:640px){#issue-cards .hermes-samples{grid-template-columns:1fr}}
</style>"""


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def build_section(public: dict) -> str:
    by_id = {issue["id"]: issue for issue in public["issues"]}
    missing = set(MEDIA) - set(by_id)
    if missing:
        raise SystemExit(f"MEDIAの論点IDが公開JSONに無い: {missing}")

    cards = []
    for iid in ISSUE_ORDER:
        issue = by_id[iid]
        posts = MEDIA[iid]
        samples = "".join(
            f'<div class="hermes-sample"><span class="hermes-sample-meta">{esc(label)}</span>'
            f'{embed_html(url)}</div>'
            for url, label in posts
        )
        cards.append(
            f'<article class="ic" id="issue-{esc(iid)}">'
            f'<div class="ic-head"><h3>{esc(issue["label"])}</h3>'
            f'<span class="cnt">{issue["count"]}<small>件</small></span></div>'
            f'<div class="hermes-samples">{samples}</div>'
            '<a class="ic-back" href="#planet-block">↑ 地図へ戻る</a></article>'
        )
    lead = (
        "論点ごとに、実際の投稿を編集部が2件ずつ選びました。件数の多さや賛否の割合を"
        "表すものではなく、それぞれの論点でどんな声が上がっているかを具体的に知るための"
        "例です。埋め込みが表示されない場合は、リンクからXで投稿を確認してください。"
    )
    return (
        f'{START}\n'
        f'<section class="panel" id="issue-cards">{CSS}'
        '<div class="panel-title"><h2>論点ごとのX投稿</h2></div>'
        f"<p>{lead}</p>" + "".join(cards) + f'</section>\n{END}'
    )


def inject(page_text: str, section_html: str) -> str:
    """NICKNAME_ISSUE_MEDIA_START/ENDの間だけを差し替える。

    マーカーが無ければ、投票セクション(vote-section)の直前へ新規に挿入する。
    """
    if START in page_text:
        start_index = page_text.index(START)
        end_index = page_text.index(END) + len(END)
        return page_text[:start_index] + section_html + page_text[end_index:]
    if INSERT_BEFORE not in page_text:
        raise SystemExit("挿入位置のマーカー(vote-section)が見つかりません")
    return page_text.replace(INSERT_BEFORE, f"{section_html}\n{INSERT_BEFORE}", 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-html", action="store_true", help="独立セクションをdocs/へ書き込む")
    parser.add_argument("--page", type=Path, help="--write-html の対象HTML（省略時はdocs/の既定）")
    parser.add_argument("--public-theme", type=Path, help="件数の出所（省略時はdata/public/themes/の既定）")
    args = parser.parse_args()

    public = json.loads((args.public_theme or PUBLIC_THEME).read_text(encoding="utf-8"))
    if public.get("theme_id") != "school-nickname-ban":
        raise SystemExit(f"学校でのあだ名禁止の公開JSONではありません: {args.public_theme or PUBLIC_THEME}")

    section_html = build_section(public)
    if args.write_html:
        page_path = args.page or DEFAULT_PAGE
        original = page_path.read_text(encoding="utf-8")
        updated = inject(original, section_html)
        if updated != original:
            page_path.write_text(updated, encoding="utf-8")
            print(f"OK  {page_path} を更新しました（NICKNAME_ISSUE_MEDIA セクション）")
        else:
            print(f"OK  {page_path} は差分なし")
    else:
        print(f"OK  論点{len(ISSUE_ORDER)}件 / 代表投稿{sum(len(v) for v in MEDIA.values())}件")
        print("    --write-html を付けるとdocs/へ書き込みます")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
