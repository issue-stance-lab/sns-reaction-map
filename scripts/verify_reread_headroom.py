#!/usr/bin/env python3
"""編集再読の「未読合計（読み飛ばし＋読了後に増えた分）」が上限（4割）に
近づいていないかを、事故る前に見る。

independence_gate() は読み飛ばし＋読了後に増えた分の合計が4割を超えた時点で
初めて NG にする（2026-09-13、オーナー判断で読み飛ばしと増分を同じ枠に統合。
それまでは grown_count だけを見ていた）。定期収集のたびに投稿は増え続けるので、
それまでは何の予兆もなく、ある日の収集がたまたまその論点に数件当たった瞬間に
突然落ちる。2026-09-13、副首都の展開作業中に「これは編集再読の対象外だから
読み直しが要らない」という誤った判断をした際、bukatsu-chiikiの
「受け皿・指導者」「費用・家庭負担」の2論点が実測39%・38%と判明した
（限度まで1〜2ポイント）。この検査はその値を定期的に可視化し、
限度に達してから慌てて全部読み直す、という誤りを防ぐための早期警告。

このスクリプト単体はNGにしない（exit 0固定）。independence_gate自体の代わりではなく、
「まだ間に合ううちに気づく」ための別の目。`build_admin_dashboard.py` の異常検知
（scripts/admin_dashboard/actions.py）からも `headroom_findings()` として呼ばれる。
対象はTHEMES.yamlの全テーマのうち、configs/planet/{topic}.yamlにsub_issuesがあるもの。
"""
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_planet_data as bpd  # noqa: E402

WARN_AT = 0.30  # この割合を超えたら「そろそろ次の読み直しを計画する」目安
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
        if ratio >= LIMIT:
            findings.append({
                "tone": "danger",
                "title": f"{topic}: 「{issue['label']}」の編集再読が上限を超えています",
                "detail": (f"未読合計（読み飛ばし{sub['skipped_count']}件＋増分{sub['grown_count']}件）"
                           f"が{ratio:.0%}（上限{LIMIT:.0%}）。"
                           "次にこのテーマを生成するとindependence_gateでNGになります。"
                           "編集再読の追い読みが必要です。"),
            })
        elif ratio >= WARN_AT:
            remain = (LIMIT - ratio) * issue["count"]
            findings.append({
                "tone": "warn",
                "title": f"{topic}: 「{issue['label']}」の編集再読がそろそろ上限です",
                "detail": (f"未読合計（読み飛ばし{sub['skipped_count']}件＋増分{sub['grown_count']}件）"
                           f"が{ratio:.0%}（上限{LIMIT:.0%}）。"
                           f"あと{remain:.0f}件相当の新規投稿がこの論点に入ると次の生成でNGになります。"
                           "次の定期収集の前に追い読みを計画してください。"),
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
