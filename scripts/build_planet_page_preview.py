#!/usr/bin/env python3
"""山なみを公開ページの部品ごと組み立てた「差し替え見本」を作る。

公開ページ（docs/{テーマ}-reaction-map.html）を入力にして、
山なみが役目を引き継ぐ区間を外し、代わりに山なみブロックを差し込む。
ヘッダー・フッター・投票・SNS投稿サンプル・関連テーマ・広告枠・OGPは触らない。

**これは見本で、docs/ へは書かない。**本番の差し替えは、ここで形が決まってから
アダプタ（段階10）で行う。いま docs/ を書き換えると、同じ区間を作っている
既存の生成器（build_bukatsu_arena.py / build_reaction_map.py / update_bukatsu_tide.py）
と取り合いになる。

同じ入力で2回実行しても差分が出ない（課題34）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_planet_data as bpd  # noqa: E402

SCOPE = "#planet-block"

# 山なみが役目を引き継ぐ区間。ここを外さないと同じ数字が2回出る（段階8の検査）。
DROP_SECTIONS = [
    ('<section class="panel conflict-panel"><div class="panel-title"><h2>7つの論点とXの声</h2>',
     "section", "7つの論点とXの声（2Dアリーナ）"),
    ('<section class="panel explainer-section" id="explainer-section">',
     "section", "このテーマを読み解く論点（論点カード6枚）"),
    ('<div class="explainer-modal" id="explainer-modal"',
     "div", "論点カードの拡大表示"),
    ('<section class="panel arguments-panel" id="strongest-arguments"',
     "section", "30秒でわかる、両側の強い論拠"),
    ('<section class="arena-section" id="stance-map-section">',
     "section", "SNS反応マップ（2Dキャンバス）"),
]


def cut_block(html: str, start: str, tag: str) -> tuple[str, bool]:
    """start から、対応する閉じタグまでを取り除く。入れ子を数える。"""
    i = html.find(start)
    if i < 0:
        return html, False
    open_re = re.compile(rf"<{tag}\b", re.I)
    close_re = re.compile(rf"</{tag}\s*>", re.I)
    depth, pos = 0, i
    while pos < len(html):
        o = open_re.search(html, pos)
        c = close_re.search(html, pos)
        if c is None:
            raise SystemExit(f"閉じタグが見つかりません: {start[:60]}")
        if o and o.start() < c.start():
            depth += 1
            pos = o.end()
            continue
        depth -= 1
        pos = c.end()
        if depth == 0:
            return html[:i] + html[pos:], True
    raise SystemExit(f"閉じタグが見つかりません: {start[:60]}")


def scope_css(css: str) -> str:
    """試作のCSSを山なみブロックの中だけに効くようにする。

    公開ページの topic-modern.css と .panel / .lead が衝突する。
    ここで閉じ込めないと、ページ全体の見た目が壊れる（記憶: CSS特異度バグ）。
    """
    out, i, n = [], 0, len(css)
    while i < n:
        # @media などのブロックは中身を再帰的に書き換える
        if css[i] == "@":
            j = css.find("{", i)
            at = css[i:j].strip()
            depth, k = 1, j + 1
            while k < n and depth:
                if css[k] == "{":
                    depth += 1
                elif css[k] == "}":
                    depth -= 1
                k += 1
            body = css[j + 1:k - 1]
            if at.startswith("@keyframes"):
                out.append(f"{at}{{{body}}}")
            else:
                out.append(f"{at}{{{scope_css(body)}}}")
            i = k
            continue
        j = css.find("{", i)
        if j < 0:
            break
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == "{":
                depth += 1
            elif css[k] == "}":
                depth -= 1
            k += 1
        sels = re.sub(r"/\*.*?\*/", "", css[i:j], flags=re.S).strip()
        body = css[j + 1:k - 1]
        if sels:
            out.append(",".join(scope_selector(s.strip()) for s in sels.split(",") if s.strip())
                       + "{" + body + "}")
        i = k
    return "".join(out)


def scope_selector(sel: str) -> str:
    if sel in (":root", "body", "html"):
        return SCOPE
    if sel == "*":
        return f"{SCOPE},{SCOPE} *"
    head = sel.split(None, 1)
    if head and (head[0].startswith("html") or head[0].startswith(".planet-live")):
        rest = head[1] if len(head) > 1 else ""
        return f"{head[0]} {SCOPE} {rest}".rstrip()
    return f"{SCOPE} {sel}"


# 外した部品にしか触っていない素のスクリプト。残すと null 参照でJSエラーが出る。
# 呼び出し側はすべて if(window.…) で守られているので、落としても投票は動く。
DEAD_SCRIPT_IDS = ("explainer-modal", "explainer-card", "smCanvasMain", "smCanvasHeat",
                   "sm-filters", "sm-tooltip")


def drop_orphan_scripts(html: str) -> tuple[str, int]:
    pat = re.compile(r"\n?<script(?![^>]*\bsrc=)[^>]*>.*?</script>", re.S)
    n = 0

    def repl(m: re.Match) -> str:
        nonlocal n
        body = m.group(0)
        if any(k in body for k in DEAD_SCRIPT_IDS):
            n += 1
            return ""
        return body

    return pat.sub(repl, html), n


# 試作は単体で開く前提の暗い配色だが、公開ページは白いカードが並ぶ明るい面。
# そのまま入れると黒い板を貼り付けたように見える（オーナー指摘 2026-09-05）。
# ここでサイト側の配色・書体へ寄せる。図（山なみ・点の装置）だけは暗いまま残す。
# データを見せる箱が暗いのは、旧ページの2Dマップ（#0f0e2e）と同じ扱いで、浮かない。
LIGHT_SKIN = """
#planet-block{--bg:#fff;--panel:#f7f9fc;--line:#d7dce6;--fg:#172033;--muted:#667085;
  --accent:#075ef2;--rest-dot:#c9d2e0;font-family:inherit;line-height:1.8}
#planet-block .caution{background:#fbf8ec;color:#5a5340;border-left-color:#c9971a}
#planet-block .panel{box-shadow:none}
#planet-block .panel .cross,#planet-block .dot-mech{background:#eef3fb}
#planet-block .panel .cross b,#planet-block .dot-mech b{color:#0b2a5b}
#planet-block .note,#planet-block .ro{background:#f2f6fb}
#planet-block .meta code{background:#eef1f6}
#planet-block .islands .num{background:#e7ecf4;color:#172033}
#planet-block .modes button[aria-pressed=true]{background:#e4edff}
#planet-block .dive button{color:#fff}
#planet-block .bar span{color:#fff;text-shadow:0 1px 2px rgba(12,20,35,.45)}
#planet-block .gopts button.hit{background:#e8f6ec}
#planet-block .gopts button.miss{background:#fdeeee}
#planet-block .ro.down .ar,#planet-block .ro.down .to{color:#b23a48}
#planet-block .ro.up .ar,#planet-block .ro.up .to{color:#15734a}
#planet-block .qnext{color:#fff;background:var(--accent)}
/* 図の箱は暗いまま。中の文字と小箱だけ暗い面に合わせ直す */
#planet-block .dotbox{background:#0b1017;border:1px solid #2b3440;border-radius:12px;
  padding:13px 14px;margin-top:14px;color:#e6edf3;--rest-dot:#4a525c}
#planet-block .dotbox .legend{color:#9fb0c4}
#planet-block .dotbox .ro{background:#161b22;border-color:#2b3440;color:#e6edf3}
#planet-block .dotbox .dot-mech{background:#161b22;color:#e6edf3}
#planet-block .dotbox .dot-mech b{color:#f2f6fa}
/* 潜る前は海面より下（図の高さの38%）が黒い空白のまま残り、作りかけに見える。
   論点名は海面+17pxにあるので、そこだけ残して畳み、「海の水を抜く」で開く。 */
#planet-block .chart-box{overflow:hidden}
#planet-block .chart-box svg{margin-bottom:-19%;transition:margin-bottom .9s ease}
#planet-block .chart-box.dived svg{margin-bottom:0}
@media (prefers-reduced-motion:reduce){
  #planet-block .chart-box svg{transition:none}
}
"""


def render_planet(topic: str) -> str:
    data = bpd.stabilize(bpd.build(topic))
    tpl = (ROOT / "quality/prototypes/planet-prototype.template.html").read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    return bpd.render_page(data, tpl, payload)


def split_prototype(html: str) -> dict[str, str]:
    s0 = html.index("<style>") + len("<style>")
    s1 = html.index("</style>")
    w0 = html.index('<div class="wrap">')
    d0 = html.index('<script>window.PLANET_DATA')
    end = html.rindex("</script>") + len("</script>")
    return {
        "css": html[s0:s1],
        "detect": html[s1 + len("</style>"):w0].strip(),
        "body": html[w0:d0].strip(),
        "scripts": html[d0:end],
    }


def build_section(parts: dict[str, str]) -> str:
    body = parts["body"]
    # 試作の見出しは公開ページの体裁に合わせる（「試作・非公開」の札は外す）
    body = body.replace('<h1>議論の山なみ<span class="proto-tag">試作・非公開</span></h1>',
                        '<div class="panel-title"><h2>議論の山なみ</h2>'
                        '<span>幅＝意見の数 / 高さ＝強い表現の割合</span></div>')
    body = re.sub(r'^<div class="wrap">', f'<div id="{SCOPE[1:]}">', body)
    # 試作のときの言い回しを、読者に出す言葉へ直す。
    # 「3D」は球をやめた時点で嘘になっている（段階8-B）。
    for before, after in (
        ("この試作の見かた", "このページの見かた"),
        ("論点一覧（3Dが使えなくても同じ内容へ行けます）",
         "論点一覧（図が出ないときも同じ内容へ行けます）"),
    ):
        body = body.replace(before, after)
    # 開発者向けの一文（スクリプト名とコマンドの案内）は読者に出さない
    body = re.sub(r"このページの数字はすべて.*?更新されます。", "", body, flags=re.S)
    return (
        "<!-- PLANET_SECTION_START -->\n"
        '<section class="panel planet-panel" aria-labelledby="planet-heading">\n'
        f"<style>{scope_css(parts['css'])}{LIGHT_SKIN}</style>\n"
        f"{parts['detect']}\n"
        f"{body}\n"
        "</section>\n"
        f"{parts['scripts']}\n"
        "<!-- PLANET_SECTION_END -->"
    )


def localize_assets(html: str) -> str:
    """見本を quality/prototypes/ から開けるように、docs/ の部品への相対パスを直す。"""
    html = re.sub(r'(\b(?:href|src)=")(?!https?:|//|#|\.\./)([^"]+\.(?:css|js|png|webp|svg|ico|jpg))',
                  r"\1../../docs/\2", html)
    return html.replace("url('images/", "url('../../docs/images/")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", default="bukatsu-chiiki")
    ap.add_argument("--page", default=None, help="入力にする公開ページ")
    ap.add_argument("--out", default=None)
    ap.add_argument("--for-docs", action="store_true",
                    help="docs/ の位置から開く前提でパスを直さない（検査用）")
    a = ap.parse_args()

    page = Path(a.page) if a.page else ROOT / "docs" / f"{a.topic}-reaction-map.html"
    out = Path(a.out) if a.out else ROOT / "quality/prototypes" / f"{a.topic}-page-preview.html"
    html = page.read_text(encoding="utf-8")

    if "<!-- PLANET_SECTION_START -->" in html:
        raise SystemExit("入力ページに山なみが既に入っています（見本ではなく本番の更新です）")

    removed = []
    for start, tag, label in DROP_SECTIONS:
        html, hit = cut_block(html, start, tag)
        removed.append((label, hit))

    html, dropped = drop_orphan_scripts(html)

    section = build_section(split_prototype(render_planet(a.topic)))
    anchor = "<!-- BUKATSU_ENTRY_END -->"
    if anchor not in html:
        raise SystemExit(f"差し込み位置 {anchor} が見つかりません")
    html = html.replace(anchor, anchor + "\n" + section, 1)

    # 見本を開いても実サイトのアクセス数に混ざらないよう、計測タグだけ外す
    html = re.sub(r"<!-- GA_TAG_START -->.*?<!-- GA_TAG_END -->",
                  "<!-- GA_TAG: 見本では外している -->", html, flags=re.DOTALL)

    out.write_text(html if a.for_docs else localize_assets(html), encoding="utf-8")
    for label, hit in removed:
        print(("外した  " if hit else "見つからず ") + label)
    print(f"外した  取り残されたスクリプト {dropped}本")
    try:
        shown = out.relative_to(ROOT)
    except ValueError:
        shown = out
    print(f"wrote {shown}  ({len(html):,} バイト)")


if __name__ == "__main__":
    main()
