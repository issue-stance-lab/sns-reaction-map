#!/usr/bin/env python3
"""<main>直下の「調査条件」ボックス（RESEARCH_CONDITIONS区間）を組み立てる共通ヘルパー。

refresh_planet_section.py と、各テーマのビルダー（build_henoko_arena.py・
build_fukushuto_arena.py・build_koshitsu_arena.py の山なみ再生成経路）の両方から
呼ばれる。同じテーマでもどちらの経路で更新されても同じ文面になるよう、
1箇所にまとめてある（課題79 C-5、2026-09-20）。
"""
from __future__ import annotations

import html
import re


def research_conditions_html(collected_display: str, period: str) -> str:
    """他7テーマにある「調査条件」ボックスと同じ形のHTMLを組み立てる。"""
    return (
        "<!-- RESEARCH_CONDITIONS_START -->\n"
        '<aside class="research-conditions" aria-label="SNSデータの調査条件"'
        ' style="padding:16px min(6vw,72px);background:#fff;border-bottom:1px solid var(--line);'
        'font-size:13px;line-height:1.8;color:var(--muted);">\n'
        '  <p style="max-width:1000px;margin:0 auto;">'
        '<strong style="color:var(--ink);">このマップの元データ:</strong> '
        f"Yahooリアルタイム検索で取得した公開投稿 {collected_display}件<br>\n"
        f"  （取得期間: {html.escape(period)}／"
        '<span class="review-note">AI分類。代表投稿は編集部が選定</span>）<br>\n'
        "  <strong>社会全体の世論調査ではありません。</strong></p>\n"
        "</aside>\n"
        "<!-- RESEARCH_CONDITIONS_END -->"
    )


def apply_research_conditions(page: str, conditions_html: str, theme_label: str) -> str:
    """既存の（空でも中身入りでも）RESEARCH_CONDITIONS区間を丸ごと差し替える。"""
    new_page, n = re.subn(
        r"<!-- RESEARCH_CONDITIONS_START -->.*?<!-- RESEARCH_CONDITIONS_END -->",
        lambda m: conditions_html,
        page,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit(f"調査条件マーカーが見つからないか複数あります（{theme_label}）")
    return new_page
