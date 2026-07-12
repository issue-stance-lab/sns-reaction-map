#!/usr/bin/env python3
"""
自転車青切符問題の2次元スコア分類（OpenCode Go API版）

使い方:
  # 10件テスト
  python3 scripts/classify_2d_bike_blue_ticket.py --input INPUT --output OUTPUT --limit 10

  # 全量実行（途中結果から再開可能）
  python3 scripts/classify_2d_bike_blue_ticket.py --input INPUT --output OUTPUT --resume

X軸 stance_enforcement: -2(取締り不要・過剰規制) 〜 +2(取締り強化・即刻施行すべき)
Y軸 stance_priority:    -2(自転車利用者の自由・負担軽減優先) 〜 +2(歩行者・社会安全最優先)
"""
import json
import os
import sys
import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import requests

def load_dotenv():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

load_dotenv()

API_KEY = os.environ.get("OPENCODEGO_API_KEY", "")
BASE_URL = "https://opencode.ai/zen/go/v1/chat/completions"
MODEL = "minimax-m2.7"

PROJECT_ROOT = Path(__file__).parent.parent
INPUT_FILE = PROJECT_ROOT / "social-samples" / "bike-blue-ticket_classified.json"
OUTPUT_FILE = PROJECT_ROOT / "social-samples" / "bike-blue-ticket_2d_classified.json"

SYSTEM_PROMPT = """あなたはSNS投稿を分類する専門家です。
必ずJSONのみを出力してください。説明・前置き・コードブロックは不要です。
summaryを含む文字列は、外国語や不自然な混植を避け、自然な日本語だけで書いてください。"""

USER_PROMPT_TEMPLATE = """以下のSNS投稿を分析してください。スコアは0.5刻みで指定してください。

【まず判定】
is_opinion: この投稿が個人の意見・感想・主張かどうか
  true  = 個人の意見・感想・主張・ニュース解説
  false = 広告・宣伝・サービス招待・スパム・無関係な日常投稿

is_opinionがfalseの場合、スコアはすべて0.0、summaryに理由を記載してください。

【2軸の定義（is_opinion=trueの場合のみ）】

stance_enforcement（取締り強化への態度）: -2.0〜+2.0 の0.5刻み
  +2.0 = 取締り強化を強く支持・青切符制度は必要・厳格に施行すべき
  +1.0 = やや支持・ある程度必要
   0.0 = 不明・どちらでもない・ニュートラル
  -1.0 = やや懐疑・過剰・現実的ではない
  -2.0 = 取締り不要・過剰規制・反対

stance_priority（誰を優先するか）: -2.0〜+2.0 の0.5刻み
  +2.0 = 歩行者・社会の安全を最優先・被害者保護が第一
  +1.0 = やや安全寄り
   0.0 = 不明・どちらでもない
  -1.0 = やや自転車利用者寄り
  -2.0 = 自転車利用者の自由・利便性・負担軽減を最優先

emotional_intensity（感情強度）: -2.0〜+2.0 の0.5刻み
  +2.0 = 強い怒り・激しい批判・感情的な訴え
  +1.0 = やや感情的・熱量がある
   0.0 = 冷静・中立的・事実ベース
  -1.0 = 皮肉・冷笑・距離を置いた表現
  -2.0 = 諦め・冷淡・無関心

【投稿】
{text}

【出力形式】JSONのみ出力:
{{"is_opinion": true/false, "stance_enforcement": 数値, "stance_priority": 数値, "emotional_intensity": 数値, "confidence": 0.0〜1.0, "summary": "自然な日本語で40字以内"}}"""


def clean_text(text: str) -> str:
    return " ".join(text.replace("\tSTART\t", " ").replace("\tEND\t", " ").split())


def row_key(row: dict) -> str:
    return str(row.get("tweet_id") or row.get("url") or clean_text(row.get("text", "")))


def save_json(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def snap_score(value) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return max(-2.0, min(2.0, round(number * 2) / 2))


def normalize_result(result: dict) -> dict:
    try:
        confidence = float(result.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    return {
        "is_opinion": result.get("is_opinion") is True,
        "stance_enforcement": snap_score(result.get("stance_enforcement")),
        "stance_priority": snap_score(result.get("stance_priority")),
        "emotional_intensity": snap_score(result.get("emotional_intensity")),
        "confidence": max(0.0, min(1.0, confidence)),
        "summary": str(result.get("summary") or "").strip()[:80],
    }


def classify_one(text: str, *, timeout: int, retries: int) -> dict | None:
    prompt = USER_PROMPT_TEMPLATE.format(text=text[:400])
    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                BASE_URL,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.1,
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"].get("content", "").strip()
            if not content:
                content = data["choices"][0]["message"].get("reasoning_content", "").strip()
            start = content.find("{")
            end = content.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError(f"JSONが見つからない: {content[:100]!r}")
            return normalize_result(json.loads(content[start:end]))
        except Exception as exc:
            print(f"    ERROR {attempt + 1}/{retries + 1}: {type(exc).__name__}: {exc}", flush=True)
            if attempt < retries:
                time.sleep(1.0)
    return None


def print_summary(results: list):
    scores = [value / 2 for value in range(-4, 5)]

    enf_counts = {score: 0 for score in scores}
    pri_counts = {score: 0 for score in scores}
    for r in results:
        enf = r.get("stance_enforcement", 0)
        pri = r.get("stance_priority", 0)
        if enf in enf_counts: enf_counts[enf] += 1
        if pri in pri_counts: pri_counts[pri] += 1

    print("\n--- stance_enforcement ---")
    for k, v in sorted(enf_counts.items()):
        print(f"  {k:+.1f}: {'█'*v} ({v})")

    print("\n--- stance_priority ---")
    for k, v in sorted(pri_counts.items()):
        print(f"  {k:+.1f}: {'█'*v} ({v})")

    print("\n--- 象限分布 ---")
    q = {"取締り賛成×安全優先": 0, "取締り反対×安全優先": 0, "取締り賛成×利用者優先": 0, "取締り反対×利用者優先": 0, "中立含む": 0}
    for r in results:
        enf = r.get("stance_enforcement", 0)
        pri = r.get("stance_priority", 0)
        if enf == 0 or pri == 0:
            q["中立含む"] += 1
        elif enf > 0 and pri > 0:
            q["取締り賛成×安全優先"] += 1
        elif enf < 0 and pri > 0:
            q["取締り反対×安全優先"] += 1
        elif enf > 0 and pri < 0:
            q["取締り賛成×利用者優先"] += 1
        else:
            q["取締り反対×利用者優先"] += 1
    for k, v in q.items():
        print(f"  {k}: {v}件")


def main():
    parser = argparse.ArgumentParser(description="bike-blue-ticket 2D分類 (OpenCode Go)")
    parser.add_argument("--input", type=Path, default=INPUT_FILE)
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--include-low-confidence", action="store_true")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: OPENCODEGO_API_KEY が設定されていません")
        sys.exit(1)

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    samples = []
    for row in data:
        classification = row.get("classification")
        if (
            classification
            and not args.include_low_confidence
            and classification.get("confidence", 0) < 0.5
        ):
            continue
        samples.append(row)
    if args.limit:
        samples = samples[:args.limit]
    if args.workers < 1:
        parser.error("--workers must be at least 1")

    print(f"Classifying {len(samples)} posts via OpenCode Go ({MODEL})...", flush=True)
    out_path = args.output
    rejected_path = out_path.with_name(out_path.stem + "_rejected.json")
    results = []
    rejected = []
    if args.resume:
        if out_path.exists():
            results = json.loads(out_path.read_text(encoding="utf-8"))
        if rejected_path.exists():
            rejected = json.loads(rejected_path.read_text(encoding="utf-8"))
    processed = {row_key(row) for row in results + rejected}
    errors = 0
    pending = [
        (index, post, clean_text(post.get("text", "")))
        for index, post in enumerate(samples)
        if row_key(post) not in processed
    ]
    completed = len(samples) - len(pending)

    def run_one(item):
        index, post, text = item
        result = classify_one(text, timeout=args.timeout, retries=args.retries)
        if args.sleep:
            time.sleep(args.sleep)
        return index, post, text, result

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(run_one, item) for item in pending]
        for future in as_completed(futures):
            index, post, text, result = future.result()
            completed += 1
            if result is None:
                errors += 1
            elif not result.get("is_opinion", True):
                rejected.append({
                    "text": text[:400],
                    "tweet_id": post.get("tweet_id", ""),
                    "url": post.get("url", ""),
                    "query": post.get("query", ""),
                    "fetched_at": post.get("fetched_at", ""),
                    **result,
                })
                save_json(rejected_path, rejected)
            else:
                classification = post.get("classification") or {}
                results.append({
                    "text": text[:400],
                    "tweet_id": post.get("tweet_id", ""),
                    "url": post.get("url", ""),
                    "query": post.get("query", ""),
                    "fetched_at": post.get("fetched_at", ""),
                    "source": post.get("source", ""),
                    "original_category": classification.get("category", ""),
                    "original_stance": classification.get("stance", ""),
                    **result,
                })
                save_json(out_path, results)

            if completed % 10 == 0 or completed == len(samples):
                print(f"  {completed}/{len(samples)} done (errors: {errors})", flush=True)

    order = {row_key(row): index for index, row in enumerate(samples)}
    results.sort(key=lambda row: order.get(row_key(row), len(samples)))
    rejected.sort(key=lambda row: order.get(row_key(row), len(samples)))

    save_json(out_path, results)
    save_json(rejected_path, rejected)

    print(f"\nDone. Saved to {out_path}")
    print(f"Valid: {len(results)}, Rejected: {len(rejected)}, API errors: {errors}/{len(samples)}")
    print_summary(results)


if __name__ == "__main__":
    main()
