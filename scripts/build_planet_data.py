#!/usr/bin/env python3
"""「議論の惑星」の表示データを正典から生成する（試作版）。

使い方:
    python3 scripts/build_planet_data.py --topic bukatsu-chiiki

データが増えたときは、このコマンドを再実行するだけでよい。
件数・面積・色・標高・大陸の位置はすべてここで計算し、HTMLには数字を持たせない。
同じ入力からは必ず同じ出力になる（乱数を使わない）。
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------- 球面の配置

def fibonacci_points(n: int) -> np.ndarray:
    """球面上へほぼ均等に n 点を置く。面積を測るための標本点。"""
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    theta = math.pi * (1 + 5 ** 0.5) * i
    return np.stack(
        [np.sin(phi) * np.cos(theta), np.sin(phi) * np.sin(theta), np.cos(phi)], axis=1
    )


def stable_order(ids: list[str]) -> list[int]:
    """id のハッシュで並び順を決める。論点が増減しても既存の位置が動きにくい。"""
    keyed = sorted(range(len(ids)), key=lambda i: hashlib.sha1(ids[i].encode()).hexdigest())
    return keyed


def seed_directions(ids: list[str]) -> np.ndarray:
    """論点 id から決定的に中心方向を割り当てる。"""
    n = len(ids)
    base = fibonacci_points(n)
    dirs = np.zeros_like(base)
    for slot, idx in enumerate(stable_order(ids)):
        dirs[idx] = base[slot]
    return dirs


# 海岸線のゆらぎ。真っ直ぐな多角形の境界だとビーチボールに見えるので、
# 岸のあたりだけ境界を波打たせる。テンプレート側の coastNoise と同じ式で、
# 同じ振幅・同じ窓関数を使う（片方だけ変えると、測った面積と描く面積がずれる）。
COAST_NOISE_AMP = 0.085


def coast_noise(p: np.ndarray) -> np.ndarray:
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    return (np.sin(6.7 * x + 2.9 * y + 11.3 * z)
            + 0.55 * np.sin(3.1 * x + 13.1 * y - 7.7 * z)
            + 0.30 * np.sin(17.1 * x - 5.3 * y + 23.3 * z)) / 1.85


def wobble(margin: np.ndarray, noise: np.ndarray, coast: float) -> np.ndarray:
    """岸から離れるほどゆらぎを弱める。振幅は margin に対して単調なので、
    細い輪っかのような描画の破れは出ない。"""
    if coast <= 0 or COAST_NOISE_AMP <= 0:
        return margin
    win = np.maximum(0.0, 1.0 - np.abs(margin - coast) / COAST_NOISE_AMP)
    return margin + COAST_NOISE_AMP * noise * win


def assign_land(dots: np.ndarray, w: np.ndarray, neg: np.ndarray,
                coast: float, noise: np.ndarray | None = None) -> np.ndarray:
    """各標本点の所属を返す。海は -1。

    score_i(p) = dot(p, center_i) + w_i の最大値でその点の所属を決める。
    1位と2位の差が coast より小さい帯は、どの大陸にも属さない海にする
    （境界のまわりが海になるので、大陸が離れて島のように見える）。
    """
    s = dots + w + neg
    if coast <= 0:
        return np.argmax(s, axis=1)
    part = np.partition(s, -2, axis=1)
    margin = part[:, -1] - part[:, -2]
    if noise is not None:
        margin = wobble(margin, noise, coast)
    return np.where(margin >= coast, np.argmax(s, axis=1), -1)


def land_fractions(assign: np.ndarray, k: int, n: int) -> tuple[np.ndarray, float]:
    """陸だけの面積比（陸の合計を1とした比）と、陸が球面に占める割合を返す。"""
    cnt = np.bincount(assign[assign >= 0], minlength=k) / n
    total = float(cnt.sum())
    return (cnt / total if total > 0 else cnt), total


def fit_weights(points: np.ndarray, centers: np.ndarray, targets: np.ndarray,
                iters: int, lr: float = 0.6, coast: float = 0.0) -> np.ndarray:
    """加重ボロノイの重みを、面積比が targets に合うまで調整する。

    海を入れても「面積の比 = 意見数の比」を守るため、合わせるのは
    球面全体に対する割合ではなく **陸の中での割合**。海が何割を占めても、
    大陸どうしの大小関係は意見数のとおりになる。
    """
    k = len(centers)
    w = np.zeros(k)
    active = targets > 0
    dots = points @ centers.T                       # (N, K)
    neg = np.where(active, 0.0, -10.0)
    # 重みの動かし幅を、その領域での dot のばらつきに合わせる。
    # （大陸と島では dot の差の大きさが2桁ちがうため、固定の学習率だと島側が発散する）
    scale = float(dots.std()) or 1.0
    noise = coast_noise(points) if coast > 0 else None
    best_w, best_err = w.copy(), 1e9
    for t in range(iters):
        assign = assign_land(dots, w, neg, coast, noise)
        frac, _ = land_fractions(assign, k, len(points))
        err = float(np.abs(frac - targets).sum())
        if err < best_err:
            best_err, best_w = err, w.copy()
        step = lr * 2 * scale * (1 - 0.85 * t / iters)
        w += step * (targets - frac)
        w[~active] = 0.0
    return best_w


def region_stats(points: np.ndarray, centers: np.ndarray, w: np.ndarray,
                 targets: np.ndarray, coast: float = 0.0
                 ) -> tuple[np.ndarray, np.ndarray, float]:
    """所属（海は -1）、陸の中での面積比、海が球面に占める割合。"""
    neg = np.where(targets > 0, 0.0, -10.0)
    noise = coast_noise(points) if coast > 0 else None
    assign = assign_land(points @ centers.T, w, neg, coast, noise)
    frac, land = land_fractions(assign, len(centers), len(points))
    return assign, frac, 1.0 - land


def centroids(points: np.ndarray, assign: np.ndarray, k: int) -> np.ndarray:
    """大陸名を置く位置。海（-1）は含めないので、名前が海に浮かない。"""
    out = np.zeros((k, 3))
    for i in range(k):
        sel = points[assign == i]
        if len(sel) == 0:
            out[i] = [0, 0, 1]
            continue
        v = sel.mean(axis=0)
        n = np.linalg.norm(v)
        out[i] = v / n if n > 1e-9 else [0, 0, 1]
    return out


def tangent_ring(center: np.ndarray, m: int, spread: float) -> np.ndarray:
    """中心のまわりの接平面上へ m 個の下位シードを決定的に並べる。"""
    ref = np.array([0.0, 0.0, 1.0])
    if abs(float(center @ ref)) > 0.9:
        ref = np.array([1.0, 0.0, 0.0])
    u = np.cross(center, ref)
    u /= np.linalg.norm(u)
    v = np.cross(center, u)
    out = []
    for j in range(m):
        ang = 2 * math.pi * j / m
        # 1つ目は中心に置き、残りを環状に配置する
        r = 0.0 if j == 0 and m > 1 else spread
        p = center + r * (math.cos(ang) * u + math.sin(ang) * v)
        out.append(p / np.linalg.norm(p))
    return np.array(out)


# ---------------------------------------------------------------- データ読み

def dig(obj, path):
    for p in path:
        obj = obj[p]
    return obj


def load_public_theme(topic: str) -> dict:
    """段階6: 陸地の集計は公開JSON（`data/public/themes/{topic}.json`）だけを入力にする。

    非公開正典（social-samples等）を直接読まない。公開JSONは課題57の公開データ契約に
    従って別途生成済みで、論点別の件数・スタンス内訳・強度内訳・主張の照合結果を持つ。
    """
    path = ROOT / "data" / "public" / "themes" / f"{topic}.json"
    return json.loads(path.read_text())


def load_ocean_layer(topic: str) -> dict:
    """沈んだ大陸・地下水脈は公開データ契約（`data/public/themes/`）から読む。

    確認台帳（`data/verification/`）を直接読むと、投稿IDや機械一致の作業記録まで
    惑星データへ入り、そのまま試作HTMLへ埋め込まれる。公開契約を通すことで、
    人が一次資料を読んで確定したことだけが画面へ出る。

    台帳が無いテーマは `status: not_started` で空のまま返る（推測で埋めない。
    工程表「台帳に無い論点の海面下が空で出る」）。
    """
    return load_public_theme(topic).get(
        "ocean_layer",
        {"status": "not_started", "checked_on": None, "reviewer_type": None,
         "sunk_continents": [], "veins": []},
    )


# 判定（fact/gap/miss）を読者向けの文言へ直す（設計書3.3の表）。
# 10テーマ共通の言葉にする。テーマごとに言い換えると、同じ判定が別物に見える。
# miss を「嘘」と書かない。「確認できなかった」で止める（3.3の読者への注意）。
VERDICT_LABELS = {
    "fact": ("実像", "一次資料でも確認できました。「正しい意見」という意味ではありません。"),
    "gap": ("ずれ", "部分的には合っていますが、一次資料とずれている点があります。"),
    "miss": ("蜃気楼", "一次資料では確認できませんでした。誤りと決まったわけではありません。"),
}


def verdict_label(verdict: str) -> str:
    try:
        return VERDICT_LABELS[verdict][0]
    except KeyError:
        raise SystemExit(
            f"判定 '{verdict}' に表示文言がありません。"
            f"使えるのは {' / '.join(VERDICT_LABELS)} だけです（設計書3.3）。"
        ) from None



# 論点1つに複数の主張が付いたときの陸地判定の決め方（設計書14章、段階6で決定）。
# miss（蜃気楼）> gap（ずれ）> fact（実像）の順で最も厳しい判定を採用する。
# 「無いもの」（miss）を多数決で薄めて隠さないため（3.3 の非対称性を陸地の色にも反映する）。
_VERDICT_SEVERITY = {"miss": 2, "gap": 1, "fact": 0}


def _verdict_severity(claim: dict) -> int:
    """判定語を厳しさの順位へ直す。知らない語なら理由を示して止める。"""
    try:
        return _VERDICT_SEVERITY[claim["verdict"]]
    except KeyError:
        raise SystemExit(
            f"主張 {claim.get('id')} の判定 '{claim.get('verdict')}' は使えません。"
            f"使えるのは {' / '.join(_VERDICT_SEVERITY)} だけです（設計書14章、段階1で統一）。"
        ) from None


def issue_verdict(issue_id: str, claims: list[dict]) -> tuple[str | None, list[dict]]:
    matched = [c for c in claims if issue_id in c.get("issue_ids", [])]
    if not matched:
        return None, []
    worst = max(matched, key=_verdict_severity)
    return worst["verdict"], matched


# ---------------------------------------------------------------- 本体

def build(topic: str) -> dict:
    cfg = yaml.safe_load((ROOT / "configs" / "planet" / f"{topic}.yaml").read_text())
    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text())
    t = themes["themes"][topic] if "themes" in themes else themes[topic]

    public = load_public_theme(topic)
    ocean = load_ocean_layer(topic)
    claim_verification = public["claim_verification"]

    n_op = public["opinion_count"]

    stances = [s["key"] for s in cfg["stances"]]
    issues_cfg = {i["key"]: i for i in cfg["issues"]}
    geo = cfg["geometry"]

    # --- 集計（公開JSONから読む。設定ファイルにも生成器にも件数を書かない）
    # 論点も立場も、結ぶのは管理番号（id）だけにする。表示文言（label）では結ばない。
    # label で結ぶと、公開側の言い換え1つで件数が黙って欠け、陸地の色が変わる。
    id_to_key = {ic["id"]: k for k, ic in issues_cfg.items()}
    unknown_issues = [pi["id"] for pi in public["issues"] if pi["id"] not in id_to_key]
    if unknown_issues:
        raise SystemExit(
            "公開JSONに、設定ファイルへ未登録の論点があります:\n"
            + "".join(f"  - {i}\n" for i in unknown_issues)
            + f"configs/planet/{topic}.yaml の issues へ、この id と key・icon を追記してください。\n"
            "（黙って捨てると、新しい論点が画面から永久に消え、合計も合わなくなります。\n"
            " vote_issue_order は過去の投票の意味が変わるため並べ替えないこと）"
        )

    stance_id_to_key = {}
    for sc in cfg["stances"]:
        if "id" not in sc:
            raise SystemExit(
                f"configs/planet/{topic}.yaml の立場「{sc['key']}」に id がありません。"
                "公開JSONの stances[].id を書いてください（集計は id で結びます）。"
            )
        stance_id_to_key[sc["id"]] = sc["key"]
    public_stance_ids = {s["id"] for pi in public["issues"] for s in pi["stances"]}
    unknown_stances = sorted(public_stance_ids - set(stance_id_to_key))
    if unknown_stances:
        raise SystemExit(
            "公開JSONに、設定ファイルへ未登録の立場があります:\n"
            + "".join(f"  - {i}\n" for i in unknown_stances)
            + f"configs/planet/{topic}.yaml の stances へ id を追記してください。"
        )
    unused_stances = [sid for sid in stance_id_to_key if sid not in public_stance_ids]
    if unused_stances:
        # 件数0の立場なのか、id の書き間違いなのかは機械では区別できない。捨てずに知らせる。
        print("注意: 公開JSONに1件も現れない立場があります（件数0か、id の誤り）: "
              + ", ".join(unused_stances))

    counts: dict[str, int] = {}
    cross: dict[str, dict[str, int]] = {}
    inten: dict[str, dict[str, int]] = {}
    for pub_issue in public["issues"]:
        k = id_to_key[pub_issue["id"]]
        counts[k] = pub_issue["count"]
        cross[k] = {stance_id_to_key[s["id"]]: s["count"] for s in pub_issue["stances"]}
        inten[k] = {i["id"]: i["count"] for i in pub_issue["intensities"]}

    # 不変条件: 論点別の合計＝公開JSONの意見数（画面の合計が合わない状態で出さない）
    assigned = public["issue_assigned_count"]
    if sum(counts.values()) != assigned:
        raise SystemExit(
            f"論点別の合計 {sum(counts.values())} が公開JSONの issue_assigned_count {assigned} と違います。"
        )
    if assigned != n_op:
        raise SystemExit(
            f"公開JSONの issue_assigned_count {assigned} と opinion_count {n_op} が違います。"
            "面積と比率の母数が食い違うため生成しません。"
        )

    # --- 海面下（指摘2）: 台帳の母数は「編集部が確認した時点」の意見数。
    # 現在の意見数と違えば印を付けて知らせる（黙って今の数字へ差し替えない）。
    # 件数 sns_count は人が本文を読んで確定した値なので、機械で数え直さない。
    sunk_continents = []
    for item in ocean.get("sunk_continents", []):
        item = dict(item)
        item["opinion_count_now"] = n_op
        item["base_stale"] = item.get("sns_base") != n_op
        sunk_continents.append(item)
    stale_ids = [i["id"] for i in sunk_continents if i["base_stale"]]
    if stale_ids:
        print("注意: 沈んだ大陸の母数が確認時点のままです（増えた分の読み直しが要る）: "
              + ", ".join(stale_ids))

    # --- 地下水脈（指摘4）: 台帳の issue_ids で論点へ結ぶ。未登録の論点idなら止める。
    for vein in ocean.get("veins", []):
        unknown = [i for i in vein.get("issue_ids", []) if i not in id_to_key]
        if unknown:
            raise SystemExit(
                f"地下水脈 {vein['id']} が、設定ファイルに無い論点 {', '.join(unknown)} を指しています。"
            )

    keys = [k for k in issues_cfg if counts.get(k)]
    keys.sort(key=lambda k: -counts[k])
    ids = [issues_cfg[k]["id"] for k in keys]

    # --- 標高（強い表現の割合。小標本を抑える）
    high_total = sum(v.get("high", 0) for v in inten.values())
    p0 = high_total / n_op if n_op else 0.0
    kk = geo["elevation_k"]
    p_adj = {k: (inten[k].get("high", 0) + kk * p0) / (counts[k] + kk) for k in keys}
    pmax = max(p_adj.values()) if p_adj else 1.0

    # --- 面積（最小面積の床つき）。立場フィルターごとに作り直す
    def area_targets(sub_counts: dict[str, int]) -> np.ndarray:
        total = sum(sub_counts.values())
        if total == 0:
            return np.zeros(len(keys))
        raw = np.array([sub_counts.get(k, 0) / total * 100 for k in keys])
        adj = np.where(raw > 0, np.maximum(raw, geo["min_area_pct"]), 0.0)
        excess = adj.sum() - 100
        donors = (adj > geo["min_area_pct"] + 1e-9)
        if excess > 0 and donors.any():
            adj[donors] -= excess * adj[donors] / adj[donors].sum()
        return adj / 100.0

    pts = fibonacci_points(geo["fit_points"])
    centers = seed_directions(ids)
    # 大陸のあいだの海の広さ。1位と2位の差がこれ未満の帯を海にする。
    # 海は論点に属さない余白で、意味は持たない（設計書12「根拠のない地形の演出をしない」）。
    # 面積の比は陸の中で合わせ直すので、海を広げても「面積＝意見数」は崩れない。
    coast = float(geo.get("coast_margin", 0.22))

    modes = []
    mode_defs = [("all", "すべての意見", None)] + [(s, s, s) for s in stances]
    weights_by_mode = {}
    # 大陸名を置く位置は、その立場での陸の重心にする。全立場で共通の位置にすると、
    # 縮んだ大陸の名前が海の上に浮く（中立・情報の「費用・家庭負担」で実際に起きた）。
    centroid_by_mode = {}
    for mode_id, label, stance_key in mode_defs:
        if stance_key is None:
            sub = {k: counts[k] for k in keys}
        else:
            sub = {k: cross.get(k, {}).get(stance_key, 0) for k in keys}
        tgt = area_targets(sub)
        w = fit_weights(pts, centers, tgt, geo["fit_iters"], coast=coast)
        assign, frac, sea = region_stats(pts, centers, w, tgt, coast)
        weights_by_mode[mode_id] = w.tolist()
        centroid_by_mode[mode_id] = centroids(pts, assign, len(keys)).tolist()
        modes.append({
            "id": mode_id,
            "label": label,
            "total": int(sum(sub.values())),
            "counts": {issues_cfg[k]["id"]: int(sub[k]) for k in keys},
            "area_pct": {issues_cfg[k]["id"]: round(float(tgt[i] * 100), 2) for i, k in enumerate(keys)},
            "area_actual_pct": {issues_cfg[k]["id"]: round(float(frac[i] * 100), 2) for i, k in enumerate(keys)},
            "sea_pct": round(float(sea * 100), 2),
        })
        if mode_id == "all":
            base_assign = assign

    cents = centroids(pts, base_assign, len(keys))

    # --- 下位論点（島）。再読データがある論点だけ割れる
    sub_cfg = cfg.get("sub_issues") or {}
    issues = []
    for i, k in enumerate(keys):
        ic = issues_cfg[k]
        sub = None
        if k in sub_cfg:
            sc = sub_cfg[k]
            raw = dig(json.loads((ROOT / sc["file"]).read_text()), sc["path"])
            items = [{"id": bid, "label": b["label"], "count": int(b["count"])}
                     for bid, b in raw.items()]
            items.sort(key=lambda x: -x["count"])
            reread = sum(x["count"] for x in items)
            gap = counts[k] - reread
            if gap > 0:
                items.append({"id": "__unread__", "label": "まだ読み直していない分",
                              "count": gap, "unread": True})
            m = len(items)
            # 大陸の広がりに合わせて下位シードの散らばりを決める（はみ出さないように）
            frac_i = float((base_assign == i).mean())
            theta = math.acos(max(-1.0, 1 - 2 * frac_i))
            scent = tangent_ring(cents[i], m, 0.55 * math.tan(min(theta, 1.2)))
            stgt = np.array([x["count"] for x in items], dtype=float)
            stgt = stgt / stgt.sum()
            sel = pts[base_assign == i]
            # 島は1つの大陸の中の区分けなので、島どうしの間に海は作らない（coast=0）
            sw = fit_weights(sel, scent, stgt, 300) if len(sel) > 50 else np.zeros(m)
            sassign, sfrac, _ = region_stats(sel, scent, sw, stgt)
            scents = centroids(sel, sassign, m)
            for j, x in enumerate(items):
                x["centroid"] = scents[j].tolist()
                x["area_pct_in_issue"] = round(float(sfrac[j] * 100), 1)
            sub = {
                "status": "reread",
                "coverage": sc["coverage"],
                "coverage_note": sc["coverage_note"],
                "source_file": sc["file"],
                "reread_count": reread,
                "unread_count": max(gap, 0),
                "items": items,
                "centers": scent.tolist(),
                "weights": sw.tolist(),
            }
        else:
            sub = {"status": "not_reviewed",
                   "note": "この論点は、まだ編集部が投稿を1件ずつ読み直していません"}

        st = cross.get(k, {})
        top = max(stances, key=lambda s: st.get(s, 0))
        verdict, matched_claims = issue_verdict(ic["id"], claim_verification["claims"])
        issues.append({
            "id": ic["id"],
            "key": k,
            "label": k,
            "icon": ic["icon"],
            "count": counts[k],
            "share_pct": round(100 * counts[k] / n_op, 1),
            "stances": {s: int(st.get(s, 0)) for s in stances},
            "top_stance": top,
            "purity_pct": round(100 * st.get(top, 0) / counts[k], 1),
            "intensity": {x: int(inten[k].get(x, 0)) for x in ("high", "medium", "low")},
            "high_pct": round(100 * inten[k].get("high", 0) / counts[k], 1),
            "high_adjusted_pct": round(100 * p_adj[k], 1),
            "elevation": round(geo["elevation_max"] * p_adj[k] / pmax, 2),
            "center": centers[i].tolist(),
            "centroid": cents[i].tolist(),
            "sub": sub,
            "verdict": verdict,
            "claims": matched_claims,
            "veins": [v["id"] for v in ocean["veins"] if ic["id"] in v.get("issue_ids", [])],
        })

    return {
        "schema": 1,
        "theme_id": cfg["theme_id"],
        "title": cfg["title"],
        "question": cfg["question"],
        "snapshot_id": f"{cfg['theme_id']}-{str(t['updated_at']).replace('-', '')}",
        "updated_at": str(t["updated_at"]),
        "sample_period": t["sample_period"],
        "source_label": cfg["source_label"],
        "totals": {
            "collected": public["collected_count"],
            "opinions": n_op,
        },
        "elevation_formula": {
            "definition": "強い表現（intensity=high）の投稿が占める割合",
            "p0": round(p0, 4), "k": kk, "max_pct": geo["elevation_max"],
        },
        "min_area_pct": geo["min_area_pct"],
        "coast_margin": round(coast, 6),
        "coast_noise_amp": COAST_NOISE_AMP,
        "stances": [dict(s, count=sum(cross.get(k, {}).get(s["key"], 0) for k in keys))
                    for s in cfg["stances"]],
        "vote_issue_order": cfg["vote_issue_order"],
        "modes": modes,
        "weights_by_mode": weights_by_mode,
        "centroid_by_mode": centroid_by_mode,
        "issues": issues,
        "editorial": public.get("editorial_summary",
                                {"status": "not_started", "checked_on": None,
                                 "reviewer_type": None, "findings": []}),
        "ocean": {
            "claim_status": claim_verification["status"],
            "checked_on": claim_verification["checked_on"],
            "reviewer_type": claim_verification["reviewer_type"],
            "ocean_status": ocean.get("status", "not_started"),
            "ocean_checked_on": ocean.get("checked_on"),
            "ocean_reviewer_type": ocean.get("reviewer_type"),
            "sunk_continents": sunk_continents,
            "veins": ocean.get("veins", []),
        },
    }


def independence_gate(data: dict, cfg: dict) -> list[str]:
    """公開してよいだけの独自性がそろっているかを機械で確かめる。

    AdSense の診断で「自動生成コンテンツの疑い」が OK だった根拠は
    「定型的な繰り返しがなく、論点ごとに異なる構造」だった。10テーマを1つの生成器で
    作ると、この根拠がいちばん壊れやすい。だから生成器自身に、
    「中身が薄いテーマは公開ページを出さない」検査を持たせる。

    指示文に書いた禁止は別セッションで破られる。検査だけが残る。
    """
    ng = []
    # 1. 一次資料との突き合わせ（FACT_CHECK_GUIDE.md の claim_posts）
    claims = ROOT / "data" / f"{data['theme_id']}_claim_posts.json"
    if not claims.exists():
        ng.append(f"一次資料との突き合わせが無い（{claims.relative_to(ROOT)} が未作成）")

    # 2. 人が本文を読み直した論点が、意見の半分以上を占めていること
    reread_n = sum(i["count"] for i in data["issues"] if i["sub"]["status"] == "reread")
    share = 100 * reread_n / data["totals"]["opinions"]
    if share < 50:
        ng.append(f"編集部が読み直した論点が意見の{share:.0f}%しかない（50%以上必要）")

    # 3. 読み直し済みの論点でも、未読の残りが多すぎないこと
    for i in data["issues"]:
        s = i["sub"]
        if s["status"] == "reread" and s["unread_count"] > 0.4 * i["count"]:
            ng.append(f"「{i['label']}」の未読が{s['unread_count']}件（全{i['count']}件の4割超）")

    # 4. 海面下の母数が現在の意見数と一致していること（指摘2）
    for item in data["ocean"]["sunk_continents"]:
        if item.get("base_stale"):
            ng.append(
                f"沈んだ大陸「{item['id']}」の母数が確認時点の{item.get('sns_base')}件のまま"
                f"（現在は{item.get('opinion_count_now')}件）。増えた分を読み直すこと"
            )

    # 5. テーマ固有の言葉が入っていること（共通テンプレだけのページを出さない）
    if not cfg.get("question"):
        ng.append("テーマ固有の『中心の問い』が設定されていない")
    return ng


# ------------------------------------------------ 出力の安定化と静的HTML

def stabilize(obj, nd: int = 12):
    """浮動小数の末尾桁のゆらぎを丸めて落とす。

    重みの当てはめ（fit_weights）は行列積の足す順序で最後の1〜2桁が動く。
    そのままだと「同じ入力なのに再生成すると差分が出る」状態になり、
    課題34の再生成可能性と docs/ の差分0が崩れる。表示する値はすべて
    小数2桁までなので、12桁で丸めても見た目は1ドットも変わらない。
    """
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, float) or isinstance(obj, np.floating):
        return float(round(float(obj), nd)) + 0.0   # -0.0 を 0.0 に寄せる
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, dict):
        return {k: stabilize(v, nd) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [stabilize(v, nd) for v in obj]
    return obj


def text_on(hex_color: str) -> str:
    """背景色の明るさから、読める文字色を決める。"""
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#0d1117" if lum > 0.5 else "#ffffff"


def e(x) -> str:
    return html.escape(str(x), quote=True)


def static_question(d: dict) -> str:
    return e(d["question"]) + "（" + e(d["title"]) + "）"


def static_caution(d: dict) -> str:
    t = d["totals"]
    out = ['<p class="caution" id="caution">'
           + e(d["source_label"]) + "で集めた公開投稿のサンプルです。社会全体の世論ではありません。<br>"
           + "収集期間 " + e(d["sample_period"]) + "／収集" + str(t["collected"])
           + "件・<b>意見" + str(t["opinions"]) + "件</b>（惑星の母数）／更新 " + e(d["updated_at"])
           + '　<code>' + e(d["snapshot_id"]) + "</code></p>"]
    if d.get("prototype_only"):
        out.append('<p class="caution" style="border-left-color:#e5534b">'
                   + "<b>このページは公開できません。</b>独自性の検査に落ちています。<br>・"
                   + "<br>・".join(e(x) for x in d.get("gate_failures", [])) + "</p>")
    return "\n  ".join(out)


def static_meta(d: dict) -> str:
    f = d["elevation_formula"]
    return ("大陸＝論点、面積＝意見の数（最小" + str(d["min_area_pct"]) + "%の床あり）、"
            "色＝いちばん多い立場（薄いほど意見が割れている）、"
            "山の高さ＝" + e(f["definition"]) + "（小さい論点は k=" + str(f["k"])
            + " で抑制。全体平均 " + f"{f['p0'] * 100:.1f}" + "%）。"
            "大陸の位置は見やすさのための配置で、論点同士の近さを意味しません。<br>"
            "<b>青い海と海岸線の形には意味がありません。</b>大陸を見分けやすくするための余白で、"
            "球面の" + f"{d['modes'][0]['sea_pct']:.0f}" + "%を占めます。"
            "面積の比は海を除いた陸の中で合わせているので、"
            "海を広げても狭めても「面積＝意見の数」は変わりません。<br>"
            "このページの数字はすべて <code>scripts/build_planet_data.py</code> が正典から数え直したものです。"
            "データが増えたら同じコマンドを実行し直すだけで、面積・色・高さ・島が更新されます。")


def static_fallback(d: dict) -> str:
    """JS・canvas が使えない環境向けの静的HTMLを data から組み立てる。

    ここを手書きにすると、同じページの中で数字が2通りになる（段階7のレビュー指摘1）。
    テーマ固有の言葉・色も data から採るので、他テーマでもそのまま使える。
    """
    stance = {x["key"]: x for x in d["stances"]}
    nav, panels = [], []
    for it in d["issues"]:
        anchor_id = "fb-" + it["id"]
        color = stance[it["top_stance"]]["color"]
        nav.append(
            f'      <a class="continent" href="#{e(anchor_id)}"'
            f' style="background:{e(color)};border-color:{e(color)};color:{text_on(color)}">'
            f'<span class="label">{e(it["icon"])} {e(it["label"])}</span>'
            f'<span class="count">{it["count"]}件・{it["share_pct"]}%</span></a>')

        legend = "".join(
            f'<span><i style="background:{e(stance[k]["color"])}"></i>{e(k)} {n}件</span>'
            for k, n in it["stances"].items() if n)
        bar = "".join(
            f'<span style="width:{100 * n / it["count"]:.1f}%;background:{e(stance[k]["color"])};'
            f'color:{text_on(stance[k]["color"])}">{e(k) if 100 * n / it["count"] >= 12 else ""}</span>'
            for k, n in it["stances"].items() if n)

        body = [
            f'    <section class="landing-panel" id="{e(anchor_id)}" tabindex="-1">',
            f'      <h2>{e(it["icon"])} {e(it["label"])}</h2>',
            f'      <p class="sub">{it["count"]}件（{it["share_pct"]}%）'
            f'　山の高さ：強い表現{it["high_adjusted_pct"]}%</p>',
            f'      <div class="legend">{legend}</div>',
            f'      <div class="bar">{bar}</div>',
            '      <p class="sub" style="margin:2px 0 0">立場の内訳は、この論点の全件で数えています</p>',
        ]
        if it["share_pct"] < d["min_area_pct"]:
            body.append(f'      <div class="note">3Dの惑星では、この大陸を実際の割合より大きく描いています。'
                        f'小さすぎると押せないため、最小{d["min_area_pct"]}%まで拡大しています。</div>')

        sub = it["sub"]
        if sub["status"] == "reread":
            items = "".join(
                f'<li{" class=\"unread\"" if x.get("unread") else ""}>'
                f'<span class="num">{j + 1}</span>{e(x["label"])}'
                f'<span class="n">{x["count"]}件</span></li>'
                for j, x in enumerate(sub["items"]))
            body += [
                '      <p class="sub" style="margin-top:12px">'
                '<b>この論点の中身（編集部が本文を読んで分けたもの）</b></p>',
                f'      <ul class="islands">{items}</ul>',
                f'      <div class="note">{e(sub["coverage_note"])}。読み直した{sub["reread_count"]}件は '
                f'<code>{e(sub["source_file"].split("/")[-1])}</code> が出所です。'
                + (f'残り{sub["unread_count"]}件は、その後に増えた分でまだ読めていません。'
                   if sub["unread_count"] else "") + '</div>',
            ]
        else:
            body.append(f'      <div class="note">{e(sub["note"])}。<br>'
                        'AIが自動でつけた区分をここに並べることはしません。'
                        '人が読んだ結果だけを島にします。</div>')

        if it.get("claims"):
            srcs = []
            for c in it["claims"]:
                links = "".join(
                    f'<br><a href="{e(src["url"])}" rel="nofollow">{e(src["name"])}</a>'
                    for src in c.get("sources", []))
                srcs.append(f'<li>{e(c["claim"])}<br>{e(c["finding"])}{links}</li>')
            body += ['      <p class="sub" style="margin-top:12px">'
                     '<b>一次資料と照らした結果</b></p>',
                     f'      <ul class="srclist">{"".join(srcs)}</ul>']

        extras = issue_extras_html(it, d)
        if extras:
            body.append(f'      <div class="extras" id="extras-{e(it["id"])}">')
            body.append(extras)
            body.append('      </div>')
        body.append('      <a class="backlink" href="#fallback-nav">← 論点の一覧へ戻る</a>')
        body.append('    </section>')
        panels.append("\n".join(body))

    return ("\n".join([
        '  <div id="fallback">',
        '    <h3 class="sec">論点の一覧（3Dの惑星が使えないときの表示）</h3>',
        '    <p class="sub" style="color:var(--muted);font-size:12px">'
        'このページは、お使いの環境で3Dの惑星を描けなかったため、同じ内容を静的な一覧で表示しています。'
        '円をえらぶと、その論点の内訳へ移動します。円の色はいちばん多い立場です。</p>',
        '    <nav class="planet" id="fallback-nav" aria-label="論点をえらぶ">',
    ] + nav + ['    </nav>'] + panels + ['  </div>']))


def issue_extras_html(issue: dict, data: dict) -> str:
    """着陸パネルの後半（資料との照合＋海面より下への導線）を組み立てる。

    3D版の着陸パネルもこのHTMLを読んで使う（テンプレートのJSで複製する）。
    同じ内容をJavaScript側にもう一度書くと、数字と文言が2通りに分かれるため。
    """
    ocean = data["ocean"]
    out = []

    claims = issue.get("claims") or []
    if claims:
        out.append('      <p class="sub" style="margin-top:14px"><b>資料との照合</b></p>')
        rows = []
        for c in claims:
            label, note = VERDICT_LABELS[c["verdict"]]
            links = "".join(
                f'<a href="{e(src["url"])}" rel="nofollow">{e(src["name"])}</a>'
                for src in c.get("sources", []))
            rows.append(
                f'<li><span class="verdict v-{e(c["verdict"])}">{e(label)}</span>'
                f'{e(c["claim"])}<span class="finding">{e(c["finding"])}</span>'
                f'<span class="vnote">{e(note)}</span>'
                + (f'<span class="srcs">{links}</span>' if links else "") + '</li>')
        out.append(f'      <ul class="claims">{"".join(rows)}</ul>')
    elif ocean.get("claim_status") == "not_started":
        out.append('      <div class="note">この論点は、まだ一次資料との突き合わせをしていません。</div>')

    veins = [v for v in ocean.get("veins", []) if issue["id"] in v.get("issue_ids", [])]
    sunk = [x for x in ocean.get("sunk_continents", [])
            if x.get("nearest_issue_id") == issue["id"]]
    if veins or sunk:
        parts = []
        if veins:
            parts.append(f'地下水脈{len(veins)}本')
        if sunk:
            parts.append(f'沈んだ大陸{len(sunk)}件')
        out.append(
            '      <p class="sub" style="margin-top:12px">この論点に関わる海面より下：'
            + "・".join(parts)
            + ' <a class="dive" href="#ocean">ページ下の「海面より下」で読む</a></p>')
    return "\n".join(out)


def static_ocean(data: dict) -> str:
    """海面より下（沈んだ大陸・地下水脈）をテーマ全体のセクションとして組み立てる。

    沈んだ大陸は「どの論点にも入っていない」ことが中身なので、
    論点の着陸パネルの中だけに置くと、論点に結びつかない件が読者から見えなくなる。
    """
    ocean = data["ocean"]
    sunk, veins = ocean.get("sunk_continents", []), ocean.get("veins", [])
    label_of = {i["id"]: i["label"] for i in data["issues"]}

    head = ['  <section id="ocean" class="ocean" tabindex="-1">',
            '    <h3 class="sec">海面より下</h3>']
    if ocean.get("ocean_status") != "complete" or not (sunk or veins):
        head.append('    <p class="sub">このテーマは、まだ編集部が一次資料を読んで'
                    '「語られていないこと」を確かめていません。確かめるまで、ここは空のままにします。</p>')
        return "\n".join(head + ['  </section>'])

    head.append(
        '    <p class="sub">ここから下は集計ではありません。編集部が一次資料を読んで確かめたことだけを置いています。'
        f'（確認日 {e(ocean.get("ocean_checked_on"))}／'
        f'{"編集部が本文を読んで確認" if ocean.get("ocean_reviewer_type") == "editorial_review" else "AIの下読みを含む"}）</p>')

    if sunk:
        head.append('    <h4 class="subsec">沈んだ大陸 — 一次資料では争点なのに、集めた投稿にほとんど無いもの</h4>')
        for x in sunk:
            srcs = "".join(
                f'<li><a href="{e(src["url"])}" rel="nofollow">{e(src["name"])}</a>'
                + (f'<span class="when">{e(src["date"])}</span>' if src.get("date") else "")
                + f'<span class="where">{e(src["location"])}</span></li>'
                for src in x["sources"])
            near = label_of.get(x.get("nearest_issue_id"))
            head.append(
                f'    <article class="sunk">'
                f'<h5>{e(x["topic"])}</h5>'
                f'<p class="impact">{e(x["life_impact"])}</p>'
                f'<p class="count">集めた投稿での件数：<b>{x["sns_count"]}件</b>'
                f'（意見{x["sns_base"]}件のうち）'
                + (f'／いちばん近い論点：{e(near)}' if near else "") + '</p>'
                f'<p class="note">{e(x["sns_note"])}</p>'
                f'<p class="sub">一次資料</p><ul class="srclist">{srcs}</ul>'
                '</article>')

    if veins:
        head.append('    <h4 class="subsec">地下水脈 — 立場が違っても、同じ心配を語っているところ</h4>')
        for v in veins:
            sides = "".join(
                f'<li>{e(sd["stance_label"])}<span class="n">代表{sd["post_count"]}件</span></li>'
                for sd in v["sides"])
            issues = "・".join(e(label_of.get(i, i)) for i in v["issue_ids"])
            head.append(
                f'    <article class="vein">'
                f'<h5>{e(v["shared_concern"])}</h5>'
                f'<p class="impact">それでも結論が分かれる理由：{e(v["diverging_reason"])}</p>'
                f'<p class="count">関わる論点：{issues}</p>'
                f'<ul class="sides">{sides}</ul>'
                '</article>')
    return "\n".join(head + ['  </section>'])



class TemplateError(Exception):
    """テンプレートの差し込み口が足りないときに投げる。

    SystemExit にするとテストの setUpClass でプロセスごと終わってしまい、
    「差し込み口を消しても検査が素通りする」状態になる。
    """


# 横断整理の見出し（設計書4章の5）。区分と表示文言の対応をここだけで決める。
EDITORIAL_HEADINGS = {
    "shared_premise": "共通する前提",
    "real_conflict": "本当の対立",
    "still_unknown": "まだ分からないこと",
}


def static_editorial(data: dict) -> str:
    """編集部の横断整理を組み立てる（設計書4章の5）。

    本文は台帳（`data/verification/{テーマ}-editorial.json`）に人が書き、
    数字は差し込みで正典から入る。ここでは並べるだけで、文章を作らない。
    """
    ed = data.get("editorial") or {}
    out = ['  <section id="editorial" class="editorial" tabindex="-1">',
           '    <h3 class="sec">編集部の横断整理</h3>']
    findings = ed.get("findings") or []
    if ed.get("status") != "complete" or not findings:
        out.append('    <p class="sub">このテーマは、論点をまたいで言えることの整理がまだです。'
                   '書けるまで、ここは空のままにします。</p>')
        return "\n".join(out + ['  </section>'])

    out.append('    <p class="sub">論点をまたいで言えることを、編集部がまとめています。'
               f'（{e(ed.get("checked_on"))}時点）</p>')
    for kind, heading in EDITORIAL_HEADINGS.items():
        rows = [f for f in findings if f["kind"] == kind]
        if not rows:
            continue
        out.append(f'    <h4 class="subsec">{e(heading)}</h4>')
        out.append('    <ul class="findings">'
                   + "".join(f'<li>{e(f["text"])}</li>' for f in rows) + '</ul>')
    return "\n".join(out + ['  </section>'])



def render_page(data: dict, template: str, payload: str) -> str:
    """テンプレートの差し込み口を data から埋める。

    数字・色・テーマ固有の言葉をここでしか作らないことで、
    「同じページの中で数字が2通りになる」状態を作れなくする。
    """
    for mark, filler in (
        ("/*__PLANET_DATA__*/null", payload),
        ("<!--__QUESTION__-->", static_question(data)),
        ("<!--__CAUTION__-->", static_caution(data)),
        ("<!--__META__-->", static_meta(data)),
        ("<!--__FALLBACK__-->", static_fallback(data)),
        ("<!--__OCEAN__-->", static_ocean(data)),
        ("<!--__EDITORIAL__-->", static_editorial(data)),
    ):
        if mark not in template:
            raise TemplateError(f"テンプレートに差し込み口 {mark} がありません")
        template = template.replace(mark, filler)
    return template


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--prototype", action="store_true",
                    help="独自性の検査に落ちても試作として出力する（公開には使えない）")
    a = ap.parse_args()
    data = build(a.topic)
    cfg = yaml.safe_load((ROOT / "configs" / "planet" / f"{a.topic}.yaml").read_text())
    ng = independence_gate(data, cfg)
    if ng:
        print("独自性の検査に不合格:")
        for x in ng:
            print("  - " + x)
        if not a.prototype:
            print("公開ページは出力しません。試作として作るなら --prototype を付けてください。")
            raise SystemExit(1)
        print("--prototype 指定のため、試作としてだけ出力します。")
        data["prototype_only"] = True
        data["gate_failures"] = ng
    out = Path(a.out) if a.out else ROOT / "quality/prototypes/data" / f"{a.topic}-planet.json"
    data = stabilize(data)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1))

    # 試作HTMLへデータを埋め込む（file:// のままダブルクリックで開けるようにする）
    tpl = ROOT / "quality/prototypes/planet-prototype.template.html"
    if tpl.exists():
        payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
        html_out = out.parent.parent / f"{a.topic}-planet.html"
        try:
            html_out.write_text(render_page(data, tpl.read_text(), payload))
        except TemplateError as exc:
            raise SystemExit(str(exc)) from None
        print(f"wrote {html_out}")

    print(f"wrote {out}  意見{data['totals']['opinions']}件 / 論点{len(data['issues'])}")
    for i in data["issues"]:
        s = i["sub"]
        tag = f"島{len(s['items'])}（未読{s['unread_count']}）" if s["status"] == "reread" else "未再読"
        print(f"  {i['label']:<12}{i['count']:>5}件 面積{data['modes'][0]['area_actual_pct'][i['id']]:>5.1f}% "
              f"標高{i['elevation']:.2f} {i['top_stance']}{i['purity_pct']:.0f}% {tag}")


if __name__ == "__main__":
    main()
