#!/usr/bin/env python3
"""生成AIと著作権 — 一次資料照合の判定リテラルと、その出所ファイルの書き出し。

**このスクリプトは公開HTMLを書き換えない。** 他9テーマの同名スクリプトと同じく、
ここに置くのは公開JSONの入力になる `FACT_CHECKS` / `CHECKED_AT` と、人が確定した
投稿IDの写しを `data/verification/` へ出す `write_provenance_records()` だけ。
実際のクイズ描画は共通の惑星ジェネレータ（`build_planet_data.py`）が
`data/public/themes/ai-copyright.json` の `claim_verification` を読んで行う。

件数の正典は `data/ai-copyright_claim_posts.json`（2026-09-13、編集部が1件ずつ読んで
確定したもの）。ここでは数え直すだけで、キーワード抽出の結果は使わない。

山なみ変換（2026-09-14）の時点でこのスクリプトが作られず、`CLAIM_AUDIT_SOURCES`
（`scripts/public_registry_common.py`）にも未登録だったため、`claim_posts.json`が
存在するのに一次資料クイズが空のまま公開されていた（オーナー報告で発覚）。
"""
from __future__ import annotations

import argparse
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
        "claim": "AI事業者に学習データの出所を開示させる制度は、日本にはまだ存在しない",
        "source": "内閣府知的財産戦略推進事務局は「生成AIの適切な利活用等に向けた知的財産の保護及び透明性に関するプリンシプル・コード」を作成した。AI事業者に学習データの出所等の開示を求めるが、開示を強制するものではなく、実施するか実施しない場合はその理由を説明する「コンプライ・オア・エクスプレイン」方式を採用している。",
        "verdict": "gap",
        "verdict_label": "公表資料と話が合わない",
        "note": "法律による開示の義務化はされておらず、その意味では制度が「無い」という感覚は間違っていない。ただし政府はすでに任意の開示の枠組み（プリンシプル・コード）を用意しており、開示を求める仕組み自体が全く存在しないわけではない。",
        "url": "https://www.cas.go.jp/jp/seisakukaigi/titeki2/ai_kentoukai/kaisai/pdf/ai_principle_code.pdf",
        "url_label": "内閣府知的財産戦略推進事務局「生成AIの適切な利活用等に向けた知的財産の保護及び透明性に関するプリンシプル・コード」",
    },
    {
        "key": "compensation_required",
        "issues": ["クリエイター保護・権利"],
        "claim": "AI事業者はクリエイターに一切対価を支払わずに学習データを利用している",
        "source": "著作権法第30条の4は、非享受目的の利用であれば権利者の許諾も対価の支払いも法律上の要件としていない。一方で内閣府「AI時代の知的財産権検討会 中間とりまとめ」は、開発者・提供者が自ら進んで権利者と合意のうえで対価還元策を講じることは可能であり、良質な学習データに係るライセンス市場の形成と対価還元の実現が期待されるとし、拠出者へ報酬を配分する民間の取組事例を挙げている。",
        "verdict": "gap",
        "verdict_label": "公表資料と話が合わない",
        "note": "法律上、対価の支払いが義務ではないことは事実で、多くの学習で対価が支払われていないという実感は誤りではない。ただし「一切」払われていないとまでは言えず、契約に基づく対価還元の仕組みや事例は資料にも挙げられている。",
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim-posts", type=Path, help="確定済み投稿IDの正典（省略時は data/ の既定）")
    parser.add_argument("--verification-dest", type=Path, help="出所ファイルの書き出し先（省略時は data/verification）")
    args = parser.parse_args()
    rows = write_provenance_records(claim_posts(args.claim_posts), args.verification_dest)
    print(f"OK  主張{len(FACT_CHECKS)}件 / 確定投稿{len(rows)}件 → ai-copyright-claims.json")
    print("    このスクリプトは公開HTMLを書き換えません")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
