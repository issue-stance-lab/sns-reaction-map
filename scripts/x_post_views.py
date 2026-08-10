#!/usr/bin/env python3
"""docs/x-posts.md の未計測投稿を列挙し、安全に表示回数を書き戻す。

表示回数そのものはログイン済み Chrome で取得する。このスクリプトは認証情報を
扱わず、対象の特定・投稿時刻の算出・既存値の保護・表記統一だけを担当する。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "docs" / "x-posts.md"
JST = dt.timezone(dt.timedelta(hours=9))
X_EPOCH_MS = 1_288_834_974_657

_TOP_HEADING_RE = re.compile(r"^##\s+(.+?)\s+(\d{4}-\d{2}-\d{2})(?:（.*?）)?\s*$")
_FOLLOW_HEADING_RE = re.compile(r"^###\s+会話フォロー\s+(\d{4}-\d{2}-\d{2})\s*$")
_STATUS_RE = re.compile(r"https://x\.com/sns_hannou_ma/status/(\d+)")
_NUMBERED_URL_RE = re.compile(r"(\d+)\s*=\s*https://x\.com/sns_hannou_ma/status/(\d+)")
_MEASURED_RE = re.compile(r"^\*{0,2}\s*[0-9][0-9,]*(?:\.[0-9]+)?\s*(?:万|[KkMm])?")


@dataclass(frozen=True)
class PendingPost:
    status_id: str
    url: str
    kind: str
    posted_at: dt.datetime
    age_hours: float
    timing: str
    target: str
    line_index: int
    row_number: str | None = None

    def public_dict(self) -> dict:
        data = asdict(self)
        data.pop("line_index")
        data["posted_at"] = self.posted_at.isoformat()
        data["age_hours"] = round(self.age_hours, 1)
        return data


def post_datetime(status_id: str) -> dt.datetime:
    """X Snowflake ID から投稿日時を算出する。ページの <time> は使わない。"""
    unix_ms = (int(status_id) >> 22) + X_EPOCH_MS
    return dt.datetime.fromtimestamp(unix_ms / 1000, tz=dt.timezone.utc).astimezone(JST)


def _age_label(age_hours: float) -> str:
    if age_hours < 24:
        return "waiting"
    if age_hours <= 48:
        return "due"
    return "overdue"


def _is_missing(value: str) -> bool:
    return not _MEASURED_RE.match(value.strip())


def _split_table(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _sections(lines: list[str]) -> list[tuple[int, int, str, str]]:
    starts: list[tuple[int, str, str]] = []
    for index, line in enumerate(lines):
        match = _TOP_HEADING_RE.match(line)
        if match:
            starts.append((index, match.group(1), match.group(2)))
    return [
        (start, starts[pos + 1][0] if pos + 1 < len(starts) else len(lines), kind, date)
        for pos, (start, kind, date) in enumerate(starts)
    ]


def find_pending(text: str, now: dt.datetime) -> list[PendingPost]:
    """未計測のリプライ・論点ポスト・会話フォローを返す。"""
    if now.tzinfo is None:
        raise ValueError("now にはタイムゾーンが必要です")
    lines = text.splitlines()
    pending: list[PendingPost] = []

    for start, end, kind, _date in _sections(lines):
        body_indexes = range(start + 1, end)
        if kind == "リプライ実績":
            header_index = next(
                (i for i in body_indexes if lines[i].lstrip().startswith("|") and "自リプライ表示" in lines[i]),
                None,
            )
            if header_index is not None:
                header = _split_table(lines[header_index])
                number_col = header.index("#")
                own_col = header.index("自リプライ表示")
                rows: dict[str, tuple[int, str, str]] = {}
                for i in range(header_index + 1, end):
                    if not lines[i].lstrip().startswith("|"):
                        if rows:
                            break
                        continue
                    cells = _split_table(lines[i])
                    if len(cells) != len(header) or set("".join(cells)) <= set("-: "):
                        continue
                    rows[cells[number_col]] = (i, cells[own_col], cells[1])

                url_line = next((lines[i] for i in range(header_index + 1, end) if lines[i].startswith("自リプライURL:")), "")
                for row_number, status_id in _NUMBERED_URL_RE.findall(url_line):
                    row = rows.get(row_number)
                    if not row or not _is_missing(row[1]):
                        continue
                    posted_at = post_datetime(status_id)
                    age = (now.astimezone(JST) - posted_at).total_seconds() / 3600
                    pending.append(PendingPost(
                        status_id=status_id,
                        url=f"https://x.com/sns_hannou_ma/status/{status_id}",
                        kind="リプライ",
                        posted_at=posted_at,
                        age_hours=age,
                        timing=_age_label(age),
                        target=row[2],
                        line_index=row[0],
                        row_number=row_number,
                    ))

        if kind == "論点ポスト実績":
            url_index = next((i for i in body_indexes if lines[i].startswith("投稿URL:")), None)
            if url_index is not None:
                match = _STATUS_RE.search(lines[url_index])
                view_index = next((i for i in range(url_index + 1, end) if lines[i].startswith("表示回数:")), None)
                view_value = lines[view_index].split(":", 1)[1] if view_index is not None else ""
                if match and _is_missing(view_value):
                    status_id = match.group(1)
                    posted_at = post_datetime(status_id)
                    age = (now.astimezone(JST) - posted_at).total_seconds() / 3600
                    pending.append(PendingPost(
                        status_id=status_id,
                        url=match.group(0),
                        kind="論点ポスト",
                        posted_at=posted_at,
                        age_hours=age,
                        timing=_age_label(age),
                        target="",
                        line_index=view_index if view_index is not None else url_index,
                    ))

        for follow_start in range(start + 1, end):
            follow_match = _FOLLOW_HEADING_RE.match(lines[follow_start])
            if not follow_match:
                continue
            follow_end = next(
                (i for i in range(follow_start + 1, end) if lines[i].startswith("### ")),
                end,
            )
            url_index = next((i for i in range(follow_start + 1, follow_end) if lines[i].startswith("自リプライURL:")), None)
            if url_index is None:
                continue
            status_match = _STATUS_RE.search(lines[url_index])
            view_index = next((i for i in range(url_index + 1, follow_end) if lines[i].startswith("表示回数:")), None)
            view_value = lines[view_index].split(":", 1)[1] if view_index is not None else ""
            if not status_match or not _is_missing(view_value):
                continue
            target_line = next((lines[i] for i in range(follow_start + 1, follow_end) if lines[i].startswith("返信先:")), "")
            status_id = status_match.group(1)
            posted_at = post_datetime(status_id)
            age = (now.astimezone(JST) - posted_at).total_seconds() / 3600
            pending.append(PendingPost(
                status_id=status_id,
                url=status_match.group(0),
                kind="会話フォロー",
                posted_at=posted_at,
                age_hours=age,
                timing=_age_label(age),
                target=target_line.removeprefix("返信先:").strip(),
                line_index=view_index if view_index is not None else url_index,
            ))

    unique = {item.status_id: item for item in pending}
    return sorted(unique.values(), key=lambda item: item.posted_at)


def _parse_measured_at(value: str | None) -> dt.datetime:
    if not value:
        return dt.datetime.now(JST).replace(second=0, microsecond=0)
    parsed = dt.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=JST)
    return parsed.astimezone(JST)


def _measurement_text(views: int, measured_at: dt.datetime, posted_at: dt.datetime) -> str:
    hours = round((measured_at - posted_at).total_seconds() / 3600)
    if hours < 0:
        raise ValueError("計測日時が投稿日時より前です")
    return f"**{views:,}**（{measured_at:%Y-%m-%d %H:%M}計測・投稿から約{hours}時間後）"


def apply_measurements(text: str, measurements: dict[str, int], measured_at: dt.datetime) -> str:
    """全入力を検証してから未計測箇所だけを書き換える。"""
    pending = {item.status_id: item for item in find_pending(text, measured_at)}
    unknown = sorted(set(measurements) - set(pending))
    if unknown:
        raise ValueError(
            "未計測の投稿として確認できないため書き込みません（計測済みの値は上書き禁止）: "
            + ", ".join(unknown)
        )
    for status_id, views in measurements.items():
        if views < 0:
            raise ValueError(f"表示回数は0以上で指定してください: {status_id}")

    lines = text.splitlines()
    # 行挿入で後続の行番号がずれないよう、文書の下から更新する。
    ordered = sorted(measurements.items(), key=lambda pair: pending[pair[0]].line_index, reverse=True)
    for status_id, views in ordered:
        item = pending[status_id]
        value = _measurement_text(views, measured_at, item.posted_at)
        if item.kind == "リプライ":
            cells = _split_table(lines[item.line_index])
            sections = _sections(lines)
            section = next((s for s in sections if s[0] < item.line_index < s[1]), None)
            if section is None:
                raise ValueError(f"表の所属節を確認できません: {status_id}")
            header_index = next(i for i in range(section[0] + 1, item.line_index) if "自リプライ表示" in lines[i])
            own_col = _split_table(lines[header_index]).index("自リプライ表示")
            cells[own_col] = value
            lines[item.line_index] = "| " + " | ".join(cells) + " |"
        elif lines[item.line_index].startswith("表示回数:"):
            lines[item.line_index] = f"表示回数: {value}"
        else:
            lines.insert(item.line_index + 1, f"\n表示回数: {value}")

    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _parse_views(values: list[str]) -> dict[str, int]:
    measurements: dict[str, int] = {}
    for value in values:
        try:
            status_id, count = value.split("=", 1)
            if status_id in measurements:
                raise ValueError(f"同じ投稿IDが重複しています: {status_id}")
            measurements[status_id] = int(count.replace(",", ""))
        except ValueError as exc:
            if "重複" in str(exc):
                raise
            raise ValueError(f"--view は 投稿ID=表示回数 で指定してください: {value}") from exc
    return measurements


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DEFAULT_PATH)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("pending", help="未計測投稿を一覧する")
    list_parser.add_argument("--now", help="基準日時（ISO 8601、未指定は現在時刻）")
    list_parser.add_argument("--all", action="store_true", help="24時間未満の待機中も表示する")
    list_parser.add_argument("--json", action="store_true", help="JSONで出力する")

    apply_parser = subparsers.add_parser("apply", help="取得済みの表示回数を書き戻す")
    apply_parser.add_argument("--view", action="append", required=True, metavar="ID=COUNT")
    apply_parser.add_argument("--measured-at", help="計測日時（ISO 8601、未指定は現在時刻）")

    args = parser.parse_args(argv)
    text = args.file.read_text(encoding="utf-8")

    if args.command == "pending":
        now = _parse_measured_at(args.now)
        items = find_pending(text, now)
        if not args.all:
            items = [item for item in items if item.timing != "waiting"]
        if args.json:
            print(json.dumps([item.public_dict() for item in items], ensure_ascii=False, indent=2))
        elif not items:
            print("計測対象はありません。")
        else:
            for item in items:
                print(f"{item.timing:7} {item.age_hours:5.1f}時間 {item.kind:7} {item.url} {item.target}")
        return 0

    measured_at = _parse_measured_at(args.measured_at)
    measurements = _parse_views(args.view)
    updated = apply_measurements(text, measurements, measured_at)
    args.file.write_text(updated, encoding="utf-8")
    print(f"{len(measurements)}件を記録しました: {args.file}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        raise SystemExit(2)
