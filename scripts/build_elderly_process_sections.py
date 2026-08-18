#!/usr/bin/env python3
"""高齢者免許返納ページの STEP2「確かめ方」を生成する。

投稿が事実として述べていることを、省庁の公表資料と突き合わせた記録をページに載せる。
分類でも論点整理でもなく、「調べた記録」そのものを出すのが目的。

    python3 scripts/build_elderly_process_sections.py
    python3 scripts/build_elderly_process_sections.py --check

HTML 内の VERIFY_SECTION_START / END の間だけを差し替える。
主張ごとの件数は data/elderly-license-revocation_claim_posts.json の tweet_id から
毎回数え直す。本文にも直書きしない。IDは編集部が候補を1件ずつ読んで確定したもので、
キーワード抽出の結果をそのまま件数にはしない（報道見出しの共有や、提案だけの投稿が
混ざるため）。
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
THEME = "elderly-license-revocation"
START = "<!-- VERIFY_SECTION_START -->"
END = "<!-- VERIFY_SECTION_END -->"

CHECKED_AT = "2026年8月18日"

# 判定は fact / gap / miss の3種だけ。
# miss（確認できなかった）の行は消さない。空振りが残っていることが、人が調べた証拠になる。
# miss は「投稿が誤り」という意味ではない。確認できなかった、とだけ書く。
FACT_CHECKS = [
    {
        "key": "increase",
        "claim": "高齢ドライバーの事故は増えている、多すぎる",
        "source": "警察庁は「75歳以上の高齢運転者による死亡事故は、前年比13件、3.2％減（免許保有者当たりでは75歳未満の約２倍）」と書いている。件数は令和7年で397件、平成27年の458件から減っており、免許保有者10万人当たりでも9.6件から4.8件へ下がっている。一方で同じ資料は「全死亡事故に占める75歳以上の高齢運転者による死亡事故の割合は増加傾向」とも書いている。",
        "verdict": "gap",
        "verdict_label": "食い違う",
        "note": "件数としては減っており、「増えている」は資料と合わない。ただし全死亡事故に占める割合は増えているため、目立つようになったという実感の側は資料と矛盾しない。なお「2025年の統計では397件」と数字を挙げた投稿があり、これは令和7年の公表値と一致していた。",
        "url": "https://www.npa.go.jp/publications/statistics/koutsuu/jiko/R07bunseki.pdf",
        "url_label": "警察庁 令和7年における交通事故の発生状況について（PDF）",
    },
    {
        "key": "rate",
        "claim": "高齢者の事故率が高いというのは印象操作で、実際は10代20代の方が高い",
        "source": "内閣府の交通安全白書（警察庁資料）によると、令和6年の免許保有者10万人当たり交通死亡事故件数は、16〜19歳が10.3件で最も多く、次いで80歳以上が7.2件。20〜29歳は3.0件で、70〜79歳の3.5件より低い。白書本文は「16～19歳及び80歳以上が他の年齢層に比べ多くなっており、令和６年中については、16～19歳が最も多く、次いで80歳以上が多くなっている」と記している。",
        "verdict": "gap",
        "verdict_label": "数字は合うが幅が違う",
        "note": "10代が最も高いという部分は資料どおり。ただし20代は低い側にあり、「10代20代の方が高い」とまでは言えない。逆側の「高齢者は通常の約2倍」という投稿は、75歳以上と75歳未満を比べた場合の値としては資料と一致する。",
        "url": "https://www8.cao.go.jp/koutu/taisaku/r07kou_haku/zenbun/genkyo/h1/h1b1s1_2.html",
        "url_label": "内閣府 令和7年版交通安全白書 第1-22図",
    },
    {
        "key": "renewal",
        "claim": "高齢者の免許更新はほぼ無条件に通る。実技試験は2026年から始まる",
        "source": "警察庁の資料では、75歳以上は更新時に認知機能検査を受け、そのうち過去3年間に信号無視・速度超過など一定の違反歴がある者は運転技能検査の対象になる。更新期間満了までに合格しなければ「更新せず」となる。運転技能検査は令和4年（2022年）5月13日から実施されており、令和7年の対象者数は16万5,756人だった。",
        "verdict": "gap",
        "verdict_label": "時期と対象が食い違う",
        "note": "実技の検査はこれから始まるのではなく、2022年5月からすでに行われている。ただし対象は違反歴のある人に限られ、違反歴がなければ実車の合否判定はない（高齢者講習の実車指導のみ）。「無条件に通る」という言い方が、この線引きを指しているのであれば、資料と真っ向から食い違うわけではない。",
        "url": "https://www.npa.go.jp/news/release/2026/260625_kouhou.pdf",
        "url_label": "警察庁 運転技能検査合格者の追跡調査の結果等について（PDF）",
    },
    {
        "key": "skilltest",
        "claim": "運転技能検査はザルだ。期間内なら何度でも受け直せる",
        "source": "警察庁の資料には、更新の流れとして運転技能検査は「繰り返し受検可」と明記されている。令和7年は受検者15万6,513人に対し合格者14万5,935人で、「運転技能検査受検者に占める合格者の割合：93％」。さらに追跡調査で「運転技能検査に合格した者の…10万人当たりの事故件数等は、運転技能検査の対象ではない高齢運転者10万人当たりの事故件数等より多い」ことが確認されたとしている。",
        "verdict": "fact",
        "verdict_label": "資料と一致する",
        "note": "繰り返し受検できることも、合格率の高さも資料どおり。警察庁自身が「運転技能が低下して交通事故を起こしやすくなっている者が、運転技能検査に合格していることがうかがわれる」として、検査内容を見直す有識者検討会を開き、令和8年8月を目途に報告書をまとめるとしている。",
        "url": "https://www.npa.go.jp/news/release/2026/260625_kouhou.pdf",
        "url_label": "警察庁 運転技能検査合格者の追跡調査の結果等について（PDF）",
    },
    {
        "key": "benefit",
        "claim": "返納すれば運転経歴証明書がもらえ、タクシーやバスの割引などの特典を受けられる",
        "source": "警察庁は、自主返納した人は運転経歴証明書の交付を受けられるとし、「地域の実情に応じて、自治体や事業者等による様々な支援が行われています」と書いている。運転経歴証明書は「運転免許証に代わる公的な本人確認書類として、永年、利用することができます」とも案内されている。",
        "verdict": "fact",
        "verdict_label": "制度としては存在する",
        "note": "証明書も特典も実在する。ただし支援の中身を決めているのは自治体や事業者で、全国一律の制度ではない。投稿に出てくるタクシー券・コミュニティバスの割引・預金金利の上乗せ・シニアカーの購入補助は、いずれもその地域だけの例として読む必要がある。",
        "url": "https://www.npa.go.jp/policies/application/license_renewal/jishuhennou.html",
        "url_label": "警察庁 運転免許証の自主返納について",
    },
    {
        "key": "legal",
        "claim": "運転免許証の自主返納に法的な根拠はない",
        "source": "道路交通法第百四条の四は「免許を受けた者は、その者の住所地を管轄する公安委員会に免許の取消しを申請することができる」と定めており、第百五条の二が運転経歴証明書の交付を定めている。警察庁の運転免許統計も「申請による運転免許の取消件数」を毎年集計しており、令和7年は435,067件、うち70歳以上が86.2％だった。",
        "verdict": "gap",
        "verdict_label": "前提が成立しない",
        "note": "返納は法律に手続が定められた「申請による取消し」で、件数も毎年公表されている。同じ投稿にある「70歳から返納者が増える」という部分は、申請取消の86.2％が70歳以上という統計と方向としては合っている。",
        "url": "https://laws.e-gov.go.jp/law/335AC0000000105",
        "url_label": "e-Gov法令検索 道路交通法（第百四条の四・第百五条の二）",
    },
    {
        "key": "transit",
        "claim": "返納したくても、地方はバスが1日2本で、タクシーも呼べず生活できない",
        "source": "国土交通省の「乗合バス路線の廃止状況の推移」では、令和5年度に届出のあった廃止キロは8,617キロメートル。ここ10年ほど毎年7,000〜9,000キロ規模の廃止が続いている。一方で、「1日2本」「呼んでも来ない」といった個々の地域の運行本数や待ち時間を示す全国的な公的資料は、今回参照した範囲では見つけられなかった。",
        "verdict": "miss",
        "verdict_label": "確認できず",
        "note": "路線の廃止が全国で続いていること自体は資料で確かめられた。ただし投稿が語っている暮らしの水準そのものは、公表資料からは確認できていない。投稿が誤りだという意味ではなく、確かめる材料がこちらに無いということ。",
        "url": "https://www.mlit.go.jp/jidosha/content/001898907.pdf",
        "url_label": "国土交通省 乗合バス路線の廃止状況の推移（PDF）",
    },
]

VERDICT_ORDER = ("fact", "gap", "miss")


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def load(input_path: Path | None = None) -> tuple[list[dict], dict]:
    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
    theme = themes[THEME]
    samples = json.loads((input_path or ROOT / theme["sample_file"]).read_text(encoding="utf-8"))
    claim_posts = json.loads(
        (ROOT / "data" / f"{THEME}_claim_posts.json").read_text(encoding="utf-8")
    )
    return samples, claim_posts


def check_claims(samples: list[dict], claim_posts: dict) -> dict[str, int]:
    """該当投稿IDが正典に実在することを確かめ、主張ごとの件数を返す。

    正典に無いIDが残っていると、件数だけが生き残って中身が消える。ここで落とす。
    """
    known = {str(s["tweet_id"]) for s in samples}
    counts: dict[str, int] = {}
    seen: dict[str, str] = {}
    for check in FACT_CHECKS:
        ids = claim_posts["claims"].get(check["key"])
        if not ids:
            raise SystemExit(f"{check['key']}: 該当投稿が data/{THEME}_claim_posts.json にありません")
        unknown = [i for i in ids if i not in known]
        if unknown:
            raise SystemExit(f"{check['key']}: 正典に無い tweet_id があります: {unknown}")
        for tid in ids:
            if tid in seen:
                raise SystemExit(f"{tid} が {seen[tid]} と {check['key']} の両方に入っています")
            seen[tid] = check["key"]
        counts[check["key"]] = len(ids)
    extra = set(claim_posts["claims"]) - {c["key"] for c in FACT_CHECKS}
    if extra:
        raise SystemExit(f"ページに出ない主張がデータに残っています: {sorted(extra)}")
    return counts


def build_section(counts: dict[str, int]) -> str:
    cards = []
    for check in FACT_CHECKS:
        cards.append(
            f"""      <article class="ev-card" data-verdict="{check['verdict']}">
        <div class="ev-head">
          <p class="ev-claim">{esc(check['claim'])}</p>
          <span class="ev-count">{counts[check['key']]}件の投稿</span>
        </div>
        <div class="ev-body">
          <p class="ev-source"><strong>資料はどう書いているか。</strong>{esc(check['source'])}</p>
          <p class="ev-note"><span class="ev-verdict">{esc(check['verdict_label'])}</span>{esc(check['note'])}</p>
          <p class="ev-src"><a href="{check['url']}" target="_blank" rel="noopener noreferrer">{esc(check['url_label'])}</a></p>
        </div>
      </article>"""
        )
    tally = {v: sum(1 for c in FACT_CHECKS if c["verdict"] == v) for v in VERDICT_ORDER}
    body = "\n".join(cards)
    return f"""{START}
<style id="elderly-verify-css">
#elderly-verify{{padding:26px min(6vw,72px) 30px;background:var(--bg)}}
#elderly-verify .ev-inner{{max-width:1000px;margin:0 auto}}
#elderly-verify .ev-step{{display:inline-block;margin:0 0 10px;padding:5px 12px;border-radius:999px;background:var(--accent-soft);color:var(--accent);font-size:11.5px;font-weight:900;letter-spacing:.06em}}
#elderly-verify h2{{font-size:clamp(20px,3.5vw,27px);line-height:1.5;margin:0 0 10px;color:var(--ink)}}
#elderly-verify .ev-lead{{font-size:14px;line-height:1.95;color:var(--muted);margin:0 0 16px}}
#elderly-verify .ev-grid{{display:grid;gap:11px}}
#elderly-verify .ev-card{{border:1px solid var(--line);border-left:4px solid var(--line);border-radius:0 12px 12px 0;background:var(--panel,#fff);padding:15px 17px}}
#elderly-verify .ev-card[data-verdict="fact"]{{border-left-color:#15803d}}
#elderly-verify .ev-card[data-verdict="gap"]{{border-left-color:#b45309}}
#elderly-verify .ev-card[data-verdict="miss"]{{border-left-color:#64748b}}
#elderly-verify .ev-head{{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:0 0 9px}}
#elderly-verify .ev-claim{{margin:0;font-size:15px;font-weight:900;line-height:1.6;color:var(--ink)}}
#elderly-verify .ev-claim::before{{content:"投稿：「";color:var(--muted);font-weight:700;font-size:12px}}
#elderly-verify .ev-claim::after{{content:"」";color:var(--muted);font-weight:700;font-size:12px}}
#elderly-verify .ev-count{{font-size:11.5px;font-weight:800;color:var(--muted);white-space:nowrap}}
#elderly-verify .ev-body p{{margin:0 0 7px;font-size:13.5px;line-height:1.9;color:var(--ink)}}
#elderly-verify .ev-body p:last-child{{margin-bottom:0}}
#elderly-verify .ev-source strong{{font-weight:900}}
#elderly-verify .ev-note{{color:var(--muted)}}
#elderly-verify .ev-verdict{{display:inline-block;margin-right:8px;padding:2px 9px;border-radius:999px;font-size:11.5px;font-weight:900;color:#fff}}
#elderly-verify .ev-card[data-verdict="fact"] .ev-verdict{{background:#15803d}}
#elderly-verify .ev-card[data-verdict="gap"] .ev-verdict{{background:#b45309}}
#elderly-verify .ev-card[data-verdict="miss"] .ev-verdict{{background:#64748b}}
#elderly-verify .ev-src{{font-size:12px}}
#elderly-verify .ev-src a{{color:var(--muted)}}
#elderly-verify .ev-note-foot{{margin:14px 0 0;font-size:12px;line-height:1.9;color:var(--muted)}}
@media (max-width:720px){{#elderly-verify{{padding:20px 14px 24px}}}}
</style>
<section id="elderly-verify" aria-labelledby="elderly-verify-title">
  <div class="ev-inner">
    <p class="ev-step">STEP 2 — 確かめ方</p>
    <h2 id="elderly-verify-title">投稿が事実として言っていることを、公表資料と突き合わせました</h2>
    <p class="ev-lead">投稿の中から、公的な資料で真偽や幅を確かめられる主張を{len(FACT_CHECKS)}つ選び、警察庁・内閣府・国土交通省の公表資料と法令に1つずつ当たっています。結果は一致{tally['fact']}件、食い違い{tally['gap']}件、確認できず{tally['miss']}件でした。確認できなかったものも、確認できなかったまま残しています。確認日は{CHECKED_AT}です。</p>
    <div class="ev-grid">
{body}
    </div>
    <p class="ev-note-foot">件数の数え方：本文をキーワードで拾っただけでは、報道の見出しをそのまま共有した投稿や、「こうすべきだ」という提案だけの投稿まで混ざります。そのため候補を1件ずつ読み、実際にその主張を事実として述べている投稿だけを数えています。該当した投稿のIDは data/elderly-license-revocation_claim_posts.json に保存しており、以後の件数はそこから数えます。義務化に賛成・反対どちらの投稿も含みます。</p>
  </div>
</section>
{END}"""


def write_provenance_records(claim_posts: dict, destination: Path | None = None) -> None:
    """「N件の投稿」の出所を、数字の出所検査が読める配列の形で書き出す。"""
    rows = [
        {"tweet_id": tid, "claim": check["key"]}
        for check in FACT_CHECKS
        for tid in claim_posts["claims"][check["key"]]
    ]
    out = destination or ROOT / "data" / "verification"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{THEME}-claims.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def build(
    *,
    check: bool = False,
    input_path: Path | None = None,
    html_template: Path | None = None,
    output_html: Path | None = None,
    verification_dest: Path | None = None,
) -> tuple[str, bool]:
    samples, claim_posts = load(input_path)
    counts = check_claims(samples, claim_posts)
    public_path = ROOT / "docs" / f"{THEME}-reaction-map.html"
    template_path = html_template or public_path
    page_path = output_html or public_path
    page = before = template_path.read_text(encoding="utf-8")
    if page.count(START) != 1 or page.count(END) != 1:
        raise SystemExit(f"{START} / {END} が1つずつ必要です")
    head, rest = page.split(START, 1)
    _old, tail = rest.split(END, 1)
    page = f"{head}{build_section(counts)}{tail}"

    # 生成後の自己検証
    checks = [
        ('data-verdict="miss"', "確認できなかった主張のカード"),
        (CHECKED_AT, "確認日"),
        ("STEP 2 — 確かめ方", "STEP2の見出し"),
    ] + [(f">{counts[c['key']]}件の投稿<", f"{c['key']} の件数") for c in FACT_CHECKS]
    for needle, label in checks:
        if needle not in page:
            raise SystemExit(f"生成結果に {label} が見つかりません: {needle}")
    if page.count('class="conclusion-count"') != 1:
        raise SystemExit("conclusion-count は1つだけ必要です")
    if len(re.findall(r'class="ev-card"', page)) != len(FACT_CHECKS):
        raise SystemExit("カード数が主張の数と一致しません")

    changed = page != before
    if not check:
        write_provenance_records(claim_posts, verification_dest)
        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_path.write_text(page, encoding="utf-8")
    total = sum(counts.values())
    return f"OK  {page_path.name} のSTEP2を更新（主張{len(FACT_CHECKS)}件 / 該当投稿{total}件）", changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="書き込まずに差分の有無だけ見る")
    parser.add_argument("--input", type=Path, help="候補の累積正典（省略時は THEMES.yaml の sample_file）")
    parser.add_argument("--html-template", type=Path, help="差し替え元のHTML（省略時は公開ページ）")
    parser.add_argument("--output-html", type=Path, help="書き出し先のHTML（省略時は公開ページ）")
    parser.add_argument("--verification-dest", type=Path, help="出所ファイルの書き出し先")
    args = parser.parse_args()
    message, changed = build(
        check=args.check,
        input_path=args.input,
        html_template=args.html_template,
        output_html=args.output_html,
        verification_dest=args.verification_dest,
    )
    print(message + ("（差分あり）" if changed else "（差分なし）"))
    return 1 if (args.check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
