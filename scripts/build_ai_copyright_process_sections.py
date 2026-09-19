#!/usr/bin/env python3
"""生成AIと著作権 — 一次資料照合の判定リテラルと、その出所ファイルの書き出し。

`FACT_CHECKS` / `CHECKED_AT` は公開JSONの入力でもある。他9テーマの同名スクリプトと
同じく、人が確定した投稿IDの写しを `data/verification/` へ出す
`write_provenance_records()` を持つ。実際のクイズ描画は共通の惑星ジェネレータ
（`build_planet_data.py`）が `data/public/themes/ai-copyright.json` の
`claim_verification` を読んで行う（こちらは変更しない）。

件数の正典は `data/ai-copyright_claim_posts.json`（2026-09-13、編集部が1件ずつ読んで
確定したもの）。ここでは数え直すだけで、キーワード抽出の結果は使わない。

山なみ変換（2026-09-14）の時点でこのスクリプトが作られず、`CLAIM_AUDIT_SOURCES`
（`scripts/public_registry_common.py`）にも未登録だったため、`claim_posts.json`が
存在するのに一次資料クイズが空のまま公開されていた（オーナー報告で発覚、2026-09-19）。

2026-09-20、オーナー指摘で「その言い分、一次資料に当たるとどうなるか」という
独立セクションを追加（consumption-tax-cut・koshitsu-tenpakaiと同型、同じ
FACT_CHECKSを流用）。こちらは公開HTMLを書き換える（`build_audit_section()` /
`inject_audit()` / `--write-html`）。

    python3 scripts/build_ai_copyright_process_sections.py --write-html
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKED_AT = "2026年9月19日"

# 判定は fact / gap / miss の3語。読者に見せる言い方は他テーマと重ねない
# （`scripts/verify_page_originality.py` の趣旨）。
# FACT_CHECKS は ast.literal_eval で外部から読まれる（公開JSONの入力）。
# fact=「公表資料で確認できた」/ gap=「公表資料と話が合わない」/ miss=「公表資料では追えなかった」

FACT_CHECKS = [
    {
        "key": "unauthorized_learning_infringement",
        "issues": ["学習データ・無断利用"],
        "claim": "AIによる無断学習は、著作権法上、常に著作権侵害にあたる",
        "source": "著作権法第30条の4は、著作物に表現された思想又は感情の享受を目的としない利用であれば、原則として権利者の許諾なく利用できると定めている。文化庁「AIと著作権に関する考え方について」は、AIの学習のための利用はこの規定にあたり原則として著作権侵害にならないとしつつ、『学習データの創作的表現をそのまま出力させる目的』が併存する場合（特定のクリエイターの少量の作品のみで追加学習し作風を模倣する場合等）は対象外になりうるとしている。",
        "verdict": "gap",
        "verdict_label": "公表資料と話が合わない",
        "note": "無断で著作物が使われていること自体は事実で、懸念には根拠がある。ただし著作権法は学習のための利用を原則として権利者の許諾が不要な行為と位置づけており、常に著作権侵害にあたるとまでは言えない。享受目的が併存する場合など例外的に問題になりうる、という整理がより正確。",
        "url": "https://www.bunka.go.jp/seisaku/bunkashingikai/chosakuken/pdf/94037901_01.pdf",
        "url_label": "文化審議会著作権分科会法制度小委員会「AIと著作権に関する考え方について」（令和6年3月15日）",
        "extra_links": [
            (
                "https://laws.e-gov.go.jp/law/345AC0000000048",
                "e-Gov法令検索 著作権法 第30条の4",
            ),
        ],
    },
    {
        "key": "data_disclosure_needed",
        "issues": ["学習データ・無断利用", "法制度・規制整備"],
        "claim": "学習データの出所開示をAI事業者に法律で義務づける制度は、日本にはまだ無い",
        "source": "内閣府知的財産戦略推進事務局は「生成AIの適切な利活用等に向けた知的財産の保護及び透明性に関するプリンシプル・コード」を作成した。AI事業者に学習データの出所等の開示を求めるが、開示を強制するものではなく、実施するか実施しない場合はその理由を説明する「コンプライ・オア・エクスプレイン」方式を採用している。",
        "verdict": "fact",
        "verdict_label": "公表資料で確認できた",
        "note": "そのとおりです。政府（内閣府）が用意しているのは、開示するか、しない場合は理由を説明すればよい任意の枠組み（プリンシプル・コード）で、開示を法律で義務づけるものではありません。",
        "url": "https://www.cas.go.jp/jp/seisakukaigi/titeki2/ai_kentoukai/kaisai/pdf/ai_principle_code.pdf",
        "url_label": "内閣府知的財産戦略推進事務局「生成AIの適切な利活用等に向けた知的財産の保護及び透明性に関するプリンシプル・コード」",
    },
    {
        "key": "compensation_required",
        "issues": ["クリエイター保護・権利"],
        "claim": "AI事業者に、学習データの利用について対価の支払いを義務づける法律は無い",
        "source": "著作権法第30条の4は、非享受目的の利用であれば権利者の許諾も対価の支払いも法律上の要件としていない。一方で内閣府「AI時代の知的財産権検討会 中間とりまとめ」は、開発者・提供者が自ら進んで権利者と合意のうえで対価還元策を講じることは可能であり、良質な学習データに係るライセンス市場の形成と対価還元の実現が期待されるとし、拠出者へ報酬を配分する民間の取組事例を挙げている。",
        "verdict": "fact",
        "verdict_label": "公表資料で確認できた",
        "note": "そのとおりです。著作権法第30条の4は、非享受目的の利用であれば権利者の許諾も対価の支払いも法律上の要件としていません。契約に基づき自主的に対価を還元する事業者の取組事例は資料にありますが、法律上の義務ではありません。",
        "url": "https://www.cas.go.jp/jp/seisakukaigi/titeki2/chitekizaisan2024/0528_ai.pdf",
        "url_label": "内閣府「AI時代の知的財産権検討会 中間とりまとめ」（2024年5月）",
    },
    {
        "key": "creator_protection_insufficient",
        "issues": ["クリエイター保護・権利"],
        "claim": "無断でAIに学習された作品の作者は、対抗する手段を持たない",
        "source": "内閣府「中間とりまとめ－権利者のための手引き－」は、robots.txtの記載や利用規約への明示によるオプトアウトの方法を紹介する一方、「robots.txtの記載による収集制限を尊重しないクローラも存在している」「人力で別サイトに転載されてしまった場合、そこから収集されることは防げない」と限界も明記している。他方、文化庁「AIと著作権に関する考え方について」は、著作権侵害が認められれば生成物の廃棄請求や、一定の場合には学習用データセットからの除去請求ができるとしている。",
        "verdict": "gap",
        "verdict_label": "公表資料と話が合わない",
        "note": "オプトアウトの手段が不完全であることは資料にも明記されており、無力感には根拠がある。ただし著作権侵害が認められた場合の救済手段（廃棄請求・除去請求等）は制度として存在しており、対抗手段が皆無というわけではない。",
        "url": "https://www.cas.go.jp/jp/seisakukaigi/titeki2/chitekizaisan2024/2411_tebiki.pdf",
        "url_label": "内閣府「AI時代の知的財産権検討会『中間とりまとめ』－権利者のための手引き－」（2024年11月）",
        "extra_links": [
            (
                "https://www.bunka.go.jp/seisaku/bunkashingikai/chosakuken/pdf/94037901_01.pdf",
                "文化庁「AIと著作権に関する考え方について」（救済手段の整理箇所）",
            ),
        ],
    },
    {
        "key": "ai_output_has_copyright",
        "issues": ["AI生成物の権利・創作性"],
        "claim": "AIが生成した作品にも、通常の著作物と同じように著作権が認められる",
        "source": "文化審議会著作権分科会法制度小委員会では「生成物の著作物性」が議題として扱われ、人の創作的寄与が必要かどうかが論点とされている。文化庁の整理自体、AIと著作権の関係を直接的に取り扱った判例・裁判例が未だ乏しい状態であると明記している。",
        "verdict": "gap",
        "verdict_label": "公表資料と話が合わない",
        "note": "AI生成物が一律に著作物として保護される、あるいは一律に保護されないという単純な結論は資料には無い。人の創作的寄与の有無によってケースごとに判断される論点として扱われており、これを直接確定させた判例もまだ確認できていない。",
        "url": "https://www.bunka.go.jp/seisaku/bunkashingikai/chosakuken/pdf/94037901_01.pdf",
        "url_label": "文化審議会著作権分科会法制度小委員会「AIと著作権に関する考え方について」（生成物の著作物性の議論）",
    },
    {
        "key": "tech_innovation_over_regulation",
        "issues": ["技術競争・推進", "法制度・規制整備"],
        "claim": "生成AIへの法規制はほとんど進んでおらず、野放し状態にある",
        "source": "AI技術全般の研究開発・活用を推進する法律（人工知能関連技術の研究開発及び活用の推進に関する法律、令和七年法律第五十三号）が2025年6月4日に公布された。あわせて内閣府は、AI事業者に学習データの出所等の開示を求める「プリンシプル・コード」の整備を進めている。一方、著作権法そのもの（第30条の4・第47条の5）は改正されていない。",
        "verdict": "gap",
        "verdict_label": "公表資料と話が合わない",
        "note": "著作権法上のAI学習に関する条文が改正されていないのは事実だが、AI法の制定やプリンシプル・コードの整備は進んでおり、法制度の対応が「ほとんど進んでいない」「野放し」とまでは言えない。",
        "url": "https://laws.e-gov.go.jp/law/507AC0000000053",
        "url_label": "e-Gov法令検索「人工知能関連技術の研究開発及び活用の推進に関する法律」（令和七年法律第五十三号、2025年6月4日公布）",
    },
]


def claim_posts(path: Path | None = None) -> dict:
    source = path or ROOT / "data" / "ai-copyright_claim_posts.json"
    return json.loads(source.read_text(encoding="utf-8"))


def write_provenance_records(posts: dict, destination: Path | None = None) -> list[dict]:
    """人が確定した投稿IDを `data/verification/ai-copyright-claims.json` へ写す。

    公開JSONの `matched_post_count` はこのファイルを数えて作られる。判定カードの
    主張IDと過不足があれば、ここで止める（後段の検査を待たない）。
    """
    keys = {check["key"] for check in FACT_CHECKS}
    if set(posts["claims"]) != keys:
        raise SystemExit(
            f"確定データと判定カードの主張IDが一致しません: "
            f"確定のみ={sorted(set(posts['claims']) - keys)} カードのみ={sorted(keys - set(posts['claims']))}"
        )
    rows = [
        {"tweet_id": tweet_id, "claim": key}
        for key, ids in posts["claims"].items()
        for tweet_id in ids
    ]
    out = destination or ROOT / "data" / "verification"
    out.mkdir(parents=True, exist_ok=True)
    (out / "ai-copyright-claims.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return rows


# ---------------------------------------------------------------------------
# 「その言い分、一次資料に当たるとどうなるか」— consumption-tax-cut・
# koshitsu-tenpakaiと同型の独立セクション（2026-09-20、オーナー指摘）。
# 見出し・導入文・まとめ文は verify_page_originality.py の対象なので、
# 他テーマの言い回しをそのまま流用しない。判定バッジ（原典どおり／原典とズレ／
# 原典に届かず）は3〜5文字の定型語で20文字未満のため、他テーマと重ねてよい
# （koshitsu-tenpakaiが2026-09-20に同じ語を採用済み。しきい値は
# scripts/verify_page_originality.pyの「20文字以上の文」を参照）。
# ---------------------------------------------------------------------------
DEFAULT_PAGE = ROOT / "docs" / "ai-copyright-reaction-map.html"
AUDIT_START = "<!-- AI_COPYRIGHT_AUDIT_START -->"
AUDIT_END = "<!-- AI_COPYRIGHT_AUDIT_END -->"

AUDIT_H2 = "その言い分、一次資料に当たるとどうなるか"
AUDIT_SUBTITLE = "文化庁資料・内閣府検討会・国会答弁で1件ずつ照合"
VERDICT_MARK = {"fact": "原典どおり", "gap": "原典とズレ", "miss": "原典に届かず"}

# consumption-tax-cut・koshitsu-tenpakaiと同じ見た目に揃える（同じCSS）。
AUDIT_CSS = """<style>
.claim-audit .ca-lead{margin:0 0 18px;line-height:1.9}
.claim-audit .ca-list{display:grid;gap:14px}
.claim-audit .ca-item{border:1px solid var(--line,#dcdfe6);border-radius:12px;padding:16px 18px;background:var(--card,#fff)}
.claim-audit .ca-item[data-verdict="gap"]{border-left:5px solid #d1603d}
.claim-audit .ca-item[data-verdict="fact"]{border-left:5px solid #3f7d58}
.claim-audit .ca-item[data-verdict="miss"]{border-left:5px solid #8a8fa3;border-style:dashed;border-left-style:solid}
.claim-audit .ca-say{margin:0 0 10px;font-weight:700;font-size:1.02rem;line-height:1.7}
.claim-audit .ca-n{display:inline-block;margin-left:8px;padding:2px 9px;border-radius:999px;background:rgba(120,130,150,.14);font-size:.78rem;font-weight:600;white-space:nowrap;vertical-align:middle}
.claim-audit .ca-detail{margin:0;display:grid;grid-template-columns:8.4em 1fr;gap:6px 14px}
.claim-audit .ca-detail dt{font-size:.8rem;font-weight:700;opacity:.72;white-space:normal}
.claim-audit .ca-detail dd{margin:0;line-height:1.85;white-space:normal}
.claim-audit .ca-mark{display:inline-block;margin-right:.5em;padding:1px 8px;border-radius:5px;background:rgba(120,130,150,.16);font-size:.82rem}
.claim-audit .ca-item[data-verdict="gap"] .ca-mark{background:rgba(209,96,61,.16);color:#a34526}
.claim-audit .ca-item[data-verdict="fact"] .ca-mark{background:rgba(63,125,88,.16);color:#2f6144}
.claim-audit .ca-item[data-verdict="miss"] .ca-mark{background:rgba(138,143,163,.2)}
.claim-audit .ca-src{margin:10px 0 0;font-size:.82rem;line-height:1.8}
.claim-audit .ca-src a{word-break:break-word}
.claim-audit .ca-how{margin:18px 0 0;padding:12px 14px;border-radius:10px;background:rgba(120,130,150,.09);font-size:.86rem;line-height:1.85}
@media (max-width:640px){.claim-audit .ca-detail{grid-template-columns:1fr;gap:2px}
.claim-audit .ca-detail dt{margin-top:8px}}
</style>"""


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def build_audit_section(posts: dict) -> str:
    """FACT_CHECKSとclaim_postsから、独立セクションのHTMLを組み立てる。"""
    claims_map = posts["claims"]
    items = []
    counts = []
    for check in FACT_CHECKS:
        ids = claims_map[check["key"]]
        counts.append(len(ids))
        links = [(check["url"], check["url_label"]), *check.get("extra_links", [])]
        src_html = " ／ ".join(
            f'<a href="{url}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'
            for url, label in links
        )
        items.append(f"""  <article class="ca-item" data-verdict="{check['verdict']}">
    <p class="ca-say">「{esc(check['claim'])}」<span class="ca-n">該当した投稿 {len(ids)}件</span></p>
    <dl class="ca-detail">
      <dt>原典はこう書いている</dt><dd>{esc(check['source'])}</dd>
      <dt>突き合わせた結果</dt><dd><b class="ca-mark">{VERDICT_MARK[check['verdict']]}</b>{esc(check['note'])}</dd>
    </dl>
    <p class="ca-src">{src_html}</p>
  </article>""")
    body = "\n".join(items)
    total = sum(counts)
    lead = (
        "生成AIと著作権をめぐる投稿には、法律の条文名や政府資料を挙げて語られる"
        "ものが目立ちます。名前が本物でも、書いてある中身まで正確とは限りません。"
        f"ここでは投稿でよく見かける言い分のうち、公表資料で当否を確かめられるものを"
        f"{len(FACT_CHECKS)}つ取り出し、文化庁の考え方、内閣府の検討会資料、著作権法の条文、"
        f"国会答弁に当たりました。照合したのは{CHECKED_AT}です。"
    )
    how = (
        "件数の数え方について。キーワードだけで拾うと、無関係な文脈で同じ語を使った"
        "投稿も混ざります。ここでは候補となった投稿を1件ずつ本文で確認し、実際にその"
        f"言い分を述べている投稿だけを数えました（合わせて{total}件）。規制に賛成か"
        "推進に賛成かは問うていません。投稿の本文はこの節には載せず、件数と照合結果"
        "だけを示しています。"
    )
    return f"""<section class="panel claim-audit" id="ai-copyright-audit">
{AUDIT_CSS}
<div class="panel-title"><h2>{AUDIT_H2}</h2><span>{AUDIT_SUBTITLE}</span></div>
<p class="ca-lead">{lead}</p>
<div class="ca-list">
{body}
</div>
<p class="ca-how">{how}</p>
</section>"""


def inject_audit(page_text: str, section_html: str) -> str:
    """AI_COPYRIGHT_AUDIT_START/ENDの間だけを差し替える。

    マーカーがまだ無い（このセクションを初めて入れる）ときは、PLANET_SECTION_END
    の直後へ新規に挿入する（consumption-tax-cutと同じ、山なみ図を読んだ直後の位置）。
    """
    if AUDIT_START in page_text:
        import re

        pattern = re.compile(re.escape(AUDIT_START) + r".*?" + re.escape(AUDIT_END), re.S)
        return pattern.sub(f"{AUDIT_START}\n{section_html}\n{AUDIT_END}", page_text)
    anchor = "<!-- PLANET_SECTION_END -->"
    if anchor not in page_text:
        raise SystemExit(f"{anchor} が見つかりません（まだ山なみ形式ではない）")
    return page_text.replace(
        anchor, f"{anchor}\n{AUDIT_START}\n{section_html}\n{AUDIT_END}", 1
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim-posts", type=Path, help="確定済み投稿IDの正典（省略時は data/ の既定）")
    parser.add_argument("--verification-dest", type=Path, help="出所ファイルの書き出し先（省略時は data/verification）")
    parser.add_argument("--write-html", action="store_true", help="独立セクションをdocs/へ書き込む")
    parser.add_argument("--page", type=Path, help="--write-html の対象HTML（省略時はdocs/の既定）")
    args = parser.parse_args()
    posts = claim_posts(args.claim_posts)
    rows = write_provenance_records(posts, args.verification_dest)
    print(f"OK  主張{len(FACT_CHECKS)}件 / 確定投稿{len(rows)}件 → ai-copyright-claims.json")
    if args.write_html:
        page_path = args.page or DEFAULT_PAGE
        original = page_path.read_text(encoding="utf-8")
        updated = inject_audit(original, build_audit_section(posts))
        if updated != original:
            page_path.write_text(updated, encoding="utf-8")
            print(f"OK  {page_path} を更新しました（AI_COPYRIGHT_AUDIT セクション）")
        else:
            print(f"OK  {page_path} は差分なし")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
