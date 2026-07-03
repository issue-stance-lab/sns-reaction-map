#!/usr/bin/env python3
"""
高齢者免許返納問題の2次元スコア分類（OpenCode Go API版）

使い方:
  python3 scripts/classify_2d_elderly_license.py --test   # 20件テスト
  python3 scripts/classify_2d_elderly_license.py          # 全量135件

X軸 stance_restriction: -2(強制不要・本人判断) 〜 +2(法的義務化・強制返納すべき)
Y軸 stance_priority:    -2(高齢者の移動権・生活の自由優先) 〜 +2(交通安全・被害者保護優先)
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
INPUT_FILE = PROJECT_ROOT / "social-samples" / "elderly-license-revocation_classified.json"
OUTPUT_FILE = PROJECT_ROOT / "social-samples" / "elderly-license_2d_classified.json"

SYSTEM_PROMPT = """あなたはSNS投稿を分類する専門家です。
必ずJSONのみを出力してください。説明・前置き・コードブロックは不要です。"""

USER_PROMPT_TEMPLATE = """以下のSNS投稿を分析してください。スコアは0.5刻みで指定してください。

【まず判定】
is_opinion: この投稿が個人の意見・感想・主張かどうか
  true  = 個人の意見・感想・主張・ニュース解説
  false = 広告・宣伝・サービス招待・スパム・無関係な日常投稿

is_opinionがfalseの場合、スコアはすべて0.0、summaryに理由を記載してください。

【2軸の定義（is_opinion=trueの場合のみ）】

stance_restriction（返納強制への態度）: -2.0〜+2.0 の0.5刻み
  +2.0 = 法的義務化・強制返納を強く支持。一定年齢以上は問答無用で返納すべき
  +1.0 = やや義務化寄り・条件付き強制を支持
   0.0 = 不明・どちらでもない
  -1.0 = やや慎重・本人や家族の判断を尊重すべき
  -2.0 = 強制不要・本人判断に任せるべき・義務化反対

stance_priority（何を優先するか）: -2.0〜+2.0 の0.5刻み
  +2.0 = 交通安全・被害者保護を最優先。事故を防ぐことが第一
  +1.0 = やや安全優先
   0.0 = 不明・どちらでもない
  -1.0 = やや移動権寄り
  -2.0 = 高齢者の移動権・生活の自由を最優先。車がないと生活できない地方の実情重視

emotional_intensity（感情強度）: -2.0〜+2.0 の0.5刻み
  +2.0 = 強い怒り・激しい批判・感情的な訴え
  +1.0 = やや感情的・熱量がある
   0.0 = 冷静・中立的・事実ベース
  -1.0 = 皮肉・冷笑・距離を置いた表現
  -2.0 = 諦め・冷淡・無関心

【投稿】
{text}

【出力形式】JSONのみ出力:
{{"is_opinion": true/false, "stance_restriction": 数値, "stance_priority": 数値, "emotional_intensity": 数値, "confidence": 0.0〜1.0, "summary": "20字以内"}}"""


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
    res_labels = {-2: "強制反対", -1: "やや反対", 0: "中立", 1: "やや賛成", 2: "義務化賛成"}
    pri_labels = {-2: "移動権優先", -1: "やや移動権", 0: "中立", 1: "やや安全", 2: "安全優先"}

    res_counts = {k: 0 for k in res_labels}
    pri_counts = {k: 0 for k in pri_labels}
    for r in results:
        res = r.get("stance_restriction", 0)
        pri = r.get("stance_priority", 0)
        if res in res_counts: res_counts[res] += 1
        if pri in pri_counts: pri_counts[pri] += 1

    print("\n--- stance_restriction ---")
    for k, v in sorted(res_counts.items()):
        print(f"  {k:+d} {res_labels[k]:12s}: {'█'*v} ({v})")

    print("\n--- stance_priority ---")
    for k, v in sorted(pri_counts.items()):
        print(f"  {k:+d} {pri_labels[k]:10s}: {'█'*v} ({v})")

    print("\n--- 象限分布 ---")
    q = {"義務化賛成×安全優先": 0, "強制反対×安全優先": 0, "義務化賛成×移動権優先": 0, "強制反対×移動権優先": 0, "中立含む": 0}
    for r in results:
        res = r.get("stance_restriction", 0)
        pri = r.get("stance_priority", 0)
        if res == 0 or pri == 0:
            q["中立含む"] += 1
        elif res > 0 and pri > 0:
            q["義務化賛成×安全優先"] += 1
        elif res < 0 and pri > 0:
            q["強制反対×安全優先"] += 1
        elif res > 0 and pri < 0:
            q["義務化賛成×移動権優先"] += 1
        else:
            q["強制反対×移動権優先"] += 1
    for k, v in q.items():
        print(f"  {k}: {v}件")


def main():
    parser = argparse.ArgumentParser(description="elderly-license 2D分類 (OpenCode Go)")
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
