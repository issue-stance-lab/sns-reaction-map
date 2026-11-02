#!/usr/bin/env python3
"""生成AIと著作権 — 一次資料照合の判定リテラルと、その出所ファイルの書き出し。

`FACT_CHECKS` / `CHECKED_AT` は公開JSONの入力でもある。他9テーマの同名スクリプトと
同じく、人が確定した投稿IDの写しを `data/verification/` へ出す
`write_provenance_records()` を持つ。実際のクイズ描画は共通の惑星ジェネレータ
（`build_planet_data.py`）が `data/public/themes/ai-copyright.json` の
`claim_verification` を読んで行う（資料照合と条件・評価の説明を区別する）。

件数の正典は `data/ai-copyright_claim_posts.json`（編集担当が本文を確認して確定したもの）。ここでは数え直すだけで、キーワード抽出の結果は使わない。

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

CHECKED_AT = "2026年11月1日"

# 資料照合は fact / gap / miss。条件・評価の説明は assessment_kind を付け verdict=None とする。
# 読者に見せる言い方は他テーマと重ねない
# （`scripts/verify_page_originality.py` の趣旨）。
# FACT_CHECKS は ast.literal_eval で外部から読まれる（公開JSONの入力）。
# fact=「公表資料で確認できた」/ gap=「公表資料と話が合わない」/ miss=「公表資料では追えなかった」

FACT_CHECKS = [{'key': 'unauthorized_learning_infringement',
  'issues': ['学習データ・無断利用'],
  'claim': 'AIによる無断学習は、著作権法上、常に著作権侵害にあたる',
  'source': '著作権法第30条の4では、作品の思想や感情を楽しむことを目的としない利用が認められています。利用できるのは必要な限度内で、権利者の利益を不当に害しない場合です。文化庁は、学習元の創作的な表現を出力させる目的がある場合などを区別しています。',
  'verdict': 'gap',
  'verdict_label': '公表資料と話が合わない',
  'note': '無許諾という理由だけで、すべての学習を著作権侵害とすることはできません。作風が似ていることだけを、創作的表現の利用と同一視しないことも必要です。',
  'url': 'https://www.bunka.go.jp/seisaku/bunkashingikai/chosakuken/pdf/94037901_01.pdf',
  'url_label': '文化審議会著作権分科会法制度小委員会「AIと著作権に関する考え方について」（令和6年3月15日）',
  'extra_links': [('https://laws.e-gov.go.jp/law/345AC0000000048', 'e-Gov法令検索 著作権法 第30条の4')]},
 {'key': 'data_disclosure_needed',
  'issues': ['学習データ・無断利用', '法制度・規制整備'],
  'claim': '日本では、AI事業者に学習データの出所を事前に一般公開させる一律の法的義務はない',
  'source': '政府のプリンシプル・コードは、学習データの出所などの開示を求める任意の枠組みです。受け入れは任意で、実施しない場合には理由の説明を求めています。一方、著作権法第114条の3には、個別の訴訟で書類などの提出を命じる制度があります。',
  'verdict': 'fact',
  'verdict_label': '公表資料で確認できた',
  'note': 'ここで確認するのは、事業者全般に出所の事前公開を義務づける制度です。個別の訴訟で利用できる開示手段まで、存在しないという意味ではありません。',
  'url': 'https://www.cas.go.jp/jp/seisakukaigi/titeki2/ai_kentoukai/kaisai/pdf/ai_principle_code.pdf',
  'url_label': '内閣府知的財産戦略推進事務局「生成AIの適切な利活用等に向けた知的財産の保護及び透明性に関するプリンシプル・コード」',
  'extra_links': [('https://laws.e-gov.go.jp/law/345AC0000000048', '著作権法第114条の3')]},
 {'key': 'compensation_required',
  'issues': ['クリエイター保護・権利'],
  'claim': '日本では、著作権法第30条の4の要件を満たす学習に、一律の法定対価は求められない',
  'source': '著作権法第30条の4は、要件内の利用に一律の対価支払いを条件としていません。許諾を受ける契約を結んだ場合の支払義務や、権利侵害に対する損害賠償は別に考える必要があります。',
  'verdict': 'fact',
  'verdict_label': '公表資料で確認できた',
  'note': '第30条の4は、目的や利用の限度などの条件を満たす場合の規定です。契約を結ぶかどうかの任意性と、結んだ契約に従う義務を分けて考えます。',
  'url': 'https://www.cas.go.jp/jp/seisakukaigi/titeki2/chitekizaisan2024/0528_ai.pdf',
  'url_label': '内閣府「AI時代の知的財産権検討会 中間とりまとめ」（2024年5月）',
  'extra_links': [('https://laws.e-gov.go.jp/law/345AC0000000048', '著作権法第30条の4・第63条・第114条'),
                  ('https://laws.e-gov.go.jp/law/129AC0000000089', '民法第415条・第521条・第709条')]},
 {'key': 'creator_protection_insufficient',
  'issues': ['クリエイター保護・権利'],
  'claim': '無断でAIに学習された作品の作者は、対抗する手段を持たない',
  'source': '権利侵害が認められれば、差止めや損害賠償を請求する制度があります。文化庁は、一定の条件で学習用データセットからの除去を請求できると整理しています。ただし、学習済みモデルを当然に廃棄させられる制度ではありません。',
  'verdict': 'gap',
  'verdict_label': '公表資料と話が合わない',
  'note': 'すべての対抗手段がないという説明は、制度の整理と合いません。一方、収集を事前に避ける対策にも限界があります。救済制度の存在だけで、立証の難しさや費用の負担が解消するわけではありません。',
  'url': 'https://www.cas.go.jp/jp/seisakukaigi/titeki2/chitekizaisan2024/2411_tebiki.pdf',
  'url_label': '内閣府「AI時代の知的財産権検討会『中間とりまとめ』－権利者のための手引き－」（2024年11月）',
  'extra_links': [('https://www.bunka.go.jp/seisaku/bunkashingikai/chosakuken/pdf/94037901_01.pdf',
                   '文化庁「AIと著作権に関する考え方について」（救済手段の整理箇所）')]},
 {'key': 'ai_output_has_copyright',
  'issues': ['AI生成物の権利・創作性'],
  'claim': 'AIで作った作品にも、通常の作品と同じように著作権が認められる',
  'source': '文化庁は、AIを使った生成物にも通常の著作物と同じ判断基準を用いると整理しています。人の創作的寄与が認められるかを、具体的な使い方に応じて判断します。AI自体が著作者になるわけではありません。',
  'verdict': None,
  'verdict_label': '条件を確認',
  'note': '通常と同じ基準で判断するという意味なら、資料と矛盾しません。生成物がすべて自動的に保護されるという意味かどうかは、投稿に書かれた条件を確認します。条件の省略だけで、無条件の保護を主張したとは扱いません。',
  'url': 'https://www.bunka.go.jp/seisaku/bunkashingikai/chosakuken/pdf/94037901_01.pdf',
  'url_label': '文化審議会著作権分科会法制度小委員会「AIと著作権に関する考え方について」（生成物の著作物性の議論）',
  'assessment_kind': 'conditional_explanation'},
 {'key': 'tech_innovation_over_regulation',
  'issues': ['技術競争・推進', '法制度・規制整備'],
  'claim': '生成AIへの法規制は不十分だ',
  'source': '日本には著作権法やAI法があり、政府の任意のプリンシプル・コードもあります。AI法は研究開発や活用の推進を含む枠組みで、任意のコードにも法的な強制力はありません。制度があることと、規制が十分かどうかは別の論点です。',
  'verdict': None,
  'verdict_label': '評価の論点',
  'note': '規制の十分さは、法律が存在することだけでは正誤を決められません。禁止する行為や罰則、実際の運用を含めて考える評価の論点です。「規制が弱い」という批判を、法律が一切ないという主張には読み替えません。',
  'url': 'https://laws.e-gov.go.jp/law/507AC0000000053',
  'url_label': 'e-Gov法令検索「人工知能関連技術の研究開発及び活用の推進に関する法律」（令和七年法律第五十三号、2025年6月4日公布）',
  'assessment_kind': 'evaluation_context',
  'extra_links': [('https://www.cas.go.jp/jp/seisakukaigi/titeki2/ai_kentoukai/kaisai/pdf/ai_principle_code.pdf',
                   'プリンシプル・コード')]}]


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
        items.append(f"""  <article class="ca-item" data-verdict="{check['verdict'] or ''}" data-assessment-kind="{check.get('assessment_kind', 'source_comparison')}">
    <p class="ca-say">「{esc(check['claim'])}」<span class="ca-n">該当した投稿 {len(ids)}件</span></p>
    <dl class="ca-detail">
      <dt>原典はこう書いている</dt><dd>{esc(check['source'])}</dd>
      <dt>突き合わせた結果</dt><dd><b class="ca-mark">{check['verdict_label'] if check['verdict'] is None else VERDICT_MARK[check['verdict']]}</b>{esc(check['note'])}</dd>
    </dl>
    <p class="ca-src">{src_html}</p>
  </article>""")
    body = "\n".join(items)
    total = sum(counts)
    lead = (
        "生成AIと著作権をめぐる6つの主張を、文化庁の考え方や法律の条文と照合しました。"
        "著作権が認められる条件や、規制の十分さを考える論点も説明しています。"
        f"照合したのは{CHECKED_AT}です。"
    )
    how = (
        f"主張に直接当たる投稿は、合わせて{total}件です。本文に書かれた条件を確認し、"
        "提案だけの投稿や、別の意味で同じ語を使った投稿は数えていません。"
        "0件は、今回の意見にその主張への直接の表明がなかったという意味です。"
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
