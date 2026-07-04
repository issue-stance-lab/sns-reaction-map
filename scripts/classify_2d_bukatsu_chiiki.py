#!/usr/bin/env python3
"""
部活動地域移行問題の2次元スコア分類（OpenCode Go API版）

使い方:
  python3 scripts/classify_2d_bukatsu_chiiki.py --test   # 20件テスト
  python3 scripts/classify_2d_bukatsu_chiiki.py          # 全量179件

X軸 stance_transfer: -2(地域移行に強く反対) 〜 +2(地域移行に強く賛成)
Y軸 stance_priority: -2(教員負担軽減を最優先) 〜 +2(競技力・教育的価値を最優先)
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
INPUT_FILE = PROJECT_ROOT / "social-samples" / "bukatsu-chiiki_classified_v2.json"
OUTPUT_FILE = PROJECT_ROOT / "social-samples" / "bukatsu-chiiki_2d_classified.json"

SYSTEM_PROMPT = """あなたはSNS投稿を分類する専門家です。
必ずJSONのみを出力してください。説明・前置き・コードブロックは不要です。"""

USER_PROMPT_TEMPLATE = """以下のSNS投稿を分析してください。スコアは0.5刻みで指定してください。

【まず判定】
is_opinion: この投稿が部活動の地域移行問題に関する個人の意見・感想・主張かどうか
  true  = 地域移行の賛否・費用・制度設計・教員負担・競技力などへの意見・感想・体験談
  false = 広告・宣伝・スパム・部活が偶然出てきただけの無関係投稿

is_opinionがfalseの場合、スコアはすべて0.0、summaryに理由を記載してください。

【2軸の定義（is_opinion=trueの場合のみ）】

stance_transfer（地域移行への態度）: -2.0〜+2.0 の0.5刻み
  +2.0 = 地域移行を強く支持・推進すべき
  +1.0 = やや支持・条件付きで賛成
   0.0 = 不明・どちらでもない・制度論のみ
  -1.0 = やや反対・懸念が大きい
  -2.0 = 地域移行に強く反対・廃止または現状維持を望む

stance_priority（何を優先するか）: -2.0〜+2.0 の0.5刻み
  +2.0 = 競技力・部活の教育的価値・子どもの体験を最優先。部活は学校文化の核
  +1.0 = やや競技力・教育的価値寄り
   0.0 = 不明・どちらでもない・言及なし
  -1.0 = やや教員負担軽減寄り
  -2.0 = 教員負担軽減を最優先。先生を部活から解放すべき・過労改善が第一

emotional_intensity（感情強度）: -2.0〜+2.0 の0.5刻み
  +2.0 = 強い怒り・激しい批判・感情的な訴え
  +1.0 = やや感情的・熱量がある
   0.0 = 冷静・中立的・事実ベース
  -1.0 = 皮肉・冷笑・距離を置いた表現
  -2.0 = 諦め・冷淡・無関心

【投稿】
{text}

【出力形式】JSONのみ出力:
{{"is_opinion": true/false, "stance_transfer": 数値, "stance_priority": 数値, "emotional_intensity": 数値, "confidence": 0.0〜1.0, "summary": "20字以内"}}"""


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
    tr_labels = {-2: "移行強反対", -1: "やや反対", 0: "中立", 1: "やや賛成", 2: "移行強賛成"}
    pr_labels = {-2: "教員負担優先", -1: "やや負担優先", 0: "中立", 1: "やや競技力優先", 2: "競技力優先"}

    tr_counts = {k: 0 for k in tr_labels}
    pr_counts = {k: 0 for k in pr_labels}
    for r in results:
        tr = r.get("stance_transfer", 0)
        pr = r.get("stance_priority", 0)
        if tr in tr_counts: tr_counts[tr] += 1
        if pr in pr_counts: pr_counts[pr] += 1

    print("\n--- stance_transfer ---")
    for k, v in sorted(tr_counts.items()):
        print(f"  {k:+d} {tr_labels[k]:14s}: {'█'*v} ({v})")

    print("\n--- stance_priority ---")
    for k, v in sorted(pr_counts.items()):
        print(f"  {k:+d} {pr_labels[k]:14s}: {'█'*v} ({v})")

    print("\n--- 象限分布 ---")
    q = {
        "移行賛成×教員負担優先": 0,
        "移行賛成×競技力優先": 0,
        "移行反対×競技力優先": 0,
        "移行反対×教員負担優先": 0,
        "中立含む": 0,
    }
    high_emo = sum(1 for r in results if r.get("emotional_intensity", 0) >= 1.5)
    calm = sum(1 for r in results if r.get("emotional_intensity", 0) <= 0)
    for r in results:
        tr = r.get("stance_transfer", 0)
        pr = r.get("stance_priority", 0)
        if tr == 0 or pr == 0:
            q["中立含む"] += 1
        elif tr > 0 and pr < 0:
            q["移行賛成×教員負担優先"] += 1
        elif tr > 0 and pr > 0:
            q["移行賛成×競技力優先"] += 1
        elif tr < 0 and pr > 0:
            q["移行反対×競技力優先"] += 1
        else:
            q["移行反対×教員負担優先"] += 1
    for k, v in q.items():
        print(f"  {k}: {v}件")
    print(f"\n  高感情(e≥1.5): {high_emo}件")
    print(f"  冷静(e≤0): {calm}件")


def main():
    parser = argparse.ArgumentParser(description="bukatsu-chiiki 2D分類 (OpenCode Go)")
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
