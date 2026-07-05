#!/usr/bin/env python3
"""
辺野古高校生死亡事故の2次元スコア分類（OpenCode Go API版）

使い方:
  python3 scripts/classify_2d_henoko.py --test   # 20件テスト
  python3 scripts/classify_2d_henoko.py          # 全量

X軸 stance_mext:  -2(文科省判断に強く反発) 〜 +2(文科省判断を強く支持)
Y軸 stance_focus: -2(事故・安全・追悼が中心) 〜 +2(政治・制度・思想問題が中心)
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
INPUT_FILE = PROJECT_ROOT / "social-samples" / "henoko" / "henoko_structured_redesign_403.json"
OUTPUT_FILE = PROJECT_ROOT / "social-samples" / "henoko_student_accident_2d_classified.json"

SYSTEM_PROMPT = """あなたはSNS投稿を分類する専門家です。
必ずJSONのみを出力してください。説明・前置き・コードブロックは不要です。"""

USER_PROMPT_TEMPLATE = """以下のSNS投稿を分析してください。スコアは0.5刻みで指定してください。

【背景】
2024年に沖縄・辺野古沖でカヌー体験学習中の高校生が死亡する事故が発生。文部科学省はこの学校行事を「教育基本法違反（政治的中立性の逸脱）」と認定しました。この事故と文科省判断をめぐり、SNS上で様々な反応が生まれています。

【まず判定】
is_opinion: この投稿が辺野古高校生死亡事故・関連する教育政策問題に関する意見・感想・主張かどうか
  true  = 事故への追悼、安全管理批判、文科省判断への賛否、政治利用批判、平和教育論など
  false = 広告・スパム・完全に無関係な投稿

is_opinionがfalseの場合、スコアはすべて0.0、summaryに理由を記載してください。

【2軸の定義（is_opinion=trueの場合のみ）】

stance_mext（学校の行為と文科省判断への態度）: -2.0〜+2.0 の0.5刻み
  【重要な判定基準】
  - 「学校が政治的中立性を欠いている」「抗議活動に参加させるべきでない」→ プラス側（文科省判断を支持）
  - 「平和教育は正当」「文科省の介入が教育を萎縮させる」→ マイナス側（文科省判断に反発）
  - 学校や反基地活動を批判している投稿 → プラス側（文科省判断と同方向）

  +2.0 = 学校の行為は政治活動への加担。文科省の教育基本法違反認定は当然・正しい
  +1.0 = 学校の対応に疑問あり。政治的中立性への懸念がある
   0.0 = 文科省判断に言及なし・追悼や安全管理のみ・どちらでもない
  -1.0 = 平和教育の萎縮を懸念。文科省判断にやや疑問
  -2.0 = 文科省判断に強く反発。平和教育・反基地活動の自由を擁護

stance_focus（関心の焦点）: -2.0〜+2.0 の0.5刻み
  【重要な判定基準】
  - 投稿の主要な関心がどこにあるかを判定する
  - 「教育基本法違反」「政治的中立性」「イデオロギー」について論じている → プラス側
  - 「高校生が亡くなった」「安全管理」「ご冥福」が主題 → マイナス側
  - 事故に言及しつつも主に政策・制度を論じている場合は、主題に基づいてプラス側に寄せる

  +2.0 = 政治・制度・思想問題が中心。基地問題・教育の政治的中立性・イデオロギー論争
  +1.0 = やや政治・制度寄り。政治的背景に関心
   0.0 = 不明・混合・どちらでもない
  -1.0 = やや事故・安全寄り。引率責任や再発防止への関心
  -2.0 = 事故・安全・追悼が中心。亡くなった生徒への哀悼や安全管理批判

emotional_intensity（感情強度）: -2.0〜+2.0 の0.5刻み
  +2.0 = 強い怒り・激しい批判
  +1.0 = やや感情的・熱量がある
   0.0 = 冷静・中立的
  -1.0 = 皮肉・冷笑
  -2.0 = 悲しみ・やるせなさ

【判定例】

例1:「学校が抗議船に乗せるなんて政治活動の加担だ。文科省の判断は当然」
→ stance_mext: +2.0, stance_focus: +2.0（政治的中立性の議論が中心）

例2:「平和教育を萎縮させるな。文科省の介入は教育への圧力だ」
→ stance_mext: -2.0, stance_focus: +1.5（教育政策・制度の議論が中心）

例3:「高校生が亡くなったのに政治の話ばかり。安全管理はどうなっていたのか」
→ stance_mext: 0.0, stance_focus: -2.0（事故・安全が中心）

例4:「左派は同志社の非をまず認めろ」
→ stance_mext: +1.5, stance_focus: +1.5（政治的立場の議論）

例5:「教育基本法違反の認定に抗議声明。平和教育の萎縮が心配」
→ stance_mext: -1.5, stance_focus: +1.0（政策・制度の議論が主）

【投稿】
{text}

【出力形式】JSONのみ出力:
{{"is_opinion": true/false, "stance_mext": 数値, "stance_focus": 数値, "emotional_intensity": 数値, "confidence": 0.0〜1.0, "summary": "20字以内"}}"""


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
    mext_labels = {-2: "文科省強反発", -1: "やや反発", 0: "中立", 1: "やや支持", 2: "文科省強支持"}
    focus_labels = {-2: "事故・追悼中心", -1: "やや事故寄り", 0: "混合", 1: "やや政治寄り", 2: "政治・制度中心"}

    mext_counts = {k: 0 for k in mext_labels}
    focus_counts = {k: 0 for k in focus_labels}
    for r in results:
        mx = round(r.get("stance_mext", 0))
        mx = max(-2, min(2, mx))
        mext_counts[mx] += 1
        fx = round(r.get("stance_focus", 0))
        fx = max(-2, min(2, fx))
        focus_counts[fx] += 1

    print("\n--- stance_mext (文科省判断) ---")
    for k in sorted(mext_labels):
        v = mext_counts[k]
        print(f"  {k:+d} {mext_labels[k]:14s}: {'█'*v} ({v})")

    print("\n--- stance_focus (関心の焦点) ---")
    for k in sorted(focus_labels):
        v = focus_counts[k]
        print(f"  {k:+d} {focus_labels[k]:14s}: {'█'*v} ({v})")

    print("\n--- 象限分布 ---")
    q = {
        "文科省支持×政治中心": 0,
        "文科省反発×政治中心": 0,
        "文科省支持×事故中心": 0,
        "文科省反発×事故中心": 0,
        "中立含む": 0,
    }
    for r in results:
        mx = r.get("stance_mext", 0)
        fx = r.get("stance_focus", 0)
        if mx == 0 or fx == 0:
            q["中立含む"] += 1
        elif mx > 0 and fx > 0:
            q["文科省支持×政治中心"] += 1
        elif mx < 0 and fx > 0:
            q["文科省反発×政治中心"] += 1
        elif mx > 0 and fx < 0:
            q["文科省支持×事故中心"] += 1
        else:
            q["文科省反発×事故中心"] += 1
    for k, v in q.items():
        print(f"  {k}: {v}件")


def main():
    parser = argparse.ArgumentParser(description="henoko 2D分類 (OpenCode Go)")
    parser.add_argument("--test", action="store_true", help="テストモード（20件のみ）")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: OPENCODEGO_API_KEY が設定されていません")
        sys.exit(1)

    with open(INPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    data = dedup(data)
    print(f"重複除去後: {len(data)}件", flush=True)

    if args.test:
        data = data[:20]

    print(f"Classifying {len(data)} posts via OpenCode Go ({MODEL})...", flush=True)

    results = []
    errors = 0
    for i, post in enumerate(data):
        text = post.get("text", "")
        if not text.strip():
            errors += 1
            continue

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
            **result,
        })

        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(data)} done (valid: {len(results)}, errors: {errors})", flush=True)

    out_path = OUTPUT_FILE if not args.test else OUTPUT_FILE.with_suffix(".test.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Saved to {out_path}")
    print(f"Valid: {len(results)}, Errors/Non-opinion: {errors}/{len(data)} ({errors/len(data)*100:.0f}%)")
    print_summary(results)


if __name__ == "__main__":
    main()
