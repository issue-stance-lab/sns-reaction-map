#!/usr/bin/env python3
"""副首都ページに「投稿の主張を、国会と選管の記録に当ててみた」セクションを差し込む。

このテーマは page_update_mode: adapter（scripts/build_fukushuto_arena.py が正典から
論点表示を作る）だが、事実確認セクションはそれとは別の関心事なので、このスクリプトを
分けて作った。build_fukushuto_arena.py が生成しない静的なセクションを1つだけ持ち、
HTML内の FACT_CHECK_START / END の間だけを差し替える。

件数は data/fukushuto_claim_posts.json の tweet_id から毎回数え直す。本文をキーワードで
拾っただけの件数は使わない（無関係な投稿まで拾って実際より多く出るため）。

    python3 scripts/build_fukushuto_process_sections.py
    python3 scripts/build_fukushuto_process_sections.py \
        --input <候補正典> --html-template <元HTML> --output-html <候補HTML> \
        --verification-dest <候補の出所ファイル置き場>
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
THEME = "fukushuto"
START = "<!-- FACT_CHECK_START -->"
END = "<!-- FACT_CHECK_END -->"

CHECKED_AT = "2026年8月24日"

# 一次資料に当たって確かめた結果。判定は fact / gap / miss の3種
# （このリポジトリの内部区分。表示ラベルは他テーマと言い方を変えている）。
# 件数は data/fukushuto_claim_posts.json の tweet_id から数える。
FACT_CHECKS = [
    {
        "key": "referendum_twice",
        "claim": "大阪都構想は、住民投票で二度否決された",
        "source": "大阪市が公表している「大阪市における特別区の設置についての投票」結果によれば、"
        "2015年5月17日は賛成694,844票・反対705,585票、2020年11月1日は賛成675,829票・反対692,996票。"
        "いずれも反対多数で、特別区の設置は実現していない。",
        "verdict": "fact",
        "verdict_label": "資料どおり",
        "note": "2回とも僅差の反対多数。とくに2020年は賛成が反対を17,167票下回るだけの差だった。",
        "url": "https://www.city.osaka.lg.jp/fukushutosuishin/page/0000538418.html",
        "url_label": "大阪市 大阪市における特別区の設置についての投票",
    },
    {
        "key": "vote_123_121",
        "claim": "副首都法は、賛成123・反対121のわずか2票差で成立した",
        "source": "参議院の記名投票結果によれば、2026年7月24日の本会議採決は投票総数244、賛成123、反対121。",
        "verdict": "fact",
        "verdict_label": "資料どおり",
        "note": "自由民主党・無所属の会99、日本維新の会19などを合わせて123。与党の議席だけでは"
        "過半数に届かず、無所属・少数会派の賛成があって成立した。",
        "url": "https://www.sangiin.go.jp/japanese/touhyoulist/221/221-0724-v006.htm",
        "url_label": "参議院 本会議投票結果（2026年7月24日）",
    },
    {
        "key": "resolution_ban",
        "claim": "附帯決議は、住民投票と統一地方選の同日実施を禁止する内容だ",
        "source": "参議院沖縄・北方問題及び地方に関する特別委員会の議案経過には、2026年7月24日に"
        "副首都法案への附帯決議を行ったと記載されている。同日、住民投票と地方選挙の同日実施を"
        "禁じる法律案（参第18号）は参議院本会議で賛成117・反対127で否決された。",
        "verdict": "miss",
        "verdict_label": "裏付けなし",
        "note": "附帯決議が採択された事実と、同日実施を禁じる法案が否決された事実は一次資料で確認できたが、"
        "決議そのものの文言は、採択した委員会の会議録が執筆時点（2026年8月）で未公開のため一次資料で"
        "確認できなかった。禁止なのか努力目標なのかは、会議録が公開されてから確かめ直す。",
        "url": "https://www.sangiin.go.jp/japanese/joho1/kousei/koho/221/keika/ke2700437.htm",
        "url_label": "参議院 沖縄・北方問題及び地方に関する特別委員会 議案経過（附帯決議の採択を記載）",
        "extra_links": [
            (
                "https://www.sangiin.go.jp/japanese/touhyoulist/221/221-0724-v007.htm",
                "参議院 本会議投票結果（同日実施禁止法案・2026年7月24日）",
            ),
        ],
    },
    {
        "key": "cost_old_estimate",
        "claim": "副首都の整備費用は4兆円〜7.5兆円かかるとされる",
        "source": "国土交通省（旧国土庁）が公表している「移転費用の試算」は1997年（平成9年）10月時点のもので、"
        "対象は首都機能の全面移転（転入人口最大60万人規模）。1/2ステップ（30万人規模）で"
        "公的負担3.0兆円＋民間投資4.5兆円＝7.5兆円という内訳になっている。",
        "verdict": "gap",
        "verdict_label": "資料とズレる",
        "note": "数字自体は実在するが、30年近く前の別の計画（首都機能の全面移転）の試算で、"
        "2026年の副首都法（大規模災害時のバックアップ機能整備）とは対象の規模も目的も別物。"
        "政府は参院審議で、今回の法律にもとづく整備費用について「今後検討する」と答えるにとどめ、"
        "現時点で試算を示していない。",
        "url": "https://www.mlit.go.jp/kokudokeikaku/iten/relocation/qa/qa_step4_02_01.html",
        "url_label": "国土交通省 国会等の移転ホームページ「移転費用の試算」",
    },
    {
        "key": "cost_ai_estimate",
        "claim": "副首都の整備費用は、AIの試算で総額2兆円規模になる",
        "source": "投稿には「AIによる試算」とだけあり、どのAIによる、どんな前提の試算かが示されていない。"
        "政府自身も費用を公表しておらず、たどれる一次資料が見つからなかった。",
        "verdict": "miss",
        "verdict_label": "裏付けなし",
        "note": "出典不明の試算がそのまま数字として流通していること自体が、この論点で公式な費用試算が"
        "存在しない状態を映している。",
        "url": None,
        "url_label": None,
    },
]


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def load(input_path: Path | None = None):
    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
    theme = themes[THEME]
    samples = json.loads((input_path or ROOT / theme["sample_file"]).read_text(encoding="utf-8"))
    claim_posts = json.loads((ROOT / "data" / f"{THEME}_claim_posts.json").read_text(encoding="utf-8"))
    return samples, claim_posts


def build_section(samples: list[dict], claim_posts: dict) -> str:
    known = {s["tweet_id"]: s for s in samples}
    cards = []
    for check in FACT_CHECKS:
        ids = claim_posts["claims"][check["key"]]
        unknown = [i for i in ids if i not in known]
        if unknown:
            raise SystemExit(f"{check['key']}: 正典に無い tweet_id があります: {unknown}")
        rep_url = esc(known[ids[0]]["url"])
        links = []
        if check["url"]:
            links.append((check["url"], check["url_label"]))
        links.extend(check.get("extra_links") or [])
        link_html = "".join(
            f' <a href="{url}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'
            for url, label in links
        )
        src_line = f'<p class="fc-source"><strong>一次資料はどう書いているか。</strong>{esc(check["source"])}{link_html}</p>'
        cards.append(f"""      <article class="fc-card" data-verdict="{check['verdict']}">
        <div class="fc-head">
          <p class="fc-claim">{esc(check['claim'])}</p>
          <span class="fc-count">{len(ids)}件の投稿</span>
        </div>
        <div class="fc-body">
          {src_line}
          <p class="fc-note"><span class="fc-verdict">{esc(check['verdict_label'])}</span>{esc(check['note'])}</p>
          <p class="fc-example"><a href="{rep_url}" target="_blank" rel="noopener noreferrer">投稿の例を見る（𝕏）</a></p>
        </div>
      </article>""")
    body = "\n".join(cards)
    return f"""{START}
<style id="fact-check-css">
#fact-check{{padding:26px min(6vw,72px) 30px;background:var(--bg)}}
#fact-check .fc-inner{{max-width:1000px;margin:0 auto}}
#fact-check h2{{font-size:clamp(20px,3.5vw,27px);line-height:1.5;margin:0 0 10px;color:var(--ink)}}
#fact-check .fc-lead{{font-size:14px;line-height:1.95;color:var(--muted);margin:0 0 18px}}
#fact-check .fc-grid{{display:grid;gap:11px}}
#fact-check .fc-card{{border:1px solid var(--line);border-left:4px solid var(--line);border-radius:0 12px 12px 0;background:var(--panel);padding:15px 17px}}
#fact-check .fc-card[data-verdict="fact"]{{border-left-color:#15803d}}
#fact-check .fc-card[data-verdict="gap"]{{border-left-color:#b45309}}
#fact-check .fc-card[data-verdict="miss"]{{border-left-color:#64748b}}
#fact-check .fc-head{{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:0 0 9px}}
#fact-check .fc-claim{{margin:0;font-size:15px;font-weight:900;line-height:1.6;color:var(--ink)}}
#fact-check .fc-claim::before{{content:"投稿の主張：「";color:var(--muted);font-weight:700;font-size:12px}}
#fact-check .fc-claim::after{{content:"」";color:var(--muted);font-weight:700;font-size:12px}}
#fact-check .fc-count{{font-size:11.5px;font-weight:800;color:var(--muted);white-space:nowrap}}
#fact-check .fc-body p{{margin:0 0 7px;font-size:13.5px;line-height:1.9;color:var(--ink)}}
#fact-check .fc-body p:last-child{{margin-bottom:0}}
#fact-check .fc-source strong{{font-weight:900}}
#fact-check .fc-source a{{color:var(--accent)}}
#fact-check .fc-note{{color:var(--muted)!important}}
#fact-check .fc-verdict{{display:inline-block;margin-right:8px;padding:2px 9px;border-radius:999px;font-size:11.5px;font-weight:900;color:#fff}}
#fact-check .fc-card[data-verdict="fact"] .fc-verdict{{background:#15803d}}
#fact-check .fc-card[data-verdict="gap"] .fc-verdict{{background:#b45309}}
#fact-check .fc-card[data-verdict="miss"] .fc-verdict{{background:#64748b}}
#fact-check .fc-example{{font-size:12px}}
#fact-check .fc-example a{{color:var(--muted)}}
@media (max-width:720px){{#fact-check{{padding-left:14px;padding-right:14px}}}}
</style>
<section id="fact-check" aria-labelledby="fact-check-title">
  <div class="fc-inner">
    <div class="panel-title"><h2 id="fact-check-title">投稿の主張を、国会と選管の記録に当ててみた</h2><span>編集部による事実確認</span></div>
    <p class="fc-lead">副首都をめぐる投稿には、法案の採決、附帯決議、住民投票、整備費用など、数字や日付を伴う主張が多く混ざっている。これらは意見ではなく事実の主張なので、公表されている一次資料と突き合わせられる。件数の多い主張・数字が独り歩きしていそうな主張を5つ選び、参議院・大阪市・国土交通省の公表資料に1つずつ当たった。確認できなかったものも、確認できなかったまま残している。確認日は{CHECKED_AT}。</p>
    <div class="fc-grid">
{body}
    </div>
    <p class="fc-note" style="margin-top:14px;font-size:12px;line-height:1.9;color:var(--muted)">件数の数え方：本文をキーワードで拾っただけでは、無関係な話題（他県の視察費用など）まで混ざる。そのため候補を1件ずつ読み、実際にその主張をしている投稿だけを残して数えている。賛成・反対どちらの投稿も含む。</p>
  </div>
</section>
{END}"""


def write_provenance_records(samples: list[dict], claim_posts: dict, destination: Path | None = None) -> None:
    known = {s["tweet_id"] for s in samples}
    rows = []
    for key, ids in claim_posts["claims"].items():
        for tid in ids:
            if tid not in known:
                raise SystemExit(f"{key}: 正典に無い tweet_id があります: {tid}")
            rows.append({"tweet_id": tid, "claim": key})
    out = destination or ROOT / "data" / "verification"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{THEME}-claims.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="候補の累積正典（省略時は THEMES.yaml の sample_file）")
    parser.add_argument("--html-template", type=Path, help="差し替え元のHTML（省略時は公開ページ）")
    parser.add_argument("--output-html", type=Path, help="書き出し先のHTML（省略時は公開ページ）")
    parser.add_argument("--verification-dest", type=Path, help="出所ファイルの書き出し先（省略時は data/verification）")
    args = parser.parse_args()
    candidate_args = (args.input, args.html_template, args.output_html, args.verification_dest)
    if any(candidate_args) and not all(candidate_args):
        parser.error("候補生成では--input/--html-template/--output-html/--verification-destをすべて指定してください")

    samples, claim_posts = load(args.input)
    section = build_section(samples, claim_posts)

    public_path = ROOT / "docs" / f"{THEME}-reaction-map.html"
    template_path = args.html_template or public_path
    page_path = args.output_html or public_path
    page = template_path.read_text(encoding="utf-8")
    if page.count(START) != 1 or page.count(END) != 1:
        raise SystemExit(f"{START} / {END} が1つずつ必要です")
    head, rest = page.split(START, 1)
    _old, tail = rest.split(END, 1)
    page = f"{head}{section}{tail}"

    checks = [
        ("投稿の主張を、国会と選管の記録に当ててみた", "セクション見出し"),
        ('data-verdict="miss"', "確認できなかった主張のカード"),
        (CHECKED_AT, "事実確認の確認日"),
        ("fact-check-css", "セクションのCSS"),
    ]
    for needle, label in checks:
        if needle not in page:
            raise SystemExit(f"生成結果に {label} が見つかりません: {needle}")

    write_provenance_records(samples, claim_posts, args.verification_dest)
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_text(page, encoding="utf-8")
    claim_total = sum(len(v) for v in claim_posts["claims"].values())
    print(f"OK  {page_path.name} に事実確認セクションを反映（該当投稿{claim_total}件・5主張）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
