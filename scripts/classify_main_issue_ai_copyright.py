#!/usr/bin/env python3
"""
生成AIと著作権テーマの主論点（main_issue）分類（OpenCode Go API版）

ai-copyright_2d_classified.json の意見投稿に main_issue フィールドを追加する。
論点アリーナ（極座標マップ）のセクター割り当てに使う。

データ構造に注意:
  v1レコード: original_category あり、is_opinion なし（309件が意見）
  v2レコード: is_opinion=True、original_category なし（369件）

使い方:
  python3 scripts/classify_main_issue_ai_copyright.py --test   # 20件テスト
  python3 scripts/classify_main_issue_ai_copyright.py          # 全量

main_issue の値:
  学習データ・無断利用 / クリエイター保護・権利 / 法制度・規制整備 /
  技術競争・推進 / 利用者モラル・倫理 / AI生成物の権利・創作性 / その他
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
INPUT_FILE = PROJECT_ROOT / "social-samples" / "ai-copyright_2d_classified.json"
OUTPUT_FILE = PROJECT_ROOT / "social-samples" / "ai-copyright_2d_classified.json"

V1_SKIP_CATEGORIES = {"その他・分類保留", "情報共有・ニュース言及"}

VALID_ISSUES = [
    "学習データ・無断利用",
    "クリエイター保護・権利",
    "法制度・規制整備",
    "技術競争・推進",
    "利用者モラル・倫理",
    "AI生成物の権利・創作性",
    "その他",
]

SYSTEM_PROMPT = """あなたはSNS投稿を分類する専門家です。
必ずJSONのみを出力してください。説明・前置き・コードブロックは不要です。"""

USER_PROMPT_TEMPLATE = """以下のSNS投稿が、生成AIと著作権問題についてどの論点を主に論じているか1つだけ選んでください。

【背景】
文化庁が「AI学習は著作権侵害にならない」との見解を示す一方、イラストレーターや漫画家が自作品の無断学習に反発。
企業のAI活用推進と創作者保護の狭間で、法整備・モラル・競争力をめぐる議論が続いている。

【論点の定義】
- 学習データ・無断利用: AI学習に著作物を無断利用することの合法性・是非（「パクリ」「漫画村と同じ」など学習行為そのものへの賛否）を主に論じている
- クリエイター保護・権利: イラストレーター・漫画家・表現者の生計・権利・尊厳への影響（「クリエイターが廃業」「絵師を守れ」等）を主に論じている
- 法制度・規制整備: ライセンス制度・許諾要件・規制立法・政府の対応（「法律で規制を」「ルール整備が必要」等）を主に論じている
- 技術競争・推進: 過剰規制による国際競争力の低下・技術進歩の阻害・産業育成（「規制したら日本が遅れる」「イノベーション」等）を主に論じている
- 利用者モラル・倫理: AI利用者のクレジット表記・配慮・個人の使い方と倫理（「AI生成と隠して使う」「クレジットくらい書け」等）を主に論じている
- AI生成物の権利・創作性: AI出力に著作権が発生するか・創作性の定義・二次創作との整合性（「AI生成に著作権はない」「創作性を認めるべきか」等）を主に論じている
- その他: 上記のどれにも当てはまらない

【判定ルール】
- 複数の論点に触れている場合は、投稿の中心的な主張がどれかで判定する
- 「賛成/反対」の表明だけで根拠が読み取れない場合は「その他」
- 感情的な投稿でも根拠が学習データなら「学習データ・無断利用」、クリエイターの生計なら「クリエイター保護・権利」
- 「漫画村と同じ」「無断学習」「盗用」は学習行為への批判 → 「学習データ・無断利用」
- 「絵師が廃業」「クリエイターの仕事が奪われる」は職業・生計への影響 → 「クリエイター保護・権利」

【判定例】
例1:「AI学習は漫画村と同じ無断利用。著作権的に合法なわけがない」→ 学習データ・無断利用
例2:「イラストレーターが次々と廃業している。クリエイターを守る仕組みが必要」→ クリエイター保護・権利
例3:「政府はライセンス制度を整備して許諾なしの学習を禁止すべき」→ 法制度・規制整備
例4:「規制を強化したら中国やアメリカに負ける。日本だけ遅れてどうする」→ 技術競争・推進
例5:「AI生成と隠してSNSに上げる人が一番問題。クレジット表記くらいしろ」→ 利用者モラル・倫理
例6:「プロンプト入力だけで著作権が発生するのはおかしい。創作性の定義を見直すべき」→ AI生成物の権利・創作性

【投稿】
{text}

【出力形式】JSONのみ出力:
{{"main_issue": "論点名", "confidence": 0.0〜1.0}}"""


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
                "max_tokens": 1000,
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
        result = json.loads(content[start:end])
        if result.get("main_issue") not in VALID_ISSUES:
            print(f"    WARN: 不正な論点名 {result.get('main_issue')!r} → その他", flush=True)
            result["main_issue"] = "その他"
        return result
    except Exception as e:
        print(f"    ERROR: {type(e).__name__}: {e}", flush=True)
        return None


def is_target(record: dict) -> bool:
    if record.get("main_issue"):
        return False
    # v2レコード: is_opinion=True があればすべて対象
    if record.get("is_opinion") is True:
        return True
    # v1レコード: original_category が意見カテゴリなら対象
    cat = record.get("original_category")
    if cat is not None and cat not in V1_SKIP_CATEGORIES:
        return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="20件だけテスト")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: OPENCODEGO_API_KEY が .env にありません", file=sys.stderr)
        sys.exit(1)

    data = json.loads(INPUT_FILE.read_text())
    targets = [x for x in data if is_target(x)]
    print(f"全{len(data)}件中、main_issue対象 {len(targets)}件を処理")

    if args.test:
        targets = targets[:20]
        print(f"テストモード: {len(targets)}件のみ処理")

    errors = 0
    done = 0
    for i, item in enumerate(targets):
        text = item.get("text", "").strip()
        if not text:
            text = item.get("summary", "").strip()
        print(f"  [{i+1}/{len(targets)}] {text[:60]}...", flush=True)
        result = classify_one(text)
        if result is None:
            errors += 1
            continue
        item["main_issue"] = result["main_issue"]
        item["main_issue_confidence"] = result.get("confidence", 0.0)
        done += 1

    OUTPUT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"\n保存: {OUTPUT_FILE}")
    total = done + errors
    if total:
        print(f"成功: {done}件  エラー: {errors}件  エラー率: {errors/total*100:.1f}%")

    from collections import Counter
    dist = Counter(x.get("main_issue") for x in data if x.get("main_issue"))
    print("\n=== main_issue 分布 ===")
    for k in VALID_ISSUES:
        bar = "█" * dist.get(k, 0)
        print(f"  {k:>20}: {dist.get(k, 0):>3}  {bar}")


if __name__ == "__main__":
    main()
