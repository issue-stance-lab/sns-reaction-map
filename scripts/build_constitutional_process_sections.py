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

# 旧34投稿を再監査した日。全母数の網羅的な読み足しではない（背景に範囲を表示）。
CHECKED_AT = "2026年9月13日"
SOURCE_CHECKED_AT = "2026年9月13日"

# 一次資料に当たって確かめた結果。内部判定は全テーマ共通の fact / gap / miss。
# 既存ページの読者向け表示は、課題54の画面刷新まで変更しない。
# 件数は data/constitutional-amendment_claim_posts.json の tweet_id から数える。
# 機械抽出をそのまま件数にすると無関係な投稿が混入し3〜4割ぶん多く出るため、
# 必ず人が1件ずつ読んで確定した tweet_id を使う。
VERDICT_LABEL = {
    "fact": "原典にある",
    "gap": "原典とずれる",
    "miss": "原典にたどり着けず",
}

FACT_CHECKS = [{'key': 'minimum_vote_rate',
  'issues': ['国民投票・広告'],
  'claim': '国民投票には最低投票率の規定がない',
  'source': '国民投票法126条1項は賛成票が投票総数の2分の1を超えることを承認の条件とする。98条2項で投票総数は賛成票と反対票の合計とされる。最低投票率を成立条件とする規定は置かれていない。',
  'verdict': 'fact',
  'note': '国民投票法126条1項は賛成票が投票総数の2分の1を超えることを承認の条件とし、最低投票率を成立条件にしていない。98条2項の投票総数は賛成票と反対票の合計。',
  'url': 'https://laws.e-gov.go.jp/law/419AC1000000051',
  'url_label': 'e-Gov 国民投票法（日本国憲法の改正手続に関する法律）'},
 {'key': 'period_60days',
  'issues': ['国民投票・広告'],
  'claim': '国会の発議から国民投票まで最短60日だ',
  'source': '国民投票法2条では、国会の発議の日から起算して60日以後180日以内において、国会が議決した期日に国民投票を行う。',
  'verdict': 'fact',
  'note': '60日以上180日以内という数字は第2条の条文どおり。期日の決定は国会の議決によることも明記されている。',
  'url': 'https://laws.e-gov.go.jp/law/419AC1000000051',
  'url_label': 'e-Gov 国民投票法（日本国憲法の改正手続に関する法律）'},
 {'key': 'two_thirds',
  'issues': ['政党・発議手続き'],
  'claim': '憲法改正には衆参両院それぞれ3分の2以上の賛成が必要だ',
  'source': '日本国憲法第96条第1項は「この憲法の改正は、各議院の総議員の三分の二以上の賛成で、国会が、これを発議し、国民に提案してその承認を経なければならない」と定める。「各議院の」とあるため、衆議院・参議院の両院それぞれで3分の2以上が必要。',
  'verdict': 'fact',
  'note': '3分の2・各議院という条件は第96条第1項の条文どおり。「総議員」の解釈（欠員を含むか）に学説上の議論はあるが、3分の2以上という数字の読みに食い違いはない。',
  'url': 'https://laws.e-gov.go.jp/law/321CONSTITUTION',
  'url_label': 'e-Gov法令検索 日本国憲法 第96条'},
 {'key': 'emergency_law_making',
  'issues': ['緊急事態条項'],
  'claim': '緊急事態条項案では内閣が国会を経ずに法律を作れる',
  'source': '自民党の2018年条文イメージ73条の2は、大地震その他の異常かつ大規模な災害で、国会の法律制定を待ついとまがない特別の事情がある場合に、法律の定めるところにより生命・身体・財産を保護する政令を制定する案。2項は速やかに国会の承認を求めるとする。',
  'verdict': 'miss',
  'note': 'この投稿がどの年のどの案を指すかは特定できない。2018年の自民党案73条の2は大規模災害などの条件と国会の承認を求める手続きを置くが、2026年解説ではより広い緊急事態や国会機能代行も議論されている。参照する案を決めずに、この投稿を正しい・誤りとは判定しない。',
  'url': 'https://storage.jimin.jp/pdf/constitution/news/20180326_01.pdf',
  'url_label': '自民党 条文イメージ・たたき台素案（2018年3月）PDF',
  'extra_links': [['https://storage.jimin.jp/pdf/constitution/document/kenpou_manual2026.pdf',
                   '自民党 2026年解説版 p.7']]},
 {'key': 'article18_conscription',
  'issues': ['9条・自衛隊'],
  'claim': '徴兵制は憲法18条の苦役禁止に当たる',
  'source': '憲法18条は意に反する苦役を禁じる。2016年10月11日の参議院予算委員会で稲田防衛大臣は、徴兵制は憲法18条が禁止する苦役に当たると答弁した。自民党の2018年条文イメージは18条の改正を提案していない。',
  'verdict': 'fact',
  'note': '2016年10月11日の国会答弁で、政府は徴兵制を憲法18条が禁じる苦役と説明している。その政府解釈との一致を確認したもので、将来のあらゆる制度の可否を断定するものではない。',
  'url': 'https://kokkai.ndl.go.jp/txt/119215261X00320161011/151',
  'url_label': '国会会議録 2016年10月11日 参議院予算委員会 稲田防衛大臣答弁'},
 {'key': 'jieitai_iken_gaku',
  'issues': ['9条・自衛隊'],
  'claim': '自衛隊を違憲とする解釈がある',
  'source': '2017年5月9日の参議院予算委員会で安倍総理は、政府は自衛隊を合憲とする一貫した立場だと説明し、同時に違憲とする憲法学者の見解にも言及した。',
  'verdict': 'fact',
  'note': '当時の政府答弁で解釈の対立への言及を確認できる。これは学説を直接調査した資料ではなく、現在の学者の割合を示す根拠としては扱わない。',
  'url': 'https://kokkai.ndl.go.jp/txt/119315261X01820170509/43',
  'url_label': '国会会議録 2017年5月9日 参議院予算委員会 安倍総理答弁'}]


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
        verdict_label = VERDICT_LABEL[verdict]
        if verdict == "fact":
            verdict_color = "#15803d"
        elif verdict == "gap":
            verdict_color = "#b45309"
        else:
            verdict_color = "#64748b"
        cards.append(f"""      <article class="ca-card" data-verdict="{esc(verdict_label)}">
        <div class="ca-head">
          <p class="ca-claim">{esc(check['claim'])}</p>
          <span class="ca-count">{n}件の投稿</span>
        </div>
        <div class="ca-body">
          <p class="ca-source"><strong>一次資料の記述。</strong>{esc(check['source'])}</p>
          <p class="ca-note"><span class="ca-verdict" style="background:{verdict_color}">{esc(verdict_label)}</span>{esc(check['note'])}</p>
          <p class="ca-src"><a href="{esc(check['url'])}" target="_blank" rel="noopener noreferrer">{esc(check['url_label'])}</a></p>
        </div>
      </article>""")
    body = "\n".join(cards)
    return f"""{START}
{CSS}
<section id="claim-audit" aria-labelledby="claim-audit-title">
  <div class="ca-inner">
    <h2 id="claim-audit-title">原典にある数字・原典にない数字</h2>
    <p class="ca-lead">憲法改正に関する投稿の{len(FACT_CHECKS)}の主張を、憲法と国民投票法の条文、国会の会議録、政党が公表した条文案に1つずつ当たって確かめました。「原典にたどり着けず」はそのまま残しています。確認日は{CHECKED_AT}です。報道・解説サイトは参照していません。</p>
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
    if "<!-- PLANET_SECTION_START -->" in page:
        write_provenance_records(claim_posts, args.verification_dest)
        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_path.write_text(page, encoding="utf-8")
        print("OK  山なみ内の資料照合を使用（旧セクションは再挿入しません）")
        return 0
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
