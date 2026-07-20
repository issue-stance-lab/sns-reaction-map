#!/usr/bin/env python3
"""
部活動の地域移行テーマの主論点（main_issue）分類（OpenCode Go API版）

bukatsu-chiiki_2d_classified.json の is_opinion=true 投稿に main_issue フィールドを
追加する。論点アリーナ（極座標マップ）のセクター割り当てに使う。

使い方:
  python3 scripts/classify_main_issue_bukatsu_chiiki.py --test   # 20件テスト
  python3 scripts/classify_main_issue_bukatsu_chiiki.py          # 全量

main_issue の値:
  費用・家庭負担 / 受け皿・指導者 / 教員の働き方 / 教育的意義・機会 / 地域格差 / 制度・移行プロセス / その他
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
INPUT_FILE = PROJECT_ROOT / "social-samples" / "bukatsu-chiiki_2d_classified.json"
OUTPUT_FILE = PROJECT_ROOT / "social-samples" / "bukatsu-chiiki_2d_classified.json"

VALID_ISSUES = [
    "費用・家庭負担",
    "受け皿・指導者",
    "教員の働き方",
    "教育的意義・機会",
    "地域格差",
    "制度・移行プロセス",
    "その他",
]

SYSTEM_PROMPT = """あなたはSNS投稿を分類する専門家です。
必ずJSONのみを出力してください。説明・前置き・コードブロックは不要です。"""

USER_PROMPT_TEMPLATE = """以下のSNS投稿が、部活動の地域移行についてどの論点を主に論じているか1つだけ選んでください。

【背景】
少子化と教員の長時間労働を背景に、中学校の部活動を学校から地域のスポーツクラブや民間団体へ移す「地域移行」が国の方針として進められている。
まず休日の部活動から段階的に移行を進める計画で、教員の負担軽減と受け皿づくりが狙い。

【論点の定義】
- 費用・家庭負担: 月会費・年間費用・家計への経済的負担・費用格差・補助の有無・低所得家庭への影響を主に論じている
- 受け皿・指導者: 地域にクラブや指導者がいない・指導者の報酬が安い・人材確保の困難・受け入れ体制の整備を主に論じている
- 教員の働き方: 教員の長時間労働・残業・部活動の強制参加・ブラック部活・働き方改革としての地域移行を主に論じている
- 教育的意義・機会: 子どもの夢や成長機会・不登校の子の参加・人間形成・チームワーク・スポーツ文化の継承を主に論じている
- 地域格差: 都市と地方の実施環境差・自治体間の格差・チームが成立しない少子化・地域インフラの差を主に論じている
- 制度・移行プロセス: 国の方針・移行スピードの速さ遅さ・自治体の手探り状態・法制度・行政の対応を主に論じている
- その他: 上記のどれにも当てはまらない

【判定ルール】
- 複数の論点に触れている場合は、投稿の中心的な主張がどれかで判定する
- 「賛成/反対」の表明だけで根拠が読み取れない場合は「その他」
- 感情的な投稿でも根拠が費用なら「費用・家庭負担」、人材なら「受け皿・指導者」

【判定例】
例1:「月8000円×3人=年28万円。家計がヒィヒィ」→ 費用・家庭負担
例2:「報酬が安いから指導者が集まらない。ボランティア頼みは無理」→ 受け皿・指導者
例3:「教員が土日も部活に駆り出されるのはブラック。地域移行は必要」→ 教員の働き方
例4:「地域移行で夢を奪われる子どもがいる。部活は人間形成の場」→ 教育的意義・機会
例5:「都市なら代替クラブがあるが地方では無理。地域差が大きい」→ 地域格差
例6:「国の計画通りに自治体が動けるわけがない。移行スピードが速すぎる」→ 制度・移行プロセス

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
        print(f"  {k:>12}: {dist.get(k, 0):>3}  {bar}")


if __name__ == "__main__":
    main()
