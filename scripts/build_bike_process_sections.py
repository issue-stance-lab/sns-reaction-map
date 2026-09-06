#!/usr/bin/env python3
"""自転車青切符ページの冒頭「集め方 → 確かめ方 → 分かったこと」を生成する。

このテーマは page_update_mode: manual だが、この3セクションだけは再実行できる。
件数は social-samples の正典と data/ の再読マッピングから毎回数え直すので、
データを追加したあとにこのスクリプトを流せば本文の数字がずれない。

    python3 scripts/build_bike_process_sections.py
    python3 scripts/build_bike_process_sections.py \
        --input <候補正典> --html-template <元HTML> --output-html <候補HTML> \
        --verification-dest <候補の出所ファイル置き場>

HTML 内の PROCESS_SECTIONS_START / END の間だけを差し替える。

`--input` 以下は adapter（scripts/refresh_adapters/bike.py）が候補ページを作るための
引数で、公開ページと data/verification/ には触らない。
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
THEME = "bike-blue-ticket"
START = "<!-- PROCESS_SECTIONS_START -->"
END = "<!-- PROCESS_SECTIONS_END -->"

BUCKET_META = [
    ("strict", "青切符では足りない", "免許制・講習の義務化を求める。「反対」に分類されているが、要求の向きは逆。", "#b91c1c"),
    ("support", "今の青切符を支持する", "信号無視や歩道の暴走を実際に見た、という目撃の報告が根拠。", "#e0654e"),
    ("scope", "対象と順番に異議", "青切符自体は否定せず、対象を絞れ・整備と周知が先だと順序を問う。", "#8b8fd8"),
    ("place", "走る場所がない", "車道も歩道も選べないという、賛否以前の生活上の訴え。", "#4b9cf4"),
    ("distrust", "警察の運用が信用できない", "制度の中身ではなく運用への異議。説明と現場の食い違い。", "#3b6fb0"),
    ("abolish", "制度そのものに反対", "撤回・廃止すべきという立場。うち{sig}件は同一の署名定型文。", "#1e3a6b"),
]

CHECKED_AT = "2026年8月16日"

# change.org の署名文。同じ文面の貼り付けが「制度そのものに反対」を押し上げるため、
# 何件がこれなのかを本文に出す。件数は数え直すので直書きしない。
SIGNATURE_PHRASE = "自転車に対する青切符制度（罰金制度）の導入に強く反対します"

# 取得期間。正典に fetched_at が入っているのは65/181件だけなので実測からは復元できず、
# THEMES.yaml の sample_period（オーナー確認済み）が唯一の出所。ここで直書きすると
# 台帳とページがずれるため、必ず台帳から読む。

# 一次資料に当たって確かめた結果。判定は fact / gap / miss の3種。
# 件数は data/bike-blue-ticket_claim_posts.json の tweet_id から数える。
# 本文の機械抽出をそのまま件数にすると3〜4割ぶん実際より多く出る（無関係な
# 金額や、報道の共有まで拾ってしまう）ので、必ず人が確定したIDを使う。
FACT_CHECKS = [
    {
        "key": "luup",
        "issues": ["ルール曖昧・不信", "免許制要求"],
        "claim": "LUUPは免許不要で野放しなのに、自転車だけ青切符だ",
        "source": "16歳以上・免許不要・ヘルメットは努力義務、まではそのとおり。ただし警察庁は「特定小型原動機付自転車の運転者がした道路交通法の規定に違反する行為も、交通反則通告制度の対象とされました」と明記している。",
        "verdict": "gap",
        "verdict_label": "前提が食い違う",
        "note": "電動キックボードも青切符の対象。「自転車だけ」という前提は資料では成立しない。",
        "url": "https://www.npa.go.jp/bureau/traffic/anzen/tokuteikogata.html",
        "url_label": "警察庁 特定小型原動機付自転車の交通ルール",
    },
    {
        "key": "fine",
        "issues": ["ルール曖昧・不信"],
        "claim": "反則金は6,000円くらい取られる",
        "source": "警察庁が反則行為と金額の一覧を公表している。携帯電話使用等（保持）12,000円、遮断踏切立入り7,000円、信号無視6,000円（点滅信号を無視した場合は5,000円）。最も低い区分は3,000円。",
        "verdict": "fact",
        "verdict_label": "一致する",
        "note": "投稿で挙がる6,000円は、信号無視などの区分と一致する。",
        "url": "https://www.npa.go.jp/bureau/traffic/bicycle/pdf/jitensyahansokukoui.pdf",
        "url_label": "警察庁 自転車をはじめとする軽車両の反則行為と反則金の額（PDF）",
    },
    {
        "key": "age",
        "issues": ["ルール曖昧・不信"],
        "claim": "対象は16歳以上だ",
        "source": "「16歳以上の運転者が対象となります」。16歳未満の違反は「これまで多くの場合、指導警告が行われており、その取扱いに変更はありません」。",
        "verdict": "fact",
        "verdict_label": "正しい",
        "note": "年齢の理解に食い違いは見当たらなかった。",
        "url": "https://www.npa.go.jp/bureau/traffic/bicycle/portal/system.html",
        "url_label": "警察庁 自転車の新しい制度",
    },
    {
        "key": "sidewalk",
        "issues": ["車道走行への不安", "ルール曖昧・不信"],
        "claim": "歩道を少し走っただけで即青切符・罰金",
        "source": "「単に歩道通行をしたといった場合は原則として指導警告の対象です」。悪質・危険な違反や、実際に交通の危険を生じさせた場合が検挙の対象とされている。",
        "verdict": "gap",
        "verdict_label": "食い違う",
        "note": "歩道を走った全員がその場で反則金、という運用は資料からは読み取れない。",
        "url": "https://www.npa.go.jp/bureau/traffic/bicycle/portal/faq.html",
        "url_label": "警察庁 自転車ポータル よくある質問",
    },
    {
        "key": "accident",
        "issues": ["取締り強化賛成"],
        "claim": "自転車の事故は減っている／いや増えている",
        "source": "令和7年中の自転車関連事故は67,470件で、前年より61件減少。減少幅は0.09%にあたる。",
        "verdict": "gap",
        "verdict_label": "どちらの言い方とも合わない",
        "note": "投稿には「めちゃくちゃ減っている」と「死亡事故が増加中」の両方がある。公表値はほぼ横ばいで、増加とも大幅減とも読めない。",
        "url": "https://www.npa.go.jp/bureau/traffic/bicycle/info.html",
        "url_label": "警察庁 自転車は車のなかま",
    },
    {
        "key": "noenforce",
        "issues": ["取締り強化賛成"],
        "claim": "取締りなんて実際にはされていない",
        "source": "令和7年中、警察は自転車利用者に対して約110万件の指導警告票を交付し、約6万件の交通違反を検挙した。",
        "verdict": "gap",
        "verdict_label": "食い違う",
        "note": "警告を含めれば、件数としては相当数が行われている。",
        "url": "https://www.npa.go.jp/bureau/traffic/bicycle/info.html",
        "url_label": "警察庁 自転車は車のなかま",
    },
    {
        "key": "count113",
        "issues": ["ルール曖昧・不信"],
        "claim": "対象になる違反は113種類もある",
        "source": "警察庁が公表している反則行為の一覧を数えると65項目だった。113という数字は、参照した警察庁の資料では確認できなかった。",
        "verdict": "miss",
        "verdict_label": "確認できず",
        "note": "113が別の数え方（罰則のみの違反を含める、条文の号ごとに数えるなど）から出ている可能性を否定できないため、投稿が誤りとは書けない。数え方が公開資料から一意に定まらないこと自体を、そのまま残す。",
        "url": "https://www.npa.go.jp/bureau/traffic/bicycle/pdf/jitensyahansokukoui.pdf",
        "url_label": "警察庁 自転車をはじめとする軽車両の反則行為と反則金の額（PDF）",
    },
]


# 区分をどう決めたか。「なぜこの1件がこの区分か」を代表例で示す部分。
# 77件すべての理由は書かないが、判断の物差しは読者に渡す。
BASIS_START = "<!-- REREAD_BASIS_START -->"
BASIS_END = "<!-- REREAD_BASIS_END -->"

BASIS = {
    "strict": {
        "rule": "青切符を弱いと見て、免許制や講習の義務化など、より強い規制を求めているもの。",
        "cases": [
            ("「免許不要」ってのが制度設計上の最大のミス", "制度の欠陥を「罰が軽い」ではなく「学ぶ機会がない」と見ている。撤回ではなく上乗せの要求。"),
            ("青切符だけでは改善されないので、購入前に道路交通法の講習を義務付けるべき", "青切符を否定せず、その手前に義務を足せと言っている。"),
        ],
    },
    "scope": {
        "rule": "青切符そのものは認めたうえで、対象の広さか、着手の順番に異議を唱えているもの。",
        "cases": [
            ("青切符がダメな訳じゃねぇんだよなぁ", "制度の否定を本人が明示的に打ち消している。続けて「強行した事」が問題だと書く。"),
            ("青切符は例えばスマホしながらとか信号無視なんかは良いと思うんですが", "一部の違反は取締り対象として認めている。範囲の議論であって是非の議論ではない。"),
            ("無灯火・逆走・ながらスマホくらいに絞って開始して", "対象を絞れという要求そのもの。"),
        ],
    },
    "place": {
        "rule": "制度への賛否ではなく、どこを走ればよいのか分からないという体験が中心のもの。",
        "cases": [
            ("子供前後に載せてる自転車も車道走らないと罰則なんでしょう？", "評価ではなく、自分の身に起きることへの問い。"),
            ("路駐だらけの車道を走るのは、本当に怖いです", "反対の理由ではなく、走行環境の描写。"),
        ],
    },
    "distrust": {
        "rule": "制度の中身ではなく、警察の運用や動機に疑いを向けているもの。",
        "cases": [
            ("複数回や重大な違反でない限り切符切らないとか言ってなかったっけ…？", "説明と現場の食い違いを問題にしている。制度設計そのものへの反対ではない。"),
            ("全部摘発したら反則金だけで国の借金1200兆円を返済できてしまうのでは", "動機への疑い。金額の主張ではないため、事実確認の対象にも入れていない。"),
        ],
    },
    "abolish": {
        "rule": "撤回・廃止を求めているもの。理由を書かずに反対だけを表明したものもここに入れる。",
        "cases": [
            ("いっそ辞めてもむしろみんな喜ぶよ", "制度の存続そのものを否定している。"),
            ("自転車に対する青切符制度（罰金制度）の導入に強く反対します", "オンライン署名の定型文。理由が書かれていないため、内容では他の区分に振り分けられない。同じ文面が{sig}件。"),
        ],
    },
}


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def load(input_path: Path | None = None) -> tuple[list[dict], dict, dict]:
    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
    theme = themes[THEME]
    period = str(theme.get("sample_period") or "").strip()
    if not period or period.lower() == "unknown":
        raise SystemExit("THEMES.yaml の bike-blue-ticket に sample_period がありません")
    samples = json.loads((input_path or ROOT / theme["sample_file"]).read_text(encoding="utf-8"))
    config = yaml.safe_load((ROOT / theme["refresh_config"]).read_text(encoding="utf-8"))
    reread = json.loads((ROOT / "data" / f"{THEME}_opposition_reread.json").read_text(encoding="utf-8"))
    claim_posts = json.loads((ROOT / "data" / f"{THEME}_claim_posts.json").read_text(encoding="utf-8"))
    return samples, config, reread, claim_posts, period


class RereadGapError(SystemExit):
    """再読マッピングが正典の「反対」を覆っていないときに投げる。

    これは失敗させるための設計であって、直せるバグではない。ページの中心的な主張
    （「反対はひとつの塊ではない」）は、編集部が反対投稿を1件ずつ読んで5区分へ
    割り当てた結果に載っている。読み直さずに新しい件数だけ入れ替えると、古い割り当ての
    まま新しい数字が表示される。読む工程は自動化できないので、ここで止める。
    """


def check_reread_coverage(samples: list[dict], reread: dict) -> None:
    """正典の「反対」と再読マッピングを tweet_id で突き合わせる。

    件数の一致だけでは、1件足して1件消したような入れ替わりを見逃す。
    未再読の投稿は tweet_id を並べて出す。そのまま
    data/bike-blue-ticket_opposition_reread.json の該当区分へ追記できる。
    """
    oppose_ids = {
        s["tweet_id"] for s in samples
        if s["classification"]["stance"] == "反対（インフラ・制度優先）"
    }
    assigned: dict[str, str] = {}
    duplicated: list[str] = []
    for bucket, ids in reread["buckets"].items():
        for tid in ids:
            if tid in assigned:
                duplicated.append(f"{tid}({assigned[tid]}/{bucket})")
            assigned[tid] = bucket

    missing = sorted(oppose_ids - set(assigned))
    extra = sorted(set(assigned) - oppose_ids)
    if not (missing or extra or duplicated):
        return

    by_id = {s["tweet_id"]: s for s in samples}
    lines = [
        "再読マッピングが正典の「反対」と一致しません。"
        "編集部が新しい反対投稿を読み、"
        "data/bike-blue-ticket_opposition_reread.json の buckets へ追記してください。",
        f"正典の反対 {len(oppose_ids)}件 / 割り当て済み {len(assigned)}件",
    ]
    if missing:
        lines.append(f"未再読 {len(missing)}件:")
        lines += [
            f"  {tid}  {str(by_id[tid].get('text') or '')[:60].replace(chr(10), ' ')}"
            for tid in missing
        ]
    if extra:
        lines.append(f"正典に無いのに割り当てられている {len(extra)}件: {extra}")
    if duplicated:
        lines.append(f"2つの区分に入っている {len(duplicated)}件: {duplicated}")
    raise RereadGapError("\n".join(lines))


def build_counts(samples: list[dict], reread: dict) -> dict[str, int]:
    stances = [s["classification"]["stance"] for s in samples]
    support = stances.count("賛成（取締り強化支持）")
    oppose = stances.count("反対（インフラ・制度優先）")
    counts = {k: len(v) for k, v in reread["buckets"].items()}
    counts["support"] = support
    check_reread_coverage(samples, reread)
    counts["_oppose"] = oppose
    counts["_total"] = len(samples)
    counts["_sided"] = support + oppose
    counts["_unsided"] = len(samples) - support - oppose
    issues = [s["classification"]["main_issue"] for s in samples if s["classification"]["main_issue"] != "その他"]
    counts["_top_issue"] = max(issues.count(i) for i in set(issues))
    # 「制度そのものに反対」のうち、change.org の署名定型文をそのまま貼った投稿。
    # 数を押し上げている要因なので、件数は毎回本文から数え直して本文に出す。
    by_id = {s["tweet_id"]: s for s in samples}
    counts["_sig"] = sum(
        1 for tid in reread["buckets"]["abolish"]
        if SIGNATURE_PHRASE in by_id[tid]["text"]
    )
    return counts


def build_collect(samples: list[dict], config: dict, counts: dict, period: str) -> str:
    queries = "".join(f"<li>{esc(q)}</li>" for q in config["fetch_queries"])
    return f"""<section id="process-collect" aria-labelledby="process-collect-title">
  <div class="pc-inner">
    <p class="pc-step">STEP 1 — 集め方</p>
    <h2 id="process-collect-title">{counts['_total']}件を、この10本の検索語で集めました</h2>
    <p class="pc-lead">Yahooリアルタイム検索の公開投稿を、下の検索語で取得しています。同じ語を入れれば、読者も同じ範囲を見に行けます。取得期間は{esc(period)}です。</p>
    <ul class="pc-queries">{queries}</ul>
    <div class="pc-funnel">
      <div class="pc-funnel-row"><span>集めて分類できた投稿</span><b>{counts['_total']}</b><span class="pc-unit">件</span></div>
      <div class="pc-funnel-row" data-drop="1"><span>賛否が読み取れなかった（ニュース共有・日常の記録など）</span><b>−{counts['_unsided']}</b><span class="pc-unit">件</span></div>
      <div class="pc-funnel-row" data-keep="1"><span>このページで立場として数えた投稿</span><b>{counts['_sided']}</b><span class="pc-unit">件</span></div>
    </div>
    <p class="pc-note">内訳は賛成{counts['support']}件・反対{counts['_oppose']}件。分類はAIが行い、そのあと編集部が反対{counts['_oppose']}件すべてに、本文を読んで区分を割り当てています（データを追加するたびに、増えた分を読み足しています）。割り当ては<a href="#process-table">全件表</a>で1件ずつ確認できます。</p>
  </div>
</section>"""


def build_verify(samples: list[dict], counts: dict, claim_posts: dict) -> str:
    cards = []
    known = {s["tweet_id"] for s in samples}
    for check in FACT_CHECKS:
        ids = claim_posts["claims"][check["key"]]
        unknown = [i for i in ids if i not in known]
        if unknown:
            raise SystemExit(f"{check['key']}: 正典に無い tweet_id があります: {unknown}")
        cards.append(f"""      <article class="pv-card" data-verdict="{check['verdict']}">
        <div class="pv-head">
          <p class="pv-claim">{esc(check['claim'])}</p>
          <span class="pv-count">{len(ids)}件の投稿</span>
        </div>
        <div class="pv-body">
          <p class="pv-source"><strong>一次資料はどう書いているか。</strong>{esc(check['source'])}</p>
          <p class="pv-note"><span class="pv-verdict">{esc(check['verdict_label'])}</span>{esc(check['note'])}</p>
          <p class="pv-src"><a href="{check['url']}" target="_blank" rel="noopener noreferrer">{esc(check['url_label'])}</a></p>
        </div>
      </article>""")
    body = "\n".join(cards)
    return f"""<section id="process-verify" aria-labelledby="process-verify-title">
  <div class="pc-inner">
    <p class="pc-step">STEP 2 — 確かめ方</p>
    <h2 id="process-verify-title">投稿が言っていることを、警察庁の資料と突き合わせました</h2>
    <p class="pc-lead">投稿の中で事実として確かめられる主張を7つ選び、警察庁の公表資料に1つずつ当たっています。確認できなかったものも、確認できなかったまま残しています。確認日は{CHECKED_AT}です。</p>
    <div class="pv-grid">
{body}
    </div>
    <p class="pc-note">件数の数え方：本文をキーワードで拾っただけでは、無関係な金額（ポイ捨ての過料、ヘルメット購入補助）や報道の共有まで混ざり、実際より3〜4割多く出ます。そのため候補を1件ずつ読み、実際にその主張をしている投稿だけを残して数えています。賛成・反対どちらの投稿も含みます。</p>
  </div>
</section>"""


def build_found(counts: dict) -> str:
    sided = counts["_sided"]
    segs = []
    labels = []
    # 「分解前」は賛成が左端でひと塊に見える必要がある。strict と support の位置を
    # 互いの幅ぶんだけ入れ替えて描き、再生でそれを解く。ずらす量は自分の幅に対する
    # 割合なので、画面幅が変わっても比率が崩れない。
    strict_pct = counts["strict"] / sided * 100
    support_pct = counts["support"] / sided * 100
    shifts = {
        "strict": f"{support_pct / strict_pct * 100:.3f}%",
        "support": f"{-(strict_pct / support_pct * 100):.3f}%",
    }
    for key, title, desc, color in BUCKET_META:
        n = counts[key]
        pct = n / sided * 100
        side = "support" if key == "support" else "oppose"
        shift = f";--seg-shift:{shifts[key]}" if key in shifts else ""
        segs.append(
            f'<span class="pf-seg" data-key="{key}" data-side="{side}" style="--seg-w:{pct:.3f}%;--seg-c:{color}{shift}"></span>'
        )
        labels.append(
            f"""        <li class="pf-label" data-key="{key}"><span class="pf-swatch" style="background:{color}"></span>
          <b>{n}件</b><strong>{esc(title)}</strong><span>{esc(desc.replace("{sig}", str(counts["_sig"])))}</span></li>"""
        )
    abolish_pct = counts["abolish"] / sided * 100
    return f"""<section id="process-found" aria-labelledby="process-found-title">
  <div class="pc-inner">
    <p class="pc-step">STEP 3 — 分かったこと</p>
    <h2 id="process-found-title">「反対{counts['_oppose']}件」は、ひとつの塊ではありませんでした</h2>
    <p class="pc-lead">数えるだけなら、賛成{counts['support']}件に対して反対{counts['_oppose']}件。反対が2倍です。ところが本文を読むと、その内訳は同じ方向を向いていません。</p>

    <div class="pf-stage" id="pf-stage" data-state="before">
      <div class="pf-track" aria-hidden="true">{''.join(segs)}</div>
      <p class="pf-caption" data-caption-before>いまの数え方：賛成{counts['support']}件（{counts['support'] / sided * 100:.0f}%）と、反対{counts['_oppose']}件（{counts['_oppose'] / sided * 100:.0f}%）。</p>
      <p class="pf-caption" data-caption-after>読み直したあと：反対{counts['_oppose']}件は6つに分かれ、うち{counts['strict']}件は「青切符では甘い、免許制にしろ」と、賛成側より外側の要求でした。取締りそのものをやめろと読めるのは{counts['abolish']}件（{abolish_pct:.0f}%）で、そのうち{counts['_sig']}件は同じ署名の定型文です。</p>
      <button type="button" class="pf-replay" id="pf-replay"><span aria-hidden="true">▶</span>賛成{counts['support']}＋反対{counts['_oppose']}を、6区分に組み替える</button>
      <ol class="pf-labels">
{chr(10).join(labels)}
      </ol>
    </div>

    <p class="pf-conclusion">立場が読み取れた{sided}件のうち、危険な運転を取り締まること自体を否定していると読めるのは{counts['abolish']}件でした。多数派が問うているのは「やるかやらないか」ではなく、<strong>どこまでを対象にするか、どの順番で進めるか</strong>です。賛成の理由と反対の理由を左右に並べる形にしなかったのは、そこに線が引かれていなかったからです。</p>
    <p class="pc-note">この内訳はSNS投稿サンプルの構成であり、社会全体の割合ではありません。同じ人が複数回投稿している可能性、署名の定型文が数を押し上げている可能性は、公開情報だけでは排除できていません。「整備が先だ」と書いた人が整備後に取締りを受け入れるかどうかも、投稿からは分かりません。</p>
  </div>
</section>"""


def build_table(samples: list[dict], reread: dict, counts: dict) -> str:
    by_id = {s["tweet_id"]: s for s in samples}
    titles = {k: t for k, t, _d, _c in BUCKET_META}
    colors = {k: c for k, _t, _d, c in BUCKET_META}
    rows = []
    hidden = 0
    for key, _title, _desc, _color in BUCKET_META:
        if key == "support":
            continue
        for tid in reread["buckets"][key]:
            s = by_id[tid]
            c = s["classification"]
            safe = c["article_usable"] and c["risk"] == "low"
            if safe:
                excerpt = re.sub(r"\s+", " ", s["text"]).strip()
                excerpt = re.sub(r"https?://\S+", "", excerpt).strip()
                excerpt = esc(excerpt[:78] + ("…" if len(excerpt) > 78 else ""))
            else:
                hidden += 1
                excerpt = '<span class="pt-hidden">本文の掲載は見送り（表現に配慮が必要と判定）</span>'
            rows.append(
                f'<tr><td class="pt-ex">{excerpt}</td>'
                f'<td class="pt-ai">{esc(c["main_issue"])}</td>'
                f'<td class="pt-bd"><span class="pt-dot" style="background:{colors[key]}"></span>{esc(titles[key])}</td>'
                f'<td class="pt-link"><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">𝕏</a></td></tr>'
            )
    return f"""<section id="process-table" aria-labelledby="process-table-title">
  <div class="pc-inner">
    <details class="pt-details">
      <summary id="process-table-title">読み直した反対{counts['_oppose']}件を、1件ずつ確認する</summary>
      <p class="pc-lead">AIが付けた論点と、編集部が割り当てた区分を並べています。1件は1区分にのみ数えています。{hidden}件は、AIが表現に配慮が必要と判定したため本文の抜粋を載せず、投稿へのリンクだけにしています。</p>
      <div class="pt-wrap">
        <table>
          <thead><tr><th>投稿（抜粋）</th><th>AIが付けた論点</th><th>編集部の区分</th><th>原文</th></tr></thead>
          <tbody>
{chr(10).join('            ' + r for r in rows)}
          </tbody>
        </table>
      </div>
    </details>
  </div>
</section>"""


def build_basis(counts: dict) -> str:
    titles = {k: t for k, t, _d, _c in BUCKET_META}
    colors = {k: c for k, _t, _d, c in BUCKET_META}
    blocks = []
    for key, _t, _d, _c in BUCKET_META:
        if key not in BASIS:
            continue
        basis = BASIS[key]
        cases = "".join(
            f'<li><q>{esc(q)}</q><span>{esc(why.replace(chr(123) + "sig" + chr(125), str(counts["_sig"])))}</span></li>' for q, why in basis["cases"]
        )
        blocks.append(f"""      <article class="rb-card">
        <h3><span class="rb-dot" style="background:{colors[key]}"></span>{esc(titles[key])}<b>{counts[key]}件</b></h3>
        <p class="rb-rule">{esc(basis['rule'])}</p>
        <ul class="rb-cases">{cases}</ul>
      </article>""")
    body = "\n".join(blocks)
    return f"""{BASIS_START}
<style id="reread-basis-css">
#reread-basis{{padding:8px min(6vw,72px) 30px;background:var(--bg)}}
#reread-basis .rb-inner{{max-width:1000px;margin:0 auto}}
#reread-basis h2{{font-size:clamp(19px,3.2vw,24px);line-height:1.5;margin:0 0 8px;color:var(--ink)}}
#reread-basis .rb-lead{{font-size:13.5px;line-height:1.9;color:var(--muted);margin:0 0 16px}}
#reread-basis .rb-grid{{display:grid;gap:11px}}
#reread-basis .rb-card{{border:1px solid var(--line);border-radius:12px;background:var(--panel);padding:14px 16px}}
#reread-basis .rb-card h3{{display:flex;align-items:baseline;gap:8px;margin:0 0 6px;font-size:15px;font-weight:900;color:var(--ink)}}
#reread-basis .rb-card h3 b{{margin-left:auto;color:var(--accent);font-variant-numeric:tabular-nums;white-space:nowrap}}
#reread-basis .rb-dot{{width:10px;height:10px;border-radius:3px;align-self:center}}
#reread-basis .rb-rule{{margin:0 0 10px;font-size:13px;line-height:1.85;color:var(--ink)}}
#reread-basis .rb-rule::before{{content:"物差し：";font-weight:900;color:var(--muted);font-size:12px}}
#reread-basis .rb-cases{{list-style:none;margin:0;padding:0;display:grid;gap:8px}}
#reread-basis .rb-cases li{{border-left:3px solid var(--line);padding-left:11px}}
#reread-basis .rb-cases q{{display:block;font-size:13px;line-height:1.8;color:var(--ink);font-weight:700;quotes:"「" "」"}}
#reread-basis .rb-cases span{{display:block;margin-top:3px;font-size:12.5px;line-height:1.8;color:var(--muted)}}
#reread-basis .rb-note{{margin:14px 0 0;font-size:12px;line-height:1.9;color:var(--muted)}}
#reread-basis .thirty-summary{{display:block!important;margin:14px 0 0!important;max-width:none!important;grid-template-columns:none!important}}
#reread-basis .thirty-summary-title{{display:none!important}}
#reread-basis .thirty-summary ul{{display:block!important;margin:0!important;padding:0!important}}
#reread-basis .thirty-summary li{{list-style:none;display:flex!important;align-items:baseline;gap:10px;flex-wrap:wrap;background:var(--accent-soft)!important;border:1px solid var(--line)!important;border-radius:10px;padding:12px 15px!important;color:var(--ink)!important;min-height:0!important}}
#reread-basis .thirty-summary li::before,#reread-basis .thirty-summary li::after{{content:none!important;display:none!important}}
#reread-basis .thirty-summary .conclusion-count{{color:var(--accent)!important;font-weight:900;font-size:13px!important;white-space:nowrap;background:none!important;padding:0!important;position:static!important;top:auto!important;right:auto!important;border:0!important}}
#reread-basis .thirty-summary .conclusion-count b{{font-size:20px}}
#reread-basis .thirty-summary .conclusion-focus strong{{font-size:14px!important;font-weight:800;color:var(--ink)!important}}
#reread-basis .thirty-summary .conclusion-detail{{flex:1 1 100%;font-size:12.5px!important;line-height:1.8;color:var(--muted)!important;font-weight:500}}
@media (max-width:720px){{#reread-basis{{padding:4px 14px 24px}}}}
</style>
<section id="reread-basis" aria-labelledby="reread-basis-title">
  <div class="rb-inner">
    <h2 id="reread-basis-title">その1件を、どうやってその区分に入れたか</h2>
    <p class="rb-lead">冒頭の内訳は編集部の読み直しによるものです。判断が妥当かどうかを読者が確かめられるよう、区分ごとの物差しと、実際に決め手になった文言を挙げます。</p>
    <div class="rb-grid">
{body}
    </div>
    <div class="thirty-summary" aria-label="SNS投稿で最も多かった論点"><header class="thirty-summary-title"><h2>議論の中心</h2></header><ul>
      <li class="conclusion-focus"><span class="conclusion-count"><b>{counts['_top_issue']}</b>件</span><strong>AIによる5論点の分類では「取締り強化賛成」が最多</strong><span class="conclusion-detail">歩道の暴走や信号無視の実害を挙げ、取締りの強化を支持する声です。これはSNS投稿サンプルの内訳であり、賛否の結論ではありません。</span></li>
    </ul></div>
    <p class="rb-note">読み直したのは反対{counts['_oppose']}件だけです。賛成{counts['support']}件はAIの分類のまま扱っており、同じ精度で見直してはいません。1件は1区分にのみ数えています。全{counts['_oppose']}件の割り当ては<a href="#process-table">全件表</a>にあります。</p>
  </div>
</section>
{BASIS_END}"""


CSS = """<style id="process-sections-css">
#process-collect,#process-verify,#process-found,#process-table{padding:26px min(6vw,72px) 6px;background:var(--bg)}
#process-table{padding-bottom:30px}
.pc-inner{max-width:1000px;margin:0 auto}
.pc-step{display:inline-block;margin:0 0 10px;padding:5px 12px;border-radius:999px;background:var(--accent-soft);color:var(--accent);font-size:11.5px;font-weight:900;letter-spacing:.06em}
#process-collect h2,#process-verify h2,#process-found h2{font-size:clamp(20px,3.5vw,27px);line-height:1.5;margin:0 0 10px;color:var(--ink)}
.pc-lead{font-size:14px;line-height:1.95;color:var(--muted);margin:0 0 16px}
.pc-note{margin:14px 0 0;font-size:12px;line-height:1.9;color:var(--muted)}
.pc-note a,.pc-lead a{color:var(--accent)}
.pc-queries{display:flex;flex-wrap:wrap;gap:7px;list-style:none;margin:0 0 16px;padding:0}
.pc-queries li{font-size:12.5px;font-weight:700;color:var(--ink);background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:6px 13px}
.pc-queries li::before{content:"検索";font-size:10px;font-weight:900;color:var(--muted);margin-right:6px}
.pc-funnel{border:1px solid var(--line);border-radius:12px;background:var(--panel);overflow:hidden}
.pc-funnel-row{display:flex;align-items:baseline;gap:10px;padding:12px 15px;border-top:1px solid var(--line);font-size:13.5px;line-height:1.7;color:var(--ink)}
.pc-funnel-row:first-child{border-top:0}
.pc-funnel-row span:first-child{flex:1}
.pc-funnel-row b{font-size:21px;font-weight:900;font-variant-numeric:tabular-nums}
.pc-funnel-row .pc-unit{font-size:12px;color:var(--muted)}
.pc-funnel-row[data-drop] {color:var(--muted)}
.pc-funnel-row[data-drop] b{color:var(--muted)}
.pc-funnel-row[data-keep]{background:var(--accent-soft)}
.pc-funnel-row[data-keep] b{color:var(--accent)}
.pv-grid{display:grid;gap:11px}
.pv-card{border:1px solid var(--line);border-left:4px solid var(--line);border-radius:0 12px 12px 0;background:var(--panel);padding:15px 17px}
.pv-card[data-verdict="fact"]{border-left-color:#15803d}
.pv-card[data-verdict="gap"]{border-left-color:#b45309}
.pv-card[data-verdict="miss"]{border-left-color:#64748b}
.pv-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:0 0 9px}
.pv-claim{margin:0;font-size:15px;font-weight:900;line-height:1.6;color:var(--ink)}
.pv-claim::before{content:"投稿：「";color:var(--muted);font-weight:700;font-size:12px}
.pv-claim::after{content:"」";color:var(--muted);font-weight:700;font-size:12px}
.pv-count{font-size:11.5px;font-weight:800;color:var(--muted);white-space:nowrap}
.pv-body p{margin:0 0 7px;font-size:13.5px;line-height:1.9;color:var(--ink)}
.pv-body p:last-child{margin-bottom:0}
.pv-source strong{font-weight:900}
.pv-note{color:var(--muted)!important}
.pv-verdict{display:inline-block;margin-right:8px;padding:2px 9px;border-radius:999px;font-size:11.5px;font-weight:900;color:#fff}
.pv-card[data-verdict="fact"] .pv-verdict{background:#15803d}
.pv-card[data-verdict="gap"] .pv-verdict{background:#b45309}
.pv-card[data-verdict="miss"] .pv-verdict{background:#64748b}
.pv-src{font-size:12px}
.pv-src a{color:var(--muted)}
.pf-stage{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:18px 18px 16px}
.pf-track{display:flex;width:100%;height:34px;border-radius:8px;overflow:hidden;background:rgba(15,23,42,.06)}
.pf-seg{width:var(--seg-w);background:var(--seg-c);transition:background-color .5s ease,transform .7s cubic-bezier(.22,.61,.36,1),opacity .4s ease;will-change:transform}
.pf-stage[data-state="before"] .pf-seg[data-side="oppose"]{background:#3b6fb0}
.pf-stage[data-state="before"] .pf-seg[data-side="support"]{background:#e0654e}
.pf-stage[data-state="before"] .pf-seg[data-key="strict"],
.pf-stage[data-state="before"] .pf-seg[data-key="support"]{transform:translateX(var(--seg-shift))}
.pf-stage[data-state="after"] .pf-seg{background:var(--seg-c);transform:none}
.pf-caption{margin:12px 0 0;font-size:13px;line-height:1.9;color:var(--ink)}
.pf-stage[data-state="before"] [data-caption-after]{display:none}
.pf-stage[data-state="after"] [data-caption-before]{display:none}
.pf-replay{margin:12px 0 0;padding:8px 16px;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--ink);font-size:12.5px;font-weight:800;cursor:pointer}
.pf-replay span{margin-right:6px;color:var(--accent)}
.pf-replay:hover{border-color:var(--accent)}
.pf-labels{list-style:none;margin:14px 0 0;padding:0;display:grid;gap:8px}
.pf-label{display:grid;grid-template-columns:12px auto 1fr;align-items:baseline;gap:9px;font-size:13px;line-height:1.75;opacity:0;transform:translateY(4px);transition:opacity .45s ease,transform .45s ease}
.pf-stage[data-state="after"] .pf-label{opacity:1;transform:none}
.pf-label b{font-weight:900;font-variant-numeric:tabular-nums;white-space:nowrap;color:var(--accent)}
.pf-label strong{font-weight:800;color:var(--ink)}
.pf-label span:last-child{grid-column:2/-1;color:var(--muted);font-size:12.5px}
.pf-swatch{width:12px;height:12px;border-radius:3px;align-self:center}
.pf-conclusion{margin:18px 0 0;font-size:15px;line-height:2;color:var(--ink)}
.pf-conclusion strong{font-weight:900;background:linear-gradient(transparent 62%,var(--accent-soft) 62%)}
.pt-details{border:1px solid var(--line);border-radius:12px;background:var(--panel);padding:0 16px}
.pt-details>summary{cursor:pointer;padding:14px 0;font-size:14px;font-weight:800;color:var(--ink)}
.pt-details[open]>summary{border-bottom:1px solid var(--line);margin-bottom:14px}
.pt-details .pc-lead{margin-top:0}
.pt-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:0 0 16px}
.pt-wrap table{width:100%;border-collapse:collapse;font-size:12.5px;min-width:640px}
.pt-wrap th,.pt-wrap td{white-space:normal;text-align:left;vertical-align:top;padding:9px 11px;border-right:0;border-bottom:1px solid var(--line);line-height:1.75}
.pt-wrap thead th{font-size:11.5px;font-weight:900;color:var(--muted);background:rgba(15,23,42,.04)}
.pt-wrap td.pt-ex{color:var(--ink);width:46%}
.pt-wrap td.pt-ai,.pt-wrap td.pt-bd{color:var(--muted);width:22%;white-space:nowrap}
.pt-wrap td.pt-link{width:10%}
.pt-wrap td.pt-link a{color:var(--accent);font-weight:800;text-decoration:none}
.pt-dot{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:6px}
.pt-hidden{color:var(--muted);font-style:normal}
@media (max-width:720px){
  #process-collect,#process-verify,#process-found,#process-table{padding-left:14px;padding-right:14px}
  .pf-track{height:28px}
  .pf-label{grid-template-columns:12px auto;font-size:12.5px}
  .pt-wrap table{min-width:520px}
}
@media (prefers-reduced-motion:reduce){
  .pf-seg,.pf-label{transition:none}
}
</style>"""

SCRIPT = """<script id="process-found-anim">
(() => {
  const stage = document.getElementById('pf-stage');
  if (!stage) return;
  const replay = document.getElementById('pf-replay');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let played = false;
  const play = () => {
    stage.dataset.state = 'before';
    if (reduced) { stage.dataset.state = 'after'; return; }
    window.setTimeout(() => { stage.dataset.state = 'after'; }, 700);
  };
  replay.addEventListener('click', play);
  if (!('IntersectionObserver' in window)) { stage.dataset.state = 'after'; return; }
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting || played) return;
      played = true;
      play();
      io.disconnect();
    });
  }, { threshold: 0.35 });
  io.observe(stage);
})();
</script>"""


# 冒頭3セクションの件数は、賛成のAI分類と反対の編集再読を併記している。
# この数値出所配列全体を本文再読の台帳として扱わない。各行に根拠種別を付ける。
# 数字の出所検査（scripts/verify_number_provenance.py）は「レコードの配列」しか正典に
# できないため、割り当てを配列の形で書き出しておく。ページと同じ手順で作るので、
# 読み直しを足し忘れればここも一緒にずれ、検査で落ちる。
def write_provenance_records(
    samples: list[dict], reread: dict, claim_posts: dict, destination: Path | None = None
) -> None:
    support_ids = [
        s["tweet_id"] for s in samples
        if s["classification"]["stance"] == "賛成（取締り強化支持）"
    ]
    by_id = {s["tweet_id"]: s for s in samples}

    def row(tid: str, bucket: str) -> dict:
        s = by_id[tid]
        c = s["classification"]
        listed = bucket != "support"  # 全件表に載るのは反対の5区分だけ
        shown = c["article_usable"] and c["risk"] == "low"
        return {
            "tweet_id": tid,
            "bucket": bucket,
            "review_kind": "editorial_body_reread" if listed else "automated_classification",
            "body_reviewed": listed,
            # 本文に出る「うちN件は署名の定型文」「N件は抜粋を載せず」を、この配列から数える。
            # ページに出るのと同じ範囲でだけ "yes" / "hidden" にする。範囲を広げると、
            # 数字の出所検査（1次元の集計）とページの数字が合わなくなる。
            "signature": "yes" if bucket == "abolish" and SIGNATURE_PHRASE in s["text"] else "no",
            "excerpt": ("shown" if shown else "hidden") if listed else "not_listed",
        }

    rows = [row(tid, "support") for tid in support_ids]
    for key, ids in reread["buckets"].items():
        rows += [row(tid, key) for tid in ids]
    claims = [
        {"tweet_id": tid, "claim": key}
        for key, ids in claim_posts["claims"].items()
        for tid in ids
    ]
    out = destination or ROOT / "data" / "verification"
    out.mkdir(parents=True, exist_ok=True)
    for name, data in (("bike-blue-ticket-reread", rows), ("bike-blue-ticket-claims", claims)):
        (out / f"{name}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
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

    samples, config, reread, claim_posts, period = load(args.input)
    counts = build_counts(samples, reread)
    blocks = "\n\n".join([
        CSS,
        build_collect(samples, config, counts, period),
        build_verify(samples, counts, claim_posts),
        build_found(counts),
        build_table(samples, reread, counts),
        SCRIPT,
    ])
    public_path = ROOT / "docs" / f"{THEME}-reaction-map.html"
    template_path = args.html_template or public_path
    page_path = args.output_html or public_path
    page = template_path.read_text(encoding="utf-8")
    for a, b in ((START, END), (BASIS_START, BASIS_END)):
        if page.count(a) != 1 or page.count(b) != 1:
            raise SystemExit(f"{a} / {b} が1つずつ必要です")
    head, rest = page.split(START, 1)
    _old, tail = rest.split(END, 1)
    page = f"{head}{START}\n{blocks}\n{END}{tail}"

    head, rest = page.split(BASIS_START, 1)
    _old, tail = rest.split(BASIS_END, 1)
    page = f"{head}{build_basis(counts)}{tail}"

    # 生成後の自己検証
    checks = [
        (f">{counts['_total']}件を、この10本", "STEP1の総件数"),
        (f"賛成{counts['support']}件・反対{counts['_oppose']}件", "STEP1の内訳"),
        ('data-verdict="miss"', "確認できなかった主張のカード"),
        (CHECKED_AT, "事実確認の確認日"),
        ("pf-seg", "STEP3の帯"),
        ("process-found-anim", "STEP3のスクリプト"),
        ("rb-cases", "区分の根拠"),
        (f"取得期間は{period}です", "STEP1の取得期間"),
    ]
    for needle, label in checks:
        if needle not in page:
            raise SystemExit(f"生成結果に {label} が見つかりません: {needle}")
    # 取得期間はページ内の2か所（調査条件ブロックとSTEP1）に出る。台帳を更新する前に
    # このスクリプトを流すと、STEP1だけ古い期間で残る（2026-08-17に発生し、公開された）。
    # 台帳と違う期間がページのどこかに残っていたら、ここで落とす。
    stale = {m for m in re.findall(r"取得期間[:：はが]?\s*(\d{4}-\d{2}-\d{2}〜\d{4}-\d{2}-\d{2})", page)} - {period}
    if stale:
        raise SystemExit(
            f"台帳の取得期間は {period} ですが、ページに別の期間が残っています: {sorted(stale)}。"
            "先に THEMES.yaml の sample_period を直し、調査条件ブロックも作り直すこと"
        )
    seg_total = sum(float(m) for m in re.findall(r"--seg-w:([\d.]+)%", page))
    if abs(seg_total - 100) > 0.01:
        raise SystemExit(f"帯の合計が100%になりません: {seg_total}")
    if page.count('class="conclusion-count"') != 1:
        raise SystemExit("conclusion-count は1つだけ必要です")

    write_provenance_records(samples, reread, claim_posts, args.verification_dest)
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_text(page, encoding="utf-8")
    claim_total = sum(len(v) for v in claim_posts["claims"].values())
    print(f"OK  {page_path.name} を更新（母数{counts['_total']}件 / 立場{counts['_sided']}件 / 反対{counts['_oppose']}件 / 事実確認の該当投稿{claim_total}件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
