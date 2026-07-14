#!/usr/bin/env python3
"""
副首都法案・副首都構想の2次元スコア分類（OpenCode Go API版）

使い方:
  python3 scripts/classify_2d_fukushuto.py --test   # 20件テスト
  python3 scripts/classify_2d_fukushuto.py          # 全量

X軸 stance_law:      -2(法案反対・慎重) 〜 +2(法案賛成・推進)
Y軸 stance_location: -2(大阪指定に反対・別候補地) 〜 +2(大阪指定を評価・支持)
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
INPUT_FILE = PROJECT_ROOT / "social-samples" / "fukushuto_samples.json"
OUTPUT_FILE = PROJECT_ROOT / "social-samples" / "fukushuto_2d_classified.json"

SYSTEM_PROMPT = """あなたはSNS投稿を分類する専門家です。
必ずJSONのみを出力してください。説明・前置き・コードブロックは不要です。"""

USER_PROMPT_TEMPLATE = """以下のSNS投稿を分析してください。スコアは0.5刻みで指定してください。

【背景】
2026年7月、与党（自民党・公明党）・日本維新の会・チームみらいの修正合意により、副首都法案が衆院通過目前となった。
この法案は、首都（東京）の機能が大規模災害等で損なわれた場合に備え、バックアップ機能を担う「副首都」を政令で指定できるようにするもの。
大阪を軸に検討が進んでいるが、「大阪ありき」との批判や、副首都の定義・費用・場所など制度設計の不透明さへの疑問も多い。

【まず判定】
is_opinion: この投稿が副首都法案・副首都構想に関する意見・感想・主張かどうか
  true  = 法案への賛否、候補地への意見、制度への疑問・評価、費用・防災効果への見解など
  false = 広告・スパム・完全に無関係な投稿、単純なニュース転載（コメントなし）

is_opinionがfalseの場合、スコアはすべて0.0、summaryに理由を記載してください。

【2軸の定義（is_opinion=trueの場合のみ）】

stance_law（副首都法案への態度）: -2.0〜+2.0 の0.5刻み
  【重要な判定基準】
  - 「防災・首都機能バックアップに必要」「多極成長のために推進」→ プラス側（賛成・推進）
  - 「消費税より優先度が低い」「生煮え・定義が曖昧」「兆円単位の税金の無駄」→ マイナス側（反対・慎重）
  - 「制度設計の詳細が決まっていないのに法案通過はおかしい」も反対寄り

  +2.0 = 副首都法案を強く支持。防災・成長の観点から必要不可欠
  +1.0 = 概ね賛成。懸念はあるが方向性は正しい
   0.0 = 中立・制度への疑問のみ・どちらとも言えない
  -1.0 = 慎重派。今すぐでなくてよい・詳細が不透明
  -2.0 = 強く反対。税金の無駄・優先順位が間違っている・大阪ありきは不当

stance_location（大阪を副首都候補地とすることへの態度）: -2.0〜+2.0 の0.5刻み
  【重要な判定基準】
  - 「大阪・関西に維新の悲願」「大阪が最適」→ プラス側（大阪指定を評価）
  - 「大阪は東京に近すぎる」「南海トラフで共倒れ」「福岡・札幌・新潟の方がよい」→ マイナス側（大阪以外を推奨）
  - 候補地に言及しない投稿は 0.0

  +2.0 = 大阪を副首都に強く支持。インフラ・経済規模・維新の推進力を評価
  +1.0 = 大阪でおおむね良い
   0.0 = 候補地に言及なし・どちらとも言えない
  -1.0 = 大阪より他の地域が適している（やや反対）
  -2.0 = 大阪は絶対にダメ。南海トラフリスク・東京との距離が致命的

emotional_intensity（感情強度）: -2.0〜+2.0 の0.5刻み
  +2.0 = 強い怒り・激しい批判
  +1.0 = やや感情的・熱量がある
   0.0 = 冷静・中立的
  -1.0 = 皮肉・冷笑
  -2.0 = 呆れ・失望

【判定例】

例1:「首都直下地震や南海トラフに備えて首都機能を分散するのは当然。維新の主張通り大阪を副首都にして多極成長型の国家を作るべき。」
→ stance_law: +2.0, stance_location: +2.0（法案も大阪も強く支持）

例2:「消費税減税は先送りなのに副首都法案は強行。物価高に苦しむ国民より先にやることか。」
→ stance_law: -1.5, stance_location: 0.0（優先順位批判・場所への言及なし）

例3:「大阪は東京に近すぎる。南海トラフで共倒れになる。副首都なら札幌か福岡の方がいい。」
→ stance_law: 0.0, stance_location: -2.0（法案自体は否定せず、大阪選定に強く反対）

例4:「副首都って何？法案を読んでも定義が書いていない。首都の法的定義もないのに副首都を先に決めるのは矛盾では？」
→ stance_law: -1.0, stance_location: 0.0（制度設計への疑問→やや慎重）

例5:「副首都法案にチームみらいが賛成。これで衆院通過が確実に。大阪から日本の成長を。」
→ stance_law: +1.5, stance_location: +1.5（推進派・大阪支持）

【投稿】
{text}

【出力形式】JSONのみ出力:
{{"is_opinion": true/false, "stance_law": 数値, "stance_location": 数値, "emotional_intensity": 数値, "confidence": 0.0〜1.0, "summary": "20字以内"}}"""


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
    law_labels = {-2: "強く反対", -1: "慎重", 0: "中立", 1: "概ね賛成", 2: "強く賛成"}
    loc_labels = {-2: "大阪は絶対ダメ", -1: "他候補地推奨", 0: "言及なし", 1: "大阪で概ねOK", 2: "大阪を強く支持"}

    from collections import Counter
    law_counts = Counter(max(-2, min(2, round(r.get("stance_law", 0)))) for r in results)
    loc_counts = Counter(max(-2, min(2, round(r.get("stance_location", 0)))) for r in results)

    print("\n=== stance_law（法案への態度）分布 ===")
    for k in sorted(law_labels.keys()):
        bar = "█" * law_counts.get(k, 0)
        print(f"  {law_labels[k]:>12} ({k:+d}): {law_counts.get(k,0):>3}  {bar}")

    print("\n=== stance_location（大阪指定への態度）分布 ===")
    for k in sorted(loc_labels.keys()):
        bar = "█" * loc_counts.get(k, 0)
        print(f"  {loc_labels[k]:>14} ({k:+d}): {loc_counts.get(k,0):>3}  {bar}")

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
    total_processed = len(results) + errors
    if total_processed > 0:
        print(f"成功: {len(results)}件  エラー: {errors}件  エラー率: {errors/total_processed*100:.1f}%")
    print_summary(results)


if __name__ == "__main__":
    main()
