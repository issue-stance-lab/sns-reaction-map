#!/usr/bin/env python3
"""新テーマの公開前ゲート。過去に実際に抜けた登録・欠落だけを見る。

verify_theme_page.py（論拠・出典・件数）や verify_top_page.py（トップの統計）とは
守備範囲が違う。こちらは「登録し忘れ」と「公開後に人が見るまで気づかない欠落」を見る。

使い方:
    python3 .claude/skills/new-topic/scripts/check_launch.py <slug>

NG が1件でもあれば exit 1。WARN は exit code に影響しない。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

GA4 = "G-K10S4YCZFH"
ADSENSE = "ca-pub-2542211932832864"

results: list[tuple[str, str, str]] = []


def ok(name: str, detail: str = "") -> None:
    results.append(("OK", name, detail))


def ng(name: str, detail: str) -> None:
    results.append(("NG", name, detail))


def warn(name: str, detail: str) -> None:
    results.append(("WARN", name, detail))


def js_function_body(html: str, name: str) -> str | None:
    """`function name(...) { ... }` の本体を波かっこの対応で取り出す。"""
    m = re.search(rf"function\s+{re.escape(name)}\s*\([^)]*\)\s*\{{", html)
    if not m:
        return None
    depth, start = 0, m.end() - 1
    for i in range(start, len(html)):
        if html[i] == "{":
            depth += 1
        elif html[i] == "}":
            depth -= 1
            if depth == 0:
                return html[start + 1 : i]
    return None


def theme_block(slug: str) -> str | None:
    """THEMES.yaml から該当テーマのブロックを素朴に切り出す。"""
    text = (ROOT / "THEMES.yaml").read_text(encoding="utf-8")
    m = re.search(rf"^  {re.escape(slug)}:\n(.*?)(?=^  \S|\Z)", text, re.S | re.M)
    return m.group(0) if m else None


def scalar(block: str, key: str) -> str | None:
    m = re.search(rf"^\s+{re.escape(key)}:\s*(.+?)\s*(?:#.*)?$", block, re.M)
    if not m:
        return None
    return m.group(1).strip().strip("'\"")


def check_themes_yaml(slug: str) -> tuple[str | None, str | None]:
    block = theme_block(slug)
    if block is None:
        ng("THEMES.yaml", f"{slug} が登録されていない（台帳が単一の真実源）")
        return None, None
    ok("THEMES.yaml", "登録あり")

    html = scalar(block, "html")
    if not html:
        ng("THEMES.yaml html", "html: が無い")
    elif not (ROOT / html).exists():
        ng("THEMES.yaml html", f"{html} が存在しない")
    else:
        ok("THEMES.yaml html", html)

    sample = scalar(block, "sample_file")
    if sample and not (ROOT / sample).exists():
        warn("sample_file", f"{sample} が無い（非公開の正典は gitignore 対象。復元し忘れの可能性）")

    mode = scalar(block, "page_update_mode")
    if mode in ("adapter", "adapter_candidate"):
        ok("page_update_mode", mode)
    elif mode:
        warn(
            "page_update_mode",
            f"{mode} — 再実行できるページ生成スクリプトが無い。"
            "更新のたびに手作業が増える。オーナーに手動更新になる旨を伝えること（課題34）",
        )
    else:
        ng("page_update_mode", "未記入。adapter / adapter_candidate / migration / manual のどれか")

    if not scalar(block, "collect_at") and scalar(block, "collect_mode") != "event-driven":
        warn("collect_at", "次回の収集予定日が空。verify_top_page.py の期限管理から漏れる")

    if scalar(block, "sample_period") == "unknown":
        warn("sample_period", "unknown。fetched_at から特定できないか確認（推測で埋めないこと／課題28）")

    return html, mode


def check_page(slug: str, html_path: str) -> None:
    html = (ROOT / html_path).read_text(encoding="utf-8")

    for label, needle in (("GA4", GA4), ("AdSense", ADSENSE)):
        (ok if needle in html else ng)(f"保護タグ {label}", needle if needle in html else f"{needle} が無い")

    if "og:title" in html and "og:image" in html:
        ok("OGP meta", "og:title / og:image あり")
    else:
        ng("OGP meta", "og:title か og:image が無い（SNSシェア時にカードが出ない）")

    if "vote-store.js" in html or "cast-vote" in html or "vote2d.js" in html:
        ok("投票基盤", "Supabase投票の参照あり")
    else:
        ng("投票基盤", "vote-store.js / vote2d.js / cast-vote のいずれも無い")

    # 投票完了後のシェア・やり直し（constitutional-amendment で欠落した）
    if re.search(r"vote-redo|投票をやり直す|投票し直す", html):
        ok("投票やり直しボタン", "あり")
    else:
        ng("投票やり直しボタン", "vote-redo / 「投票をやり直す」がページに無い（vote2d.js は雛形の存在が前提）")

    if re.search(r"share-x|intent/tweet|でシェア", html):
        ok("シェアボタン", "あり")
    else:
        ng("シェアボタン", "share-x / intent/tweet が無い")

    # ヒーロー画像のフォールバック事故
    if "topic-modern.css" in html:
        if "--topic-hero-image" in html:
            ok("ヒーロー画像", "--topic-hero-image を指定済み")
        else:
            ng(
                "ヒーロー画像",
                "--topic-hero-image が無い。topic-modern.css のフォールバックで"
                "生成AI著作権テーマの画像が表示される",
            )

    # 2Dスタンスマップを載せている場合のみ
    if "canvasHeat" in html or "smCanvasHeat" in html:
        # ID + 要素セレクタ（特異度101）が #canvasMain（100）に勝ってしまうパターン。
        # background:transparent を指定しているだけの規則は問題ない。
        bad = [
            m.group(0).split("{")[0].strip()
            for m in re.finditer(r"#[\w-]+[^{}<>]*\scanvas\s*\{([^}]*)\}", html)
            if re.search(r"background[^;}]*:", m.group(1))
            and not re.search(r"background[^;}]*:\s*(transparent|none)", m.group(1))
        ]
        if bad:
            ng(
                "スタンスマップCSS",
                f"`{bad[0]} {{ ... background ... }}` がある。"
                "特異度101が #canvasMain(100) に勝ち、ヒートマップが隠れる",
            )
        else:
            ok("スタンスマップCSS", "ID+要素セレクタに background なし")

        bodies = {
            name: body
            for name in ("drawHeat", "drawHeatmap")
            if (body := js_function_body(html, name)) is not None
        }
        if not bodies:
            warn(
                "ヒートマップ描画",
                "drawHeat / drawHeatmap が見つからない。外部JSかもしれないので目視で確認する"
                "（別タブから戻したときに描画されるか）",
            )
        else:
            guilty = [n for n, b in bodies.items() if re.search(r"anim(?:ating|Frame)", b)]
            if guilty:
                ng(
                    "ヒートマップ描画",
                    f"{guilty[0]}() がアニメーション状態（animating / animFrame）を見ている。"
                    "requestAnimationFrame は背景タブで止まるため、別タブから戻ると永久に描画されない",
                )
            else:
                ok("ヒートマップ描画", f"{'/'.join(bodies)}() はアニメーション状態に依存していない")


def check_vote_registration(slug: str, html_path: str) -> None:
    """ページの投票定義と Supabase の TOPIC_CHOICES を突き合わせる。"""
    html = (ROOT / html_path).read_text(encoding="utf-8")
    fn = ROOT / "supabase/functions/cast-vote/index.ts"
    if not fn.exists():
        warn("投票トピック登録", "supabase/functions/cast-vote/index.ts が無い")
        return

    registered = dict(
        (m.group(1), int(m.group(2)))
        for m in re.finditer(r'"([^"]+)":\s*(\d+)', fn.read_text(encoding="utf-8"))
    )

    topic = re.search(r"var TOPIC\s*=\s*'([^']+)'", html) or re.search(
        r"""topic_id['"]?\s*[:=]\s*['"]([^'"]+)['"]""", html
    )
    if not topic:
        warn("投票トピック登録", "ページから TOPIC を読み取れなかった（手で確認すること）")
        return
    topic_id = topic.group(1)

    if topic_id not in registered:
        ng(
            "投票トピック登録",
            f"{topic_id} が TOPIC_CHOICES に無い。投票は invalid_topic で全部弾かれる"
            "（ページ側は無言で失敗する）",
        )
        return

    issues = re.search(r"var VOTE_ISSUES\s*=\s*\[(.*?)\];", html, re.S)
    stances = re.search(r"var STANCES\s*=\s*\[(.*?)\];", html, re.S)
    if issues and stances:
        n = len(re.findall(r"\bk:'", issues.group(1))) * len(re.findall(r"\bk:'", stances.group(1)))
        if n and n != registered[topic_id]:
            ng(
                "投票選択肢数",
                f"ページは論点×立場={n} だが TOPIC_CHOICES は {registered[topic_id]}。"
                "範囲外のインデックスが弾かれる",
            )
        else:
            ok("投票選択肢数", f"{topic_id} = {registered[topic_id]}")
    else:
        ok("投票トピック登録", f"{topic_id}（選択肢数は目視で確認）")

    warn(
        "supabase デプロイ",
        "index.ts を変えたら `supabase functions deploy cast-vote --no-verify-jwt` が要る。"
        "オーナーへの依頼を忘れないこと（自動では確認できない）",
    )


def check_registrations(slug: str, html_path: str) -> None:
    page = Path(html_path).name

    cases = json.loads((ROOT / "configs/site-cases.json").read_text(encoding="utf-8"))
    case_urls = {c.get("reaction_map_url") for c in cases.get("cases", [])}
    seo = json.loads((ROOT / "configs/theme-seo.json").read_text(encoding="utf-8"))
    seo_urls = {t.get("url") for t in seo.get("themes", [])}

    (ok if page in case_urls else ng)(
        "site-cases.json", page if page in case_urls else f"{page} が未登録"
    )
    (ok if page in seo_urls else ng)(
        "theme-seo.json", page if page in seo_urls else f"{page} が未登録"
    )

    diff = (case_urls ^ seo_urls) - {None}
    if diff:
        warn(
            "URL集合の一致",
            f"site-cases と theme-seo で食い違い: {sorted(diff)}。"
            "一致しないと apply_theme_trust.py が落ちる",
        )
    else:
        ok("URL集合の一致", "site-cases と theme-seo が一致")

    sitemap = (ROOT / "docs/sitemap.xml").read_text(encoding="utf-8")
    (ok if page in sitemap else ng)(
        "sitemap.xml", page if page in sitemap else f"{page} が未掲載"
    )

    index = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    (ok if page in index else ng)(
        "index.html トピックカード", page if page in index else f"{page} へのリンクが無い"
    )

    tax = ROOT / f"scripts/{slug.replace('-', '_')}_taxonomy.py"
    if tax.exists():
        ok("taxonomy 定義", tax.name)
        test = ROOT / f"tests/test_{slug.replace('-', '_')}_taxonomy.py"
        if not test.exists():
            warn("taxonomy テスト", f"{test.name} が無い（論点体系の退行を検出できない）")
    else:
        warn("taxonomy 定義", f"{tax.name} が無い（論点の唯一の定義を置く場所）")


def main() -> int:
    parser = argparse.ArgumentParser(description="新テーマの公開前ゲート")
    parser.add_argument("slug", help="THEMES.yaml のテーマキー（例: consumption-tax-cut）")
    args = parser.parse_args()

    html_path, _ = check_themes_yaml(args.slug)
    if html_path and (ROOT / html_path).exists():
        check_page(args.slug, html_path)
        check_vote_registration(args.slug, html_path)
        check_registrations(args.slug, html_path)

    def cells(text: str) -> int:  # 全角は2桁ぶんの幅を取る
        return sum(2 if unicodedata.east_asian_width(c) in "WFA" else 1 for c in text)

    width = max(cells(name) for _, name, _ in results)
    for status, name, detail in results:
        mark = {"OK": "  OK ", "NG": "  NG ", "WARN": "WARN "}[status]
        print(f"{mark}{name}{' ' * (width - cells(name))}  {detail}")

    ng_count = sum(1 for s, _, _ in results if s == "NG")
    warn_count = sum(1 for s, _, _ in results if s == "WARN")
    print(f"\nNG {ng_count}件 / WARN {warn_count}件（WARN は自分で確認すべき項目。exit code には影響しない）")
    return 1 if ng_count else 0


if __name__ == "__main__":
    sys.exit(main())
