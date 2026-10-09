#!/usr/bin/env python3
"""過去から残る理由分類・記録への未反映を監視する（本文未確認数とは異なる）。

今回の追加・変更分は refresh_completion.py が未完了0件を要求する。
この早期警告は過去の残件の4割上限を監視するだけで、持ち越しを許可しない。
"""
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_planet_data as bpd  # noqa: E402

WARN_AT = 0.30  # 過去の理由記録の不足を確認する目安
LIMIT = 0.40    # independence_gate（build_planet_data.py）が落とす境界と同じ値。
                # 向こうを変えたらこちらも合わせる（一元化はしていない）


def topic_findings(topic: str) -> list[dict]:
    """{tone: "warn"|"danger", title, detail} の形で返す。sub_issues未設定なら空。"""
    cfg_path = ROOT / "configs" / "planet" / f"{topic}.yaml"
    if not cfg_path.exists():
        return []
    cfg = yaml.safe_load(cfg_path.read_text())
    if not cfg.get("sub_issues"):
        return []
    try:
        data = bpd.stabilize(bpd.build(topic))
    except SystemExit as exc:
        return [{"tone": "warn", "title": f"{topic}: 再読カバー率を確認できません",
                 "detail": f"生成が別の理由でNGになっています — {exc}"}]
    except FileNotFoundError:
        return []  # このworktreeに正典が無いだけ。他のworktree/共有ツリーで確認する

    findings = []
    for issue in data["issues"]:
        sub = issue["sub"]
        if sub["status"] != "reread" or not issue["count"]:
            continue
        unread = sub["skipped_count"] + sub["grown_count"]
        ratio = unread / issue["count"]
        if ratio > LIMIT:
            findings.append({
                "tone": "danger",
                "title": f"{topic}: 「{issue['label']}」の理由分類・記録の未完了が上限を超えています",
                "detail": (f"理由記録に未接続（既存分{sub['skipped_count']}件＋増分{sub['grown_count']}件）"
                           f"が{ratio:.0%}（上限{LIMIT:.0%}）。"
                           "次にこのテーマを生成するとindependence_gateでNGになります。"
                           "本文確認済みかを確かめ、必要な理由分類と記録への反映を完了してください。"),
            })
        elif ratio >= WARN_AT:
            findings.append({
                "tone": "warn",
                "title": f"{topic}: 「{issue['label']}」の理由分類・記録の未完了が上限に近づいています",
                "detail": (f"理由記録に未接続（既存分{sub['skipped_count']}件＋増分{sub['grown_count']}件）"
                           f"が{ratio:.0%}（上限{LIMIT:.0%}）。"
                           "本文未確認数とは異なります。今回の追加・変更分は割合に関係なく完了が必要です。"),
            })
    return findings


def headroom_findings(topics: list[str] | None = None) -> list[dict]:
    if topics is None:
        themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text())["themes"]
        topics = list(themes.keys())
    found = []
    for topic in topics:
        found.extend(topic_findings(topic))
    return found


def main() -> int:
    findings = headroom_findings(sys.argv[1:] or None)
    if not findings:
        print("OK: 上限に近づいている論点はありません")
        return 0
    print(f"警告 {len(findings)}件:")
    for f in findings:
        print(f"  - [{f['tone']}] {f['title']}\n      {f['detail']}")
    return 0  # 早期警告なので検査全体は落とさない


if __name__ == "__main__":
    raise SystemExit(main())
