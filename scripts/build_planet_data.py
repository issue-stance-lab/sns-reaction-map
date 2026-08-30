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


def fit_weights(points: np.ndarray, centers: np.ndarray, targets: np.ndarray,
                iters: int, lr: float = 0.6) -> np.ndarray:
    """加重ボロノイの重みを、面積比が targets に合うまで調整する。

    score_i(p) = dot(p, center_i) + w_i   の最大値でその点の所属を決める。
    """
    k = len(centers)
    w = np.zeros(k)
    active = targets > 0
    dots = points @ centers.T                       # (N, K)
    neg = np.where(active, 0.0, -10.0)
    # 重みの動かし幅を、その領域での dot のばらつきに合わせる。
    # （大陸と島では dot の差の大きさが2桁ちがうため、固定の学習率だと島側が発散する）
    scale = float(dots.std()) or 1.0
    best_w, best_err = w.copy(), 1e9
    for t in range(iters):
        assign = np.argmax(dots + w + neg, axis=1)
        frac = np.bincount(assign, minlength=k) / len(points)
        err = float(np.abs(frac - targets).sum())
        if err < best_err:
            best_err, best_w = err, w.copy()
        step = lr * 2 * scale * (1 - 0.85 * t / iters)
        w += step * (targets - frac)
        w[~active] = 0.0
    return best_w


def region_stats(points: np.ndarray, centers: np.ndarray, w: np.ndarray,
                 targets: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    neg = np.where(targets > 0, 0.0, -10.0)
    assign = np.argmax(points @ centers.T + w + neg, axis=1)
    frac = np.bincount(assign, minlength=len(centers)) / len(points)
    return assign, frac


def centroids(points: np.ndarray, assign: np.ndarray, k: int) -> np.ndarray:
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

def load_records(sample_file: Path) -> list[dict]:
    recs = json.loads(sample_file.read_text())
    out = []
    for r in recs:
        c = r.get("classification") or {}
        if c.get("is_relevant") and c.get("is_opinion"):
            out.append(c)
    return out


def dig(obj, path):
    for p in path:
        obj = obj[p]
    return obj


# ---------------------------------------------------------------- 本体

def build(topic: str) -> dict:
    cfg = yaml.safe_load((ROOT / "configs" / "planet" / f"{topic}.yaml").read_text())
    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text())
    t = themes["themes"][topic] if "themes" in themes else themes[topic]

    sample_file = ROOT / t["sample_file"]
    all_recs = json.loads(sample_file.read_text())
    recs = load_records(sample_file)
    n_op = len(recs)

    stances = [s["key"] for s in cfg["stances"]]
    issues_cfg = {i["key"]: i for i in cfg["issues"]}
    geo = cfg["geometry"]

    # --- 集計（正典から数え直す。設定ファイルに件数を書かない）
    counts: dict[str, int] = {}
    cross: dict[str, dict[str, int]] = {}
    inten: dict[str, dict[str, int]] = {}
    for c in recs:
        k = c.get("main_issue")
        if k not in issues_cfg:
            k = "その他"
        counts[k] = counts.get(k, 0) + 1
        cross.setdefault(k, {}).setdefault(c.get("stance"), 0)
        cross[k][c.get("stance")] += 1
        inten.setdefault(k, {}).setdefault(c.get("intensity"), 0)
        inten[k][c.get("intensity")] += 1

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

    modes = []
    mode_defs = [("all", "すべての意見", None)] + [(s, s, s) for s in stances]
    weights_by_mode = {}
    for mode_id, label, stance_key in mode_defs:
        if stance_key is None:
            sub = {k: counts[k] for k in keys}
        else:
            sub = {k: cross.get(k, {}).get(stance_key, 0) for k in keys}
        tgt = area_targets(sub)
        w = fit_weights(pts, centers, tgt, geo["fit_iters"])
        assign, frac = region_stats(pts, centers, w, tgt)
        weights_by_mode[mode_id] = w.tolist()
        modes.append({
            "id": mode_id,
            "label": label,
            "total": int(sum(sub.values())),
            "counts": {issues_cfg[k]["id"]: int(sub[k]) for k in keys},
            "area_pct": {issues_cfg[k]["id"]: round(float(tgt[i] * 100), 2) for i, k in enumerate(keys)},
            "area_actual_pct": {issues_cfg[k]["id"]: round(float(frac[i] * 100), 2) for i, k in enumerate(keys)},
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
            sw = fit_weights(sel, scent, stgt, 300) if len(sel) > 50 else np.zeros(m)
            sassign, sfrac = region_stats(sel, scent, sw, stgt)
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
            "collected": len(all_recs),
            "relevant": sum(1 for r in all_recs if (r.get("classification") or {}).get("is_relevant")),
            "opinions": n_op,
        },
        "elevation_formula": {
            "definition": "強い表現（intensity=high）の投稿が占める割合",
            "p0": round(p0, 4), "k": kk, "max_pct": geo["elevation_max"],
        },
        "min_area_pct": geo["min_area_pct"],
        "stances": [dict(s, count=sum(1 for c in recs if c.get("stance") == s["key"]))
                    for s in cfg["stances"]],
        "vote_issue_order": cfg["vote_issue_order"],
        "modes": modes,
        "weights_by_mode": weights_by_mode,
        "issues": issues,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    data = build(a.topic)
    out = Path(a.out) if a.out else ROOT / "quality/prototypes/data" / f"{a.topic}-planet.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1))

    # 試作HTMLへデータを埋め込む（file:// のままダブルクリックで開けるようにする）
    tpl = ROOT / "quality/prototypes/planet-prototype.template.html"
    if tpl.exists():
        payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
        html_out = out.parent.parent / f"{a.topic}-planet.html"
        html_out.write_text(tpl.read_text().replace("/*__PLANET_DATA__*/null", payload))
        print(f"wrote {html_out}")

    print(f"wrote {out}  意見{data['totals']['opinions']}件 / 論点{len(data['issues'])}")
    for i in data["issues"]:
        s = i["sub"]
        tag = f"島{len(s['items'])}（未読{s['unread_count']}）" if s["status"] == "reread" else "未再読"
        print(f"  {i['label']:<12}{i['count']:>5}件 面積{data['modes'][0]['area_actual_pct'][i['id']]:>5.1f}% "
              f"標高{i['elevation']:.2f} {i['top_stance']}{i['purity_pct']:.0f}% {tag}")


if __name__ == "__main__":
    main()
