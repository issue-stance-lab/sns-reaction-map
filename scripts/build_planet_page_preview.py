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
from build_planet_data import e as esc  # noqa: E402

SCOPE = "#planet-block"

# 山なみが役目を引き継ぐ区間。ここを外さないと同じ数字が2回出る（段階8の検査）。
DROP_SECTIONS = [
    # 編集部の横断整理が同じ役目をする
    ('<section class="panel arguments-panel" id="strongest-arguments"',
     "section", "30秒でわかる、両側の強い論拠"),
    # 図が引き継ぐ。地図の見え方として戻す予定（切り替え）
    ('<section class="arena-section" id="stance-map-section">',
     "section", "SNS反応マップ（2Dキャンバス・切り替えとして戻す予定）"),
    # 前回比 +5.8pt は母数146件の誤差 ±10.1pt より小さく、増減を断定できない
    ('<section class="update-dashboard" aria-label="更新データと世論の潮目">',
     "section", "世論の潮目（誤差の範囲内）"),
    # 図と同じ数字（460 / 323 / 247）の繰り返し
    ('<section class="panel conflict-panel"><div class="panel-title"><h2>投稿の分類結果</h2>',
     "section", "投稿の分類結果（数字の重複）"),
    ('<section class="stats insight-stats"',
     "section", "4つの注目ポイント（数字の重複）"),
    # 本文は data/verification/{テーマ}-background.json へ移し、第1部として先頭で出す
    ('<section class="panel background-panel">',
     "section", "この争点の背景（第1部へ移動）"),
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


def take_block(html: str, start: str, tag: str) -> tuple[str, str]:
    """start から対応する閉じタグまでを切り取り、（残り, 切り取った中身）を返す。"""
    i = html.find(start)
    if i < 0:
        raise SystemExit(f"見つかりません: {start[:60]}")
    rest, _ = cut_block(html, start, tag)
    taken = html[i:len(html) - (len(rest) - i)]
    return rest, taken


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
DEAD_SCRIPT_IDS = ("smCanvasMain", "smCanvasHeat", "sm-filters", "sm-tooltip")


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
/* 図もサイトの色にする（オーナー指示 2026-09-05「マップの背景がまだ黒」）。
   SVGの色は描画時に属性で付いているが、CSSのほうが強いので上から塗り替えられる。 */
#planet-block .chart-box{background:#F2F6FD;border-color:#DCE3EF}
#planet-block .chart-box svg rect:first-of-type{fill:#DCE9F7}
#planet-block .chart-box svg #seacover{fill:#F2F6FD;opacity:.96}
#planet-block .chart-box svg line[stroke="#2b3440"]{stroke:#E3E9F3}
#planet-block .chart-box svg line[stroke="#5b9bf0"][stroke-width="1"]{stroke:#B9CCE6}
#planet-block .chart-box svg line[stroke="#5b9bf0"][stroke-width="1.6"]{stroke:#075EF2}
/* 目盛りの文字は線の真上に置かれていて、0%だけ海面の線に隠れる。5だけ持ち上げる */
#planet-block .chart-box svg text[fill="#8b949e"]{fill:#667085;transform:translateY(-5px)}
#planet-block .chart-box svg text[fill="#c7d1dc"]{fill:#172033}
#planet-block .chart-box svg text[fill="#e6edf3"]{fill:#0F1A3D}
#planet-block .chart-box svg path[stroke="#f2f6fa"]{stroke:#0F1A3D}
#planet-block .chart-box svg #seafloor path[fill="#122642"]{fill:#E7F0FB;stroke:#7FA6D8}
#planet-block .chart-box svg #seafloor text[fill="#7fb3c4"]{fill:#2C5C8F}
#planet-block .chart-box svg text[fill="#e0663a"]{fill:#C4462A}
#planet-block .chart-box svg path[stroke="#e0663a"]{stroke:#C4462A}
/* 点の装置も同じ面にそろえる */
#planet-block .dotbox{background:#F2F6FD;border:1px solid #DCE3EF;border-radius:12px;
  padding:13px 14px;margin-top:14px;--rest-dot:#D3DCEA}
#planet-block .dotbox .legend{color:#667085}
/* 潜る前は海面より下（図の高さの38%）が黒い空白のまま残り、作りかけに見える。
   論点名は海面+17pxにあるので、そこだけ残して畳み、「海の水を抜く」で開く。 */
#planet-block .chart-box{overflow:hidden}
#planet-block .chart-box svg{margin-bottom:-17.5%;transition:margin-bottom .9s ease}
#planet-block .chart-box.dived svg{margin-bottom:0}
@media (prefers-reduced-motion:reduce){
  #planet-block .chart-box svg{transition:none}
}
"""


BG_CSS = """
#bukatsu-background .bg-def{font-size:17px;font-weight:700;line-height:1.85;margin:0 0 6px}
#bukatsu-background .bg-now{font-size:14px;color:var(--muted);margin:0 0 20px}
#bukatsu-background h3{font-size:15px;font-weight:900;margin:24px 0 8px;padding-left:10px;
  border-left:3px solid var(--accent);line-height:1.5}
#bukatsu-background p{font-size:14.5px;line-height:1.95;margin:0 0 .9em}
#bukatsu-background ol.bg-tl{list-style:none;margin:6px 0 0;padding:0}
#bukatsu-background ol.bg-tl li{display:grid;grid-template-columns:132px 1fr;gap:18px;
  padding:14px 0;border-top:1px solid var(--line)}
#bukatsu-background ol.bg-tl .when{font-size:13px;font-weight:900;color:var(--accent);line-height:1.6}
#bukatsu-background ol.bg-tl .when em{display:block;font-style:normal;font-size:11.5px;
  font-weight:400;color:var(--muted)}
#bukatsu-background ol.bg-tl .what{font-size:14.5px;line-height:1.9;margin:0}
#bukatsu-background ol.bg-tl .src{display:block;margin-top:6px;font-size:12px;line-height:1.7}
#bukatsu-background ol.bg-tl .src a{color:var(--muted)}
#bukatsu-background .bg-jump{margin:22px 0 0;font-size:14px;font-weight:700}
@media (max-width:560px){
  #bukatsu-background ol.bg-tl li{grid-template-columns:1fr;gap:4px}
}
"""


def build_background(topic: str) -> str:
    """第1部「この問題を知る」を台帳から組み立てる。

    本文は人（編集部AI）が一次資料に当たって書いたものを台帳に置き、ここでは並べるだけ。
    件数・割合は一切入れない（同じ数字は1ページに1回だけ／段階8）。
    """
    src = ROOT / "data" / "verification" / f"{topic}-background.json"
    if not src.exists():
        return ""
    d = json.loads(src.read_text(encoding="utf-8"))
    if d.get("status") != "complete":
        return ""
    df = d["definition"]
    out = [f"<style>{BG_CSS}</style>",
           '<section class="panel" id="bukatsu-background" aria-labelledby="bg-title">',
           '<div class="panel-title"><h2 id="bg-title">この問題は、何の話か</h2>'
           '<span>官庁の資料で確かめた範囲</span></div>',
           f'<p class="bg-def">{esc(df["one_line"])}</p>',
           f'<p class="bg-now">{esc(df["now"])}</p>',
           "<h3>なぜ始まったか</h3>"]
    out += [f"<p>{esc(t)}</p>" for t in d["cause"]]
    out.append("<h3>これまでの経緯</h3>")
    out.append('<ol class="bg-tl">')
    for x in d["timeline"]:
        links = "／".join(
            f'<a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["name"])}</a>'
            for s in x["sources"])
        out.append(
            f'<li><div class="when">{esc(x["when"])}<em>{esc(x["era"])}</em></div>'
            f'<div><p class="what">{esc(x["text"])}</p>'
            f'<span class="src">出典: {links}</span></div></li>')
    out.append("</ol>")
    out.append('<p class="bg-jump"><a href="#vote-section">意見のほうを先に見る →</a></p>')
    out.append("</section>")
    return "\n".join(out)


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
                        '<div class="panel-title"><h2>SNS反応マップ</h2>'
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

    # 使い方ページの約束は「①テーマを選ぶ ②投票する ③分布と理由を読む」。
    # 投票が図より後ろにあると順番が逆になるので、図の前へ移す。
    # 中に入っている「編集・分析情報」は長いので、投票からは外して後ろへ回す。
    trust_start, trust_end = "<!-- ARTICLE_TRUST_START -->", "<!-- ARTICLE_TRUST_END -->"
    ti, tj = html.find(trust_start), html.find(trust_end)
    if ti < 0 or tj < 0:
        raise SystemExit("編集・分析情報の目印が見つかりません")
    trust = html[ti:tj + len(trust_end)]
    html = html[:ti] + html[tj + len(trust_end):]

    html, vote = take_block(html, '<section class="panel" id="vote-section"', "section")

    rel = '<section class="panel" id="related-topics">'
    if rel not in html:
        raise SystemExit("「次に見るテーマ」が見つかりません")
    html = html.replace(rel, trust + "\n" + rel, 1)

    bg = build_background(a.topic)
    bg_anchor = "<!-- BUKATSU_ENTRY_START -->"
    if bg and bg_anchor in html:
        html = html.replace(bg_anchor, bg + "\n" + bg_anchor, 1)

    section = build_section(split_prototype(render_planet(a.topic)))
    anchor = "<!-- BUKATSU_ENTRY_END -->"
    if anchor not in html:
        raise SystemExit(f"差し込み位置 {anchor} が見つかりません")
    html = html.replace(anchor, anchor + "\n" + vote + "\n" + section, 1)

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
