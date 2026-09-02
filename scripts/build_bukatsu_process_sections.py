#!/usr/bin/env python3
"""部活動の地域移行 — 一次資料照合の判定リテラルと、その出所ファイルの書き出し。

**このスクリプトは公開HTMLを書き換えない。** 他6テーマの同名スクリプトはページに
事実確認セクションを描くが、部活動は課題54の段階7で惑星ページとして作り直すため、
いまページへ差し込むと段階1の「公開ページのHTMLはバイト単位で変わらない」を破る。
ここに置くのは、公開JSONの入力になる `FACT_CHECKS` / `CHECKED_AT` と、人が確定した
投稿IDの写しを `data/verification/` へ出す `write_provenance_records()` だけ。

件数の正典は `data/bukatsu-chiiki_claim_posts.json`（編集部が1件ずつ読んで確定したもの）。
ここでは数え直すだけで、キーワード抽出の結果は使わない。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKED_AT = "2026年9月2日"

# 判定は fact / gap / miss の3語。読者に見せる言い方は他テーマと重ねない
# （`scripts/verify_page_originality.py` の趣旨。表示は段階7のページで使う）。
# FACT_CHECKS は ast.literal_eval で外部から読まれる（公開JSONの入力）。
# 変数参照を混ぜるとリテラルとして読めなくなるので、判定の言い方は各カードに直接書く。
# fact=「公表資料で確認できた」/ gap=「公表資料と話が合わない」/ miss=「公表資料では追えなかった」

FACT_CHECKS = [
    {
        "key": "original-deadline",
        "issues": ["制度・移行プロセス"],
        "claim": "部活動の地域移行は、もともと2023〜2025年度（令和5〜7年度）で完了する計画だった",
        "source": "令和4年12月のガイドラインは「令和５年度から令和７年度までの３年間を改革推進期間と位置付けて支援」するとし、「休日の学校部活動の段階的な地域連携・地域移行を進める」「地域の実情等に応じて可能な限り早期の実現を目指す」と書いている。令和7年12月のガイドラインは「令和８年度から令和 13 年度までの６年間を新たに『改革実行期間』と位置付け」、その期間内に原則すべての学校部活動で休日の地域展開を目指すとしている。",
        "verdict": "gap",
        "verdict_label": "公表資料と話が合わない",
        "note": "3年間という期間はそのとおりだが、資料はそれを「重点的に支援する期間」と書いており、全国の移行を終える期限としては書いていない。",
        "url": "https://www.mext.go.jp/sports/content/20221227-spt_oripara-000026750_2.pdf",
        "url_label": "スポーツ庁・文化庁 学校部活動及び新たな地域クラブ活動の在り方等に関する総合的なガイドライン（令和4年12月・PDF）",
        "extra_links": [
            (
                "https://www.mext.go.jp/sports/content/20251226-spt_oripara-000046627_00234.pdf",
                "文部科学省 部活動改革及び地域クラブ活動の推進等に関する総合的なガイドライン（令和7年12月・PDF）",
            ),
        ],
    },
    {
        "key": "national-funding",
        "issues": ["費用・家庭負担", "制度・移行プロセス"],
        "claim": "地域移行に国はほとんど金を出さず、あとは自治体と家庭任せだ",
        "source": "スポーツ庁の令和8年度当初予算資料は「部活動の地域展開等の全国的な実施」に令和8年度予算額57億円（前年度37億円）、令和7年度補正予算額82億円と記載している。補助割合は原則「国1/3、都道府県1/3、市区町村1/3」で、平日も含めた地域展開の加速化に係る重点課題対応は「定額補助：国10/10」。国の会議録では浅野スポーツ庁次長が「139億円の予算を確保させていただいて、これに補助分の地方交付税もつきますので、300億円以上の公費の負担を計画しております」と述べている。",
        "verdict": "gap",
        "verdict_label": "公表資料と話が合わない",
        "note": "国費は付いており、額も公表されている。ただし補助の対象は運営経費側で、家庭が払う会費そのものを国が肩代わりする仕組みではないため、負担が残るという感覚のほうは資料と矛盾しない。",
        "url": "https://www.mext.go.jp/sports/content/20260409-spt_oripara-000028257_1.pdf",
        "url_label": "スポーツ庁 部活動の地域展開等の全国的な実施（令和8年度当初予算・PDF）",
        "extra_links": [
            (
                "https://www.mext.go.jp/sports/b_menu/shingi/043_index/001/gijiroku/jsa_00003.html",
                "スポーツ庁 学習指導要領における部活動・地域クラブ活動の取扱いに関する検討ワーキンググループ（第2回）議事録",
            ),
        ],
    },
    {
        "key": "coach-pay",
        "issues": ["受け皿・指導者"],
        "claim": "地域移行後の指導者の報酬は最低賃金並みで、だから引き受け手がいない",
        "source": "熊本市教育委員会の素案は指導者の報酬を「顧問：1,600円/ｈ 副顧問：1,000円/ｈ」と試算している。厚生労働省の令和7年度地域別最低賃金は熊本1,034円（令和8年1月1日発効）、東京1,226円（令和7年10月3日発効）。一方、部活動指導員として自治体が公表している時間額は、熊本市1,600円、練馬区1,872円（地域手当相当額を含む）、東京都の都立学校2,360円など。",
        "verdict": "gap",
        "verdict_label": "公表資料と話が合わない",
        "note": "最低賃金に届かない試算（熊本市の副顧問1,000円）は実在するが、公表されている時間額は1,000円台後半から2,000円台までひらきがある。全国どこでも最低賃金並み、という形にはなっていない。",
        "url": "https://www.city.kumamoto.jp/kiji00354887/5_54887_419171_up_PHDXW6PS.pdf",
        "url_label": "熊本市教育委員会 熊本市立中学校における新しい学校部活動の在り方（素案）（PDF）",
        "extra_links": [
            (
                "https://www.mhlw.go.jp/content/11200000/001571192.pdf",
                "厚生労働省 令和7年度 地域別最低賃金 全国一覧（PDF）",
            ),
            (
                "https://www.city.kumamoto.jp/kiji00370419/index.html",
                "熊本市 令和8年度 熊本市立中学校部活動指導員（会計年度任用職員）募集",
            ),
        ],
    },
    {
        "key": "shidoin-role",
        "issues": ["受け皿・指導者"],
        "claim": "部活動指導員は顧問を任され大会の引率もできるが、外部指導者は技術指導しかできない",
        "source": "スポーツ庁の制度説明は、部活動指導員の職務として「実技指導」「学校外での活動（大会・練習試合等）の引率」等を挙げ、「学校長は、部活動指導員に部活動の顧問を命じることができる」と書いている。根拠となる学校教育法施行規則第七十八条の二は「部活動指導員は、中学校におけるスポーツ、文化、科学等に関する教育活動（中学校の教育課程として行われるものを除く。）に係る技術的な指導に従事する。」の一文。",
        "verdict": "fact",
        "verdict_label": "公表資料で確認できた",
        "note": "顧問を命じられること、大会の引率ができることは、どちらも資料に書いてある。ただし投稿が添える「会計年度任用の非常勤職員」という身分は国の資料には無く、身分や任用は学校の設置者が規則で定める（自治体ごとに違う）。",
        "url": "https://www.mext.go.jp/sports/content/20240930-spt_oripara-000014391_2.pdf",
        "url_label": "スポーツ庁 部活動指導員の概要（PDF）",
        "extra_links": [
            (
                "https://laws.e-gov.go.jp/law/322M40000080011",
                "e-Gov法令検索 学校教育法施行規則 第七十八条の二",
            ),
        ],
    },
    {
        "key": "chutairen-entry",
        "issues": ["教育的意義・機会"],
        "claim": "中体連の大会に地域クラブのチームが出られるようになっている",
        "source": "日本中学校体育連盟が都道府県中体連あてに出した「令和7年度全国中学校体育大会 地域クラブ活動の参加資格の特例競技部細則」（令６日中体発第305号）は、地域クラブ活動として大会に参加する場合の競技別の要件を定めている。同細則は「同一年度内に選手が登録できる地域クラブ活動は１クラブとし、地域クラブ活動への二重登録、ならびに、複数都道府県予選大会への出場は認めない」とも定める。",
        "verdict": "fact",
        "verdict_label": "公表資料で確認できた",
        "note": "参加できるようになっているのはそのとおり。ただし細則を読むと、学校の部活動と地域クラブの掛け持ちで大会に出ることは認められておらず、生徒はどちらか一方を選ぶことになる。",
        "url": "https://www.fukui-jpa.com/data/saisoku061011.pdf",
        "url_label": "日本中学校体育連盟 令和7年度全国中学校体育大会 地域クラブ活動の参加資格の特例競技部細則（令６日中体発第305号・PDF）",
    },
    {
        "key": "club-cost-survey",
        "issues": ["費用・家庭負担"],
        "claim": "運動部の費用は年平均8万4千円で、保護者の65%が負担を感じている",
        "source": "この数字を出している公的な統計は見つけられなかった。スポーツ庁の世論調査・全国体力運動能力調査、文部科学省の子供の学習費調査のいずれにも、この組み合わせの数字は無い。報道が引用しているのは民間企業（スポーツブル社のANYTEAM）が中高生214人・保護者300人・顧問100人にインターネットで行った調査である。",
        "verdict": "miss",
        "verdict_label": "公表資料では追えなかった",
        "note": "投稿が間違いという意味ではない。国や自治体が公表した統計としては裏が取れなかった、というだけ。数字の出どころは、規模と方法が公表されている民間のネット調査だった。",
    },
    {
        "key": "kyushokuchoseigaku",
        "issues": ["教員の働き方"],
        "claim": "給特法は改正されたが、教職調整額は4%のままだ",
        "source": "給特法（昭和46年法律第77号）第三条第一項は、教育職員に「その者の給料月額の百分の十（幼稚園の教育職員にあっては、百分の四）に相当する額を基準として」教職調整額を支給すると定める。附則の表により、令和8年1月1日から同年12月31日までは「百分の五」、以後1年ごとに百分の六・七・八・九と上がり、令和13年から本則の百分の十になる。",
        "verdict": "gap",
        "verdict_label": "公表資料と話が合わない",
        "note": "この投稿が書かれた2026年8月の時点で、教職調整額はすでに5%へ上がっている。足りないという評価は評価として、4%のままという事実の部分は法律の条文と合わない。",
        "url": "https://laws.e-gov.go.jp/law/346AC0000000077",
        "url_label": "e-Gov法令検索 公立の義務教育諸学校等の教育職員の給与等に関する特別措置法 第三条・附則",
    },
]


def claim_posts(path: Path | None = None) -> dict:
    source = path or ROOT / "data" / "bukatsu-chiiki_claim_posts.json"
    return json.loads(source.read_text(encoding="utf-8"))


def write_provenance_records(posts: dict, destination: Path | None = None) -> list[dict]:
    """人が確定した投稿IDを `data/verification/bukatsu-chiiki-claims.json` へ写す。

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
    (out / "bukatsu-chiiki-claims.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim-posts", type=Path, help="確定済み投稿IDの正典（省略時は data/ の既定）")
    parser.add_argument("--verification-dest", type=Path, help="出所ファイルの書き出し先（省略時は data/verification）")
    args = parser.parse_args()
    rows = write_provenance_records(claim_posts(args.claim_posts), args.verification_dest)
    print(f"OK  主張{len(FACT_CHECKS)}件 / 確定投稿{len(rows)}件 → bukatsu-chiiki-claims.json")
    print("    このスクリプトは公開HTMLを書き換えません（課題54 段階7でページを作り直すため）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
