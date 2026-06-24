#!/usr/bin/env python3
"""Import classified social reactions into a local SQLite database."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS issues (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  description TEXT DEFAULT '',
  source_label TEXT DEFAULT '',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  issue_id INTEGER NOT NULL,
  source_row_index INTEGER NOT NULL,
  source TEXT DEFAULT '',
  query TEXT DEFAULT '',
  fetched_at TEXT DEFAULT '',
  text TEXT NOT NULL,
  tweet_id TEXT DEFAULT '',
  url TEXT DEFAULT '',
  user_id TEXT DEFAULT '',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(issue_id, source_row_index),
  FOREIGN KEY(issue_id) REFERENCES issues(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS classifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  reaction_id INTEGER NOT NULL UNIQUE,
  category TEXT NOT NULL,
  stance TEXT NOT NULL,
  target TEXT DEFAULT '',
  topic_target TEXT DEFAULT '',
  actor_target TEXT DEFAULT '',
  criticized_target TEXT DEFAULT '',
  stance_to_target TEXT DEFAULT '',
  issue TEXT DEFAULT '',
  quote_direction TEXT DEFAULT '',
  stance_to_quoted_author TEXT DEFAULT '',
  stance_to_quoted_claim TEXT DEFAULT '',
  confidence_level TEXT DEFAULT '',
  alternate_categories_json TEXT DEFAULT '[]',
  review_required INTEGER DEFAULT 0,
  review_reason TEXT DEFAULT '',
  summary TEXT DEFAULT '',
  reason TEXT DEFAULT '',
  confidence REAL DEFAULT 0,
  article_usable INTEGER DEFAULT 0,
  risk TEXT DEFAULT '',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(reaction_id) REFERENCES reactions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scorecards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  issue_id INTEGER NOT NULL,
  topic TEXT NOT NULL,
  criticism_score INTEGER,
  defense_score INTEGER,
  verdict TEXT DEFAULT '',
  reason TEXT DEFAULT '',
  sort_order INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(issue_id) REFERENCES issues(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  issue_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  source_type TEXT DEFAULT '',
  note TEXT DEFAULT '',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(issue_id, url),
  FOREIGN KEY(issue_id) REFERENCES issues(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reactions_issue_query ON reactions(issue_id, query);
CREATE INDEX IF NOT EXISTS idx_classifications_category ON classifications(category);
CREATE INDEX IF NOT EXISTS idx_classifications_stance ON classifications(stance);
CREATE INDEX IF NOT EXISTS idx_scorecards_issue ON scorecards(issue_id, sort_order);
"""


DEFAULT_SCORECARDS = [
    ("本人の責任", 8, 6, "本人指示は未確定。ただし説明責任は残る", "陣営や公設秘書が関与したとされる以上、政治責任としての説明論点は残る。", 1),
    ("文春報道の信用性", 7, 7, "追加検証待ち", "文春は資料・証言を報じている一方、SNS上では報道への疑義も強い。", 2),
    ("陣営・秘書の管理責任", 8, 5, "批判側がやや優勢", "本人指示とは別に、陣営管理と秘書の関与は説明責任につながる。", 3),
    ("玉木代表との比較", 4, 7, "同列視は弱い", "松井氏との接点は論点になるが、中傷動画疑惑と動画制作依頼は同じではない。", 4),
    ("ネット選挙の透明性", 8, 6, "制度論として重要", "外注、広告、AI、ショート動画の発信主体と対価の透明性は今後の制度論になる。", 5),
    ("サナエトークンへの接続", 5, 6, "関心は高いが、事実接続は慎重に扱うべき", "SNS上の連想としては多いが、事実関係として一本化するには追加確認が必要。", 6),
]


DEFAULT_SOURCES = [
    ("文春オンライン 高市陣営中傷動画問題", "https://bunshun.jp/articles/-/89485", "article", "高市陣営、木下公設第一秘書、松井健氏をめぐる報道。"),
    ("ABEMA TIMES 玉木代表と松井健氏の説明", "https://times.abema.tv/articles/-/10251745", "article", "玉木代表側の動画制作依頼・松井氏との関係説明。"),
]


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def read_optional_json(path: str) -> Any | None:
    if not path:
        return None
    p = resolve(path)
    if not p.exists():
        raise FileNotFoundError(p)
    return json.loads(p.read_text(encoding="utf-8"))


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    ensure_classification_columns(conn)
    return conn


def ensure_classification_columns(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(classifications)").fetchall()}
    columns = {
        "target": "TEXT DEFAULT ''",
        "topic_target": "TEXT DEFAULT ''",
        "actor_target": "TEXT DEFAULT ''",
        "criticized_target": "TEXT DEFAULT ''",
        "stance_to_target": "TEXT DEFAULT ''",
        "issue": "TEXT DEFAULT ''",
        "quote_direction": "TEXT DEFAULT ''",
        "stance_to_quoted_author": "TEXT DEFAULT ''",
        "stance_to_quoted_claim": "TEXT DEFAULT ''",
        "confidence_level": "TEXT DEFAULT ''",
        "alternate_categories_json": "TEXT DEFAULT '[]'",
        "review_required": "INTEGER DEFAULT 0",
        "review_reason": "TEXT DEFAULT ''",
    }
    for name, definition in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE classifications ADD COLUMN {name} {definition}")


def upsert_issue(conn: sqlite3.Connection, slug: str, title: str, description: str, source_label: str) -> int:
    conn.execute(
        """
        INSERT INTO issues(slug, title, description, source_label, updated_at)
        VALUES(?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(slug) DO UPDATE SET
          title=excluded.title,
          description=excluded.description,
          source_label=excluded.source_label,
          updated_at=CURRENT_TIMESTAMP
        """,
        (slug, title, description, source_label),
    )
    row = conn.execute("SELECT id FROM issues WHERE slug = ?", (slug,)).fetchone()
    return int(row["id"])


def import_reaction(conn: sqlite3.Connection, issue_id: int, source_row_index: int, row: dict[str, Any]) -> None:
    c = row.get("classification") or {}
    conn.execute(
        """
        INSERT INTO reactions(issue_id, source_row_index, source, query, fetched_at, text, tweet_id, url, user_id)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(issue_id, source_row_index) DO UPDATE SET
          source=excluded.source,
          query=excluded.query,
          fetched_at=excluded.fetched_at,
          text=excluded.text,
          tweet_id=excluded.tweet_id,
          url=excluded.url,
          user_id=excluded.user_id
        """,
        (
            issue_id,
            source_row_index,
            row.get("source", ""),
            row.get("query", ""),
            row.get("fetched_at", ""),
            row.get("text", ""),
            row.get("tweet_id", ""),
            row.get("url", ""),
            row.get("user_id", ""),
        ),
    )
    reaction = conn.execute(
        """
        SELECT id FROM reactions
        WHERE issue_id = ? AND source_row_index = ?
        """,
        (issue_id, source_row_index),
    ).fetchone()
    if reaction is None:
        return
    conn.execute(
        """
        INSERT INTO classifications(
          reaction_id, category, stance, target, topic_target, actor_target, criticized_target,
          stance_to_target, issue, quote_direction, stance_to_quoted_author, stance_to_quoted_claim,
          confidence_level, alternate_categories_json, review_required, review_reason,
          summary, reason, confidence, article_usable, risk
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(reaction_id) DO UPDATE SET
          category=excluded.category,
          stance=excluded.stance,
          target=excluded.target,
          topic_target=excluded.topic_target,
          actor_target=excluded.actor_target,
          criticized_target=excluded.criticized_target,
          stance_to_target=excluded.stance_to_target,
          issue=excluded.issue,
          quote_direction=excluded.quote_direction,
          stance_to_quoted_author=excluded.stance_to_quoted_author,
          stance_to_quoted_claim=excluded.stance_to_quoted_claim,
          confidence_level=excluded.confidence_level,
          alternate_categories_json=excluded.alternate_categories_json,
          review_required=excluded.review_required,
          review_reason=excluded.review_reason,
          summary=excluded.summary,
          reason=excluded.reason,
          confidence=excluded.confidence,
          article_usable=excluded.article_usable,
          risk=excluded.risk
        """,
        (
            int(reaction["id"]),
            c.get("category", "未分類"),
            c.get("stance") or c.get("stance_to_target", "その他"),
            c.get("target", ""),
            c.get("topic_target", ""),
            c.get("actor_target", ""),
            c.get("criticized_target", ""),
            c.get("stance_to_target", ""),
            c.get("issue", ""),
            c.get("quote_direction", ""),
            c.get("stance_to_quoted_author", ""),
            c.get("stance_to_quoted_claim", ""),
            c.get("confidence_level", ""),
            json.dumps(c.get("alternate_categories", []), ensure_ascii=False),
            1 if c.get("review_required") else 0,
            c.get("review_reason", ""),
            c.get("summary", ""),
            c.get("reason", ""),
            float(c.get("confidence") or 0.0),
            1 if c.get("article_usable") else 0,
            c.get("risk", ""),
        ),
    )


def scorecard_tuple(row: Any, sort_order: int) -> tuple:
    if isinstance(row, dict):
        return (
            row.get("topic", ""),
            row.get("criticism_score"),
            row.get("defense_score"),
            row.get("verdict", ""),
            row.get("reason", ""),
            int(row.get("sort_order") or sort_order),
        )
    return tuple(row)


def replace_scorecards(conn: sqlite3.Connection, issue_id: int, scorecards: list[Any]) -> None:
    conn.execute("DELETE FROM scorecards WHERE issue_id = ?", (issue_id,))
    conn.executemany(
        """
        INSERT INTO scorecards(issue_id, topic, criticism_score, defense_score, verdict, reason, sort_order)
        VALUES(?, ?, ?, ?, ?, ?, ?)
        """,
        [(issue_id, *scorecard_tuple(row, i)) for i, row in enumerate(scorecards, 1)],
    )


def source_tuple(row: Any) -> tuple:
    if isinstance(row, dict):
        return (row.get("title", ""), row.get("url", ""), row.get("source_type", ""), row.get("note", ""))
    return tuple(row)


def upsert_sources(conn: sqlite3.Connection, issue_id: int, sources: list[Any]) -> None:
    for row in sources:
        title, url, source_type, note = source_tuple(row)
        if not title or not url:
            continue
        conn.execute(
            """
            INSERT INTO sources(issue_id, title, url, source_type, note)
            VALUES(?, ?, ?, ?, ?)
            ON CONFLICT(issue_id, url) DO UPDATE SET
              title=excluded.title,
              source_type=excluded.source_type,
              note=excluded.note
            """,
            (issue_id, title, url, source_type, note),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Import classified reactions to SQLite")
    parser.add_argument("--input", required=True)
    parser.add_argument("--db", default="data/reaction_map.sqlite3")
    parser.add_argument("--issue-slug", default="takaichi-bunshun-smear-video")
    parser.add_argument("--issue-title", default="高市文春問題 SNS反応まっぷ")
    parser.add_argument("--description", default="高市陣営の中傷動画問題をめぐるSNS反応サンプル分類。")
    parser.add_argument("--source-label", default="Yahooリアルタイム検索")
    parser.add_argument("--scorecards", default="", help="Optional JSON list of scorecards")
    parser.add_argument("--sources", default="", help="Optional JSON list of sources")
    parser.add_argument("--replace-issue", action="store_true", help="Delete existing issue rows before import")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate the SQLite file before import")
    args = parser.parse_args()

    rows = json.loads(resolve(args.input).read_text(encoding="utf-8"))
    db_path = resolve(args.db)
    if args.reset and db_path.exists():
        db_path.unlink()
    conn = connect(db_path)
    with conn:
        if args.replace_issue:
            conn.execute("DELETE FROM issues WHERE slug = ?", (args.issue_slug,))
        issue_id = upsert_issue(conn, args.issue_slug, args.issue_title, args.description, args.source_label)
        for source_row_index, row in enumerate(rows, 1):
            import_reaction(conn, issue_id, source_row_index, row)
        scorecards = read_optional_json(args.scorecards) or DEFAULT_SCORECARDS
        sources = read_optional_json(args.sources) or DEFAULT_SOURCES
        replace_scorecards(conn, issue_id, scorecards)
        upsert_sources(conn, issue_id, sources)
    reaction_count = conn.execute("SELECT COUNT(*) AS n FROM reactions WHERE issue_id = ?", (issue_id,)).fetchone()["n"]
    print(f"db={resolve(args.db)}")
    print(f"issue_id={issue_id}")
    print(f"reactions={reaction_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
