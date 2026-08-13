#!/usr/bin/env python3
"""X（旧Twitter）投稿の埋め込みHTMLを作る。

埋め込みは長らくこの形で出力されていた（2026-08-12 に公開ページで142件）。

    <blockquote class="twitter-tweet" ...><a href="https://x.com/…/status/…"></a></blockquote>

リンクの表示文字が空なので、X の widgets.js が読み込めなかった場合、読者にも
クローラーにも「空の箱」しか残らない。誰の投稿かも、元投稿へ辿る手段も無い。
投稿が削除された場合や、通信がブロックされた場合も同じ。

出典と元投稿へのリンクを中に置く。widgets.js が読み込めたときは blockquote ごと
実際の投稿カードへ置き換わるので、通常の読者の見え方は変わらない。

**投稿の要旨をここに入れてはいけない。** 要旨は埋め込みの直前の <p> に既にあり、
中にも入れると同一文が2回並ぶ。同じ文の反復は「質の低いコンテンツ」の兆候として
扱われるため、審査対策として逆効果になる（2026-08-12 に一度入れて戻した）。

投稿本文の全文転載もしない（about.html に明記した「引用の範囲で要旨を紹介し、
元投稿へのリンクを併記」に従う）。
"""

from __future__ import annotations

import html
import re


# https://x.com/<handle>/status/<id> と twitter.com 形式の両方を受ける
_STATUS_URL = re.compile(
    r"^https?://(?:www\.)?(?:x|twitter)\.com/(?P<handle>[^/?#]+)/status/(?P<id>\d+)"
)

BLOCKQUOTE_ATTRS = 'class="twitter-tweet" data-conversation="none" data-dnt="true"'


def handle_from_url(url: str) -> str:
    """投稿URLから @ を除いたハンドル名を返す。取れなければ空文字。"""
    match = _STATUS_URL.match(str(url).strip())
    return match.group("handle") if match else ""


def fallback_link(url: str) -> str:
    """widgets.js が読み込めなかったときに出す出典リンク。"""
    escaped_url = html.escape(str(url).strip(), quote=True)
    handle = handle_from_url(url)
    label = f"@{handle} の投稿をXで見る" if handle else "元の投稿をXで見る"
    return f'<a href="{escaped_url}">{html.escape(label)}</a>'


def embed_html(url: str, *, attrs: str = BLOCKQUOTE_ATTRS) -> str:
    """出典リンク入りの blockquote を返す。"""
    return f"<blockquote {attrs}>{fallback_link(url)}</blockquote>"


# ── 調査条件の表示ラベル ────────────────────────────────────────────────
# THEMES.yaml の sample_period が unknown のとき、ページには長く「記録なし」と
# 出していた。信頼性の表示（代表投稿の確認）のすぐ隣に並ぶため、いちばん印象が悪い。
#
# 4テーマ（ai-copyright / bike-blue-ticket / elderly-license-revocation / takaichi）が
# 該当する。いずれも sample_period を記録する運用より前に公開したテーマで、
# 収集期間の始まりは復元できない（TASK_BOARD 課題28）。更新記録から最終収集日は
# 分かるが、範囲の始まりは残っていない。推測で埋めず、理由を書く。

UNKNOWN_PERIOD_LABEL = "未記録 — 収集期間の記録を始める前に公開したテーマ"


def period_label(period: str) -> str:
    """sample_period の表示ラベル。unknown は理由つきの文言に置き換える。"""
    value = str(period or "").strip()
    return UNKNOWN_PERIOD_LABEL if value.lower() == "unknown" else value
