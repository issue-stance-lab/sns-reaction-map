"""副首都法案・副首都構想テーマの論点・立場の唯一の定義。

2026-07-26 に新設した Hermes 分類器が公開ページの論点定義を参照せずに書かれ、
論点の切り口そのものが分岐した（公開側は「定義・中身／候補地／都構想・維新／
防災・災害／費用・財源／優先順位」、分類器は「副首都法案の是非／大阪・関西中心の問題／
首都機能分散の必要性／財政・実現可能性」）。ai-copyright と同じ原因。
公開物（正典255件・論点カード・アリーナ・投票）はすべて公開側の7論点で一貫しているため、
2026-08-07 に分類器を公開側へ合わせた。以後はこのモジュールだけを直し、参照側は必ずここから読む。

公開ページ側の定義（変更するとユーザーの投票が壊れるもの）:

- `docs/fukushuto-reaction-map.html` の `const ISSUES`（アリーナのセクター）
- 同 `var VOTE_ISSUES` / `var V2I` / `var STANCES`（投票の選択肢とセクター対応）
- `supabase/functions/cast-vote/index.ts` の `fukushuto-issue-stance-v1: 21`
- `configs/fukushuto-reaction-map.json` の `issue_counts.cards`

`tests/test_fukushuto_taxonomy.py` がこの4つとの一致を検査する。

2026-08-08 に「世論の潮目」ウィジェット（`datasets.issue`）も移行し、旧論点は全廃した。
7/14・7/26 の Hermes 結果をこの論点で分類し直し、`*_v2.json` として別名保存している
（更新回のファイルは記録なので改変しない）。移行前に「stance 側は旧分類器と同じ3択なので
そのまま連続する」と見込んでいたが、実際には再分類が賛否も判定し直すため、
292件中29件で stance が変わった。以後の移行でも stance の変化は必ず実測して報告する。
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TOPIC_ID = "fukushuto-issue-stance-v1"

# アリーナのセクター順。const ISSUES と同じ並びでなければセクター番号がずれる。
# 「その他」が末尾ではなく5番目にあるのは、公開時に件数降順で並べたため。
ISSUE_ORDER: tuple[str, ...] = (
    "定義・中身",
    "候補地",
    "都構想・維新",
    "防災・災害",
    "その他",
    "費用・財源",
    "優先順位",
)

# 2026-07-26 の分類器が使っていた旧論点。2026-08-08 に潮目ウィジェットを移行して全廃した。
# ページに1つでも残っていれば同一画面での二重表示に戻るため、テストが出現を禁じる。
RETIRED_ISSUE_LABELS: tuple[str, ...] = (
    "副首都法案の是非",
    "大阪・関西中心の問題",
    "首都機能分散の必要性",
    "財政・実現可能性",
)

# 投票の選択肢順。var VOTE_ISSUES と同じ並び。「その他」を最後に置くためアリーナとは順序が違う。
VOTE_ISSUE_ORDER: tuple[str, ...] = (
    "定義・中身",
    "候補地",
    "都構想・維新",
    "防災・災害",
    "費用・財源",
    "優先順位",
    "その他",
)

# 投票の選択肢ラベル。アリーナのセクター名と1対1で対応する（「その他」だけ表記が違う）。
VOTE_ISSUE_LABELS: dict[str, str] = {
    "定義・中身": "定義・中身",
    "候補地": "候補地",
    "都構想・維新": "都構想・維新",
    "防災・災害": "防災・災害",
    "費用・財源": "費用・財源",
    "優先順位": "優先順位",
    "その他": "その他・わからない",
}

# 投票の選択肢番号 → アリーナのセクター番号。ページの var V2I と同じ。
VOTE_ISSUE_TO_ARENA_INDEX: tuple[int, ...] = tuple(
    ISSUE_ORDER.index(name) for name in VOTE_ISSUE_ORDER
)

OTHER = "その他"
ISSUES = set(ISSUE_ORDER)

# 分類の立場。投票の3択と対応する。
NEUTRAL_STANCE = "中立・情報"
STANCE_ORDER: tuple[str, ...] = (
    "法案反対",
    NEUTRAL_STANCE,
    "法案賛成・推進",
)
STANCES = set(STANCE_ORDER)

VOTE_STANCE_LABELS: dict[str, str] = {
    "法案反対": "反対・慎重",
    "中立・情報": "どちらでもない",
    "法案賛成・推進": "賛成・推進",
}

INTENSITIES = {"low", "medium", "high"}
RISKS = {"low", "medium", "high"}

# アリーナの座標。SM_RAW の x / e と同じ意味で、公開分は 2D分類の
# stance_law / emotional_intensity をそのまま写したもの（どちらも -2.0〜2.0）。
# x は負が反対側（赤）、正が賛成側（緑）。ページの colorOf() が ±0.5 を境にするため、
# 立場が中立でない限り絶対値が 0.5 を下回らないようにする。
STANCE_X: dict[str, float] = {
    "法案反対": -1.0,
    "中立・情報": 0.0,
    "法案賛成・推進": 1.0,
}
INTENSITY_X_GAIN: dict[str, float] = {"low": 0.5, "medium": 1.0, "high": 1.5}
# e は半径（冷静=中心 / 感情的=外周）。公開分の最頻値 0.0 / 1.0 / 2.0 に合わせる。
INTENSITY_E: dict[str, float] = {"low": 0.0, "medium": 1.0, "high": 2.0}

# ページの colorOf() が色を切り替える閾値。テストが座標定義との整合を見る。
COLOR_THRESHOLD = 0.5
# SM_RAW が取りうる値域。2D分類の出力範囲と同じ。
COORD_LIMIT = 2.0


def issue_index(main_issue: str) -> int:
    """論点名から、アリーナのセクター番号を返す。"""
    return ISSUE_ORDER.index(main_issue)


def vote_issue_index(main_issue: str) -> int:
    """論点名から、投票の選択肢番号を返す。"""
    return VOTE_ISSUE_ORDER.index(main_issue)


def vote_choice_index(main_issue: str, stance: str) -> int:
    """論点と立場から、Edge Function へ送る choiceIdx を返す。

    ページの `issueIdx*STANCES.length+stanceIdx` と同じ計算。
    """
    return vote_issue_index(main_issue) * len(STANCE_ORDER) + STANCE_ORDER.index(stance)


def arena_x(stance: str, intensity: str) -> float:
    """立場と強度から、アリーナの横軸（-2.0〜2.0）を決める。"""
    direction = STANCE_X.get(stance, 0.0)
    if direction == 0.0:
        return 0.0
    return round(direction * INTENSITY_X_GAIN.get(intensity, 1.0), 2)


def arena_e(intensity: str) -> float:
    """強度から、アリーナの半径（0.0〜2.0）を決める。"""
    return INTENSITY_E.get(intensity, 1.0)


# 論点の説明。プロンプトの論点メニューはここから生成する。
# 文言は正典255件へラベルを付けた scripts/classify_main_issue_fukushuto.py の定義を引き継ぐ。
# 並びは「その他」を最後にした説明順（＝VOTE_ISSUE_ORDER）で、アリーナの並びとは別。
ISSUE_DEFS: tuple[tuple[str, str], ...] = (
    ("定義・中身", "副首都の定義がない・法案が生煮え・制度設計が不透明など、法案の中身や立法手続き"),
    ("候補地", "大阪・福岡・札幌・新潟・名古屋・日本海側など「どこが副首都になるべきか」"),
    ("都構想・維新", "大阪都構想との関係・維新の政治的動機・「大阪ありき」批判"),
    ("防災・災害", "首都直下・南海トラフ・バックアップ機能・一極集中の是正など、災害対応や防災効果"),
    ("費用・財源", "兆円単位の整備費・税金の使い方・財源・コスト"),
    ("優先順位", "物価対策・減税・社会保障が先だという「今やることか」批判、国会運営"),
    ("その他", "上記に当てはまらない、論点不明、無関係"),
)

# 立場の説明。プロンプトの立場メニューはここから生成する。
STANCE_DEFS: tuple[tuple[str, str], ...] = (
    ("法案反対", "副首都法案・副首都構想に否定的・批判的"),
    ("法案賛成・推進", "副首都法案・副首都構想を支持・推進"),
    ("中立・情報", "ニュース・情報共有、または立場が不明"),
)
