#!/usr/bin/env python3
"""
生成AIと著作権問題の2次元スコア分類（OpenCode Go API版）

使い方:
  # プロジェクトルートに .env を作成して APIキーを設定
  echo 'OPENCODEGO_API_KEY=sk-xxx' > .env

  # テスト実行（50件）
  python3 scripts/classify_2d_opencodego.py --test

  # 全量実行（904件）
  python3 scripts/classify_2d_opencodego.py

X軸 stance_regulation: -2(規制強く反対) 〜 +2(規制強く賛成)
Y軸 stance_beneficiary: -2(産業/社会全体優先) 〜 +2(クリエイター個人優先)
"""
import json
import os
import sys
import argparse
from pathlib import Path
import requests

# .env ファイルから読み込み（python-dotenv 不要の簡易版）
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
INPUT_FILE = PROJECT_ROOT / "social-samples" / "ai-copyright_classified.json"
OUTPUT_FILE = PROJECT_ROOT / "social-samples" / "ai-copyright_2d_classified.json"

SYSTEM_PROMPT = """あなたはSNS投稿を分類する専門家です。
必ずJSONのみを出力してください。説明・前置き・コードブロックは不要です。"""

USER_PROMPT_TEMPLATE = """以下のSNS投稿を分析してください。スコアは0.5刻みで指定してください。

【まず判定】
is_opinion: この投稿が個人の意見・感想・主張かどうか
  true  = 個人の意見・感想・主張・ニュース解説
  false = 広告・宣伝・サービス招待・スパム・無関係な日常投稿

is_opinionがfalseの場合、スコアはすべて0.0、summaryに理由を記載してください。

【3軸の定義（is_opinion=trueの場合のみ）】

stance_regulation（規制への態度）: -2.0〜+2.0 の0.5刻み
  +2.0 = 生成AIを強く規制すべき・禁止せよ
  +1.5 = かなり規制寄り
  +1.0 = やや規制寄り
  +0.5 = 弱く規制寄り
   0.0 = 不明・どちらでもない
  -0.5 = 弱く自由化寄り
  -1.0 = やや自由化寄り
  -1.5 = かなり自由化寄り
  -2.0 = 規制不要・AIを完全に自由に使うべき

stance_beneficiary（誰を優先するか）: -2.0〜+2.0 の0.5刻み
  +2.0 = クリエイター個人の権利を最優先・産業は二の次
  +1.5 = かなり個人権利寄り
  +1.0 = やや個人権利寄り
  +0.5 = 弱く個人権利寄り
   0.0 = 不明・どちらでもない
  -0.5 = 弱く産業・社会寄り
  -1.0 = やや産業・社会全体の利益寄り
  -1.5 = かなり産業・社会寄り
  -2.0 = AI産業・社会全体の発展を最優先

emotional_intensity（感情強度）: -2.0〜+2.0 の0.5刻み
  +2.0 = 強い怒り・激しい批判・感情的な訴え
  +1.0 = やや感情的・熱量がある
   0.0 = 冷静・中立的・事実ベース
  -1.0 = 皮肉・冷笑・距離を置いた表現
  -2.0 = 諦め・冷淡・無関心

【投稿】
{text}

【出力形式】JSONのみ出力:
{{"is_opinion": true/false, "stance_regulation": 数値, "stance_beneficiary": 数値, "emotional_intensity": 数値, "confidence": 0.0〜1.0, "summary": "20字以内"}}"""


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
    reg_labels = {-2: "規制強く反対", -1: "やや反対", 0: "中立", 1: "やや賛成", 2: "規制強く賛成"}
    ben_labels = {-2: "産業優先", -1: "やや産業", 0: "中立", 1: "やや個人", 2: "個人優先"}

    reg_counts = {k: 0 for k in reg_labels}
    ben_counts = {k: 0 for k in ben_labels}
    for r in results:
        reg = r.get("stance_regulation", 0)
        ben = r.get("stance_beneficiary", 0)
        if reg in reg_counts: reg_counts[reg] += 1
        if ben in ben_counts: ben_counts[ben] += 1

    print("\n--- stance_regulation ---")
    for k, v in sorted(reg_counts.items()):
        print(f"  {k:+d} {reg_labels[k]:12s}: {'█'*v} ({v})")

    print("\n--- stance_beneficiary ---")
    for k, v in sorted(ben_counts.items()):
        print(f"  {k:+d} {ben_labels[k]:10s}: {'█'*v} ({v})")

    print("\n--- 象限分布 ---")
    q = {"規制賛成×個人優先": 0, "規制反対×個人優先": 0, "規制賛成×産業優先": 0, "規制反対×産業優先": 0, "中立含む": 0}
    for r in results:
        reg = r.get("stance_regulation", 0)
        ben = r.get("stance_beneficiary", 0)
        if reg == 0 or ben == 0:
            q["中立含む"] += 1
        elif reg > 0 and ben > 0:
            q["規制賛成×個人優先"] += 1
        elif reg < 0 and ben > 0:
            q["規制反対×個人優先"] += 1
        elif reg > 0 and ben < 0:
            q["規制賛成×産業優先"] += 1
        else:
            q["規制反対×産業優先"] += 1
    for k, v in q.items():
        print(f"  {k}: {v}件")


def main():
    parser = argparse.ArgumentParser(description="ai-copyright 2D分類 (OpenCode Go)")
    parser.add_argument("--test", action="store_true", help="テストモード（50件のみ）")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: OPENCODEGO_API_KEY が設定されていません")
        print("  .env ファイルに OPENCODEGO_API_KEY=sk-xxx を追加してください")
        sys.exit(1)

    with open(INPUT_FILE) as f:
        data = json.load(f)

    samples = [d for d in data if d["classification"].get("confidence", 0) >= 0.5]
    if args.test:
        samples = samples[:50]

    print(f"Classifying {len(samples)} posts via OpenCode Go ({MODEL})...", flush=True)
    if args.test:
        print("(テストモード: 50件)", flush=True)

    results = []
    errors = 0
    for i, post in enumerate(samples):
        text = post["text"]
        result = classify_one(text)
        if result is None:
            errors += 1
            result = {"is_opinion": False, "stance_regulation": 0, "stance_beneficiary": 0, "confidence": 0.0, "summary": "エラー"}

        # 広告・宣伝投稿はスキップ
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
    print(f"Errors: {errors}/{len(samples)} ({errors/len(samples)*100:.0f}%)")
    print_summary(results)


if __name__ == "__main__":
    main()
