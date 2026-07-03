#!/usr/bin/env python3
"""
自転車青切符問題の2次元スコア分類（OpenCode Go API版）

使い方:
  # テスト実行（20件）
  python3 scripts/classify_2d_bike_blue_ticket.py --test

  # 全量実行（137件）
  python3 scripts/classify_2d_bike_blue_ticket.py

X軸 stance_enforcement: -2(取締り不要・過剰規制) 〜 +2(取締り強化・即刻施行すべき)
Y軸 stance_priority:    -2(自転車利用者の自由・負担軽減優先) 〜 +2(歩行者・社会安全最優先)
"""
import json
import os
import sys
import argparse
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
必ずJSONのみを出力してください。説明・前置き・コードブロックは不要です。"""

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
{{"is_opinion": true/false, "stance_enforcement": 数値, "stance_priority": 数値, "emotional_intensity": 数値, "confidence": 0.0〜1.0, "summary": "20字以内"}}"""


def classify_one(text: str) -> dict | None:
    prompt = USER_PROMPT_TEMPLATE.format(text=text[:400])
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
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"].get("content", "").strip()
        if not content:
            content = data["choices"][0]["message"].get("reasoning_content", "").strip()
        start = content.find("{")
        end = content.rfind("}") + 1
        if start == -1 or end == 0:
            print(f"    ERROR: JSONが見つからない。content={repr(content[:100])}", flush=True)
            return None
        return json.loads(content[start:end])
    except Exception as e:
        print(f"    ERROR: {type(e).__name__}: {e}", flush=True)
        return None


def print_summary(results: list):
    enf_labels = {-2: "取締り反対", -1: "やや反対", 0: "中立", 1: "やや賛成", 2: "取締り賛成"}
    pri_labels = {-2: "利用者優先", -1: "やや利用者", 0: "中立", 1: "やや安全", 2: "安全優先"}

    enf_counts = {k: 0 for k in enf_labels}
    pri_counts = {k: 0 for k in pri_labels}
    for r in results:
        enf = r.get("stance_enforcement", 0)
        pri = r.get("stance_priority", 0)
        if enf in enf_counts: enf_counts[enf] += 1
        if pri in pri_counts: pri_counts[pri] += 1

    print("\n--- stance_enforcement ---")
    for k, v in sorted(enf_counts.items()):
        print(f"  {k:+d} {enf_labels[k]:12s}: {'█'*v} ({v})")

    print("\n--- stance_priority ---")
    for k, v in sorted(pri_counts.items()):
        print(f"  {k:+d} {pri_labels[k]:10s}: {'█'*v} ({v})")

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
    parser.add_argument("--test", action="store_true", help="テストモード（20件のみ）")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: OPENCODEGO_API_KEY が設定されていません")
        sys.exit(1)

    with open(INPUT_FILE) as f:
        data = json.load(f)

    samples = [d for d in data if d["classification"].get("confidence", 0) >= 0.5]
    if args.test:
        samples = samples[:20]

    print(f"Classifying {len(samples)} posts via OpenCode Go ({MODEL})...", flush=True)
    if args.test:
        print("(テストモード: 20件)", flush=True)

    results = []
    errors = 0
    for i, post in enumerate(samples):
        text = post["text"]
        result = classify_one(text)
        if result is None:
            errors += 1
            continue

        if not result.get("is_opinion", True):
            errors += 1
            continue

        results.append({
            "text": text[:200],
            "tweet_id": post.get("tweet_id", ""),
            "url": post.get("url", ""),
            "original_category": post["classification"].get("category", ""),
            "original_stance": post["classification"].get("stance", ""),
            **result,
        })

        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(samples)} done (errors: {errors})", flush=True)

    out_path = OUTPUT_FILE if not args.test else OUTPUT_FILE.with_suffix(".test.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Saved to {out_path}")
    print(f"Valid: {len(results)}, Errors/Ads: {errors}/{len(samples)} ({errors/len(samples)*100:.0f}%)")
    print_summary(results)


if __name__ == "__main__":
    main()
