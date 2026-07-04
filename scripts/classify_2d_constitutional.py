#!/usr/bin/env python3
"""
憲法改正問題の2次元スコア分類（OpenCode Go API版）

使い方:
  python3 scripts/classify_2d_constitutional.py --test   # 20件テスト
  python3 scripts/classify_2d_constitutional.py          # 全量417件

X軸 stance_amendment: -2(改憲に強く反対・護憲) 〜 +2(改憲に強く賛成)
Y軸 stance_priority:  -2(平和主義・9条護持を最優先) 〜 +2(安全保障強化・現実的防衛を優先)
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
INPUT_FILE = PROJECT_ROOT / "social-samples" / "constitutional_amendment_classified_refreshed.json"
OUTPUT_FILE = PROJECT_ROOT / "social-samples" / "constitutional_amendment_2d_classified.json"

SYSTEM_PROMPT = """あなたはSNS投稿を分類する専門家です。
必ずJSONのみを出力してください。説明・前置き・コードブロックは不要です。"""

USER_PROMPT_TEMPLATE = """以下のSNS投稿を分析してください。スコアは0.5刻みで指定してください。

【まず判定】
is_opinion: この投稿が日本の憲法改正問題に関する個人の意見・感想・主張かどうか
  true  = 改憲賛否・9条・緊急事態条項・自衛隊・安全保障などへの意見・感想・体験談・解説
  false = 広告・宣伝・スパム・憲法が偶然出てきただけの無関係投稿

is_opinionがfalseの場合、スコアはすべて0.0、summaryに理由を記載してください。

【2軸の定義（is_opinion=trueの場合のみ）】

stance_amendment（憲法改正への態度）: -2.0〜+2.0 の0.5刻み
  +2.0 = 憲法改正を強く支持。現行憲法は時代遅れ・現実に合わない
  +1.0 = やや改憲支持・特定条文の追加・修正が必要
   0.0 = 不明・どちらでもない・手続き論のみ（国民投票法の議論など）
  -1.0 = やや護憲・改憲に慎重・懸念がある
  -2.0 = 改憲に強く反対・護憲派。現行憲法（特に9条）を守るべき

stance_priority（何を優先するか）: -2.0〜+2.0 の0.5刻み
  +2.0 = 安全保障・防衛強化を最優先。現実的な防衛力・抑止力が必要。9条の制約を問題視
  +1.0 = やや安全保障寄り。防衛力強化もある程度必要
   0.0 = 不明・どちらでもない・言及なし
  -1.0 = やや平和主義寄り。軍拡より対話・外交を重視
  -2.0 = 平和主義・9条護持を最優先。戦争放棄・非武装が日本の誇り。軍拡に強く反対

emotional_intensity（感情強度）: -2.0〜+2.0 の0.5刻み
  +2.0 = 強い怒り・激しい批判・感情的な訴え
  +1.0 = やや感情的・熱量がある
   0.0 = 冷静・中立的・事実ベース
  -1.0 = 皮肉・冷笑・距離を置いた表現
  -2.0 = 諦め・冷淡・無関心

【投稿】
{text}

【出力形式】JSONのみ出力:
{{"is_opinion": true/false, "stance_amendment": 数値, "stance_priority": 数値, "emotional_intensity": 数値, "confidence": 0.0〜1.0, "summary": "20字以内"}}"""


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
    am_labels = {-2: "改憲強反対", -1: "やや護憲", 0: "中立", 1: "やや改憲", 2: "改憲強賛成"}
    pr_labels = {-2: "平和主義優先", -1: "やや平和主義", 0: "中立", 1: "やや安保優先", 2: "安全保障優先"}

    am_counts = {k: 0 for k in am_labels}
    pr_counts = {k: 0 for k in pr_labels}
    for r in results:
        am = r.get("stance_amendment", 0)
        pr = r.get("stance_priority", 0)
        if am in am_counts: am_counts[am] += 1
        if pr in pr_counts: pr_counts[pr] += 1

    print("\n--- stance_amendment ---")
    for k, v in sorted(am_counts.items()):
        print(f"  {k:+d} {am_labels[k]:14s}: {'█'*v} ({v})")

    print("\n--- stance_priority ---")
    for k, v in sorted(pr_counts.items()):
        print(f"  {k:+d} {pr_labels[k]:14s}: {'█'*v} ({v})")

    print("\n--- 象限分布 ---")
    q = {
        "改憲賛成×安全保障優先": 0,
        "改憲反対×平和主義優先": 0,
        "改憲賛成×平和主義優先": 0,
        "改憲反対×安全保障優先": 0,
        "中立含む": 0,
    }
    high_emo = sum(1 for r in results if r.get("emotional_intensity", 0) >= 1.5)
    calm = sum(1 for r in results if r.get("emotional_intensity", 0) <= 0)
    for r in results:
        am = r.get("stance_amendment", 0)
        pr = r.get("stance_priority", 0)
        if am == 0 or pr == 0:
            q["中立含む"] += 1
        elif am > 0 and pr > 0:
            q["改憲賛成×安全保障優先"] += 1
        elif am < 0 and pr < 0:
            q["改憲反対×平和主義優先"] += 1
        elif am > 0 and pr < 0:
            q["改憲賛成×平和主義優先"] += 1
        else:
            q["改憲反対×安全保障優先"] += 1
    for k, v in q.items():
        print(f"  {k}: {v}件")
    print(f"\n  高感情(e≥1.5): {high_emo}件")
    print(f"  冷静(e≤0): {calm}件")


def main():
    parser = argparse.ArgumentParser(description="constitutional_amendment 2D分類 (OpenCode Go)")
    parser.add_argument("--test", action="store_true", help="テストモード（20件のみ）")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: OPENCODEGO_API_KEY が設定されていません")
        sys.exit(1)

    with open(INPUT_FILE) as f:
        data = json.load(f)

    samples = [d for d in data if d.get("classification", {}).get("confidence", 0) >= 0.5]
    if args.test:
        samples = samples[:20]

    print(f"Classifying {len(samples)} posts via OpenCode Go ({MODEL})...", flush=True)
    if args.test:
        print("(テストモード: 20件)", flush=True)

    results = []
    errors = 0
    for i, post in enumerate(samples):
        text = post.get("text", "")
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
            "original_category": post.get("classification", {}).get("category", ""),
            "original_stance": post.get("classification", {}).get("stance", ""),
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
