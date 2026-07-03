#!/usr/bin/env python3
"""
あだ名禁止問題の2次元スコア分類（OpenCode Go API版）

使い方:
  python3 scripts/classify_2d_nickname_ban.py --test   # 20件テスト
  python3 scripts/classify_2d_nickname_ban.py          # 全量344件

X軸 stance_ban:     -2(禁止に強く反対) 〜 +2(禁止に強く賛成)
Y軸 stance_culture: -2(子どもの自由・文化を尊重すべき) 〜 +2(学校の管理・配慮を優先すべき)
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
INPUT_FILE = PROJECT_ROOT / "social-samples" / "school-nickname-ban_classified_v2_final.json"
OUTPUT_FILE = PROJECT_ROOT / "social-samples" / "school-nickname-ban_2d_classified.json"

SYSTEM_PROMPT = """あなたはSNS投稿を分類する専門家です。
必ずJSONのみを出力してください。説明・前置き・コードブロックは不要です。"""

USER_PROMPT_TEMPLATE = """以下のSNS投稿を分析してください。スコアは0.5刻みで指定してください。

【まず判定】
is_opinion: この投稿が「あだ名禁止」問題に関する個人の意見・感想・主張かどうか
  true  = あだ名禁止・呼称ルールに関する意見・感想・体験談・ニュース解説
  false = 広告・宣伝・スパム・あだ名が偶然出てきただけの無関係投稿・単なる日常投稿

is_opinionがfalseの場合、スコアはすべて0.0、summaryに理由を記載してください。

【2軸の定義（is_opinion=trueの場合のみ）】

stance_ban（あだ名禁止への態度）: -2.0〜+2.0 の0.5刻み
  +2.0 = あだ名禁止を強く支持。学校でのあだ名・呼び捨てを禁止すべき
  +1.0 = やや禁止支持・条件付きで制限すべき
   0.0 = 不明・どちらでもない・体験談のみ
  -1.0 = やや禁止反対・過剰規制と感じる
  -2.0 = 禁止に強く反対。子どもの自由・文化を尊重すべき

stance_culture（何を優先するか）: -2.0〜+2.0 の0.5刻み
  +2.0 = 学校の管理・配慮を最優先。いじめ・ハラスメント防止のためルール整備は当然
  +1.0 = やや管理・配慮寄り。一定のルールは必要
   0.0 = 不明・どちらでもない・言及なし
  -1.0 = やや自由・文化寄り。過剰な管理に違和感がある
  -2.0 = 子どもの自由・呼称文化を最優先。管理主義的・息苦しい・子どもの自然なコミュニケーションを壊す

emotional_intensity（感情強度）: -2.0〜+2.0 の0.5刻み
  +2.0 = 強い怒り・激しい批判・感情的な訴え
  +1.0 = やや感情的・熱量がある
   0.0 = 冷静・中立的・事実ベース
  -1.0 = 皮肉・冷笑・距離を置いた表現
  -2.0 = 諦め・冷淡・無関心

【投稿】
{text}

【出力形式】JSONのみ出力:
{{"is_opinion": true/false, "stance_ban": 数値, "stance_culture": 数値, "emotional_intensity": 数値, "confidence": 0.0〜1.0, "summary": "20字以内"}}"""


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
    ban_labels = {-2: "禁止強反対", -1: "やや反対", 0: "中立", 1: "やや賛成", 2: "禁止強賛成"}
    cul_labels = {-2: "自由・文化優先", -1: "やや自由優先", 0: "中立", 1: "やや管理優先", 2: "管理・配慮優先"}

    ban_counts = {k: 0 for k in ban_labels}
    cul_counts = {k: 0 for k in cul_labels}
    for r in results:
        ban = r.get("stance_ban", 0)
        cul = r.get("stance_culture", 0)
        if ban in ban_counts: ban_counts[ban] += 1
        if cul in cul_counts: cul_counts[cul] += 1

    print("\n--- stance_ban ---")
    for k, v in sorted(ban_counts.items()):
        print(f"  {k:+d} {ban_labels[k]:14s}: {'█'*v} ({v})")

    print("\n--- stance_culture ---")
    for k, v in sorted(cul_counts.items()):
        print(f"  {k:+d} {cul_labels[k]:14s}: {'█'*v} ({v})")

    print("\n--- 象限分布 ---")
    q = {
        "禁止賛成×管理優先": 0,
        "禁止反対×自由優先": 0,
        "禁止賛成×自由優先": 0,
        "禁止反対×管理優先": 0,
        "中立含む": 0,
    }
    high_emo = sum(1 for r in results if r.get("emotional_intensity", 0) >= 1.5)
    calm = sum(1 for r in results if r.get("emotional_intensity", 0) <= 0)
    for r in results:
        ban = r.get("stance_ban", 0)
        cul = r.get("stance_culture", 0)
        if ban == 0 or cul == 0:
            q["中立含む"] += 1
        elif ban > 0 and cul > 0:
            q["禁止賛成×管理優先"] += 1
        elif ban < 0 and cul < 0:
            q["禁止反対×自由優先"] += 1
        elif ban > 0 and cul < 0:
            q["禁止賛成×自由優先"] += 1
        else:
            q["禁止反対×管理優先"] += 1
    for k, v in q.items():
        print(f"  {k}: {v}件")
    print(f"\n  高感情(e≥1.5): {high_emo}件")
    print(f"  冷静(e≤0): {calm}件")


def main():
    parser = argparse.ArgumentParser(description="school-nickname-ban 2D分類 (OpenCode Go)")
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
