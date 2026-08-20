#!/usr/bin/env python3
"""憲法改正ページの「原典にある数字・原典にない数字」セクションを生成する。

このテーマは page_update_mode: adapter。次回の収集で adapter が HTML を再生成するため、
マーカーコメントの間だけを差し替える方式にしている。adapter 呼び出し時に
このスクリプトが走り、CLAIM_AUDIT_START / END の間だけが毎回上書きされる。

    python3 scripts/build_constitutional_process_sections.py
    python3 scripts/build_constitutional_process_sections.py \\
        --input <候補正典> --html-template <元HTML> --output-html <候補HTML> \\
        --verification-dest <候補の出所ファイル置き場>

`--input` 以下は scripts/refresh_adapters/constitutional.py が候補ページを
作るときにのみ渡す引数。省略すると公開ページを直接更新する。
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
THEME = "constitutional-amendment"
START = "<!-- CLAIM_AUDIT_START -->"
END = "<!-- CLAIM_AUDIT_END -->"

CHECKED_AT = "2026年8月20日"

# 一次資料に当たって確かめた結果。判定は 原典にある / 原典とずれる / 原典にたどり着けず の3種。
# 件数は data/constitutional-amendment_claim_posts.json の tweet_id から数える。
# 機械抽出をそのまま件数にすると無関係な投稿が混入し3〜4割ぶん多く出るため、
# 必ず人が1件ずつ読んで確定した tweet_id を使う。
FACT_CHECKS = [
    {
        "key": "minimum_vote_rate",
        "claim": "国民投票は有効投票の過半数で成立し、最低投票率の規定はない",
        "source": (
            "国民投票法（日本国憲法の改正手続に関する法律）第98条第1項は"
            "「憲法改正案に対する賛成の投票の数が投票総数の二分の一を超えた場合は、"
            "当該憲法改正について日本国憲法第九十六条第1項の国民の承認があったものとする」"
            "と定める。法文中に最低投票率の規定はなく、附則第11条に"
            "「投票率が低い場合における措置について検討する」という努力義務が置かれているのみ。"
            "施行から18年が経つが、最低投票率を義務づける立法措置は講じられていない。"
        ),
        "verdict": "原典にある",
        "note": (
            "過半数で成立・最低投票率なしは、いずれも条文の直接の読みとして正確。"
            "附則の検討条項は法的効力を持たない。"
        ),
        "url": "https://laws.e-gov.go.jp/law/419AC1000000051",
        "url_label": "e-Gov 国民投票法（日本国憲法の改正手続に関する法律）",
    },
    {
        "key": "cm_broadcast_14days",
        "claim": "国民投票の放送CM規制は投票日前14日間だけで、それ以前は無制限だ",
        "source": (
            "国民投票法第105条第1項は「何人も、国民投票の期日前十四日に当たる日から"
            "国民投票の期日までの間、憲法改正に関する広告放送（テレビジョン放送及び"
            "ラジオ放送に限る）をしてはならない」と定める。"
            "同条はその14日間に限定して放送CMを禁止しており、それより前の期間や"
            "インターネット広告については禁止規定が本則に置かれていない。"
        ),
        "verdict": "原典にある",
        "note": (
            "14日間という数字は第105条の条文どおり。"
            "14日より前は放送CM量の上限も設けられておらず、"
            "「それ以前は無制限」という読みも条文上は否定できない。"
        ),
        "url": "https://laws.e-gov.go.jp/law/419AC1000000051",
        "url_label": "e-Gov 国民投票法（日本国憲法の改正手続に関する法律）",
    },
    {
        "key": "period_60days",
        "claim": "国会が発議してから国民投票まで最短60日、最長180日だ",
        "source": (
            "国民投票法第2条は「国民投票は、少なくとも六十日、"
            "多くとも百八十日の範囲で国会が議決した期日にこれを行う」と定める。"
        ),
        "verdict": "原典にある",
        "note": (
            "60日以上180日以内という数字は第2条の条文どおり。"
            "期日の決定は国会の議決によることも明記されている。"
        ),
        "url": "https://laws.e-gov.go.jp/law/419AC1000000051",
        "url_label": "e-Gov 国民投票法（日本国憲法の改正手続に関する法律）",
    },
    {
        "key": "two_thirds",
        "claim": "衆参両院それぞれで総議員の3分の2以上の賛成がないと発議できない",
        "source": (
            "日本国憲法第96条第1項は「この憲法の改正は、各議院の総議員の三分の二以上の"
            "賛成で、国会が、これを発議し、国民に提案してその承認を経なければならない」と定める。"
            "「各議院の」とあるため、衆議院・参議院の両院それぞれで3分の2以上が必要。"
        ),
        "verdict": "原典にある",
        "note": (
            "3分の2・各議院という条件は第96条第1項の条文どおり。"
            "「総議員」の解釈（欠員を含むか）に学説上の議論はあるが、"
            "3分の2以上という数字の読みに食い違いはない。"
        ),
        "url": "https://laws.e-gov.go.jp/law/321CONSTITUTION",
        "url_label": "e-Gov法令検索 日本国憲法 第96条",
    },
    {
        "key": "emergency_law_making",
        "claim": "自民党の改憲案では緊急事態条項が通ると内閣が国会を経ずに法律を作れる",
        "source": (
            "自民党の条文イメージ（2018年3月）第73条の2第1項は"
            "「大規模な自然災害その他の法律の定める緊急事態において、"
            "特に必要があると認めるときは、閣議にかけて、法律に代わる政令を制定することができる」"
            "と定める。ただし、第64条の2では宣言には国会の承認が、政令には国会の事後承認が"
            "それぞれ必要とされており、承認を得られなければ政令は効力を失う。"
        ),
        "verdict": "原典とずれる",
        "note": (
            "政令は閣議決定だけで制定できる段階が存在するため「国会を経ずに」という表現は"
            "一面では当たっているが、国会の事後承認がなければ効力が続かない仕組みは落ちている。"
            "「国会を完全に迂回して永続的に効力を持つ法律を作れる」という読みは条文と合わない。"
        ),
        "url": "https://storage.jimin.jp/pdf/constitution/news/20180326_01.pdf",
        "url_label": "自民党 条文イメージ・たたき台素案（2018年3月）PDF",
    },
    {
        "key": "article9_no_jieitai",
        "claim": "現行の9条には「自衛隊」という文字はなく、戦力不保持と交戦権の否認が書かれている",
        "source": (
            "日本国憲法第9条第1項は「日本国民は、正義と秩序を基調とする国際平和を誠実に希求し、"
            "国権の発動たる戦争と、武力による威嚇又は武力の行使は、国際紛争を解決する手段としては、"
            "永久にこれを放棄する」、第2項は「前項の目的を達するため、陸海空軍その他の戦力は、"
            "これを保持しない。国の交戦権は、これを認めない」と定める。"
            "「自衛隊」の語は第9条のどの項にも存在しない。"
        ),
        "verdict": "原典にある",
        "note": (
            "「自衛隊の文字がない」「戦力不保持・交戦権否認が書かれている」"
            "はいずれも第9条の条文の直接引用に基づく。"
            "自衛隊の存在根拠を9条の枠外に求める政府解釈については第9条に条文はない。"
        ),
        "url": "https://laws.e-gov.go.jp/law/321CONSTITUTION",
        "url_label": "e-Gov法令検索 日本国憲法 第9条",
    },
    {
        "key": "jieitai_inscription_only",
        "claim": "自民党の改憲案は9条に「自衛隊」を書き加えるだけで、実質は変わらない",
        "source": (
            "自民党の条文イメージ（2018年3月）第9条の2第1項は"
            "「前条の規定は、我が国の平和と独立を守り、国及び国民の安全を保つために必要な"
            "自衛の措置をとることを妨げず、そのための実力組織として、法律の定めるところにより、"
            "内閣の首長たる内閣総理大臣を最高の指揮監督者とする自衛隊を保持する」と定める。"
        ),
        "verdict": "原典とずれる",
        "note": (
            "「自衛隊」の文字を加えることに加え、「必要な自衛の措置をとることを妨げず」という"
            "留保条項と「内閣総理大臣を最高の指揮監督者とする」という指揮命令の明文化が盛り込まれている。"
            "現行9条には存在しないこれらの文言が追加されるため、"
            "「書き加えるだけ」という表現は変化の範囲を過小評価している。"
        ),
        "url": "https://storage.jimin.jp/pdf/constitution/news/20180326_01.pdf",
        "url_label": "自民党 条文イメージ・たたき台素案（2018年3月）PDF",
    },
    {
        "key": "net_ad_regulation",
        "claim": "2026年の国民投票法改正でインターネット広告規制が明文化された",
        "source": (
            "現行の国民投票法（令和4年改正時点）附則第12条は"
            "「インターネット等を用いた意見表明に係る規制の在り方については、（中略）"
            "検討を加え、必要な法制上の措置を講ずる」という努力義務の検討条項にとどまる。"
            "2026年6月に衆院憲法審査会を通過したとされる改正法案の条文テキストは、"
            "公開されているe-Govのデータベースに未収録であり、条文の確認ができなかった。"
        ),
        "verdict": "原典にたどり着けず",
        "note": (
            "現行法（令和4年版）の時点では、ネット広告規制は附則の「検討事項」であり禁止規定ではない。"
            "投稿が言及している2026年改正の条文は公式データベースに掲載がなく、"
            "「明文化された」かどうかを確認する原典にたどり着けなかった。"
        ),
        "url": "https://laws.e-gov.go.jp/law/419AC1000000051",
        "url_label": "e-Gov 国民投票法（令和4年改正時点、2026年改正は未収録）",
    },
    {
        "key": "article18_conscription",
        "claim": "9条に自衛隊を明記しても18条（苦役の禁止）を変えない限り、徴兵制は憲法上できない",
        "source": (
            "日本国憲法第18条は「何人も、いかなる奴隷的拘束も受けない。"
            "又、犯罪に因る処罰の場合を除いては、その意に反する苦役に服させられない」と定める。"
            "自民党の条文イメージ（2018年3月）が提案する改正対象は第9条の2・第73条の2・第64条の2・"
            "第47条・第92条・第26条の6項目であり、第18条の改正は含まれていない。"
            "徴兵制の根拠となる「苦役」の禁止が維持される以上、憲法上の制約は残る。"
        ),
        "verdict": "原典にある",
        "note": (
            "「9条明記だけで徴兵制になる」という議論は、18条の制約を考慮していない。"
            "徴兵制を憲法上可能にするには18条の改正が別途必要であり、"
            "現在議論されているいずれの改正案にも18条の改正は盛り込まれていない。"
        ),
        "url": "https://laws.e-gov.go.jp/law/321CONSTITUTION",
        "url_label": "e-Gov法令検索 日本国憲法 第18条",
    },
    {
        "key": "jieitai_iken_gaku",
        "claim": "憲法学説では自衛隊の存在を違憲とする解釈と合憲とする解釈が並立している",
        "source": (
            "日本国憲法第9条第2項は「前項の目的を達するため、陸海空軍その他の戦力は、"
            "これを保持しない。国の交戦権は、これを認めない」と定める。"
            "「戦力」の定義をめぐり、自衛隊は戦力に当たらないとする政府解釈（内閣法制局）と、"
            "自衛隊は同項が禁じる戦力に当たるとする「不能説」が学説上並立している。"
            "政府は「自衛のための必要最小限度の実力は戦力に当たらない」と繰り返し答弁してきた。"
        ),
        "verdict": "原典にある",
        "note": (
            "「合憲・違憲の両論がある」という投稿の指摘は条文の読み方として成り立つ。"
            "第9条第2項の「戦力」をどう解するかによって結論が分かれ、"
            "政府見解の合憲論が唯一の読みではない点は条文から確認できる。"
        ),
        "url": "https://laws.e-gov.go.jp/law/321CONSTITUTION",
        "url_label": "e-Gov法令検索 日本国憲法 第9条",
    },
]


def esc(s: str) -> str:
    return html.escape(s)


def load(input_path: Path | None) -> tuple[list[dict], dict, dict]:
    config_path = ROOT / "configs" / f"{THEME}-reaction-map.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))

    themes_path = ROOT / "THEMES.yaml"
    themes = yaml.safe_load(themes_path.read_text(encoding="utf-8"))
    theme_cfg = themes["themes"][THEME]
    sample_file = input_path or (ROOT / theme_cfg["sample_file"])
    samples = json.loads(sample_file.read_text(encoding="utf-8"))

    claim_posts_path = ROOT / "data" / f"{THEME}_claim_posts.json"
    claim_posts = json.loads(claim_posts_path.read_text(encoding="utf-8"))
    return samples, config, claim_posts


def build_section(samples: list[dict], claim_posts: dict) -> str:
    known = {s["tweet_id"] for s in samples}
    cards = []
    total_posts = 0
    for check in FACT_CHECKS:
        ids = claim_posts["claims"][check["key"]]
        unknown = [i for i in ids if i not in known]
        if unknown:
            raise SystemExit(f"{check['key']}: 正典に無い tweet_id があります: {unknown}")
        n = len(ids)
        total_posts += n
        verdict = check["verdict"]
        if verdict == "原典にある":
            verdict_color = "#15803d"
        elif verdict == "原典とずれる":
            verdict_color = "#b45309"
        else:
            verdict_color = "#64748b"
        cards.append(f"""      <article class="ca-card" data-verdict="{esc(verdict)}">
        <div class="ca-head">
          <p class="ca-claim">{esc(check['claim'])}</p>
          <span class="ca-count">{n}件の投稿</span>
        </div>
        <div class="ca-body">
          <p class="ca-source"><strong>一次資料の記述。</strong>{esc(check['source'])}</p>
          <p class="ca-note"><span class="ca-verdict" style="background:{verdict_color}">{esc(verdict)}</span>{esc(check['note'])}</p>
          <p class="ca-src"><a href="{esc(check['url'])}" target="_blank" rel="noopener noreferrer">{esc(check['url_label'])}</a></p>
        </div>
      </article>""")
    body = "\n".join(cards)
    return f"""{START}
{CSS}
<section id="claim-audit" aria-labelledby="claim-audit-title">
  <div class="ca-inner">
    <h2 id="claim-audit-title">原典にある数字・原典にない数字</h2>
    <p class="ca-lead">憲法改正に関する投稿の{len(FACT_CHECKS)}つの主張を、条文・政党の公表資料などの一次資料に1つずつ当たって確かめました。「原典にたどり着けず」はそのまま残しています。確認日は{CHECKED_AT}です。報道・解説サイトは参照していません。</p>
    <div class="ca-grid">
{body}
    </div>
    <p class="ca-note-bottom">件数の数え方：本文をキーワードで検索すると、趣旨が異なる投稿や報道の引用まで拾って実際より3〜4割多く出ます。候補を1件ずつ読み、実際にその主張をしている投稿だけを残して数えています。賛成・反対どちらの投稿も含みます。</p>
  </div>
</section>
{END}"""


CSS = """<style id="claim-audit-css">
#claim-audit{padding:26px min(6vw,72px) 30px;background:var(--bg)}
#claim-audit .ca-inner{max-width:1000px;margin:0 auto}
#claim-audit h2{font-size:clamp(20px,3.5vw,27px);line-height:1.5;margin:0 0 10px;color:var(--ink)}
.ca-lead{font-size:14px;line-height:1.95;color:var(--muted);margin:0 0 16px}
.ca-grid{display:grid;gap:11px}
.ca-card{border:1px solid var(--line);border-left:4px solid var(--line);border-radius:0 12px 12px 0;background:var(--panel);padding:15px 17px}
.ca-card[data-verdict="原典にある"]{border-left-color:#15803d}
.ca-card[data-verdict="原典とずれる"]{border-left-color:#b45309}
.ca-card[data-verdict="原典にたどり着けず"]{border-left-color:#64748b}
.ca-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:0 0 9px}
.ca-claim{margin:0;font-size:15px;font-weight:900;line-height:1.6;color:var(--ink)}
.ca-claim::before{content:"投稿：「";color:var(--muted);font-weight:700;font-size:12px}
.ca-claim::after{content:"」";color:var(--muted);font-weight:700;font-size:12px}
.ca-count{font-size:11.5px;font-weight:800;color:var(--muted);white-space:nowrap}
.ca-body p{margin:0 0 7px;font-size:13.5px;line-height:1.9;color:var(--ink)}
.ca-body p:last-child{margin-bottom:0}
.ca-source strong{font-weight:900}
.ca-note{color:var(--muted)!important}
.ca-verdict{display:inline-block;margin-right:8px;padding:2px 9px;border-radius:999px;font-size:11.5px;font-weight:900;color:#fff}
.ca-src{font-size:12px}
.ca-src a{color:var(--muted)}
.ca-note-bottom{margin:14px 0 0;font-size:12px;line-height:1.9;color:var(--muted)}
@media (max-width:720px){
  #claim-audit{padding-left:14px;padding-right:14px}
}
</style>"""


def write_provenance_records(claim_posts: dict, destination: Path | None = None) -> None:
    claims = [
        {"tweet_id": tid, "claim": entry["id"]}
        for entry in claim_posts["claims"]
        for tid in entry["tweet_ids"]
    ]
    out = destination or ROOT / "data" / "verification"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{THEME}-claims.json").write_text(
        json.dumps(claims, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
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
        parser.error("候補生成では --input/--html-template/--output-html/--verification-dest をすべて指定してください")

    samples, config, claim_posts = load(args.input)

    # claim_posts の "claims" は list of dicts。build_section が期待するキーに変換する。
    claim_posts_by_key = {
        "claims": {entry["id"]: entry["tweet_ids"] for entry in claim_posts["claims"]}
    }

    section_html = build_section(samples, claim_posts_by_key)

    public_path = ROOT / "docs" / f"{THEME}-reaction-map.html"
    template_path = args.html_template or public_path
    page_path = args.output_html or public_path
    page = template_path.read_text(encoding="utf-8")
    if page.count(START) != 1 or page.count(END) != 1:
        raise SystemExit(f"{START} / {END} が1つずつ必要です")
    head, rest = page.split(START, 1)
    _old, tail = rest.split(END, 1)
    page = f"{head}{section_html}{tail}"

    # 生成後の自己検証
    checks = [
        (CHECKED_AT, "確認日"),
        ('data-verdict="原典にある"', "「原典にある」カード"),
        ('data-verdict="原典とずれる"', "「原典とずれる」カード"),
        ('data-verdict="原典にたどり着けず"', "「原典にたどり着けず」カード"),
        ("ca-verdict", "判定バッジ"),
        ("claim-audit", "セクションID"),
    ]
    for needle, label in checks:
        if needle not in page:
            raise SystemExit(f"生成結果に {label} が見つかりません: {needle}")

    write_provenance_records(claim_posts, args.verification_dest)
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_text(page, encoding="utf-8")
    claim_total = sum(len(entry["tweet_ids"]) for entry in claim_posts["claims"])
    print(f"OK  {page_path.name} を更新（事実確認の該当投稿 {claim_total} 件・{len(FACT_CHECKS)} 主張）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
