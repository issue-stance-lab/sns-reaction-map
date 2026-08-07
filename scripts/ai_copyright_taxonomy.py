"""生成AIと著作権テーマの論点・立場の唯一の定義。

分類器・ページ生成・投票の3つが別々に論点を持っていたため、2026-07-26 に新設した
分類器だけが独自の6論点になり、公開ページ（7論点）と食い違ったまま気づけなかった。
以後はこのモジュールだけを直し、参照側は必ずここから読む。

公開ページ側の定義（変更するとユーザーの投票が壊れるもの）:

- `docs/ai-copyright-reaction-map.html` の `const ISSUES`（アリーナのセクター）
- 同 `var VOTE_ISSUES` / `var STANCES`（投票の選択肢）
- `supabase/functions/cast-vote/index.ts` の `ai-copyright-issue-stance-v1: 21`
- `configs/ai-copyright-reaction-map.json` の `issue_counts.cards`

`tests/test_ai_copyright_taxonomy.py` がこの4つとの一致を検査する。
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TOPIC_ID = "ai-copyright-issue-stance-v1"

# アリーナのセクター順。const ISSUES と同じ並びでなければセクター番号がずれる。
ISSUE_ORDER: tuple[str, ...] = (
    "学習データ・無断利用",
    "クリエイター保護・権利",
    "法制度・規制整備",
    "技術競争・推進",
    "利用者モラル・倫理",
    "AI生成物の権利・創作性",
    "その他",
)

# アリーナのセクターに出す表示名。データ側のラベルと文言が違う箇所がある
# （データ「技術競争・推進」／表示「技術競争・AI推進」）ので、対応をここで持つ。
ARENA_LABELS: dict[str, str] = {
    "学習データ・無断利用": "学習データ・無断利用",
    "クリエイター保護・権利": "クリエイター保護・権利",
    "法制度・規制整備": "法制度・規制整備",
    "技術競争・推進": "技術競争・AI推進",
    "利用者モラル・倫理": "利用者モラル・倫理",
    "AI生成物の権利・創作性": "AI生成物の権利・創作性",
    "その他": "その他",
}

# 投票の選択肢ラベル。アリーナのセクター名と1対1で対応する（「その他」だけ表記が違う）。
VOTE_ISSUE_LABELS: dict[str, str] = {
    "学習データ・無断利用": "学習データ・無断利用",
    "法制度・規制整備": "法制度・規制整備",
    "利用者モラル・倫理": "利用者モラル・倫理",
    "クリエイター保護・権利": "クリエイター保護・権利",
    "技術競争・推進": "技術競争・AI推進",
    "AI生成物の権利・創作性": "AI生成物の権利・創作性",
    "その他": "その他・わからない",
}

OTHER = "その他"
ISSUES = set(ISSUE_ORDER)

# 分類の立場。投票の3択と対応する。
STANCE_ORDER: tuple[str, ...] = (
    "規制・制限強化支持",
    "中立・情報",
    "推進・活用支持",
)
STANCES = set(STANCE_ORDER)

VOTE_STANCE_LABELS: dict[str, str] = {
    "規制・制限強化支持": "規制賛成・著作権保護",
    "中立・情報": "どちらでもない",
    "推進・活用支持": "AI活用推進・規制反対",
}

INTENSITIES = {"low", "medium", "high"}
RISKS = {"low", "medium", "high"}

# アリーナの座標。x は 2026-07-22 生成分と同じ意味（正が規制側・赤、負が推進側・青）。
# 旧データは 2D分類の stance_regulation をそのまま x にしていたので、その範囲へ写す。
STANCE_X: dict[str, float] = {
    "規制・制限強化支持": 1.0,
    "中立・情報": 0.0,
    "推進・活用支持": -1.0,
}
INTENSITY_X_GAIN: dict[str, float] = {"low": 0.5, "medium": 1.0, "high": 1.5}
INTENSITY_E: dict[str, float] = {"low": 1.0, "medium": 2.0, "high": 3.0}


def issue_index(main_issue: str) -> int:
    return ISSUE_ORDER.index(main_issue)


def arena_x(stance: str, intensity: str) -> float:
    """立場と強度から、アリーナの横軸（-2.0〜2.0）を決める。"""
    direction = STANCE_X.get(stance, 0.0)
    if direction == 0.0:
        return 0.0
    return round(direction * INTENSITY_X_GAIN.get(intensity, 1.0), 2)


def arena_e(intensity: str) -> float:
    """強度から、アリーナの半径（0.0〜3.5）を決める。"""
    return INTENSITY_E.get(intensity, 1.0)


ISSUE_DEFS: tuple[tuple[str, str], ...] = (
    ("学習データ・無断利用", "著作物を無断でAIに学習させること自体への賛否・問題意識"),
    ("クリエイター保護・権利", "イラストレーター・作家・音楽家などクリエイターの権利・生計保護"),
    ("法制度・規制整備", "著作権法改正・ガイドライン・規制立法・国際条約"),
    ("技術競争・推進", "日本の技術力・産業競争力・規制による開発停滞への懸念"),
    ("利用者モラル・倫理", "AIの使い方のモラル・倫理・表示義務・二次利用の是非"),
    ("AI生成物の権利・創作性", "AIが生成したものに著作権・創作性を認めるか"),
    ("その他", "上記に当てはまらない、論点不明、無関係"),
)

# ページの見出しで使う短い名前（insight カード用）。
SHORT_ISSUE_LABELS: dict[str, str] = {
    "学習データ・無断利用": "無断学習",
    "クリエイター保護・権利": "権利保護",
    "法制度・規制整備": "法制度",
    "技術競争・推進": "技術競争",
    "利用者モラル・倫理": "モラル",
    "AI生成物の権利・創作性": "生成物の権利",
    "その他": "その他",
}

SHORT_STANCE_LABELS: dict[str, str] = {
    "規制・制限強化支持": "規制支持",
    "推進・活用支持": "規制反対",
    "中立・情報": "中立",
}

STANCE_NOTES: dict[str, str] = {
    "規制・制限強化支持": "無断学習への反発とクリエイター保護を重視",
    "推進・活用支持": "AIの自由利用や技術革新を重視",
    "中立・情報": "ニュース共有や事実の確認が中心",
}
