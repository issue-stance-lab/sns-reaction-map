#!/usr/bin/env python3
"""皇室典範改正ページの「条文・資料に当たる」セクションを生成する。

    python3 scripts/build_koshitsu_process_sections.py
    python3 scripts/build_koshitsu_process_sections.py --output-html <候補HTML>

HTML 内の KOSHITSU_AUDIT_START / KOSHITSU_AUDIT_END の間だけを差し替える。
--output-html を省くと docs/koshitsu-tenpakai-reaction-map.html を直接更新する。
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = "koshitsu-tenpakai"
CANONICAL_JSON = ROOT / "social-samples" / "koshitsu-tenpakai_hermes_cur_20260726.json"
CLAIM_POSTS_JSON = ROOT / "data" / "koshitsu-tenpakai_claim_posts.json"
DEFAULT_PAGE = ROOT / "docs" / "koshitsu-tenpakai-reaction-map.html"

START = "<!-- KOSHITSU_AUDIT_START -->"
END = "<!-- KOSHITSU_AUDIT_END -->"

CHECKED_AT = "2026年9月13日"

FACT_CHECKS = [{'key': 'claim_1_条文第一条', 'issues': ['男系vs女系'], 'claim': '皇室典範第一条には「皇統に属する男系の男子」が継承すると書いてある', 'source': '「皇位は、皇統に属する男系の男子が、これを継承する。」（皇室典範第一条）。「男系の男子」という表現は条文に明記されており、投稿が引用する文言と一致する。', 'verdict': 'fact', 'verdict_label': '条文と一致', 'note': '9月13日に現行条文と10月24日施行版の第一条を確認。いずれも資格は「男系の男子」です。女性天皇への希望を、今回案全体への賛否と同一視はできません。', 'url': 'https://laws.e-gov.go.jp/law/322AC0000000003', 'url_label': 'e-Gov法令検索 皇室典範'}, {'key': 'claim_2_旧11宮家と改正法', 'issues': ['旧宮家養子縁組'], 'claim': '旧11宮家は1947年（昭和22年）に皇籍を離れた。改正皇室典範は7月24日公布・10月24日施行', 'source': '内閣官房資料に「昭和22年に皇籍離脱した11宮家（男子26方、女子25方）」と記載がある。e-Gov附則（令和8年7月24日法律第66号）は「公布の日から起算して三月を経過した日から施行する」と定めており、公布日の7月24日から3か月後は10月24日になる。', 'verdict': 'fact', 'verdict_label': '両方確認できた', 'note': '旧11宮家の皇籍離脱は内閣官房の第11回資料1、公布日と施行日はe-Govの改正履歴・附則で確認しました。', 'url': 'https://www.cas.go.jp/jp/seisaku/taii_tokurei/dai11/siryou1.pdf', 'url_label': '内閣官房 安定的な皇位継承の確保に関する懇談会 第11回資料1（PDF）', 'extra_links': [('https://laws.e-gov.go.jp/api/2/law_data/322AC0000000003_20261024_508AC0000000066', 'e-Gov 2026年10月24日施行版')]}, {'key': 'claim_3_養子継承資格', 'issues': ['旧宮家養子縁組'], 'claim': '旧宮家から迎える養子本人には皇位継承資格を与えない', 'source': '改正後第三十八条第四項は、養子皇族男子には第二条を適用しないと規定しています。同条第六項はその子孫には実方の系統で第二条を適用すると定めています。', 'verdict': 'fact', 'verdict_label': '改正後条文で確認', 'note': '養子本人には継承順序の規定を適用しません。子孫は別扱いです。改正後第三十八条と7月15日の国会答弁を今回取得できたため、従来の「確認できず」を更新しました。', 'url': 'https://laws.e-gov.go.jp/api/2/law_data/322AC0000000003_20261024_508AC0000000066', 'url_label': 'e-Gov 皇室典範・2026年10月24日施行版', 'extra_links': [('https://kokkai.ndl.go.jp/txt/122115389X00220260715/93', '参議院特別委員会・木原国務大臣答弁')]}, {'key': 'claim_4_有識者会議意見分布', 'issues': ['女性天皇・女系天皇'], 'claim': '有識者会議（2021年）で女性天皇または女系天皇に賛成したのは21人中11人、男系男子は7人', 'source': '有識者会議の報告書本文（令和3年12月22日）には「ヒアリングの中では、皇位継承のルールについて悠仁親王殿下までは変えるべきでないとの意見がほとんどを占め、現時点において直ちに変更すべきとの意見は一つのみでありました」という記述がある。女性天皇・女系天皇への賛否を「11人・7人」と区分した集計表は本文中に見当たらなかった。意見の詳細整理は参考資料8（別文書）に収録されているが、そちらは今回確認できていない。', 'verdict': 'miss', 'verdict_label': '確認できず', 'note': '21名がヒアリングに参加した事実と報告書の一般的な記述は確認できた。しかし「11人賛成・7人男系」という具体的な内訳は、確認できた報告書本文の中には記載がなかった。', 'url': 'https://www.cas.go.jp/jp/seisaku/taii_tokurei/pdf/houkoku_honbun_20211222.pdf', 'url_label': '内閣官房 有識者会議 報告書（令和3年12月22日、PDF）'}, {'key': 'claim_5_継承資格者3名', 'issues': ['男系vs女系'], 'claim': '皇位継承資格者は3人で、改正の前後も変わらない', 'source': '2021年の報告書は当時の皇位継承資格者を三方と記載しています。ただし、改正後第三十八条は養子本人と子孫の扱いを分けています。報告書の人数だけで、将来の人数が変わらないとは確認できません。', 'verdict': 'gap', 'verdict_label': '現在と将来を分ける', 'note': '2021年の報告書に三方とありますが、それだけで2026年の人数や将来の人数まで確かめたことにはなりません。改正後は養子本人と子孫の扱いが異なります。最新の人数確認はこの照合では行っていません。', 'url': 'https://www.cas.go.jp/jp/seisaku/taii_tokurei/pdf/houkoku_honbun_20211222.pdf', 'url_label': '内閣官房 有識者会議 報告書（令和3年12月22日、PDF）', 'extra_links': [('https://laws.e-gov.go.jp/api/2/law_data/322AC0000000003_20261024_508AC0000000066', 'e-Gov 皇室典範・2026年10月24日施行版')]}, {'key': 'claim_6_第二条継承順序', 'issues': ['男系vs女系'], 'claim': '現在の皇位継承は「直系優先かつ男子優先」である', 'source': '皇室典範第二条は「皇位は、左の順序により、皇族に、これを伝える。一 皇長子 二 皇長孫 三 その他の皇長子の子孫 四 皇次子及びその子孫…」と定め、同条第三項は「長系を先にし、同等内では、長を先にする」と明記している。', 'verdict': 'gap', 'verdict_label': '「男子優先」と「男子に限る」は別', 'note': '第二条は皇長子などの順序を定めますが、第一条は男系の男子に資格を限っています。女性にも資格があって男性を先にする「男子優先」という説明では、現行の資格条件を取り落とします。', 'url': 'https://laws.e-gov.go.jp/law/322AC0000000003', 'url_label': 'e-Gov法令検索 皇室典範'}]


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def load_known_ids() -> set[str]:
    samples = json.loads(CANONICAL_JSON.read_text(encoding="utf-8"))
    if isinstance(samples, list):
        return {s["tweet_id"] for s in samples if "tweet_id" in s}
    if isinstance(samples, dict) and "posts" in samples:
        return {s["tweet_id"] for s in samples["posts"] if "tweet_id" in s}
    raise SystemExit(f"正典JSONの形式が不明です: {CANONICAL_JSON}")


def load_claim_posts() -> dict[str, list[str]]:
    raw = json.loads(CLAIM_POSTS_JSON.read_text(encoding="utf-8"))
    result: dict[str, list[str]] = {}
    for key, val in raw.items():
        if isinstance(val, dict) and "tweet_ids" in val:
            result[key] = val["tweet_ids"]
        elif isinstance(val, list):
            result[key] = val
        else:
            raise SystemExit(f"claim_posts.json の形式が不明です: key={key}")
    return result


def validate(claim_posts: dict[str, list[str]], known_ids: set[str]) -> None:
    for check in FACT_CHECKS:
        key = check["key"]
        if key not in claim_posts:
            raise SystemExit(f"claim_posts.json に {key} がありません")
        unknown = [i for i in claim_posts[key] if i not in known_ids]
        if unknown:
            raise SystemExit(f"{key}: 正典に存在しない tweet_id があります: {unknown}")


def build_section(claim_posts: dict[str, list[str]]) -> str:
    cards = []
    for check in FACT_CHECKS:
        ids = claim_posts[check["key"]]
        cards.append(f"""    <article class="pv-card" data-verdict="{check['verdict']}">
      <div class="pv-head">
        <p class="pv-claim">{esc(check['claim'])}</p>
        <span class="pv-count">{len(ids)}件の投稿</span>
      </div>
      <div class="pv-body">
        <p class="pv-source"><strong>一次資料には何と書いてあるか。</strong>{esc(check['source'])}</p>
        <p class="pv-note"><span class="pv-verdict">{esc(check['verdict_label'])}</span>{esc(check['note'])}</p>
        <p class="pv-src"><a href="{check['url']}" target="_blank" rel="noopener noreferrer">{esc(check['url_label'])}</a></p>
      </div>
    </article>""")
    body = "\n".join(cards)
    return f"""<section class="panel" id="koshitsu-audit" aria-labelledby="koshitsu-audit-title">
  <div class="pc-inner">
    <p class="pc-step">資料を当たる</p>
    <h2 id="koshitsu-audit-title">投稿が引く条文・数字を、皇室典範の原文と官公庁の公表資料で確かめました</h2>
    <p class="pc-lead">条文の引用・人数の根拠・施行日など、投稿が事実として示す主張を6件取り上げ、皇室典範の原文（e-Gov法令検索）・内閣官房の公表資料・有識者会議の報告書を一件ずつ調べました。根拠まで届かなかった項目は、何が確認できて何が届かなかったかを残しています。調査日は{CHECKED_AT}です。</p>
    <div class="pv-grid">
{body}
    </div>
    <p class="pc-note">件数の数え方：本文の機械検索では、関係のない文脈で同じ語が出てくる投稿も拾ってしまいます。そのため候補を1件ずつ読み、実際にその主張をしている投稿だけを手で選んで数えています。賛成・反対どちらの投稿も含みます。</p>
  </div>
</section>"""


def inject(page_text: str, section_html: str) -> str:
    pattern = re.compile(
        re.escape(START) + r".*?" + re.escape(END),
        re.DOTALL,
    )
    replacement = f"{START}\n{section_html}\n{END}"
    if not pattern.search(page_text):
        raise SystemExit(f"マーカーが見つかりません: {START!r} / {END!r}")
    return pattern.sub(replacement, page_text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-html", type=Path, default=None)
    args = parser.parse_args()

    page = args.output_html or DEFAULT_PAGE
    if not page.exists():
        raise SystemExit(f"HTMLが見つかりません: {page}")

    known_ids = load_known_ids()
    claim_posts = load_claim_posts()
    validate(claim_posts, known_ids)

    section_html = build_section(claim_posts)
    original = page.read_text(encoding="utf-8")
    updated = inject(original, section_html)
    page.write_text(updated, encoding="utf-8")
    print(f"OK: {page} を更新しました（KOSHITSU_AUDIT セクション）")


if __name__ == "__main__":
    main()
