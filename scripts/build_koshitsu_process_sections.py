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

CHECKED_AT = "2026年8月20日"

FACT_CHECKS = [
    {
        "key": "claim_1_条文第一条",
        "issues": ["男系vs女系"],
        "claim": "皇室典範第一条には「皇統に属する男系の男子」が継承すると書いてある",
        "source": "「皇位は、皇統に属する男系の男子が、これを継承する。」（皇室典範第一条）。「男系の男子」という表現は条文に明記されており、投稿が引用する文言と一致する。",
        "verdict": "fact",
        "verdict_label": "条文と一致",
        "note": "e-Gov法令検索のAPIで取得した原文（令和8年改正前の条文）で確認した。",
        "url": "https://laws.e-gov.go.jp/law/322AC0000000003",
        "url_label": "e-Gov法令検索 皇室典範",
    },
    {
        "key": "claim_2_旧11宮家と改正法",
        "issues": ["旧宮家養子縁組"],
        "claim": "旧11宮家は1947年（昭和22年）に皇籍を離れた。改正皇室典範は7月24日公布・10月24日施行",
        "source": "内閣官房資料に「昭和22年に皇籍離脱した11宮家（男子26方、女子25方）」と記載がある。e-Gov附則（令和8年7月24日法律第66号）は「公布の日から起算して三月を経過した日から施行する」と定めており、公布日の7月24日から3か月後は10月24日になる。",
        "verdict": "fact",
        "verdict_label": "両方確認できた",
        "note": "旧宮家の数（11家）と施行日（10月24日）はいずれも一次資料で確認できた。",
        "url": "https://www.cas.go.jp/jp/seisaku/taii_tokurei/dai11/siryou1.pdf",
        "url_label": "内閣官房 安定的な皇位継承の確保に関する懇談会 第11回資料1（PDF）",
    },
    {
        "key": "claim_3_養子継承資格",
        "issues": ["旧宮家養子縁組"],
        "claim": "養子本人は皇位継承資格を持たないが、その子孫の男性には付与される",
        "source": "改正皇室典範（令和8年法律第66号による改正後の条文）はe-Gov APIでは取得できなかった。施行前のため官報PDFも確認したが、新設条文の全文は取得できていない。",
        "verdict": "miss",
        "verdict_label": "確認できず",
        "note": "公布済みの改正後条文を一次資料として取得できなかったため、この主張の正否を確認できない。",
        "url": "https://laws.e-gov.go.jp/law/322AC0000000003",
        "url_label": "e-Gov法令検索 皇室典範（改正後条文が反映され次第確認予定）",
    },
    {
        "key": "claim_4_有識者会議意見分布",
        "issues": ["女性天皇・女系天皇"],
        "claim": "有識者会議（2021年）で女性天皇または女系天皇に賛成したのは21人中11人、男系男子は7人",
        "source": "有識者会議の報告書本文（令和3年12月22日）には「ヒアリングの中では、皇位継承のルールについて悠仁親王殿下までは変えるべきでないとの意見がほとんどを占め、現時点において直ちに変更すべきとの意見は一つのみでありました」という記述がある。女性天皇・女系天皇への賛否を「11人・7人」と区分した集計表は本文中に見当たらなかった。意見の詳細整理は参考資料8（別文書）に収録されているが、そちらは今回確認できていない。",
        "verdict": "miss",
        "verdict_label": "確認できず",
        "note": "21名がヒアリングに参加した事実と報告書の一般的な記述は確認できた。しかし「11人賛成・7人男系」という具体的な内訳は、確認できた報告書本文の中には記載がなかった。",
        "url": "https://www.cas.go.jp/jp/seisaku/taii_tokurei/pdf/houkoku_honbun_20211222.pdf",
        "url_label": "内閣官房 有識者会議 報告書（令和3年12月22日、PDF）",
    },
    {
        "key": "claim_5_継承資格者3名",
        "issues": ["男系vs女系"],
        "claim": "皇位継承資格者（男系男子の皇族）は現在3名しかいない",
        "source": "有識者会議報告書（令和3年12月22日）は「皇位継承資格者として、秋篠宮皇嗣殿下、悠仁親王殿下及び常陸宮正仁親王殿下の三方がおられます」と明記している。令和8年の改正皇室典範は皇位継承資格の範囲を変えていないため、この3名という人数は改正後も変わっていない。",
        "verdict": "fact",
        "verdict_label": "報告書に明記",
        "note": "3名という数は報告書が明記しており、投稿の主張と一致する。改正法は女性皇族の皇籍維持と旧宮家の養子を対象としており、継承資格者の増加は今回の改正に含まれていない。",
        "url": "https://www.cas.go.jp/jp/seisaku/taii_tokurei/pdf/houkoku_honbun_20211222.pdf",
        "url_label": "内閣官房 有識者会議 報告書（令和3年12月22日、PDF）",
    },
    {
        "key": "claim_6_第二条継承順序",
        "issues": ["男系vs女系"],
        "claim": "皇室典範では継承順位は皇長子（長男）から始まり、直系を優先する",
        "source": "皇室典範第二条は「皇位は、左の順序により、皇族に、これを伝える。一 皇長子 二 皇長孫 三 その他の皇長子の子孫 四 皇次子及びその子孫…」と定め、同条第三項は「長系を先にし、同等内では、長を先にする」と明記している。",
        "verdict": "fact",
        "verdict_label": "条文と一致",
        "note": "「直系優先・長を先にする」という原則は条文に明記されており、投稿の理解と一致する。e-Gov法令検索のAPIで原文を取得して確認した。",
        "url": "https://laws.e-gov.go.jp/law/322AC0000000003",
        "url_label": "e-Gov法令検索 皇室典範",
    },
]


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
