#!/usr/bin/env python3
"""note「消費税減税」第4回の数字と図を、正典のJSONから再現する。

使い方（非公開の正典 social-samples/ を復元した作業ツリーのルートで実行する）:
    python3 content/note/drafts/figures/consumption-tax-cut4_build.py numbers
    python3 content/note/drafts/figures/consumption-tax-cut4_build.py figs

numbers: 記事の本文・図・注記に使う数字をすべて表示する（品質監査はここを突き合わせる）。
figs   : 図2（話題ごとの賛成の割合。決定の前と後）を content/note/drafts/images/ に書き出す（1800x1040）。
         図1は、サイトの推移グラフの画像（docs/images/trend/consumption-tax-cut-stance-trend-summary.png。ひと目版）を
         書き換えずにそのまま使う（利用条件: 出典とリンクを明記する。切り取りや書き換えはしない）。

集計の対象は classification.is_relevant かつ classification.is_opinion の投稿（意見）。
「回」は fetched_at（UTC）を日本時間に直した収集日。サイトの「意見の推移」と同じ定義で、
scripts/build_trend_section.py の rounds_for と全回の件数・割合が一致することを、この中で確かめる。
決定の前＝大綱の閣議決定（2026-09-15）より前に収集した6回、決定のあと＝9/15以降に収集した3回。
"""

from __future__ import annotations

import collections
import datetime
import json
import math
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
SAMPLE = ROOT / "social-samples" / "consumption-tax-cut_hermes_arena_classified.json"
OUT_DIR = Path(os.environ.get("FIG_OUT") or ROOT / "content" / "note" / "drafts" / "images")

JST = datetime.timezone(datetime.timedelta(hours=9))
OUTLINE_DAY = "2026-09-15"  # 大綱の閣議決定。これ以降に収集した回を「決定のあと」とする
Z95 = 1.96

PRO, COND, CON, NEU = "減税推進", "条件付き賛成・政府案に不満", "減税反対・慎重", "中立・情報"
STANCES = [PRO, COND, CON, NEU]
ISSUES = ["公約と政治不信", "減税の対象範囲", "減税の効果", "財源と社会保障", "給付など他策との比較", "事業者の実務負担", "その他"]
SHOWN = ["公約と政治不信", "減税の対象範囲", "減税の効果", "財源と社会保障"]  # 図2に出す論点（件数が十分ある4つ）
SMALL = ["給付など他策との比較", "事業者の実務負担"]  # 件数が少ないので本文・図に出さず、注記で触れる

# 毎回20件以上拾えた検索語（20本のうち12本）。検索語の拾える量が回で違う影響を除く確認に使う
SKEPTIC_QUERIES = {"消費税減税 意味ない", "消費税減税 効果", "消費税減税 反対"}
SUPPORT_RX = r"支援金"  # 大綱が設けた現金給付（就業者負担軽減支援金）の通称。ほかの支援金（補助金の言い換えなど）も含む
BENEFIT_RX = r"給付付き|税額控除"  # 別の制度（給付付き税額控除）に触れる語


def load() -> list[dict]:
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    return [x for x in data if x["classification"].get("is_relevant") and x["classification"].get("is_opinion")]


def collected_day(x: dict) -> str:
    stamp = datetime.datetime.fromisoformat(x["fetched_at"].replace("Z", "+00:00"))
    return stamp.astimezone(JST).date().isoformat()


def posted_day(x: dict) -> datetime.date:
    ms = (int(x["tweet_id"]) >> 22) + 1288834974657  # X の snowflake ID から投稿時刻を復元
    return datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc).astimezone(JST).date()


def pct(k: int, n: int) -> float:
    return k / n * 100 if n else float("nan")


def margin(k: int, n: int) -> float:
    p = k / n
    return Z95 * math.sqrt(p * (1 - p) / n) * 100


def beyond(k0: int, n0: int, k1: int, n1: int) -> bool:
    """2つの割合の差が、投稿の拾い方に偏りがない場合のぶれ（95%）を超えるか（サイトと同じ判定）。"""
    p0, p1 = k0 / n0, k1 / n1
    se = math.sqrt(p0 * (1 - p0) / n0 + p1 * (1 - p1) / n1)
    return abs(p1 - p0) > Z95 * se


def share(rows: list[dict], key: str, value: str) -> tuple[int, int]:
    return sum(1 for x in rows if x[key] == value), len(rows)


def prepare(op: list[dict]) -> list[dict]:
    for x in op:
        x["_day"] = collected_day(x)
        x["_st"] = x["classification"]["stance"]
        x["_is"] = x["classification"]["main_issue"]
        x["_lag"] = (datetime.date.fromisoformat(x["_day"]) - posted_day(x)).days  # 収集日の何日前に書かれたか
    return op


def stats(op: list[dict]) -> dict:
    s: dict = {"n_opinion": len(op)}
    rounds = sorted({x["_day"] for x in op})
    s["rounds"] = rounds
    pre_days = [r for r in rounds if r < OUTLINE_DAY]
    post_days = [r for r in rounds if r >= OUTLINE_DAY]
    s["pre_days"], s["post_days"] = pre_days, post_days
    pre = [x for x in op if x["_day"] in pre_days]
    post = [x for x in op if x["_day"] in post_days]

    def table(rows: list[dict]) -> dict:
        out = {}
        for r in rounds:
            rr = [x for x in rows if x["_day"] == r]
            out[r] = {"n": len(rr), **{st: sum(1 for x in rr if x["_st"] == st) for st in STANCES}}
        return out

    s["by_round"] = table(op)

    # サイトの「意見の推移」と同じ数字か（表の割合・件数が一致すること）
    import build_trend_section as site  # type: ignore[import-not-found]

    site_rounds = site.rounds_for("consumption-tax-cut", SAMPLE, "stance")
    mine = s["by_round"]
    s["site_match"] = all(
        row["date"] == r and row["n"] == mine[r]["n"] and all(row["counts"][st] == mine[r][st] for st in STANCES)
        for row, r in zip(site_rounds, rounds)
    ) and len(site_rounds) == len(rounds)

    def pooled(rows: list[dict]) -> dict:
        return {st: (sum(1 for x in rows if x["_st"] == st), len(rows)) for st in STANCES}

    s["pre"], s["post"] = pooled(pre), pooled(post)
    s["pre_n"], s["post_n"] = len(pre), len(post)
    # 同じAI（kimi-k2.6）で判定した回だけ。10/3の回は kimi-k2.7-code に替わった
    post_same_ai = [x for x in op if x["_day"] in ("2026-09-17", "2026-09-24")]
    s["post_same_ai"] = pooled(post_same_ai)
    s["post_same_ai_topics"] = {
        i: (sum(1 for x in post_same_ai if x["_is"] == i and x["_st"] == PRO), sum(1 for x in post_same_ai if x["_is"] == i)) for i in ISSUES
    }

    # 話題ごとの賛成の割合（決定の前・後）
    topics = {}
    for i in ISSUES:
        a = [x for x in pre if x["_is"] == i]
        b = [x for x in post if x["_is"] == i]
        ka, na = share(a, "_st", PRO)
        kb, nb = share(b, "_st", PRO)
        topics[i] = {"pre": (ka, na), "post": (kb, nb), "beyond": beyond(ka, na, kb, nb), "mix_pre": pct(na, len(pre)), "mix_post": pct(nb, len(post))}
    s["topics"] = topics
    # 話題の構成を決定の前に揃えたときの、全体の賛成の割合（構成の入れ替わりでは説明できないことの確認）
    mix_pre = {i: topics[i]["pre"][1] / len(pre) for i in ISSUES}
    s["post_with_pre_mix"] = sum(mix_pre[i] * pct(*topics[i]["post"]) for i in ISSUES if topics[i]["post"][1])

    # 1回の収集で新しく見つかった意見の数（平均）。割合の低下が、賛成の減少か反対の増加かを見る
    def per_round_mean(rows: list[dict], days: list[str]) -> float:
        return sum(1 for x in rows if x["_day"] in days) / len(days)

    s["per_round"] = {
        st: (per_round_mean([x for x in op if x["_st"] == st], pre_days), per_round_mean([x for x in op if x["_st"] == st], post_days))
        for st in STANCES
    }
    s["per_round"]["意見全体"] = (per_round_mean(op, pre_days), per_round_mean(op, post_days))
    s["per_round_topic"] = {
        i: {
            st: (
                per_round_mean([x for x in op if x["_is"] == i and x["_st"] == st], pre_days),
                per_round_mean([x for x in op if x["_is"] == i and x["_st"] == st], post_days),
            )
            for st in (PRO, CON)
        }
        for i in ISSUES
    }
    users_per_round = lambda st, days: sum(len({x["user_id"] for x in op if x["_day"] == r and x["_st"] == st}) for r in days) / len(days)
    s["users_per_round"] = {st: (users_per_round(st, pre_days), users_per_round(st, post_days)) for st in (PRO, CON)}
    # 対象範囲の賛成の投稿の中身（AIの要約に「廃止」「一律」を含む割合）。決定の前後でほぼ同じか
    scope = {"pre": [x for x in pre if x["_is"] == "減税の対象範囲" and x["_st"] == PRO], "post": [x for x in post if x["_is"] == "減税の対象範囲" and x["_st"] == PRO]}
    s["scope_pro"] = {
        k: {"n": len(v), "abolish": sum(1 for x in v if "廃止" in x["classification"].get("summary", "")), "flat": sum(1 for x in v if "一律" in x["classification"].get("summary", ""))}
        for k, v in scope.items()
    }

    # 頑健性: 数え方を変えても、決定のあとが前より低いか
    def pro_pre_post(rows: list[dict], label: str) -> tuple[str, float, int, float, int]:
        a = [x for x in rows if x["_day"] in pre_days]
        b = [x for x in rows if x["_day"] in post_days]
        return label, pct(sum(1 for x in a if x["_st"] == PRO), len(a)), len(a), pct(sum(1 for x in b if x["_st"] == PRO), len(b)), len(b)

    recent = [x for x in op if x["_lag"] <= 2]
    seen: set = set()
    one_per_user = []
    for x in sorted(op, key=lambda r: (r["_day"], r["tweet_id"])):
        k = (x["_day"], x["user_id"])
        if k not in seen:
            seen.add(k)
            one_per_user.append(x)
    qn = collections.defaultdict(collections.Counter)
    for x in op:
        qn[x["query"]][x["_day"]] += 1
    stable = sorted(q for q in qn if all(qn[q][r] >= 20 for r in rounds))
    s["stable_queries"] = stable
    s["robust"] = [
        pro_pre_post(op, "そのまま（サイトと同じ）"),
        pro_pre_post(recent, "収集日の2日前までに書かれた投稿だけ"),
        pro_pre_post(one_per_user, "同じ人は1回の収集に1投稿だけ"),
        pro_pre_post([x for x in op if x["query"] in stable], "毎回20件以上拾えた検索語12本だけ"),
        pro_pre_post([x for x in op if x["query"] not in SKEPTIC_QUERIES], "検索語「意味ない」「効果」「反対」を除く"),
        pro_pre_post([x for x in recent if x["query"] in stable], "2日前まで かつ 検索語12本"),
    ]
    # 検索語の構成を全期間の割合に固定して数え直す（各回5件以上の検索語のみ）
    tot = collections.Counter(x["query"] for x in op)

    def standardised(day_set: list[str]) -> float:
        num = den = 0.0
        for q in tot:
            rows = [x for x in op if x["query"] == q and x["_day"] in day_set]
            if len(rows) < 5 * len(day_set):
                continue
            num += tot[q] * sum(1 for x in rows if x["_st"] == PRO) / len(rows)
            den += tot[q]
        return num / den * 100

    s["standardised"] = (standardised(pre_days), standardised(post_days))
    s["recent_by_round"] = table(recent)
    s["recent_pre_post"] = (pooled([x for x in recent if x["_day"] in pre_days]), pooled([x for x in recent if x["_day"] in post_days]))
    s["old_share_by_round"] = {r: pct(sum(1 for x in op if x["_day"] == r and x["_lag"] >= 4), s["by_round"][r]["n"]) for r in rounds}

    # 誰が書いているか
    by_user = collections.defaultdict(list)
    for x in op:
        by_user[x["user_id"]].append(x)
    multi = {u: v for u, v in by_user.items() if len({x["_day"] for x in v}) >= 2}
    s["users"] = (len(by_user), len(multi), sum(len(v) for v in multi.values()))
    both_all = both = 0
    pro_before = pro_stay = pro_to_con = pro_to_cond = pro_to_neu = 0
    con_before = con_stay = con_to_pro = 0
    for v in by_user.values():
        a = [x for x in v if x["_day"] in pre_days]
        b = [x for x in v if x["_day"] in post_days]
        if not (a and b):
            continue
        both_all += 1

        def major(vs: list[dict]) -> str | None:
            c = collections.Counter(x["_st"] for x in vs).most_common()
            return None if len(c) > 1 and c[0][1] == c[1][1] else c[0][0]

        ma, mb = major(a), major(b)
        if ma is None or mb is None:
            continue
        both += 1
        if ma == PRO:
            pro_before += 1
            pro_stay += mb == PRO
            pro_to_con += mb == CON
            pro_to_cond += mb == COND
            pro_to_neu += mb == NEU
        if ma == CON:
            con_before += 1
            con_stay += mb == CON
            con_to_pro += mb == PRO
    s["panel"] = {"both_all": both_all, "both": both, "pro_before": pro_before, "pro_stay": pro_stay, "pro_to_con": pro_to_con,
                  "pro_to_cond": pro_to_cond, "pro_to_neu": pro_to_neu, "con_before": con_before, "con_stay": con_stay, "con_to_pro": con_to_pro}
    heavy = sorted(((len(v), u) for u, v in by_user.items()), reverse=True)
    s["heavy"] = {"ge10_users": sum(1 for c, _ in heavy if c >= 10), "ge10_posts": sum(c for c, _ in heavy if c >= 10), "top": heavy[0][0]}

    # 件数の動きは割合の言い直しか（検索1回で拾える数に上限があるため）。記事では件数を根拠に使わない
    stable_set = set(stable)
    s["counts_by_group"] = {}
    for label, qs in (("毎回20件以上拾えた検索語12本", stable_set), ("残りの8本", {q for q in qn if q not in stable_set}), ("全20本", set(qn))):
        s["counts_by_group"][label] = {
            st: (per_round_mean([x for x in op if x["query"] in qs and x["_st"] == st], pre_days),
                 per_round_mean([x for x in op if x["query"] in qs and x["_st"] == st], post_days))
            for st in STANCES
        }
    raw_max = []
    for f in sorted((ROOT / "social-samples" / "updates" / "consumption-tax-cut").glob("*/raw.json")):
        rows = json.loads(f.read_text(encoding="utf-8"))
        c = collections.Counter(r.get("query") for r in rows)
        raw_max.append((f.parent.name, len(rows), max(c.values())))
    s["raw_cap"] = raw_max  # 取得した1ページ全体の件数と、1検索語あたりの最大件数
    # 決定の前後の両方に書いた人（179人）だけで見た、賛成の割合
    both_users = {u for u, v in by_user.items() if any(x["_day"] in pre_days for x in v) and any(x["_day"] in post_days for x in v)}
    pa = [x for x in pre if x["user_id"] in both_users]
    pb = [x for x in post if x["user_id"] in both_users]
    s["both_users_share"] = (len(both_users), sum(1 for x in pa if x["_st"] == PRO), len(pa), sum(1 for x in pb if x["_st"] == PRO), len(pb))
    # 本文が同じ投稿を除く／書いた日で分ける
    def norm(x: dict) -> str:
        t = re.sub(r"https?://\S+", "", x["text"].replace("\tSTART\t", "").replace("\tEND\t", ""))
        return re.sub(r"[\s　]+", "", re.sub(r"@\w+", "", t))

    seen_text: set = set()
    dedup = []
    for x in sorted(op, key=lambda r: (r["_day"], r["tweet_id"])):
        k = norm(x)
        if k not in seen_text:
            seen_text.add(k)
            dedup.append(x)
    s["dup_text"] = (len(op) - len(dedup),) + pro_pre_post(dedup, "本文が同じ投稿を除く")[1:]
    cut = datetime.date.fromisoformat(OUTLINE_DAY)
    pb_dates = [(x, posted_day(x)) for x in op]
    pre_p = [x for x, d in pb_dates if d < cut]
    post_p = [x for x, d in pb_dates if d >= cut]
    s["by_posted_day"] = (pct(sum(1 for x in pre_p if x["_st"] == PRO), len(pre_p)), len(pre_p), pct(sum(1 for x in post_p if x["_st"] == PRO), len(post_p)), len(post_p))
    r17 = [x for x in op if x["_day"] == "2026-09-17"]
    s["r17_old"] = (sum(1 for x in r17 if posted_day(x) < cut), len(r17))

    # 大綱で設けた現金給付（就業者負担軽減支援金）は、SNSでどれだけ語られたか
    def text_of(x: dict) -> str:
        return x["text"].replace("\tSTART\t", "").replace("\tEND\t", "") + " " + x["classification"].get("summary", "")

    s["support_mentions"] = sum(1 for x in op if re.search(SUPPORT_RX, text_of(x)))
    s["support_mentions_post"] = sum(1 for x in post if re.search(SUPPORT_RX, text_of(x)))  # 大綱（9/15）のあとの3回
    s["benefit_mentions"] = sum(1 for x in op if re.search(BENEFIT_RX, text_of(x)))
    return s


def show(s: dict) -> None:
    print(f"意見 n={s['n_opinion']:,}  収集 {len(s['rounds'])}回（日本時間の収集日 {s['rounds'][0]}〜{s['rounds'][-1]}）  （標本: {SAMPLE.name}）")
    print(f"サイトの「意見の推移」の表（scripts/build_trend_section.py）と、全回の件数・立場別の件数が一致: {s['site_match']}")
    print(f"\n[決定の前＝{OUTLINE_DAY}より前に収集した{len(s['pre_days'])}回 {s['pre_days'][0]}〜{s['pre_days'][-1]} / 決定のあと＝{len(s['post_days'])}回 {', '.join(s['post_days'])}]")
    print("\n[回ごとの立場（サイトと同じ）] 収集日 意見数 推進 条件付き 反対慎重 中立")
    for r in s["rounds"]:
        d = s["by_round"][r]
        print(f"  {r}  {d['n']:4d}  " + "  ".join(f"{pct(d[st], d['n']):5.1f}%" for st in STANCES))
    print("\n[決定の前後でまとめた立場の割合（±は95%のぶれ）]")
    for st in STANCES:
        ka, na = s["pre"][st]
        kb, nb = s["post"][st]
        flag = "ぶれを超える" if beyond(ka, na, kb, nb) else "ぶれの範囲"
        print(f"  {st}: {pct(ka, na):.1f}%（±{margin(ka, na):.1f}, n={na}）→ {pct(kb, nb):.1f}%（±{margin(kb, nb):.1f}, n={nb}）  差 {pct(kb, nb) - pct(ka, na):+.1f}  {flag}")
    kb, nb = s["post_same_ai"][PRO]
    print(f"  同じAIで判定した決定後2回（9/17・9/24）だけ: 減税推進 {pct(kb, nb):.1f}%（±{margin(kb, nb):.1f}, n={nb}）")
    print("  同じAIで判定した決定後2回だけの、話題ごとの賛成の割合: " + "、".join(f"{i} {pct(*v):.1f}%（n={v[1]}）" for i, v in s["post_same_ai_topics"].items() if i in SHOWN))
    print(f"  何らかの減税を望む側（推進＋条件付き）: {pct(s['pre'][PRO][0] + s['pre'][COND][0], s['pre_n']):.1f}% → {pct(s['post'][PRO][0] + s['post'][COND][0], s['post_n']):.1f}%")
    print("\n[話題ごとの賛成（減税推進）の割合 決定の前 → 後]")
    for i in ISSUES:
        t = s["topics"][i]
        (ka, na), (kb, nb) = t["pre"], t["post"]
        print(f"  {i}: {pct(ka, na):.1f}%（±{margin(ka, na):.1f}, n={na}）→ {pct(kb, nb):.1f}%（±{margin(kb, nb):.1f}, n={nb}）  差 {pct(kb, nb) - pct(ka, na):+.1f}  {'ぶれを超える' if t['beyond'] else 'ぶれの範囲'}"
              f"  [話題の割合 {t['mix_pre']:.1f}% → {t['mix_post']:.1f}%]")
    print(f"  話題の構成を決定の前に揃えて、決定後の話題ごとの賛成の割合を当てはめた全体: {s['post_with_pre_mix']:.1f}%（実際の決定後は {pct(*s['post'][PRO]):.1f}%）")
    print("\n[1回の収集で新しく見つかった意見の数（平均）決定の前6回 → あと3回]")
    for k, (a, b) in s["per_round"].items():
        print(f"  {k}: {a:.1f} → {b:.1f}  ({(b / a - 1) * 100:+.0f}%)")
    for st, (a, b) in s["users_per_round"].items():
        print(f"  {st}を書いた投稿者の数（1回あたり）: {a:.1f} → {b:.1f}")
    print("  話題×立場ごと（1回あたり）:")
    for i in ISSUES[:6]:
        t = s["per_round_topic"][i]
        print(f"    {i}: 賛成 {t[PRO][0]:.1f} → {t[PRO][1]:.1f} ({(t[PRO][1] / t[PRO][0] - 1) * 100:+.0f}%) / 反対・慎重 {t[CON][0]:.1f} → {t[CON][1]:.1f} ({(t[CON][1] / t[CON][0] - 1) * 100:+.0f}%)")
    sp = s["scope_pro"]
    print(f"  対象範囲の賛成の投稿の要約に「廃止」を含む割合: 決定の前 {pct(sp['pre']['abolish'], sp['pre']['n']):.1f}%（n={sp['pre']['n']}）→ あと {pct(sp['post']['abolish'], sp['post']['n']):.1f}%（n={sp['post']['n']}）、「一律」を含む割合 {pct(sp['pre']['flat'], sp['pre']['n']):.1f}% → {pct(sp['post']['flat'], sp['post']['n']):.1f}%")
    print("\n[数え方を変えても、決定のあとは前より低いか（減税推進の割合 前 → 後）]")
    for label, a, na, b, nb in s["robust"]:
        print(f"  {label}: {a:.1f}%（n={na}）→ {b:.1f}%（n={nb}）  差 {b - a:+.1f}")
    print(f"  検索語の構成を全期間の割合に固定: {s['standardised'][0]:.1f}% → {s['standardised'][1]:.1f}%  差 {s['standardised'][1] - s['standardised'][0]:+.1f}")
    print("\n[収集日の2日前までに書かれた投稿だけの、回ごとの減税推進の割合]")
    print("  " + "  ".join(f"{r[5:]} {pct(d[PRO], d['n']):.1f}%(n={d['n']})" for r, d in s["recent_by_round"].items()))
    print("  収集日の4日以上前に書かれた投稿の割合: " + "  ".join(f"{r[5:]} {v:.0f}%" for r, v in s["old_share_by_round"].items()))
    (a, b) = s["recent_pre_post"]
    print(f"  2日前まで・決定の前後: 減税推進 {pct(*a[PRO]):.1f}% → {pct(*b[PRO]):.1f}%、反対・慎重 {pct(*a[CON]):.1f}% → {pct(*b[CON]):.1f}%、中立・情報 {pct(*a[NEU]):.1f}% → {pct(*b[NEU]):.1f}%")
    u, m, mp = s["users"]
    print(f"\n[誰が書いているか] 投稿者 {u:,}人。2回以上の収集に登場した投稿者 {m}人（{pct(m, u):.1f}%、その投稿 {mp:,}件）。1回の収集にしか登場しない投稿者 {pct(u - m, u):.1f}%")
    p = s["panel"]
    print(f"  決定の前にも後にも書いた投稿者 {p['both_all']}人。立場が同点の人を除く{p['both']}人のうち、前に賛成が多数だった{p['pro_before']}人は、後も賛成 {p['pro_stay']}人・反対・慎重へ {p['pro_to_con']}人・条件付き賛成へ {p['pro_to_cond']}人・中立へ {p['pro_to_neu']}人。"
          f"前に反対・慎重が多数だった{p['con_before']}人は、後も反対・慎重 {p['con_stay']}人・賛成へ {p['con_to_pro']}人")
    h = s["heavy"]
    print(f"  意見を10件以上書いた投稿者 {h['ge10_users']}人で {h['ge10_posts']}件（全体の{pct(h['ge10_posts'], s['n_opinion']):.1f}%）。最多は1人で{h['top']}件")
    print(f"\n[現金給付への言及] 「支援金」という語を含む意見 {s['support_mentions']}件（うち大綱のあとの3回に{s['support_mentions_post']}件。残りは8/3の別の話題）、「給付付き」「税額控除」に触れる意見 {s['benefit_mentions']}件（意見{s['n_opinion']:,}件中）")
    print("\n[件数の動きは割合の言い直し（記事では件数を根拠に使わない）] 1回の収集で新しく見つかった意見の数（平均）前6回 → あと3回")
    for label, d in s["counts_by_group"].items():
        print(f"  {label}: " + " / ".join(f"{st[:4]} {a:.0f}→{b:.0f}({(b / a - 1) * 100:+.0f}%)" for st, (a, b) in d.items()))
    print("  生データ（取得した1ページ全体）の件数と、1検索語あたりの最大件数: " + "、".join(f"{d} {n}件・最大{m}" for d, n, m in s["raw_cap"]))
    nb, ka, na, kb, nb2 = s["both_users_share"]
    print(f"\n[決定の前後の両方に書いた{nb}人だけで見た賛成の割合] {pct(ka, na):.1f}%（{na}投稿）→ {pct(kb, nb2):.1f}%（{nb2}投稿）")
    d = s["dup_text"]
    print(f"[本文が同じ投稿{d[0]}件を除く] 賛成 {d[1]:.1f}%（n={d[2]}）→ {d[3]:.1f}%（n={d[4]}）")
    bp = s["by_posted_day"]
    print(f"[書いた日（日本時間）で分ける] 9/14まで {bp[0]:.1f}%（n={bp[1]}）→ 9/15以降 {bp[2]:.1f}%（n={bp[3]}）。9月17日の回のうち9/14以前に書かれた投稿 {s['r17_old'][0]}/{s['r17_old'][1]}件")


# ---- 図 -------------------------------------------------------------------

def figs(s: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager as fm

    reg = fm.FontProperties(fname="/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc")
    bold = fm.FontProperties(fname="/System/Library/Fonts/ヒラギノ角ゴシック W7.ttc")
    teal, pale, grey, gold = "#3f7f6f", "#a9c9c0", "#8a9199", "#b8862b"
    FONT_SCALE = 1.2
    fs = lambda size: round(size * FONT_SCALE, 1)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    d0, d1 = s["rounds"][0][5:].replace("-", "/"), s["rounds"][-1][5:].replace("-", "/")
    caption = (f"データ: SNS反応まっぷ「消費税減税」公開投稿サンプル（収集日2026/{d0}〜{d1}・日本時間、意見{s['n_opinion']:,}件中）。"
               "世論調査ではありません")
    small = [(i, s["topics"][i]) for i in SMALL]
    note1 = "賛成＝減税推進（条件付き賛成は含みません）。話題は、AIが付けた投稿の主な論点です"
    note2 = "省略: " + "、".join(f"{i}（{pct(*t['pre']):.0f}%→{pct(*t['post']):.0f}%）" for i, t in small) + "は件数が少なく、ぶれが大きいため。どちらも下がる向きです"

    rows = [("全体", s["pre"][PRO], s["post"][PRO])] + [(lab, s["topics"][i]["pre"], s["topics"][i]["post"]) for lab, i in
                                                       (("公約と政治不信", "公約と政治不信"), ("減税の効果", "減税の効果"), ("財源と社会保障", "財源と社会保障"), ("対象範囲", "減税の対象範囲"))]
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=200)
    fig.patch.set_facecolor("white")
    ys = list(range(len(rows)))[::-1]
    for y, (label, (ka, na), (kb, nb)) in zip(ys, rows):
        a_, b_ = pct(ka, na), pct(kb, nb)
        flat = label == "対象範囲"
        if flat:
            ax.add_patch(plt.Rectangle((-0.5, y - 0.46), 112.0, 0.92, fill=False, ec=gold, lw=2.2, zorder=0))
        ax.annotate("", xy=(b_, y), xytext=(a_, y), arrowprops=dict(arrowstyle="-|>", color=grey, lw=2.2, shrinkA=8, shrinkB=8), zorder=1)
        ax.scatter([a_], [y], s=140, color=pale, edgecolor=teal, linewidth=1.8, zorder=3)
        ax.scatter([b_], [y], s=140, color=teal, edgecolor=teal, linewidth=1.8, zorder=3)
        lf = a_ < b_
        ax.text(a_ + (-3.0 if lf else 3.0), y, f"{a_:.0f}%", ha="right" if lf else "left", va="center", fontproperties=reg, fontsize=fs(11), color="#555555", zorder=4)
        ax.text(b_ + (3.0 if lf else -3.0), y, f"{b_:.0f}%", ha="left" if lf else "right", va="center", fontproperties=bold, fontsize=fs(11.5), color=teal, zorder=4)
        diff = b_ - a_
        ax.text(110, y + 0.03, f"{diff:+.0f}ポイント".replace("-", "−"), ha="right", va="center", fontproperties=bold, fontsize=fs(11.5), color="#7a3b1a" if diff < -4 else "#444444")
        ax.text(-4.0, y + 0.07, label, ha="right", va="center", fontproperties=bold if label in ("全体", "対象範囲") else reg, fontsize=fs(12.5))
        ax.text(-4.0, y - 0.25, f"{na:,}→{nb:,}件", ha="right", va="center", fontproperties=reg, fontsize=fs(8.8), color="#666666")
    ax.set_xlim(0, 112)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.axis("off")
    fig.text(0.5, 0.955, "話題ごとに見た、「賛成」の割合の変化", ha="center", va="center", fontproperties=bold, fontsize=fs(17))
    fig.text(0.5, 0.905, "各話題の意見の投稿に占める、減税推進の割合", ha="center", va="center", fontproperties=reg, fontsize=fs(10.5), color="#666666")
    fig.text(0.5, 0.862, "薄い点＝大綱の前（7/28〜9/1の6回）　濃い点＝大綱のあと（9/17〜10/3の3回）", ha="center", va="center", fontproperties=reg, fontsize=fs(9.6), color="#444444")
    fig.text(0.015, 0.118, note1, ha="left", va="bottom", fontproperties=reg, fontsize=fs(8.2), color="#666666")
    fig.text(0.015, 0.072, note2, ha="left", va="bottom", fontproperties=reg, fontsize=fs(8.2), color="#666666")
    fig.text(0.015, 0.022, caption, ha="left", va="bottom", fontproperties=reg, fontsize=fs(8.0), color="#666666")
    fig.subplots_adjust(left=0.215, right=0.985, top=0.78, bottom=0.255)
    out = OUT_DIR / "consumption-tax-cut4_fig2-topic-support.png"
    fig.savefig(out)
    plt.close(fig)
    print("書き出し:", out)


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "numbers"
    s = stats(prepare(load()))
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
