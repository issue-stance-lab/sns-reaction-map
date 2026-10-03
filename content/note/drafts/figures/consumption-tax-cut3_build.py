#!/usr/bin/env python3
"""note「消費税減税」第3回の数字と図を、正典のJSONから再現する。

使い方（非公開の正典 social-samples/ を復元した作業ツリーのルートで実行する）:
    python3 content/note/drafts/figures/consumption-tax-cut3_build.py numbers
    python3 content/note/drafts/figures/consumption-tax-cut3_build.py figs

numbers: 記事の本文・図・注記に使う数字をすべて表示する（品質監査はここを突き合わせる）。
figs   : 図1・図2を content/note/drafts/images/ に書き出す（1800x1040、第1・2回と同じ様式）。

集計の対象は classification.is_relevant かつ classification.is_opinion の投稿（意見）。
理由の型は、AIが付けた要約文（classification.summary）を、下の正規表現で機械的に分けた概数
（1つの投稿が複数の型に入ることがある）。賛成側の「返事」と「減税がなかった場合と比べる投稿」は、
編集部が要約を全件読んで目視で仕分けた結果を consumption-tax-cut3_hand-labels.json に残してある。
"""

from __future__ import annotations

import collections
import datetime
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SAMPLE = ROOT / "social-samples" / "consumption-tax-cut_hermes_arena_classified.json"
OUT_DIR = Path(os.environ.get("FIG_OUT") or ROOT / "content" / "note" / "drafts" / "images")

JST = datetime.timezone(datetime.timedelta(hours=9))
CUT = datetime.datetime(2026, 9, 16, tzinfo=JST)  # 大綱の閣議決定（9/15）の翌日。決定日当日の閣議前の投稿を含めない

PRO, CON, COND, NEU = "減税推進", "減税反対・慎重", "条件付き賛成・政府案に不満", "中立・情報"
STANCES = [PRO, COND, NEU, CON]  # 第1・2回の図と同じ並び
ISSUES = ["公約と政治不信", "減税の対象範囲", "減税の効果", "財源と社会保障", "給付など他策との比較", "事業者の実務負担", "その他"]
EFFECT = "減税の効果"

# 効果を疑う投稿（反対・慎重×効果）が挙げた理由の型。要約文だけを語句で分けた概数。
# 独立確認で全件を目視した結果（前後の値札型は約4分の1、設計型・財源型は1割台）と数ポイントの範囲で一致する。
PRICE = (
    r"相殺|帳消し|吹き飛|打ち消|消失|消え(る|て|た)|緩衝|価格(は|が)下がら|価格が反映|安くならな|安くなら|下げな|値段を下げ"
    r"|値下げ(さ)?れ|値下がり(し|せ)|吸収|便乗|転嫁|店次第|届かな|届くか"
    r"|(値上げ|物価高|物価上昇|インフレ|円安|物価)(で|が|に|の中|下).{0,16}(意味|効果|実感|減税分)"
    r"|(意味|効果|実感)(が|は)?(ない|なし|薄|乏|限定|消).{0,14}(値上げ|物価高|物価上昇|インフレ)|値上げ(で|して|され|すれば|ラッシュ)"
)
BACK = (
    r"(減税|消費税|財源なき|国債).{0,18}(円安|インフレ|物価高|物価上昇).{0,8}(招|加速|悪化|助長|促進|進行|誘発|押し上げ)"
    r"|(円安|インフレ|物価高).{0,6}(を)?(招|加速|悪化|助長)|インフレ(時|下|円安下)の?減税"
)
DES = (
    r"食料品限定|食品限定|飲食料品限定|限定減税|食料品だけ|食品だけ|食料品のみ|1%|１%|1％|１％|焼け?石"
    r"|期限付き|期間限定|時限|2年|一時的|短期|全品目|一律"
)
FUND = r"財源|財政|国債|増税|プラマイ|二重取り|回収"
EXPAND = r"一律|恒久|拡大|全品目|全項目|廃止|広げ"
# 参考: 賛成側の効果の投稿で、反対論や批判に答えていると読める語（語句判定。目視の仕分けとの突き合わせ用）
REPLY = (
    r"反論|批判|反駁|論破|非難|否定論|無効論|無意味説|難癖|ネガティブ|詭弁|罠|嘘|矛盾|貶め|歪曲|反対派|反対論"
    r"|反対は|反対する|抵抗|煽り|疑問を呈|おかしい|不可解|言い訳|拡散を|主張の根拠を問い|懸念を嘲弄|疑問視|宣伝"
)
HAND_LABELS = Path(__file__).with_name("consumption-tax-cut3_hand-labels.json")
SKEPTIC_QUERIES = {"消費税減税 意味ない", "消費税減税 効果", "消費税減税 反対"}

# スマホ幅（375px）まで縮小しても読めるよう、フォントを一律に拡大する
FONT_SCALE = 1.2


def fs(size: float) -> float:
    return round(size * FONT_SCALE, 1)


def load() -> list[dict]:
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    return [x for x in data if x["classification"].get("is_relevant") and x["classification"].get("is_opinion")]


def posted_at(x: dict) -> datetime.datetime:
    ms = (int(x["tweet_id"]) >> 22) + 1288834974657  # X の snowflake ID から投稿時刻を復元
    return datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc).astimezone(JST)


def norm(text: str) -> str:
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = text.replace("\tSTART\t", "").replace("\tEND\t", "")
    return re.sub(r"[\s　]+", "", text)


def pct(n: int, d: int) -> float:
    return round(n / d * 100, 1) if d else 0.0


def dist(posts: list[dict], key: str, order: list[str]) -> dict[str, tuple[int, float]]:
    c = collections.Counter(p["classification"][key] for p in posts)
    return {k: (c[k], pct(c[k], len(posts))) for k in order}


def stats(op: list[dict]) -> dict:
    s: dict = {"n_opinion": len(op)}
    s["stance_all"] = dist(op, "stance", STANCES)
    s["issue_all"] = dist(op, "main_issue", ISSUES)
    s["stance_by_issue"] = {i: dist([p for p in op if p["classification"]["main_issue"] == i], "stance", STANCES) for i in ISSUES}
    s["issue_by_stance"] = {st: dist([p for p in op if p["classification"]["stance"] == st], "main_issue", ISSUES) for st in STANCES}
    eff = [p for p in op if p["classification"]["main_issue"] == EFFECT]
    s["n_effect"] = len(eff)
    s["wants_some_cut"] = (
        s["stance_all"][PRO][0] + s["stance_all"][COND][0],
        pct(s["stance_all"][PRO][0] + s["stance_all"][COND][0], len(op)),
    )
    # 頑健性: 検索語・重複・時期を変えても効果の論点の傾向が動かないか
    def eff_line(posts: list[dict]) -> dict:
        e = [p for p in posts if p["classification"]["main_issue"] == EFFECT]
        c = collections.Counter(p["classification"]["stance"] for p in e)
        share = {}
        for st in (PRO, CON):
            sub = [p for p in posts if p["classification"]["stance"] == st]
            share[st] = pct(sum(1 for p in sub if p["classification"]["main_issue"] == EFFECT), len(sub))
        return {"n": len(posts), "n_effect": len(e), "pro": pct(c[PRO], len(e)), "con": pct(c[CON], len(e)),
                "cond": pct(c[COND], len(e)), "effect_share_pro": share[PRO], "effect_share_con": share[CON]}

    seen, one_user = set(), []
    for p in op:
        if p.get("user_id") in seen:
            continue
        seen.add(p.get("user_id"))
        one_user.append(p)
    seen, no_dup = set(), []
    for p in op:
        k = norm(p["text"])
        if k in seen:
            continue
        seen.add(k)
        no_dup.append(p)
    # 効果の論点だけで、同じ人の投稿を1件に絞る
    seen_e, eff_one = set(), []
    for p in eff:
        if p.get("user_id") in seen_e:
            continue
        seen_e.add(p.get("user_id"))
        eff_one.append(p)
    ce = collections.Counter(p["classification"]["stance"] for p in eff_one)
    eff_one_line = {"n": len(eff_one), "pro": pct(ce[PRO], len(eff_one)), "con": pct(ce[CON], len(eff_one))}
    s["eff_one_per_user"] = eff_one_line
    s["robust"] = {
        "そのまま": eff_line(op),
        "検索語『意味ない/効果/反対』の投稿を除く": eff_line([p for p in op if p.get("query") not in SKEPTIC_QUERIES]),
        "全体で1ユーザー1投稿に絞る": eff_line(one_user),
        "同一本文の重複を除く": eff_line(no_dup),
        "大綱決定前（9/16より前）": eff_line([p for p in op if posted_at(p) < CUT]),
        "大綱決定の翌日以降（9/16以降）": eff_line([p for p in op if posted_at(p) >= CUT]),
    }
    # 効果を疑う投稿の理由の型（要約文の語句判定。重複あり）
    con = [p for p in eff if p["classification"]["stance"] == CON]
    summ = lambda p: p["classification"].get("summary", "")
    price = [p for p in con if re.search(PRICE, summ(p))]
    back = [p for p in con if re.search(BACK, summ(p)) and not re.search(PRICE, summ(p))]
    des = [p for p in con if re.search(DES, summ(p))]
    fund = [p for p in con if re.search(FUND, summ(p))]
    none = [p for p in con if not (re.search(PRICE, summ(p)) or re.search(BACK, summ(p)) or re.search(DES, summ(p)) or re.search(FUND, summ(p)))]
    users = lambda ps: len({p.get("user_id") for p in ps})
    s["n_effect_con"] = len(con)
    s["reasons"] = {
        "前後の値札型（値上げ・物価高で減税分が消える／価格が下がらない／店が取り込む）": (len(price), pct(len(price), len(con)), users(price)),
        "減税が円安・物価高を招く（前後の値札型に入らないもの）": (len(back), pct(len(back), len(con)), users(back)),
        "食料品だけ・1%・期間という設計が小さい／短い": (len(des), pct(len(des), len(con)), users(des)),
        "財源・財政への心配": (len(fund), pct(len(fund), len(con)), users(fund)),
    }
    s["reasons_none"] = (len(none), pct(len(none), len(con)))
    # 賛成側の効果の投稿（目視の仕分け + 語句判定との突き合わせ）
    pro = [p for p in eff if p["classification"]["stance"] == PRO]
    labels = json.loads(HAND_LABELS.read_text(encoding="utf-8"))
    ids = {p["tweet_id"] for p in pro}
    e_ids, g_ids, cf_ids = set(labels["effect_reply"]), set(labels["general_reply"]), set(labels["counterfactual_explicit"])
    assert (e_ids | g_ids | cf_ids) <= ids, "ラベルのIDがデータに無い"
    reply_regex = [p for p in pro if re.search(REPLY, summ(p))]
    s["n_effect_pro"] = len(pro)
    s["pro_reply_effect"] = (len(e_ids), pct(len(e_ids), len(pro)))
    s["pro_reply_any"] = (len(e_ids | g_ids), pct(len(e_ids | g_ids), len(pro)))
    s["pro_counterfactual"] = (len(cf_ids), pct(len(cf_ids), len(pro)))
    s["pro_reply_regex"] = (len(reply_regex), pct(len(reply_regex), len(pro)))
    # 条件付き賛成の効果の投稿
    cond = [p for p in eff if p["classification"]["stance"] == COND]
    small = [p for p in cond if re.search(DES, summ(p))]
    expand = [p for p in small if re.search(EXPAND, summ(p))]
    s["n_effect_cond"] = len(cond)
    s["cond_small"] = (len(small), pct(len(small), len(cond)), users(small))
    s["cond_expand"] = (len(expand), pct(len(expand), len(small)))
    return s


def show(s: dict) -> None:
    print(f"意見 n={s['n_opinion']:,}  効果の論点 n={s['n_effect']:,}  （標本: {SAMPLE.name}）")
    print("\n[全体の立場]")
    for k, (n, p) in s["stance_all"].items():
        print(f"  {k}: {n:,} ({p}%)")
    print(f"  何らかの減税を望む側（推進+条件付き）: {s['wants_some_cut'][0]:,} ({s['wants_some_cut'][1]}%)")
    print("\n[論点ごとの立場（図1）]")
    for i in ISSUES:
        n = sum(v[0] for v in s["stance_by_issue"][i].values())
        print(f"  {i} n={n:,}: " + " / ".join(f"{k[:4]} {v[0]}({v[1]}%)" for k, v in s["stance_by_issue"][i].items()))
    print("\n[立場ごとに語っていた論点（図2）]")
    for st in STANCES:
        n = sum(v[0] for v in s["issue_by_stance"][st].values())
        print(f"  {st} n={n:,}: " + " / ".join(f"{k} {v[0]}({v[1]}%)" for k, v in s["issue_by_stance"][st].items()))
    print("\n[頑健性（効果の論点の立場と、立場ごとの『効果が主題』の割合）]")
    for k, v in s["robust"].items():
        print(f"  {k}: 全体n={v['n']:,} 効果n={v['n_effect']} 推進{v['pro']}% 反対・慎重{v['con']}% 条件付き{v['cond']}% | 効果が主題: 推進{v['effect_share_pro']}% 反対・慎重{v['effect_share_con']}%")
    print(f"\n[効果の論点で同じ人を1件に絞る] n={s['eff_one_per_user']['n']} 推進{s['eff_one_per_user']['pro']}% 反対・慎重{s['eff_one_per_user']['con']}%")
    print(f"\n[効果を疑う投稿（反対・慎重×効果）n={s['n_effect_con']} が挙げた理由の型（要約文の語句判定・重複あり）]")
    for k, (n, p, u) in s["reasons"].items():
        print(f"  {k}: {n}件 ({p}%) / 投稿者{u}人")
    print(f"  どの型にも該当しない: {s['reasons_none'][0]}件 ({s['reasons_none'][1]}%)")
    pe, pa, pc, pr = s["pro_reply_effect"], s["pro_reply_any"], s["pro_counterfactual"], s["pro_reply_regex"]
    print(f"\n[賛成側の効果の投稿 n={s['n_effect_pro']}（要約を全件読んで目視で仕分け）]")
    print(f"  反対論や批判全般への返事（効果への返事を含む）: {pa[0]}件 ({pa[1]}%)")
    print(f"  うち、効果をめぐる反対の主張（効果はない・価格は下がらない・円安や物価高を招く等）への返事: {pe[0]}件 ({pe[1]}%)")
    print(f"  「減税がなかった場合」と明示して比べる投稿: {pc[0]}件 ({pc[1]}%)")
    print(f"  参考: 語句判定（REPLY）で選ぶと {pr[0]}件 ({pr[1]}%)")
    print(f"[条件付き賛成の効果の投稿 n={s['n_effect_cond']}] 設計が小さい/短いと書く: {s['cond_small'][0]}件 ({s['cond_small'][1]}%) / 投稿者{s['cond_small'][2]}人。"
          f"そのうち対象の拡大・一律・恒久などを求める: {s['cond_expand'][0]}件 ({s['cond_expand'][1]}%)")


def place_small_labels(ax, smalls, y, bar_h, fp, color="#555555"):
    """幅の狭い区間の数値を棒の上に小さく出す。近い値同士は高さをずらして重ねない。"""
    smalls = sorted(smalls)
    last_x, level = -99.0, 0
    for cx, text in smalls:
        level = level + 1 if cx - last_x < 6.0 else 0
        ax.text(cx, y + bar_h / 2 + 0.07 + 0.17 * (level % 2), text, ha="center", va="bottom", fontproperties=fp, fontsize=fs(9.6), color=color, zorder=5)
        last_x = cx


# ---- 図 -------------------------------------------------------------------

def figs(s: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager as fm

    reg = fm.FontProperties(fname="/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc")
    bold = fm.FontProperties(fname="/System/Library/Fonts/ヒラギノ角ゴシック W7.ttc")
    color = {PRO: "#3f7f6f", COND: "#8c7fc6", NEU: "#9aa1a8", CON: "#c8805a"}
    short = {PRO: "減税推進", COND: "条件付き賛成・政府案に不満", NEU: "中立・情報", CON: "減税反対・慎重"}
    caption = f"データ: SNS反応まっぷ「消費税減税」公開投稿サンプル（2026-07-28〜09-24収集、意見{s['n_opinion']:,}件中）"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 図1 論点ごとの立場（100%積み上げ横棒）。賛成→条件付き→反対の順に並べ、中立は右端に置く
    order1 = [PRO, COND, CON, NEU]
    rows =[("全体", None), ("公約と政治不信", "公約と政治不信"), ("対象範囲", "減税の対象範囲"), ("効果", EFFECT), ("財源と社会保障", "財源と社会保障")]
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=200)
    fig.patch.set_facecolor("white")
    ys = list(range(len(rows)))[::-1]
    for y, (label, issue) in zip(ys, rows):
        d = s["stance_all"] if issue is None else s["stance_by_issue"][issue]
        n = s["n_opinion"] if issue is None else sum(v[0] for v in d.values())
        left = 0.0
        if issue == EFFECT:
            ax.add_patch(plt.Rectangle((-0.5, y - 0.47), 101.0, 0.94, fill=False, ec="#b8862b", lw=2.2, zorder=0))
        for st in order1:
            w = d[st][1]
            ax.barh(y, w, left=left, height=0.62, color=color[st], edgecolor="white", linewidth=1.2, zorder=2)
            if st == NEU:
                # 中立・情報は棒の右端に置き、数値は右の余白に出す（幅が狭くても読める）
                ax.text(100.9, y, f"中立 {w:.1f}%", ha="left", va="center", fontproperties=reg, fontsize=fs(10), color="#5f666d", zorder=3)
            elif w >= 5.0:
                size = fs(11.5) if w >= 12.0 else (fs(9.5) if w >= 8.0 else 9.2)
                ax.text(left + w / 2, y, f"{w:.1f}%", ha="center", va="center", color="white", fontproperties=bold, fontsize=size, zorder=3)
            left += w
        ax.text(-2.0, y + 0.06, label, ha="right", va="center", fontproperties=bold if issue == EFFECT else reg, fontsize=fs(12.5))
        ax.text(-2.0, y - 0.24, f"{n:,}件", ha="right", va="center", fontproperties=reg, fontsize=fs(9.5), color="#666666")
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.axis("off")
    handles = [plt.Rectangle((0, 0), 1, 1, color=color[st]) for st in order1]
    ax.legend(handles, [short[st] for st in order1], loc="upper center", bbox_to_anchor=(0.46, 1.13), ncol=4, frameon=False, prop=reg, fontsize=fs(9.5), handlelength=1.1, columnspacing=1.2)
    fig.text(0.5, 0.955, "論点ごとに見た、賛否の割合", ha="center", va="center", fontproperties=bold, fontsize=fs(17))
    omitted = [(k, sum(v[0] for v in s["stance_by_issue"][k].values())) for k in ("給付など他策との比較", "事業者の実務負担", "その他")]
    fig.text(0.015, 0.062, "ほかの論点は表示を省略: " + "、".join(f"{k}{n:,}件" for k, n in omitted), ha="left", va="bottom", fontproperties=reg, fontsize=fs(8.6), color="#666666")
    fig.text(0.015, 0.02, caption, ha="left", va="bottom", fontproperties=reg, fontsize=fs(8.6), color="#666666")
    fig.subplots_adjust(left=0.20, right=0.865, top=0.795, bottom=0.13)
    fig.savefig(OUT_DIR / "consumption-tax-cut3_fig1-stance-by-issue.png")
    plt.close(fig)

    # 図2 立場ごとに語っていた論点
    palette = {"公約と政治不信": "#5b7c99", "減税の対象範囲": "#93aec6", EFFECT: "#d9a441", "財源と社会保障": "#6f6f6f", "その他": "#cfcfcf"}
    order = ["公約と政治不信", "減税の対象範囲", EFFECT, "財源と社会保障", "その他"]
    names = {"公約と政治不信": "公約と政治不信", "減税の対象範囲": "対象範囲", EFFECT: "効果", "財源と社会保障": "財源と社会保障", "その他": "給付など他策との比較・事業者の実務負担・その他"}
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=200)
    fig.patch.set_facecolor("white")
    rows2 = [(PRO, "減税推進"), (CON, "減税反対・慎重")]
    for y, (st, label) in zip([1, 0], rows2):
        d = s["issue_by_stance"][st]
        n = sum(v[0] for v in d.values())
        merged = {k: d[k][1] for k in order[:-1]}
        other_n = d["給付など他策との比較"][0] + d["事業者の実務負担"][0] + d["その他"][0]
        merged["その他"] = pct(other_n, n)  # 丸めた値を足さず、件数から求める
        left = 0.0
        smalls = []
        for k in order:
            w = merged[k]
            ax.barh(y, w, left=left, height=0.52, color=palette[k], edgecolor="white", linewidth=1.2, zorder=2)
            if k == EFFECT:
                ax.add_patch(plt.Rectangle((left + 0.15, y - 0.30), w - 0.3, 0.60, fill=False, ec="#8a5a00", lw=2.0, zorder=3))
            if w >= 8.0:
                size = fs(11.2) if k == EFFECT else (fs(12) if w >= 12.0 else fs(9.8))
                ax.text(left + w / 2, y, f"{w:.1f}%", ha="center", va="center", color="white" if k not in ("その他", "減税の対象範囲") else "#222222", fontproperties=bold, fontsize=size, zorder=4)
            else:
                smalls.append((left + w / 2, f"{w:.1f}%"))
            left += w
        place_small_labels(ax, smalls, y, 0.52, reg)
        ax.text(-2.0, y + 0.05, label, ha="right", va="center", fontproperties=bold, fontsize=fs(13.5))
        ax.text(-2.0, y - 0.2, f"{n:,}件", ha="right", va="center", fontproperties=reg, fontsize=fs(10), color="#666666")
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.6, 1.6)
    ax.axis("off")
    handles = [plt.Rectangle((0, 0), 1, 1, color=palette[k]) for k in order]
    ax.legend(handles, [names[k] for k in order], loc="upper center", bbox_to_anchor=(0.5, -0.04), ncol=3, frameon=False, prop=reg, fontsize=fs(10), handlelength=1.1, columnspacing=1.4)
    fig.text(0.5, 0.955, "減税推進と反対・慎重の投稿が、主に語っていた論点", ha="center", va="center", fontproperties=bold, fontsize=fs(17))
    fig.text(0.5, 0.905, "各投稿の主な論点は1つに決めて集計", ha="center", va="center", fontproperties=reg, fontsize=fs(10.5), color="#666666")
    fig.text(0.015, 0.02, caption, ha="left", va="bottom", fontproperties=reg, fontsize=fs(8.6), color="#666666")
    fig.subplots_adjust(left=0.235, right=0.975, top=0.84, bottom=0.22)
    fig.savefig(OUT_DIR / "consumption-tax-cut3_fig2-issue-by-stance.png")
    plt.close(fig)
    print("書き出し:", OUT_DIR / "consumption-tax-cut3_fig1-stance-by-issue.png")
    print("書き出し:", OUT_DIR / "consumption-tax-cut3_fig2-issue-by-stance.png")


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "numbers"
    s = stats(load())
    if mode == "numbers":
        show(s)
    elif mode == "figs":
        figs(s)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
