#!/usr/bin/env python3
"""
副首都テーマの主論点（main_issue）分類（OpenCode Go API版）

fukushuto_2d_classified.json の is_opinion=true 投稿に main_issue フィールドを
追加する。論点アリーナ（極座標マップ）のセクター割り当てに使う。

使い方:
  python3 scripts/classify_main_issue_fukushuto.py --test   # 20件テスト
  python3 scripts/classify_main_issue_fukushuto.py          # 全量

main_issue の値:
  防災・災害 / 候補地 / 費用・財源 / 都構想・維新 / 定義・中身 / 優先順位 / その他
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
INPUT_FILE = PROJECT_ROOT / "social-samples" / "fukushuto_2d_classified.json"
OUTPUT_FILE = PROJECT_ROOT / "social-samples" / "fukushuto_2d_classified.json"

VALID_ISSUES = ["防災・災害", "候補地", "費用・財源", "都構想・維新", "定義・中身", "優先順位", "その他"]

SYSTEM_PROMPT = """あなたはSNS投稿を分類する専門家です。
必ずJSONのみを出力してください。説明・前置き・コードブロックは不要です。"""

USER_PROMPT_TEMPLATE = """以下のSNS投稿が、副首都法案のどの論点を主に論じているか1つだけ選んでください。

【背景】
2026年7月、与党・維新・チームみらいの修正合意により副首都法案が衆院通過目前。
首都機能のバックアップ都市を政令指定できるようにする法案で、大阪を軸に検討が進む。

【論点の定義】
- 防災・災害: 首都直下・南海トラフ・津波・戦争リスク・バックアップ機能・一極集中の是正など、災害対応や防災効果を主に論じている
- 候補地: 大阪・福岡・札幌・新潟・名古屋・京都・日本海側など「どこが副首都になるべきか」を主に論じている
- 費用・財源: 兆円単位の整備費・税金の使い方・財源・住民税・コストを主に論じている
- 都構想・維新: 大阪都構想との関係・「都」への名称変更・維新の利権や政治的動機・「大阪ありき」批判を主に論じている
- 定義・中身: 副首都の定義がない・法案が生煮え・制度設計が不透明・首都の法的定義がないなど法案の中身や立法手続きを主に論じている
- 優先順位: 物価対策・消費税減税・社会保障が先だろうという「今やることか」批判・国会運営（会期延長など）を主に論じている
- その他: 上記のどれにも当てはまらない

【判定ルール】
- 複数の論点に触れている場合は、投稿の中心的な主張がどれかで判定する
- 政党・政治家への言及があっても、批判の根拠が費用なら「費用・財源」、動機への疑念なら「都構想・維新」
- 「賛成/反対」の表明だけで根拠が読み取れない場合は「その他」

【判定例】
例1:「南海トラフで大阪も被災するのに副首都にする意味がない」→ 防災・災害
例2:「副首都は福岡か札幌がいい。太平洋側はリスクが高い」→ 候補地
例3:「兆円単位の税金を使う話なのに費用の試算すら出ていない」→ 費用・財源
例4:「副首都法案は都構想の隠れ蓑。維新の利権のための法案」→ 都構想・維新
例5:「副首都の定義が法案に書かれていない。生煮えのまま通すな」→ 定義・中身
例6:「物価高対策が先だろ。なんで今副首都なんだ」→ 優先順位

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="20件だけテスト")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: OPENCODEGO_API_KEY が .env にありません", file=sys.stderr)
        sys.exit(1)

    data = json.loads(INPUT_FILE.read_text())
    targets = [x for x in data if x.get("is_opinion") and not x.get("main_issue")]
    print(f"全{len(data)}件中、意見・未分類 {len(targets)}件を処理")

    if args.test:
        targets = targets[:20]
        print(f"テストモード: {len(targets)}件のみ処理")

    errors = 0
    done = 0
    for i, item in enumerate(targets):
        text = item.get("text", "").strip()
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
        print(f"  {k:>8}: {dist.get(k, 0):>3}  {bar}")


if __name__ == "__main__":
    main()
