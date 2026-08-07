#!/usr/bin/env python3
"""
辺野古高校生死亡事故の2次元スコア分類（Ollama qwen2.5:7b版）

使い方:
  python3 scripts/classify_2d_henoko_ollama.py --test   # 20件テスト
  python3 scripts/classify_2d_henoko_ollama.py          # 全量403件

X軸 stance_mext:  -2(文科省判断に強く反発) 〜 +2(文科省判断を強く支持)
Y軸 stance_focus: -2(事故・安全・追悼が中心) 〜 +2(政治・制度・思想問題が中心)
"""
import json
import sys
import argparse
import urllib.request
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma4:latest"

PROJECT_ROOT = Path(__file__).parent.parent
INPUT_FILE = PROJECT_ROOT / "social-samples" / "henoko" / "henoko_structured_redesign_403.json"
OUTPUT_FILE = PROJECT_ROOT / "social-samples" / "henoko_student_accident_2d_classified.json"

PROMPT_TEMPLATE = """あなたはSNS投稿を分類する専門家です。必ずJSONのみを出力してください。

以下のSNS投稿を分析してください。スコアは0.5刻みで指定してください。

【背景】
2024年に沖縄・辺野古沖でカヌー体験学習中の高校生が死亡する事故が発生。文部科学省はこの学校行事を「教育基本法違反（政治的中立性の逸脱）」と認定しました。この事故と文科省判断をめぐり、SNS上で様々な反応が生まれています。

【まず判定】
is_opinion: この投稿が辺野古高校生死亡事故・関連する教育政策問題に関する意見・感想・主張かどうか
  true  = 事故への追悼、安全管理批判、文科省判断への賛否、政治利用批判、平和教育論など
  false = 広告・スパム・完全に無関係な投稿

is_opinionがfalseの場合、スコアはすべて0.0、summaryに「無関係」と記載。

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
→ stance_mext: +2.0（学校を批判＝文科省判断と同方向＝支持）

例2:「平和教育を萎縮させるな。文科省の介入は教育への圧力だ」
→ stance_mext: -2.0（文科省を批判＝文科省判断に反発）

例3:「高校生が亡くなったのに政治の話ばかり。安全管理はどうなっていたのか」
→ stance_mext: 0.0（文科省判断に言及なし）, stance_focus: -2.0（事故・安全中心）

例4:「左派は同志社の非をまず認めろ」
→ stance_mext: +1.5（学校・左派を批判＝文科省判断と同方向）

【投稿】
{text}

必ず以下の形式のJSONのみを出力してください:
{{"is_opinion": true, "stance_mext": 0.0, "stance_focus": 0.0, "emotional_intensity": 0.0, "confidence": 0.8, "summary": "20字以内"}}"""


def call_ollama(prompt: str, timeout: int = 60) -> str:
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1, "num_predict": 300},
    }).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("response", "")


def classify_one(text: str) -> dict | None:
    prompt = PROMPT_TEMPLATE.format(text=text[:400])
    try:
        raw = call_ollama(prompt)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == 0:
            print(f"    ERROR: JSONが見つからない: {repr(raw[:80])}", flush=True)
            return None
        return json.loads(raw[start:end])
    except Exception as e:
        print(f"    ERROR: {type(e).__name__}: {e}", flush=True)
        return None


def print_summary(results: list):
    mext_labels = {-2: "文科省強反発", -1: "やや反発", 0: "中立/言及なし", 1: "やや支持", 2: "文科省強支持"}
    focus_labels = {-2: "事故・追悼中心", -1: "やや事故寄り", 0: "混合", 1: "やや政治寄り", 2: "政治・制度中心"}

    mext_counts = {k: 0 for k in mext_labels}
    focus_counts = {k: 0 for k in focus_labels}
    opinion_count = 0
    non_opinion_count = 0
    total_conf = 0.0

    for r in results:
        c = r.get("classification_2d", {})
        if not c.get("is_opinion", True):
            non_opinion_count += 1
            continue
        opinion_count += 1
        total_conf += c.get("confidence", 0)
        mx = round(c.get("stance_mext", 0))
        mx = max(-2, min(2, mx))
        mext_counts[mx] = mext_counts.get(mx, 0) + 1
        fx = round(c.get("stance_focus", 0))
        fx = max(-2, min(2, fx))
        focus_counts[fx] = focus_counts.get(fx, 0) + 1

    print("\n=== 2D分類結果サマリ ===")
    print(f"  意見あり: {opinion_count}件  非意見: {non_opinion_count}件")
    if opinion_count:
        print(f"  平均confidence: {total_conf / opinion_count:.2f}")
    print("\n  文科省判断への態度:")
    for k in sorted(mext_labels):
        print(f"    {mext_labels[k]:>14}: {mext_counts.get(k, 0):>4}件")
    print("\n  関心の焦点:")
    for k in sorted(focus_labels):
        print(f"    {focus_labels[k]:>14}: {focus_counts.get(k, 0):>4}件")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="20件テスト")
    args = parser.parse_args()

    with open(INPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    if args.test:
        data = data[:20]

    total = len(data)
    print(f"[henoko 2D] 分類開始: {total}件", flush=True)

    results = []
    errors = 0
    for i, item in enumerate(data):
        text = item.get("text", "")
        if not text.strip():
            errors += 1
            item["classification_2d"] = {"is_opinion": False, "stance_mext": 0, "stance_focus": 0, "emotional_intensity": 0, "confidence": 0, "summary": "空テキスト"}
            results.append(item)
            continue

        print(f"  [{i+1}/{total}] {text[:50]}...", flush=True)
        c2d = classify_one(text)
        if c2d is None:
            errors += 1
            item["classification_2d"] = {"is_opinion": False, "stance_mext": 0, "stance_focus": 0, "emotional_intensity": 0, "confidence": 0, "summary": "分類エラー"}
        else:
            item["classification_2d"] = c2d
        results.append(item)

    out_path = OUTPUT_FILE if not args.test else OUTPUT_FILE.with_name(OUTPUT_FILE.stem + ".test.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n[henoko 2D] 完了: {total}件 (エラー: {errors}件)")
    print(f"  出力: {out_path}")
    print_summary(results)


if __name__ == "__main__":
    main()
