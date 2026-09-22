#!/usr/bin/env python3
"""自転車青切符ページの、正典から導ける部分をまとめて作り直す。

    python3 scripts/build_bike_arena.py
    python3 scripts/build_bike_arena.py --check
    python3 scripts/build_bike_arena.py --input ... --html-template ... --output-html ...

2026-08-17 まで、ここで生成する場所はすべて手書きだった。更新のたびに十数か所を
手で書き換えていて、書き換え漏れがそのまま公開されうる状態だった。

生成するのは次の5か所だけ。ページの文章そのものは生成しない。

    1. アリーナの点（SM_RAW）
    2. アリーナ見出しの「N件 | セクター=論点 …」
    3. 注目ポイント4枚（insight-stats）
    4. 論点ごとの帯（temp-bar）と内訳（issue-sides）を含む論点ブロック5本
    5. 「本当の対立点」段落の論点別件数

**ここが書かない場所**（1つの文の書き手は1つ）:

    論点カード・論点ナビ・議論の中心・アリーナのセクター配列・リード文
        → scripts/sync_issue_counts.py
    冒頭3セクション・全件表・区分の根拠
        → scripts/build_bike_process_sections.py
    調査条件ブロック・信頼性メタ
        → scripts/seo/apply_theme_trust.py
    世論の潮目
        → scripts/refresh_adapters/bike.py（更新回どうしの比較）
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from .issue_card_counts import IssueCountError
    from .sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml
    from .x_embed import embed_html
except ImportError:
    from issue_card_counts import IssueCountError  # type: ignore[no-redef]
    from sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml  # type: ignore[no-redef]
    from x_embed import embed_html  # type: ignore[no-redef]

THEME = "bike-blue-ticket"
PUBLIC_THEME = ROOT / "data" / "public" / "themes" / f"{THEME}.json"

# ページ内 const ISSUES=[…] と同じ並び。ここがずれるとセクターと点が食い違う。
ISSUE_ORDER = (
    "取締り強化賛成",
    "インフラ整備優先",
    "車道走行への不安",
    "免許制要求",
    "ルール曖昧・不信",
    "その他",
)
# 「その他」を除いた5論点。ページが「5つの論点に分類できたN件」と書く母数。
MAIN_ISSUES = ISSUE_ORDER[:-1]

SUPPORT = "賛成（取締り強化支持）"
NEUTRAL = "どちらでもない"
OPPOSE = "反対（インフラ・制度優先）"
STANCE_ORDER = (SUPPORT, NEUTRAL, OPPOSE)
STANCE_X = {SUPPORT: 2.0, NEUTRAL: 0.0, OPPOSE: -2.0}
INTENSITY_E = {"low": 0.5, "medium": 1.2, "high": 2.0}

# 注目ポイントの3枚目「最も話された論点」に出す短いラベルと、その説明文。
# 論点そのものの説明なので、件数が変わっても文章は変わらない。
SHORT_LABEL = {
    "取締り強化賛成": "取締り強化",
    "インフラ整備優先": "インフラ整備",
    "車道走行への不安": "車道走行",
    "免許制要求": "免許・講習",
    "ルール曖昧・不信": "ルール曖昧",
}
TOP_ISSUE_NOTE = {
    "取締り強化賛成": "危険運転やマナー違反を止めたいという声",
    "インフラ整備優先": "走れる道を先に用意すべきだという声",
    "車道走行への不安": "車道を走れというルールへの不安の声",
    "免許制要求": "罰則より先に学ぶ機会を求める声",
    "ルール曖昧・不信": "違反の基準と運用への不信の声",
}

# 論点ブロック5本。件数以外（見出し・説明・代表投稿）は編集部が決めた内容で、
# データが増えても変わらない。件数と帯の幅だけを毎回数え直す。
#
# sides は3つのスタンスをちょうど1回ずつ覆うこと（下の _check_definitions が検査する）。
# 覆えていないスタンスがあると、その件数がページのどこにも出ないまま消える。
BLOCKS: tuple[dict[str, Any], ...] = (
    {
        "issue": "取締り強化賛成",
        "anchor": "issue-torishimari",
        "heading": "取締り強化賛成・マナー違反を止めよ",
        "temp_label": "取締り強化への姿勢",
        "temp_names": ("取締り支持", "中立", "反対"),
        "legend": ("取締り強化を支持", "中立", "慎重・反対"),
        "desc": "信号無視・ながらスマホ・歩道の無謀走行など、自転車の危険行為を止めるために取り締まりは当然という立場。「歩行者が怖い思いをしている」という視点から、青切符による制裁強化を支持します。",
        "sides": (
            ("neg", "取締り強化支持", (SUPPORT,), "マナーの悪い自転車をこのまま放置するのはおかしい。事故が起きてからでは遅い。"),
            ("pos", "中立・反対", (NEUTRAL, OPPOSE), "取締りの話題に触れつつ、賛否を示さない投稿と、進め方に異議を示す投稿。"),
        ),
        "samples": (
            ("取締り支持 / 感情やや高め", "無法状態の自転車に怒り、青切符でも甘いとして厳格な対応を要求", "https://x.com/shocker108/status/2061387437340045705"),
            ("取締り支持 / 安全優先", "自転車の一時不停止に怒り、厳格な取り締まりを強く求める", "https://x.com/bjayway/status/2070305605852836233"),
        ),
    },
    {
        "issue": "インフラ整備優先",
        "anchor": "issue-infra",
        "heading": "インフラ整備が先・専用レーンなしに取締りは不公平",
        "temp_label": "インフラ整備への立場",
        "temp_names": ("取締り寄り", "中立", "インフラ優先"),
        "legend": ("取締り支持（条件付き含む）", "中立", "インフラ整備が先"),
        "desc": "「安全に走れる自転車専用レーンがないのに、車道を走れというのは無理だ」という立場。インフラ整備なしの罰則強化は自転車利用者への一方的な押しつけで、本末転倒という批判です。",
        "sides": (
            ("pos", "インフラ整備優先派", (OPPOSE,), "自転車レーンが整備されてから取り締まるべき。先にルールありきでは混乱するだけ。"),
            ("neu", "中立", (NEUTRAL,), "インフラ整備と取り締まりを並行して進める現実的な視点。"),
            ("neg", "整備を待たず取締りを", (SUPPORT,), "整備の遅れは認めつつ、危険行為の取り締まりは先に始めるべきだという立場。"),
        ),
        "samples": (
            ("インフラ優先 / 感情高め", "インフラ整備不足を批判し、青切符制度に強く反対する声", "https://x.com/15jacnamagiga/status/2070261164618158443"),
            ("条件付き支持 / 冷静", "インフラ整備優先を主張しつつ青切符制度を条件付きで支持", "https://x.com/suzuking408/status/2069735857695891855"),
        ),
    },
    {
        "issue": "車道走行への不安",
        "anchor": "issue-sharido",
        "heading": "車道走行への不安・「車道を走れ」は危険",
        "temp_label": "車道走行ルールへの評価",
        "temp_names": ("歩道批判", "中立", "車道不安派"),
        "legend": ("ルール強化支持（歩行者目線）", "中立", "車道走行が怖い（自転車目線）"),
        "desc": "青切符と合わせて「自転車は原則車道」というルールが強調されることへの不安。「子どもを車道に出せるか」「路駐があって走れない」といった現実的な危険を訴える声があります。一方で、歩道を飛ばす自転車が危険だという歩行者目線も存在します。",
        "sides": (
            ("pos", "車道走行が怖い", (OPPOSE,), "車道はトラックや路駐車があって危険。子どもや高齢者には無理なルールだ。"),
            ("neu", "中立", (NEUTRAL,), "車道・歩道どちらにも問題があるという複合的な視点。"),
            ("neg", "歩道走行こそ危険", (SUPPORT,), "歩道を飛ばす自転車が怖いという歩行者目線から、車道原則とその徹底を支持する立場。"),
        ),
        "samples": (
            ("車道不安 / 感情高め", "青切符への疑念と子どもへの車道走行要求に強く反対", "https://x.com/isaiah8_1/status/2067988251760345275"),
            ("歩行者安全重視 / 感情高め", "路駐問題の解消と自転車の安全確保を要望する", "https://x.com/Mid_observatory/status/2021148538013671884"),
        ),
    },
    {
        "issue": "免許制要求",
        "anchor": "issue-mensyo",
        "heading": "免許制が必要・青切符だけでは不十分",
        "temp_label": "免許制度要求への立場",
        "temp_names": ("免許制支持", "中立", "慎重"),
        "legend": ("免許制・講習義務化を支持", "中立", "慎重・反対"),
        "desc": "「青切符だけでは甘い」「自転車にも免許制度か事前講習を義務付けるべきだ」という主張です。標識を理解していない自転車利用者が多いため、罰則より先に教育が必要という考え方です。",
        "sides": (
            ("neg", "免許・講習義務化派", (SUPPORT,), "自転車にもルールを学ぶ機会が必要。原付のように免許制か事前講習で知識を担保すべき。"),
            ("pos", "慎重・反対派", (OPPOSE,), "免許制は自転車利用の障壁になる。費用や手続き負担が増えて利便性が下がる。"),
            ("neu", "中立", (NEUTRAL,), "条件次第では免許制や講習義務化もあり得るという立場。"),
        ),
        "samples": (
            ("免許制支持 / 感情高め", "自転車への免許制や講習制度の導入を強く主張", "https://x.com/r70OylZbSZeiIIz/status/2070149487566418240"),
            ("免許制支持 / 安全優先", "自転車に免許制導入を提唱し安全優先の立場から現行ルールに疑問", "https://x.com/yamazakibusu/status/2070074656128917921"),
        ),
    },
    {
        "issue": "ルール曖昧・不信",
        "anchor": "issue-ambiguity",
        "heading": "ルールが曖昧・警察への不信感",
        "temp_label": "ルール整備への評価",
        "temp_names": ("取締り支持", "中立", "慎重・反対"),
        "legend": ("ルール整備後の取締り支持", "中立", "現行のルールへの疑念"),
        "desc": "「何が違反になるのか現場でわからない」「警察が恣意的に取り締まるのではないか」という不信感が中心。「113種類もの違反基準は覚えられない」「点数稼ぎ目的ではないか」という批判です。",
        "sides": (
            ("pos", "ルール不信派", (OPPOSE,), "違反の基準が複雑すぎる。警察の裁量が広く、正直者がバカを見る取り締まりになりかねない。"),
            ("neu", "中立", (NEUTRAL,), "ルールの周知や整備状況を見ながら判断したい。"),
            ("neg", "周知を整えたうえで取締りを", (SUPPORT,), "基準の分かりにくさは認めつつ、周知を整えたうえで取り締まること自体は支持する立場。"),
        ),
        "samples": (
            ("ルール不信 / 感情高め", "青切符に強く反対、監視社会的な取り締まりへの怒り", "https://x.com/kress813/status/2032229649317814760"),
            ("基準複雑さへの批判", "113種は多すぎ、簡略化と周知整備の後に実施すべきと主張", "https://x.com/Clifrennie/status/2068026232860537188"),
        ),
    },
)

SEGMENT_CLASS = {SUPPORT: "neg", NEUTRAL: "neu", OPPOSE: "pos"}
# 帯の中に「N%」の文字を出す下限。狭い区画に文字を入れるとはみ出す。
SEGMENT_LABEL_MIN = 10.0


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def _check_definitions() -> None:
    """BLOCKS の定義そのものを検査する。データではなく書き手の取りこぼしを止める。"""
    anchors = [block["anchor"] for block in BLOCKS]
    if len(set(anchors)) != len(anchors):
        raise IssueCountError(f"論点ブロックのアンカーが重複しています: {anchors}")
    if tuple(block["issue"] for block in BLOCKS) != MAIN_ISSUES:
        raise IssueCountError("BLOCKS の並びが MAIN_ISSUES と一致しません")
    for block in BLOCKS:
        covered = [stance for _cls, _label, stances, _desc in block["sides"] for stance in stances]
        if sorted(covered) != sorted(STANCE_ORDER):
            raise IssueCountError(
                f"{block['issue']}: sides が3つのスタンスをちょうど1回ずつ覆っていません: {covered}"
            )


def classification(record: dict[str, Any]) -> dict[str, Any]:
    nested = record.get("classification")
    if not isinstance(nested, dict):
        raise IssueCountError("classification を持たないレコードがあります")
    return nested


def is_opinion(record: dict[str, Any]) -> Any:
    """このテーマの is_opinion はレコードのトップレベルにある（旧2D分類の名残）。"""
    return classification(record).get("is_opinion", record.get("is_opinion"))


def load_opinions(input_path: Path | None = None) -> tuple[list[dict[str, Any]], str, int]:
    themes = parse_themes_yaml(THEMES_YAML)
    sample_file = str(themes[THEME].get("sample_file") or "")
    if not sample_file or "synthetic" in sample_file:
        raise IssueCountError(f"{THEME}: 正典 sample_file が不正です: {sample_file}")
    source = input_path or ROOT / sample_file
    records = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise IssueCountError(f"{THEME}: 正典が空、またはJSON配列ではありません")

    missing = [
        str(record.get("tweet_id"))
        for record in records
        if not isinstance(record, dict) or not isinstance(is_opinion(record), bool)
    ]
    if missing:
        # 2026-08-17 の更新で実際に起きた。is_opinion が無いレコードは論点カードの
        # 母数（issue_counts.basis: opinion）から丸ごと消えるが、ページの他の場所は
        # 全件で数えるため、1つのページに2つの母数が並ぶ。
        raise IssueCountError(
            f"is_opinion が無いレコードが{len(missing)}件あります。"
            f"分類器（scripts/classify_bike_arena_hermes.py）が付けます: {missing[:5]}"
        )

    opinions: list[dict[str, Any]] = []
    for number, record in enumerate(records, start=1):
        c = classification(record)
        if not is_opinion(record):
            continue
        if c.get("main_issue") not in ISSUE_ORDER:
            raise IssueCountError(f"{number}件目: 未知の main_issue: {c.get('main_issue')}")
        if c.get("stance") not in STANCE_X:
            raise IssueCountError(f"{number}件目: 未知の stance: {c.get('stance')}")
        if c.get("intensity") not in INTENSITY_E:
            raise IssueCountError(f"{number}件目: 未知の intensity: {c.get('intensity')}")
        opinions.append(record)
    if not opinions:
        raise IssueCountError("意見と判定されたレコードがありません")
    return opinions, str(source), len(records)


def build_sm_raw(rows: list[dict[str, Any]]) -> str:
    index = {issue: i for i, issue in enumerate(ISSUE_ORDER)}
    points = []
    for row in rows:
        c = classification(row)
        points.append(
            '  {{x:{x},y:0.0,e:{e},c:{c:.2f},s:"{s}",u:"{u}",i:{i}}}'.format(
                x=STANCE_X[str(c["stance"])],
                e=INTENSITY_E[str(c["intensity"])],
                c=float(c.get("confidence") or 0.7),
                s=str(c.get("summary") or "").replace("\\", "\\\\").replace('"', '\\"'),
                u=str(row.get("url") or "").replace("\\", "\\\\").replace('"', '\\"'),
                i=index[str(c["main_issue"])],
            )
        )
    return "const SM_RAW = [\n" + ",\n".join(points) + "\n];"


def cross_tab(rows: list[dict[str, Any]]) -> dict[str, Counter[str]]:
    """論点 × 立場のクロス集計。帯と内訳はここからしか作らない。"""
    table: dict[str, Counter[str]] = {issue: Counter() for issue in ISSUE_ORDER}
    for row in rows:
        c = classification(row)
        table[str(c["main_issue"])][str(c["stance"])] += 1
    return table


def _build_insight_stats(total: int, table: dict[str, Counter[str]]) -> str:
    issue_totals = {issue: sum(table[issue].values()) for issue in MAIN_ISSUES}
    five = sum(issue_totals.values())
    other = total - five
    if five <= 0:
        raise IssueCountError("5論点に分類された意見が0件です")
    ranked = sorted(MAIN_ISSUES, key=lambda issue: (-issue_totals[issue], MAIN_ISSUES.index(issue)))
    top = ranked[0]
    largest = issue_totals[top]
    menkyo = issue_totals["免許制要求"]

    items = "\n".join(
        f'          <li><span>{esc(issue)}</span><b>{issue_totals[issue]}件</b>'
        f'<span class="insight-issue-bar"><i style="width:{issue_totals[issue] / largest * 100:.0f}%"></i></span></li>'
        for issue in ranked
    )
    return f"""<section class="stats insight-stats" aria-label="このテーマの4つの注目ポイント">
      <article class="stat insight-stat">
        <div class="insight-head"><span class="insight-icon" aria-hidden="true">🗣️</span><span class="insight-label">分析対象の意見</span></div>
        <strong class="insight-value">{total}<small>件</small></strong>
        <p class="insight-note">うち5つの論点に分類できた{five}件（残る{other}件は「その他・分類保留」）</p>
        <div class="insight-meter" aria-hidden="true"><i style="width:100%"></i></div>
      </article>
      <article class="stat insight-stat" data-tone="debate">
        <div class="insight-head"><span class="insight-icon" aria-hidden="true">⚔️</span><span class="insight-label">5論点の内訳</span></div>
        <ul class="insight-issue-list">
{items}
        </ul>
      </article>
      <article class="stat insight-stat" data-tone="topic">
        <div class="insight-head"><span class="insight-icon" aria-hidden="true">🔥</span><span class="insight-label">最も話された論点</span></div>
        <strong class="insight-value">{esc(SHORT_LABEL[top])} {largest}<small>件</small></strong>
        <p class="insight-note">{esc(TOP_ISSUE_NOTE[top])}。5論点{five}件の{largest / five * 100:.0f}%</p>
        <div class="insight-meter" aria-hidden="true"><i style="width:{largest / five * 100:.0f}%"></i></div>
      </article>
      <article class="stat insight-stat" data-tone="option">
        <div class="insight-head"><span class="insight-icon" aria-hidden="true">💡</span><span class="insight-label">第三の選択</span></div>
        <strong class="insight-value">免許・講習 {menkyo}<small>件</small></strong>
        <p class="insight-note">罰則だけでなく、先にルールを学ぶ機会を求める</p>
        <div class="insight-meter" aria-hidden="true"><i style="width:{menkyo / five * 100:.0f}%"></i></div>
      </article>
    </section>"""


def build_insight_stats(rows: list[dict[str, Any]], table: dict[str, Counter[str]]) -> str:
    return _build_insight_stats(len(rows), table)


def build_issue_block(block: dict[str, Any], number: int, counts: Counter[str], is_largest: bool) -> str:
    total = sum(counts.values())
    if total <= 0:
        raise IssueCountError(f"{block['issue']}: この論点に分類された意見が0件です")

    segments = "".join(
        '<div class="temp-seg {cls}" style="width:{width:.1f}%">{label}</div>'.format(
            cls=SEGMENT_CLASS[stance],
            width=counts[stance] / total * 100,
            label=(
                f"{counts[stance] / total * 100:.0f}%"
                if counts[stance] / total * 100 >= SEGMENT_LABEL_MIN
                else ""
            ),
        )
        for stance in STANCE_ORDER
    )
    summary = " / ".join(
        f"{name} {counts[stance]}"
        for name, stance in zip(block["temp_names"], STANCE_ORDER)
    )
    legend = "".join(
        f'<span><i style="background:{color}"></i>{esc(text)}</span>'
        for text, color in zip(block["legend"], ("#e04949", "#94a3b8", "#4b9cf4"))
    )
    sides = "".join(
        '<div class="side {cls}"><strong>{label}（{n}件）</strong>{desc}</div>'.format(
            cls=cls, label=esc(label), n=sum(counts[s] for s in stances), desc=esc(desc)
        )
        for cls, label, stances, desc in block["sides"]
        if sum(counts[s] for s in stances)
    )
    samples = "\n".join(
        f'<div class="sample-card"><div class="meta">{esc(meta)}</div><p>{esc(text)}</p>{embed_html(url)}</div>'
        for meta, text, url in block["samples"]
    )
    kicker = f"論点{number}・最大勢力" if is_largest else f"論点{number}"
    return f"""<article class="issue-block" id="{block['anchor']}">
<div class="issue-head"><span class="axis-kicker">{kicker}</span>
<h3>{esc(block['heading'])}</h3>
<div class="temp-bar-wrap">
<div class="temp-bar-label"><span>{esc(block['temp_label'])}</span><span>{summary}</span></div>
<div class="temp-bar">{segments}</div>
<div class="temp-bar-legend">{legend}</div>
</div>
<p class="issue-desc">{esc(block['desc'])}</p>
<div class="issue-sides">{sides}</div>
</div>
<div class="sample-grid">
{samples}
</div>
</article>"""


def build_conflict_paragraph(table: dict[str, Counter[str]]) -> str:
    totals = {issue: sum(table[issue].values()) for issue in MAIN_ISSUES}
    return (
        '<article class="argument-point"><h3>本当の対立点</h3><p>'
        "対立しているのは取締りの有無より、安全のための責任と実施の順序です。"
        "警告・反則金という個人への働きかけを先に実効化し、道路と教育は並行して改善するのか。"
        "それとも、連続した車道上の通行空間、歩道通行の例外を現場で判断できる周知、"
        "年齢を問わない学習機会を先に保障するのか。分類データでは、"
        f"インフラ整備優先{totals['インフラ整備優先']}件と車道走行への不安{totals['車道走行への不安']}件に加え、"
        f"免許制要求{totals['免許制要求']}件とルール曖昧・不信{totals['ルール曖昧・不信']}件があり、"
        "単純な取締り反対より「現在の進め方では安全の条件が足りない」という不満が対立の中心だと読めます。"
        "</p></article>"
    )


# 投票の選択肢キー → 論点名。1文字違いのものがあるので明示する。
VOTE_ALIAS = {
    "取締り強化": "取締り強化賛成",
    "インフラ整備が先": "インフラ整備優先",
    "車道走行への不安": "車道走行への不安",
    "免許制が必要": "免許制要求",
    "ルールが曖昧": "ルール曖昧・不信",
}
VOTE_DESC = re.compile(r"(\{k:'(?P<key>[^']+)',\s*icon:'[^']*',\s*desc:'[^']*?)（\d[\d,]*件）(')")


def sync_vote_counts(page: str, totals: dict[str, int]) -> str:
    """投票の選択肢の説明文にある「（N件）」を論点別件数に合わせる。

    選択肢そのもの（k）は触らない。選択肢の数が変わると choiceIdx の意味がずれ、
    Edge Function の再デプロイと既存票の破棄が要る。ここで変えるのは説明文の中の件数だけ。
    """

    def replace(match: re.Match[str]) -> str:
        key = match.group("key")
        if key not in VOTE_ALIAS:
            raise IssueCountError(f"投票の選択肢が論点にありません: {key}")
        return f"{match.group(1)}（{totals[VOTE_ALIAS[key]]}件）{match.group(3)}"

    result, replaced = VOTE_DESC.subn(replace, page)
    if replaced != len(VOTE_ALIAS):
        raise IssueCountError(f"投票の選択肢の件数が{len(VOTE_ALIAS)}個必要です（{replaced}個）")
    return result


def replace_once(page: str, pattern: str, replacement: str, label: str, *, flags: int = 0) -> str:
    result, count = re.subn(pattern, lambda _match: replacement, page, count=1, flags=flags)
    if count != 1:
        raise IssueCountError(f"{label}: 1箇所だけ一致する必要があります（{count}箇所）")
    return result


def _public_table(data: dict[str, Any]) -> dict[str, Counter[str]]:
    """公開JSONの論点×立場集計を、ページ生成器と同じ形にする。"""
    if data.get("theme_id") != THEME:
        raise IssueCountError(f"自転車青切符の公開JSONではありません: {data.get('theme_id')}")
    by_label = {str(issue["label"]): issue for issue in data.get("issues", [])}
    if set(by_label) != set(ISSUE_ORDER):
        raise IssueCountError(
            "自転車青切符の公開JSONの論点がページ定義と一致しません: "
            + ", ".join(sorted(by_label))
        )
    table: dict[str, Counter[str]] = {issue: Counter() for issue in ISSUE_ORDER}
    for issue in ISSUE_ORDER:
        item = by_label[issue]
        stance_counts = Counter(
            {str(stance["label"]): int(stance["count"]) for stance in item.get("stances", [])}
        )
        if set(stance_counts) != set(STANCE_ORDER):
            raise IssueCountError(f"公開JSONの立場定義が一致しません: {issue}")
        if sum(stance_counts.values()) != int(item["count"]):
            raise IssueCountError(f"公開JSONの論点数と立場数が一致しません: {issue}")
        table[issue] = stance_counts
    opinions = int(data["opinion_count"])
    if sum(sum(counts.values()) for counts in table.values()) != opinions:
        raise IssueCountError("公開JSONの意見数と論点別合計が一致しません")
    return table


def apply_public_counts(html: str, public_theme: Path = PUBLIC_THEME) -> str:
    """公開JSONを正典とし、ページの管理対象数字を貼り直す。

    候補生成では先に公開JSONが固定される。その後にこの関数を実行し、
    ヒーロー、注目ポイント、論点帯、投票説明、マップ見出しを同じ公開物に揃える。
    賛否を明示できた投稿の編集部再読集計は別の検証データなので触らない。
    """
    data = json.loads(public_theme.read_text(encoding="utf-8"))
    table = _public_table(data)
    collected = int(data["collected_count"])
    opinions = int(data["opinion_count"])
    totals = {issue: sum(table[issue].values()) for issue in MAIN_ISSUES}
    five = sum(totals.values())
    other = sum(table["その他"].values())
    largest = max(totals.values())
    # 山なみ形式では、ヒーロー文・アリーナ見出し・注目ポイント・論点帯・本当の対立点は
    # 山なみ本体か編集部の横断整理が引き継ぐ（旧セクションごと除かれる）。投票の説明文
    # （vote-section）は山なみでも残るので、そこだけは通常どおり更新する
    # （2026-09-11、高齢者テーマの展開で確立したガード。段階1）。
    planet_mode = "<!-- PLANET_SECTION_START -->" in html

    if not planet_mode:
        html = replace_once(
            html,
            r'<p class="lead">収集したSNS投稿.*?</p>',
            f'<p class="lead">収集したSNS投稿{collected}件のうち、分析対象の意見{opinions}件をAIで整理し、'
            f'主要5論点{five}件に分類し、残る{other}件は「その他・分類保留」としました。'
            '世論調査ではなく、SNS反応サンプルの論点比較です。</p>',
            "ヒーローの収集数・意見数・論点数",
            flags=re.S,
        )
        html = replace_once(
            html,
            r'<div class="panel-title"><h2>SNS反応マップ</h2><span>[^<]*</span></div>',
            f'<div class="panel-title"><h2>SNS反応マップ</h2><span>{opinions}件 | '
            'セクター=論点 / 中心に近いほど冷静 / 色=賛否 | ホバーで詳細</span></div>',
            "アリーナ見出し",
        )
        html = replace_once(
            html,
            r'<section class="stats insight-stats".*?</section>',
            _build_insight_stats(opinions, table),
            "注目ポイント",
            flags=re.S,
        )
        for number, block in enumerate(BLOCKS, start=1):
            counts = table[str(block["issue"])]
            html = replace_once(
                html,
                rf'<article class="issue-block" id="{block["anchor"]}">.*?\n</article>',
                build_issue_block(block, number, counts, sum(counts.values()) == largest),
                f'論点ブロック {block["anchor"]}',
                flags=re.S,
            )
    html = sync_vote_counts(html, totals)
    if not planet_mode:
        html = replace_once(
            html,
            r'<article class="argument-point"><h3>本当の対立点</h3>.*?</article>',
            build_conflict_paragraph(table),
            "本当の対立点",
            flags=re.S,
        )
    return html


STANCE_GLANCE_START = "<!-- STANCE_GLANCE_START -->"
STANCE_GLANCE_END = "<!-- STANCE_GLANCE_END -->"
STANCE_GLANCE_ANCHOR = "<!-- RESEARCH_CONDITIONS_START -->"

# configs/planet/bike-blue-ticket.yaml の stances[].key と対応させる。
# 集計(count/color)は正典から取得済みの値をそのまま使い、ここでは新たに数えない。
# 投票ウィジェット独自の色(neutral=#64748b等)ではなく、山なみ本体と同じ
# yaml定義の色(#e04949/#4b9cf4/#8B9199)を使う。
STANCE_GLANCE_META = {
    "enforcement_support": {
        "short": "賛成", "icon": "✓", "bg": "#FDEDED", "shadow": "rgba(224,73,73,.22)",
        "desc": "違反への取り締まりを強化すべきだとする投稿",
    },
    "infrastructure_first": {
        "short": "反対", "icon": "✕", "bg": "#EAF3FE", "shadow": "rgba(75,156,244,.22)",
        "desc": "取り締まりより、走行環境や制度の整備を優先すべきだとする投稿",
    },
    "neutral": {
        "short": "どちらでもない", "icon": "?", "bg": "#F1F2F3", "shadow": "rgba(139,145,153,.22)",
        "desc": "賛否を示さず、制度の説明や感想にとどまる投稿",
    },
}

STANCE_GLANCE_CSS = """<style>
#stance-glance {
  width: min(1180px, 100%);
  margin: 14px auto 0;
  padding: 30px 34px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: #fff;
  box-shadow: var(--topic-shadow-sm);
  box-sizing: border-box;
}
#stance-glance .sg-lead{font-size:14.5px;line-height:1.9;margin:0 0 18px;color:var(--navy)}
#stance-glance .sg-headline{font-size:15px;font-weight:800;margin:0 0 10px;color:var(--navy)}
#stance-glance .sg-headline b{font-size:30px;font-weight:900;color:var(--blue);margin-right:2px}
#stance-glance .sg-bar-wrap{margin:0 0 24px}
@keyframes sgSegPulse{
  0%{filter:brightness(1);box-shadow:inset 0 0 0 0 rgba(255,255,255,0)}
  35%{filter:brightness(1.4);box-shadow:inset 0 0 0 3px rgba(255,255,255,.9)}
  100%{filter:brightness(1);box-shadow:inset 0 0 0 0 rgba(255,255,255,0)}
}
#stance-glance .temp-seg.sg-pulse{animation:sgSegPulse .7s ease}
@keyframes sgLegendPulse{
  0%{transform:scale(1)}
  35%{transform:scale(1.12)}
  100%{transform:scale(1)}
}
#stance-glance .temp-bar-legend span{display:inline-flex;align-items:center;border-radius:6px;
  padding:2px 4px;margin:-2px -4px;transition:background .2s ease}
#stance-glance .temp-bar-legend span.sg-pulse{animation:sgLegendPulse .5s ease;background:#F2F6FD}
#stance-glance .sg-pick-label{font-size:16px;font-weight:900;margin:0 0 4px;color:var(--navy)}
#stance-glance .sg-pick-hint{font-size:12.5px;color:var(--muted);margin:0 0 12px}
#stance-glance .sg-pick-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
#stance-glance .sg-pick-btn{position:relative;display:flex;flex-direction:column;align-items:center;
  gap:8px;border:2px solid var(--line);border-radius:14px;padding:20px 10px 16px;background:#fff;
  cursor:pointer;font-family:inherit;color:var(--navy);
  transition:border-color .18s ease,background .18s ease,transform .18s ease,box-shadow .18s ease}
#stance-glance .sg-pick-btn:hover{transform:translateY(-3px);border-color:var(--sg-color);
  box-shadow:0 10px 22px -10px rgba(16,24,40,.25)}
#stance-glance .sg-pick-btn:focus-visible{outline:2px solid var(--sg-color);outline-offset:2px}
#stance-glance .sg-pick-icon{font-size:25px;line-height:1;color:var(--sg-color)}
#stance-glance .sg-pick-name{font-size:12.5px;font-weight:800;letter-spacing:.01em}
#stance-glance .sg-pick-btn[aria-pressed="true"]{border-color:var(--sg-color);background:var(--sg-bg)}
#stance-glance .sg-pick-btn[aria-pressed="true"] .sg-pick-name{color:var(--sg-color)}
#stance-glance .sg-pick-check{position:absolute;top:-8px;right:-8px;width:20px;height:20px;
  border-radius:50%;background:var(--sg-color);color:#fff;display:none;align-items:center;
  justify-content:center;font-size:11px;font-weight:900;box-shadow:0 2px 6px rgba(16,24,40,.3)}
#stance-glance .sg-pick-btn[aria-pressed="true"] .sg-pick-check{display:flex}
#stance-glance .sg-result{margin-top:14px;padding:14px 16px;border-radius:10px;background:#F2F6FD;
  display:none}
#stance-glance .sg-result p{margin:0;font-size:14px;line-height:1.8;font-weight:700;color:var(--navy)}
#stance-glance .sg-note{margin:10px 0 0;font-size:11.5px;color:var(--muted);line-height:1.7}
@media (max-width:720px){
  #stance-glance{padding:22px 18px}
}
</style>"""


def stance_glance(stances: list[dict], opinions: int) -> str:
    """ヒーロー直後、立場の内訳＋「まず、あなたは？」を組み立てる。

    stances は bpd.build("bike-blue-ticket")["stances"]（configs/planet/
    bike-blue-ticket.yaml の3区分に正典の件数を足したもの）をそのまま使う。
    ここで新たに集計しない。投票データへの書き込みは行わない。
    """
    by_key = {s["key"]: int(s["count"]) for s in stances}
    enforcement_count = by_key.get("enforcement_support", 0)
    infra_count = by_key.get("infrastructure_first", 0)
    neutral_count = by_key.get("neutral", 0)
    enforcement_pct = 100 * enforcement_count / opinions if opinions else 0.0
    infra_pct = 100 * infra_count / opinions if opinions else 0.0

    segs, legend, buttons, js_rows = [], [], [], []
    for i, s in enumerate(stances):
        meta = STANCE_GLANCE_META[s["key"]]
        count = int(s["count"])
        share = 100 * count / opinions if opinions else 0.0
        seg_label = f"{share:.0f}%" if share >= 5 else ""
        segs.append(
            f'<div class="temp-seg" data-i="{i}" style="width:{share:.1f}%;background:{s["color"]}">{seg_label}</div>'
        )
        legend.append(
            f'<span data-i="{i}"><i style="background:{s["color"]}"></i>{html.escape(meta["short"])}<b>{count}件</b></span>'
        )
        buttons.append(
            f'<button type="button" class="sg-pick-btn" data-i="{i}" aria-pressed="false" '
            f'style="--sg-color:{s["color"]};--sg-bg:{meta["bg"]}">'
            f'<span class="sg-pick-check" aria-hidden="true">✓</span>'
            f'<span class="sg-pick-icon" aria-hidden="true">{html.escape(meta["icon"])}</span>'
            f'<span class="sg-pick-name">{html.escape(meta["short"])}</span></button>'
        )
        js_rows.append(
            "{short:%s,pct:%s,desc:%s}"
            % (
                json.dumps(meta["short"], ensure_ascii=False),
                share,
                json.dumps(meta["desc"], ensure_ascii=False),
            )
        )
    bar = (
        '<div class="temp-bar-wrap sg-bar-wrap"><div class="temp-bar-label">'
        f'<span>意見{opinions:,}件の立場別内訳</span><span>意見に占める割合</span></div>'
        f'<div class="temp-bar">{"".join(segs)}</div>'
        f'<div class="temp-bar-legend">{"".join(legend)}</div></div>'
    )
    script = f"""<script>
(function(){{
  var DATA=[{",".join(js_rows)}];
  var root=document.getElementById('stance-glance');
  var box=document.getElementById('stance-glance-buttons');
  if(!root||!box)return;
  var buttons=box.querySelectorAll('.sg-pick-btn');
  var result=document.getElementById('stance-glance-result');
  var text=document.getElementById('stance-glance-result-text');
  function pulse(i){{
    root.querySelectorAll('.sg-pulse').forEach(function(el){{el.classList.remove('sg-pulse');}});
    var seg=root.querySelector('.temp-seg[data-i="'+i+'"]');
    var leg=root.querySelector('.temp-bar-legend span[data-i="'+i+'"]');
    [seg,leg].forEach(function(el){{
      if(!el)return;
      void el.offsetWidth;
      el.classList.add('sg-pulse');
    }});
  }}
  buttons.forEach(function(btn){{
    btn.addEventListener('click',function(){{
      buttons.forEach(function(b){{b.setAttribute('aria-pressed', b===btn ? 'true' : 'false');}});
      var i=parseInt(btn.dataset.i,10);
      var d=DATA[i];
      text.textContent='「'+d.short+'」: '+d.desc+'（'+d.pct.toFixed(1)+'%）';
      result.style.display='block';
      pulse(i);
    }});
  }});
}})();
</script>"""
    return f"""{STANCE_GLANCE_START}
{STANCE_GLANCE_CSS}
<aside id="stance-glance" aria-labelledby="stance-glance-title">
<div class="panel-title"><h2 id="stance-glance-title">自転車の青切符導入、最多は取り締まりより整備を求める声</h2><span>内訳を、投票の前に</span></div>
<p class="sg-lead">取り締まり強化を求める声は{enforcement_count}件（{enforcement_pct:.1f}%）にとどまり、インフラ・制度整備を優先すべきという声が{infra_count}件（{infra_pct:.1f}%）で最も多くなっています。「どちらでもない」も{neutral_count}件あり、単純な賛否では語れません。</p>
<div class="sg-headline"><b>{opinions:,}</b>件の意見における、立場の内訳です</div>
{bar}
<div class="sg-pick"><p class="sg-pick-label">近い考えのボタンを押すと</p>
<p class="sg-pick-hint">その立場の投稿がどんな内容かを表示します</p>
<div class="sg-pick-grid" id="stance-glance-buttons">
{"".join(buttons)}
</div>
<div class="sg-result" id="stance-glance-result" aria-live="polite"><p id="stance-glance-result-text"></p></div>
<p class="sg-note">※ これは内容を確かめるための表示で、投票にはなりません。投票はこのページ下部から参加できます。</p>
</div>
</aside>
{script}
{STANCE_GLANCE_END}"""


def apply_bike_stance_glance(page: str) -> str:
    """ヒーロー直後に、立場の内訳＋「まず、あなたは？」を貼り直す。

    このページの定例更新経路(build()のplanet_mode分岐)はRESEARCH_CONDITIONS_
    START直前の領域を素通りする(この関数以外に同領域へ触れる箇所が無いことを
    実装前に確認済み)ため、放っておくと件数が更新されず古いまま残る。
    他テーマの後付け補完処理と同じ「除去してから再挿入」の型で毎回貼り直す。
    """
    if __package__:
        from .build_planet_page_preview import bpd
    else:  # python3 scripts/build_bike_arena.py
        from build_planet_page_preview import bpd  # type: ignore[no-redef]

    data = bpd.build("bike-blue-ticket")
    opinions = int(data["totals"]["opinions"])
    stances = data["stances"]

    if STANCE_GLANCE_START in page and STANCE_GLANCE_END in page:
        start = page.index(STANCE_GLANCE_START)
        end = page.index(STANCE_GLANCE_END) + len(STANCE_GLANCE_END)
        page = page[:start] + page[end:]
        # 外したあと・貼る前の空行を2行に揃える(揃えないと貼り直しのたびに
        # 空行が増え、adapterの冪等性検査が通らない)。
        page = re.sub(r"\n\s*\n+(<!-- RESEARCH_CONDITIONS_START -->)", r"\n\n\1", page)
    block = stance_glance(stances, opinions)
    idx = page.index(STANCE_GLANCE_ANCHOR)
    page = page[:idx] + block + "\n\n" + page[idx:]

    if page.count(STANCE_GLANCE_START) != 1 or page.count(STANCE_GLANCE_END) != 1:
        raise IssueCountError("内訳セクションのマーカーが1組でない")
    if '<h2 id="stance-glance-title">' not in page:
        raise IssueCountError("内訳セクションの見出しがページにない")
    check_block = page[page.index(STANCE_GLANCE_START):page.index(STANCE_GLANCE_END)]
    seg_count = check_block.count('<div class="temp-seg"')
    btn_count = check_block.count('class="sg-pick-btn"')
    if seg_count != len(stances):
        raise IssueCountError(f"内訳バーの区画が{len(stances)}個でない: {seg_count}個")
    if btn_count != len(stances):
        raise IssueCountError(f"「あなたは？」ボタンが{len(stances)}個でない: {btn_count}個")
    if page.index(STANCE_GLANCE_START) > page.index(STANCE_GLANCE_ANCHOR):
        raise IssueCountError("内訳セクションが調査条件より後ろにある(ヒーロー直後に置くこと)")
    if '<aside id="stance-glance"' not in page:
        raise IssueCountError(
            "内訳セクションがasideでなくなっている"
            "(sectionにするとpanel:nth-of-type(even)の縞模様が後続セクション全部でずれる)"
        )
    return page


def build(
    *,
    check: bool = False,
    input_path: Path | None = None,
    html_template: Path | None = None,
    output_html: Path | None = None,
) -> tuple[list[str], bool]:
    _check_definitions()
    rows, sample_file, collected = load_opinions(input_path)
    table = cross_tab(rows)
    totals = {issue: sum(table[issue].values()) for issue in MAIN_ISSUES}
    largest = max(totals.values())

    public_path = ROOT / "docs" / f"{THEME}-reaction-map.html"
    template = html_template or public_path
    destination = output_html or public_path
    before = template.read_text(encoding="utf-8")
    page = before
    planet_mode = "<!-- PLANET_SECTION_START -->" in page

    known = {str(record.get("tweet_id")) for record in rows}
    for block in BLOCKS:
        for _meta, _text, url in block["samples"]:
            tweet_id = url.rsplit("/", 1)[-1]
            if tweet_id not in known:
                raise IssueCountError(
                    f"{block['issue']}: 代表投稿が正典の意見にありません（削除・分類変更）: {url}"
                )

    # 山なみページにも残る旧配列は、現行分類から再生成できる。母数を古いまま残さない。
    if '<script id="bike-arena-points">' not in page:
        raise IssueCountError('SM_RAW を囲む <script id="bike-arena-points"> がありません')
    page = replace_once(page, r"const SM_RAW = \[.*?\n\];", build_sm_raw(rows), "SM_RAW", flags=re.S)
    if not planet_mode:
        page = replace_once(
            page,
            r'<div class="panel-title"><h2>SNS反応マップ</h2><span>[^<]*</span></div>',
            f'<div class="panel-title"><h2>SNS反応マップ</h2><span>{len(rows)}件 | セクター=論点 / 中心に近いほど冷静 / 色=賛否 | ホバーで詳細</span></div>',
            "アリーナ見出し",
        )
        page = replace_once(
            page,
            r'<section class="stats insight-stats".*?</section>',
            build_insight_stats(rows, table),
            "注目ポイント",
            flags=re.S,
        )
        for number, block in enumerate(BLOCKS, start=1):
            counts = table[str(block["issue"])]
            page = replace_once(
                page,
                rf'<article class="issue-block" id="{block["anchor"]}">.*?\n</article>',
                build_issue_block(block, number, counts, sum(counts.values()) == largest),
                f'論点ブロック {block["anchor"]}',
                flags=re.S,
            )
    page = sync_vote_counts(page, totals)
    if not planet_mode:
        page = replace_once(
            page,
            r'<article class="argument-point"><h3>本当の対立点</h3>.*?</article>',
            build_conflict_paragraph(table),
            "本当の対立点",
            flags=re.S,
        )
    if planet_mode:
        page = apply_bike_stance_glance(page)

    changed = page != before
    if not check:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(page, encoding="utf-8")
    detail = " / ".join(f"{issue}={totals[issue]}" for issue in MAIN_ISSUES)
    stances = Counter(str(classification(row)["stance"]) for row in rows)
    return (
        [
            f"出所: {sample_file}（収集{collected}件 / 意見{len(rows)}件）",
            f"論点: {detail} / その他={sum(table['その他'].values())}",
            "立場: " + " / ".join(f"{stance}={stances[stance]}" for stance in STANCE_ORDER),
        ],
        changed,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--public-counts-only",
        action="store_true",
        help="公開JSONからページの管理対象数字だけを貼り直す",
    )
    parser.add_argument("--input", type=Path)
    parser.add_argument("--html-template", type=Path)
    parser.add_argument("--output-html", type=Path)
    args = parser.parse_args()
    try:
        if args.public_counts_only:
            if args.check or args.input or args.html_template:
                parser.error("--public-counts-onlyは--output-html以外と併用できません")
            destination = args.output_html or ROOT / "docs" / f"{THEME}-reaction-map.html"
            destination.write_text(
                apply_public_counts(destination.read_text(encoding="utf-8")), encoding="utf-8"
            )
            print(f"updated public JSON counts in {destination}")
            return 0
        if args.check and any((args.input, args.html_template, args.output_html)):
            parser.error("--checkは公開ページと正典の一致確認専用です")
        if any((args.input, args.html_template, args.output_html)) and not all(
            (args.input, args.html_template, args.output_html)
        ):
            parser.error("候補生成では--input/--html-template/--output-htmlをすべて指定してください")
        lines, changed = build(
            check=args.check,
            input_path=args.input,
            html_template=args.html_template,
            output_html=args.output_html,
        )
        print("\n".join(lines))
        if args.check and changed:
            print("NG: HTMLに差分があります", file=sys.stderr)
            return 1
        print("OK: 差分なし" if not changed else "UPDATE: HTMLを更新しました")
        return 0
    except (IssueCountError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
