#!/usr/bin/env python3
"""
高市文春問題の2次元スコア分類（OpenCode Go API版）

使い方:
  python3 scripts/classify_2d_takaichi.py --test   # 20件テスト
  python3 scripts/classify_2d_takaichi.py          # 全量

X軸 stance_accountability: -2(高市擁護・報道批判) 〜 +2(説明責任追及・批判)
Y軸 stance_focus:          -2(派生論点・サナエトークン) 〜 +2(中傷動画・政治責任の本筋)
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
INPUT_FILE = PROJECT_ROOT / "social-samples" / "takaichi_realtime_ollama_final_reclassified.json"
OUTPUT_FILE = PROJECT_ROOT / "social-samples" / "takaichi_2d_classified.json"

SYSTEM_PROMPT = """あなたはSNS投稿を分類する専門家です。
必ずJSONのみを出力してください。説明・前置き・コードブロックは不要です。"""

USER_PROMPT_TEMPLATE = """以下のSNS投稿を分析してください。スコアは0.5刻みで指定してください。

【背景】
2025年に文春が高市早苗総理（当時）の陣営がSNS上で対立候補への中傷動画を組織的に拡散させていた疑惑を報道。松井健氏がネット工作を主導したとされ、高市氏の関与・認知の有無が焦点に。
また、高市氏の名前を冠した暗号資産「サナエトークン」が無断で発行・販売され、被害者への補償問題も並行して議論されている。

【まず判定】
is_opinion: この投稿が高市文春問題（中傷動画疑惑・サナエトークン等）に関する意見・感想・主張かどうか
  true  = 高市氏への批判・擁護、文春報道への評価、松井健氏の関与、サナエトークン等
  false = 広告・スパム・完全に無関係な投稿

is_opinionがfalseの場合、スコアはすべて0.0、summaryに理由を記載してください。

【2軸の定義（is_opinion=trueの場合のみ）】

stance_accountability（説明責任への態度）: -2.0〜+2.0 の0.5刻み
  【重要な判定基準】
  - 「高市氏は説明責任を果たせ」「関与が疑われる」「辞任すべき」→ プラス側（責任追及）
  - 「文春が捏造」「報道が先走り」「証拠不十分」→ マイナス側（擁護・報道批判）
  - 高市氏の政治姿勢そのものを批判している場合もプラス側

  +2.0 = 高市氏の関与を強く批判。説明責任・辞任を要求
  +1.0 = 高市氏の対応に疑問あり。説明が不十分
   0.0 = どちらでもない・中立・事実伝達のみ
  -1.0 = 報道に疑問。高市氏をやや擁護
  -2.0 = 文春報道は捏造・偏向。高市氏を強く擁護

stance_focus（関心の焦点）: -2.0〜+2.0 の0.5刻み
  【重要な判定基準】
  - 投稿の主要な関心がどこにあるかを判定する
  - 「中傷動画」「松井健」「ネット工作」「説明責任」について論じている → プラス側（本筋）
  - 「サナエトークン」「暗号資産」「補償」が主題 → マイナス側（派生）
  - 「玉木氏との比較」「他の政治家」への接続 → ややマイナス側

  +2.0 = 中傷動画疑惑・松井健氏との関係・政治責任が中心
  +1.0 = やや本筋寄り。ネット選挙の透明性・メディア批判
   0.0 = 不明・混合・どちらでもない
  -1.0 = やや派生寄り。玉木氏比較・他政治家への接続
  -2.0 = サナエトークン・暗号資産・陰謀論が中心

emotional_intensity（感情強度）: -2.0〜+2.0 の0.5刻み
  +2.0 = 強い怒り・激しい批判
  +1.0 = やや感情的・熱量がある
   0.0 = 冷静・中立的
  -1.0 = 皮肉・冷笑
  -2.0 = 呆れ・失望

【判定例】

例1:「高市総理は中傷動画への関与を否定しているが、松井健氏との関係を説明すべき」
→ stance_accountability: +1.5, stance_focus: +2.0（本筋の中傷動画問題）

例2:「文春の捏造がまたバレた。高市叩きはいい加減にしろ」
→ stance_accountability: -2.0, stance_focus: +1.0（本筋だが擁護側）

例3:「サナエトークンの補償問題、結局泣き寝入りか」
→ stance_accountability: 0.0, stance_focus: -2.0（サナエトークンが主題）

例4:「玉木は不倫で説明責任、高市は中傷動画で説明責任。結局どっちもどっち」
→ stance_accountability: +1.0, stance_focus: -0.5（比較論点）

例5:「松井健が影響工作を認めてるのに、高市が知らなかったはずがない」
→ stance_accountability: +2.0, stance_focus: +2.0（本筋の責任追及）

【投稿】
{text}

【出力形式】JSONのみ出力:
{{"is_opinion": true/false, "stance_accountability": 数値, "stance_focus": 数値, "emotional_intensity": 数値, "confidence": 0.0〜1.0, "summary": "20字以内"}}"""


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


def dedup(data: list) -> list:
    seen = set()
    result = []
    for item in data:
        text = item.get("text", "").strip()
        if text in seen:
            continue
        seen.add(text)
        result.append(item)
    return result


def print_summary(results: list):
    acc_labels = {-2: "強く擁護", -1: "やや擁護", 0: "中立", 1: "やや追及", 2: "強く追及"}
    focus_labels = {-2: "派生・トークン", -1: "やや派生寄り", 0: "混合", 1: "やや本筋寄り", 2: "本筋・中傷動画"}

    acc_counts = {k: 0 for k in acc_labels}
    focus_counts = {k: 0 for k in focus_labels}
    for r in results:
        ax = round(r.get("stance_accountability", 0))
        ax = max(-2, min(2, ax))
        acc_counts[ax] += 1
        fx = round(r.get("stance_focus", 0))
        fx = max(-2, min(2, fx))
        focus_counts[fx] += 1

    print("\n=== stance_accountability 分布 ===")
    for k in sorted(acc_labels.keys()):
        bar = "█" * acc_counts[k]
        print(f"  {acc_labels[k]:>10} ({k:+d}): {acc_counts[k]:>3}  {bar}")

    print("\n=== stance_focus 分布 ===")
    for k in sorted(focus_labels.keys()):
        bar = "█" * focus_counts[k]
        print(f"  {focus_labels[k]:>12} ({k:+d}): {focus_counts[k]:>3}  {bar}")

    total = len(results)
    opinions = sum(1 for r in results if r.get("is_opinion"))
    print(f"\n合計: {total}件  意見: {opinions}件  非意見: {total - opinions}件")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="20件だけテスト")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: OPENCODEGO_API_KEY が .env にありません", file=sys.stderr)
        sys.exit(1)

    raw = json.loads(INPUT_FILE.read_text())
    data = dedup(raw)
    print(f"入力: {len(raw)}件 → 重複除去後: {len(data)}件")

    if args.test:
        data = data[:20]
        print(f"テストモード: {len(data)}件のみ処理")

    results = []
    errors = 0

    for i, item in enumerate(data):
        text = item.get("text", "").strip()
        if not text:
            continue
        print(f"  [{i+1}/{len(data)}] {text[:60]}...", flush=True)

        result = classify_one(text)
        if result is None:
            errors += 1
            continue

        result["text"] = text
        result["tweet_id"] = item.get("tweet_id", "")
        result["url"] = item.get("url", "")
        results.append(result)

    OUTPUT_FILE.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\n保存: {OUTPUT_FILE}")
    print(f"成功: {len(results)}件  エラー: {errors}件  エラー率: {errors/(len(results)+errors)*100:.1f}%")
    print_summary(results)


if __name__ == "__main__":
    main()
