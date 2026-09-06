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
DEAD_SCRIPT_IDS = ("smCanvasMain", "smCanvasHeat", "sm-filters", "sm-tooltip",
                   "explainer-modal", "explainer-card")


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
/* 選択肢が押せると分からない・正誤が弱い（オーナー指摘）。触れる形と結果を強くする */
#planet-block .gopts{gap:9px}
#planet-block .gopts button{background:#fff;border:2px solid #D7DCE6;border-radius:10px;
  padding:13px 15px 13px 44px;font-size:14.5px;font-weight:500;position:relative;
  transition:border-color .15s,box-shadow .15s,transform .1s}
#planet-block .gopts button::before{content:"";position:absolute;left:15px;top:50%;
  width:17px;height:17px;margin-top:-8.5px;border:2px solid #B9C2D2;border-radius:50%}
#planet-block .gopts button:hover:not(:disabled){border-color:var(--accent);
  box-shadow:0 3px 10px rgba(7,94,242,.14);transform:translateY(-1px)}
#planet-block .gopts button:hover:not(:disabled)::before{border-color:var(--accent)}
#planet-block .gopts button:disabled{opacity:.55}
#planet-block .gopts button.hit{background:#E6F6EC;border-color:#1B7A55;opacity:1;font-weight:700}
#planet-block .gopts button.hit::before{content:"✓";border-color:#1B7A55;background:#1B7A55;
  color:#fff;font-size:12px;font-weight:700;display:grid;place-items:center;line-height:1}
#planet-block .gopts button.miss{background:#FDECEC;border-color:#C4392C;opacity:1}
#planet-block .gopts button.miss::before{content:"×";border-color:#C4392C;background:#C4392C;
  color:#fff;font-size:13px;font-weight:700;display:grid;place-items:center;line-height:1}
#planet-block .gans,#planet-block .qans{background:#F4F7FC;border-radius:10px;padding:13px 15px;
  margin-top:13px}
#planet-block .gans .lead{font-size:17px;font-weight:900;margin:0 0 5px}
#planet-block .guess:has(.hit:not(:disabled)) .gans .lead{color:#1B7A55}
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
/* 山が押せると分からない（オーナー指摘）。触れる合図を出す */
#planet-block .chart-box .hill path{transition:opacity .18s ease,filter .18s ease}
#planet-block .chart-box .hill:hover path,
#planet-block .chart-box .hill:focus-visible path{opacity:1!important;
  filter:drop-shadow(0 0 6px rgba(7,94,242,.5))}
#planet-block .chart-box .hill:hover text,
#planet-block .chart-box .hill:focus-visible text{font-weight:700}
#planet-block .tap-hint{display:flex;align-items:center;gap:8px;margin:0 0 8px;
  padding:9px 13px;border-radius:10px;background:var(--blue-tint,#E7EEFE);
  font-size:13.5px;font-weight:700;color:#0B3FA8;line-height:1.6}
#planet-block .tap-hint span[aria-hidden]{font-size:16px}
#planet-block a.go-card{display:inline-block;background:var(--accent);color:#fff;
  font-weight:700;font-size:14px;text-decoration:none;border-radius:8px;padding:10px 18px}
#planet-block a.go-card:hover{filter:brightness(1.08)}
/* 進み具合はページの一番上に固定する（オーナー指示「常に上に表示してアピールしたい」） */
#progress{position:sticky;top:0;z-index:60;display:flex;align-items:center;gap:10px;
  padding:9px clamp(14px,4vw,28px);background:#fff;border-bottom:1px solid #DCE3EF;font-size:13px;color:#42527A}
#progress .track{flex:1;height:7px;background:#E7ECF4;border-radius:99px;overflow:hidden;
  min-width:60px;max-width:340px}
#progress .track i{display:block;height:100%;width:0;background:var(--accent,#075EF2);
  border-radius:99px;transition:width .4s ease}
#progress b{font-weight:900;color:#0F1A3D;font-variant-numeric:tabular-nums}
#progress .how{color:#7C89A8;font-size:12px}
@media (max-width:640px){ #progress .how{display:none} }
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
/* 確かめること。3列の表は375pxで潰れるので、1件1枚のカードにする */
#bukatsu-check .ck{display:grid;grid-template-columns:150px 1fr;gap:0;
  border:1px solid var(--line);border-radius:12px;overflow:hidden;margin:0 0 10px}
#bukatsu-check .ck .k{background:#F2F6FD;padding:14px 16px;border-right:1px solid var(--line)}
#bukatsu-check .ck .k b{display:block;font-size:15px;font-weight:900;line-height:1.5}
#bukatsu-check .ck .k span{display:block;margin-top:5px;font-size:12.5px;color:var(--muted);
  line-height:1.7}
#bukatsu-check .ck .v{padding:14px 18px;font-size:14.5px;line-height:1.9}
#bukatsu-check .ck .v .src{display:block;margin-top:7px;font-size:11.5px;line-height:1.7}
#bukatsu-check .ck .v .src a{color:var(--muted)}
#bukatsu-check .ck-note{margin:14px 0 0;padding:12px 15px;border-radius:10px;
  background:#FBF8EC;border-left:3px solid #C9971A;font-size:13.5px;line-height:1.85}
@media (max-width:560px){
  #bukatsu-check .ck{grid-template-columns:1fr}
  #bukatsu-check .ck .k{border-right:none;border-bottom:1px solid var(--line)}
}
@media (max-width:560px){
  #bukatsu-background ol.bg-tl li{grid-template-columns:1fr;gap:4px}
}
"""


VOTE_MSG_CSS = """
#vote-msg{margin:14px 0 0;padding:12px 15px;border-radius:10px;font-size:14px;line-height:1.8;
  font-weight:700;display:flex;gap:9px;align-items:flex-start}
#vote-msg[hidden]{display:none}
#vote-msg.err{background:#FDECEC;border:1px solid #E4B4B0;color:#8E2318}
#vote-msg.info{background:#E7EEFE;border:1px solid #B9CCE6;color:#0B3FA8}
#vote-msg .ic{flex:none;font-size:16px;line-height:1.5}
"""

VOTE_MSG_JS = """
(function(){
  /* 送信に失敗したとき、ブラウザの alert ではなく画面の中に出す。
     alert は読み上げの相性が悪く、環境によっては出ないまま黙って終わる。 */
  window.voteMsg = function(text, kind){
    var el = document.getElementById("vote-msg");
    if (!el){ window.alert(text); return; }
    el.className = (kind === "info" ? "info" : "err");
    el.innerHTML = '<span class="ic" aria-hidden="true">'
      + (kind === "info" ? "\u2139" : "\u26a0") + '</span><span></span>';
    el.lastChild.textContent = text
      + (kind === "info" ? "" : " もう一度、立場のボタンを押してください。");
    el.hidden = false;
  };
  window.voteMsgClear = function(){
    var el = document.getElementById("vote-msg");
    if (el) el.hidden = true;
  };
})();
"""


def fix_vote_feedback(html: str) -> tuple[str, int]:
    """投票の失敗をブラウザの alert で知らせるのをやめ、画面の中に出す。

    alert は画面の外に出るため読み上げと相性が悪く、環境によっては抑止されて
    黙って終わる。押しても何も起きないページに見える。
    """
    n = 0
    pairs = [
        ("alert(VoteStore.friendlyError(error))",
         "voteMsg(VoteStore.friendlyError(error))"),
        ("alert('24時間以内にすでに投票されています。前回の投票が集計されています。')",
         "voteMsg('24時間以内にすでに投票されています。前回の投票が集計されています。','info')"),
    ]
    for a, b in pairs:
        if a in html:
            n += html.count(a)
            html = html.replace(a, b)
    # 送信が通ったときは前の失敗表示を消す
    html = html.replace("if(saved)showVote(selIssue,stanceIdx);",
                        "if(saved){voteMsgClear();showVote(selIssue,stanceIdx);}")
    return html, n


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
           '<div class="panel-title"><h2 id="bg-title">何が、どこまで進んでいるのか</h2>'
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
    out.append('<p class="bg-jump"><a href="#planet-block">意見の分布のほうを先に見る →</a></p>')
    out.append("</section>")

    ck = d.get("checklist")
    if ck:
        out += ['<section class="panel" id="bukatsu-check" aria-labelledby="ck-title">',
                '<div class="panel-title"><h2 id="ck-title">学校の外へ出した後、だれが続けるか</h2>'
                '<span>判断の前に確かめること</span></div>',
                f'<p>{esc(ck["lead"])}</p>']
        for x in ck["items"]:
            links = "／".join(
                f'<a href="{esc(t["url"])}" target="_blank" rel="noopener">{esc(t["name"])}</a>'
                for t in x["sources"])
            out.append(
                f'<div class="ck"><div class="k"><b>{esc(x["label"])}</b>'
                f'<span>{esc(x["ask"])}</span></div>'
                f'<div class="v">{esc(x["found"])}'
                f'<span class="src">出典: {links}</span></div></div>')
        out.append(f'<p class="ck-note"><b>このページで未確認のこと</b><br>{esc(ck["unknown"])}'
                   f'<br>{esc(ck["caveat"])}</p>')
        out.append("</section>")
    return "\n".join(out)


ISSUE_CSS = """
#issue-cards .ic{border-top:2px solid #0F1A3D;padding:22px 0 30px;scroll-margin-top:64px}
#issue-cards .ic + .ic{border-top-color:#DCE3EF}
#issue-cards .ic:target .ic-head h3{color:var(--accent)}
#issue-cards .ic-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:10px}
#issue-cards .ic-head .dot{width:11px;height:11px;border-radius:3px;flex:none;align-self:center}
#issue-cards .ic-head h3{margin:0;font-size:21px;font-weight:900;line-height:1.4;letter-spacing:.01em}
#issue-cards .ic-head .cnt{margin-left:auto;font-weight:900;font-size:26px;line-height:1;
  font-variant-numeric:tabular-nums;color:#0F1A3D}
#issue-cards .ic-head .cnt small{font-size:13px;font-weight:700;color:var(--muted);margin-left:2px}
#issue-cards .ic-body{font-size:15px;line-height:1.95;margin:12px 0 0;max-width:44rem}
#issue-cards .ic figure{margin:16px 0 0}
#issue-cards .ic img{width:100%;height:auto;border-radius:8px;display:block}
#issue-cards .ic-back{display:inline-block;margin-top:16px;font-size:13px;font-weight:700}
"""

def _articles(html: str, cls: str) -> list[str]:
    out, i = [], 0
    needle = f'<article class="{cls}"'
    while True:
        i = html.find(needle, i)
        if i < 0:
            return out
        rest, _ = cut_block(html[i:], needle, "article")
        out.append(html[i:i + (len(html) - i) - len(rest)])
        i += 1


def merge_issue_cards(html: str, data: dict) -> tuple[str, str]:
    """「7つの論点とXの声」と「このテーマを読み解く論点」を論点ごとに1枚へ統合する。

    同じ7論点を2か所で別々に並べていたので、件数も見出しも二重に出ていた。
    地図の山から飛べる1つの場所にまとめる（オーナー指示 2026-09-05）。
    """
    label2id = {it["label"]: it["id"] for it in data["issues"]}
    colors = {x["key"]: x.get("color") for x in data.get("stances", []) if x.get("color")}
    posts, figs = {}, {}
    for art in _articles(html, "hermes-issue-card"):
        m = re.search(r"<h3>(.*?)</h3>", art, re.S)
        if m and m.group(1).strip() in label2id:
            posts[label2id[m.group(1).strip()]] = art
    for art in _articles(html, "explainer-card"):
        m = re.search(r'id="issue-count-([^"]+)"', art)
        if m:
            figs[m.group(1)] = art

    def inner(art: str, tag: str, cls: str) -> str:
        m = re.search(rf'<{tag} class="{cls}"[^>]*>(.*?)</{tag}>', art, re.S)
        return m.group(1) if m else ""

    out = [f"<style>{ISSUE_CSS}</style>",
           '<section class="panel" id="issue-cards" aria-labelledby="ic-title">',
           '<div class="panel-title"><h2 id="ic-title">論点ごとに、なかを見る</h2>'
           '<span>7つすべてを、図解と投稿つきで</span></div>']
    for it in data["issues"]:
        iid, art_p, art_f = it["id"], posts.get(it["id"], ""), figs.get(it["id"], "")
        out.append(f'<article class="ic" id="issue-{esc(iid)}">')
        col = colors.get(it.get("top_stance"), "#8b9199")
        out.append(f'<div class="ic-head"><span class="dot" style="background:{esc(col)}"></span>'
                   f'<h3>{esc(it["label"])}</h3>'
                   f'<span class="cnt">{it["count"]}<small>件</small></span></div>')
        bar = re.search(r'<div class="hermes-stance-bar">.*?</div>\s*'
                        r'<div class="hermes-legend">.*?</div>', art_p, re.S)
        if bar:
            out.append(bar.group(0))
        desc = re.search(r'<p class="explainer-card-desc">(.*?)</p>', art_f, re.S)
        if desc:
            out.append(f'<p class="ic-body">{desc.group(1)}</p>')
        sides = re.search(r'<div class="explainer-sides">.*?</div>\s*</div>', art_f, re.S)
        if sides:
            out.append(sides.group(0).rsplit("</div>", 1)[0])
        img = re.search(r'<img src="[^"]*"[^>]*>', art_f)
        if img:
            out.append(f'<figure>{img.group(0)}</figure>')
        samples = re.search(r'<div class="hermes-samples">.*?</div>\s*</article>', art_p, re.S)
        if samples:
            out.append(samples.group(0).rsplit("</article>", 1)[0])
        out.append('<a class="ic-back" href="#planet-block">↑ 地図へ戻る</a>')
        out.append("</article>")
    out.append("</section>")
    return html, "\n".join(out)


def render_planet(data: dict) -> str:
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
    # 図の上に「押せる」と書く。下の小さい灰色の一行では気づかれない
    body = re.sub(r'<div class="progress" id="progress"[^>]*>.*?</div>', "", body, flags=re.S)
    body = body.replace(
        '<div class="stage">',
        '<p class="tap-hint"><span aria-hidden="true">👆</span>'
        '山を押すと、その論点の図解と、賛成・反対それぞれの投稿が読めます</p>'
        '<div class="stage">', 1)
    # 試作のときの言い回しを、読者に出す言葉へ直す。
    # 「3D」は球をやめた時点で嘘になっている（段階8-B）。
    for before, after in (
        ("この試作の見かた", "このページの見かた"),
        # 「探査記録」は惑星・海だった頃の名前。何を数えているかも分からなかった
        ("<span>探査記録</span>",
         '<span title="予想2問・論点7・沈んだ大陸4・一次資料クイズ7問・地下水脈2の'
         '合計22か所のうち、開いた数です">読んだところ</span>'),
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


def protected_fragments(html: str) -> list[str]:
    """Editorial notices and service contracts must survive page composition."""
    parts = []
    for marker in ("ARTICLE_TRUST", "RESEARCH_CONDITIONS", "ADSENSE_TAG", "GA_TAG"):
        parts += re.findall(r"<!-- " + marker + r"_START -->.*?<!-- " + marker + r"_END -->", html, re.S)
    for match in re.finditer(r"<aside\b[^>]*>", html):
        _, block = take_block(html[match.start():], match.group(0), "aside")
        parts.append(block)
    parts += re.findall(r'<meta\b[^>]*(?:property|name)="(?:og:|twitter:)[^"]*"[^>]*>', html)
    parts += re.findall(r'<section\b[^>]*\bid="vote-section"[^>]*>', html)
    for script in re.findall(r"<script\b[^>]*>.*?</script>", html, re.S):
        if "VoteStore.cast(" in script or re.search(r'\bsrc="[^\"]*vote-(?:config|store)\.js', script):
            parts.append(script)
    return parts


def verify_preserved(source: str, result: str) -> None:
    for fragment in protected_fragments(source):
        # The existing bukatsu adapter changes only error presentation, not vote contracts.
        changed, _ = fix_vote_feedback(fragment)
        if fragment not in result and changed not in result:
            raise SystemExit("保護された編集情報・調査条件・注記・計測・投票の要素が失われました")


def apply_preview_policy(html: str, failures: list[str], for_docs: bool) -> str:
    if failures and for_docs:
        raise SystemExit("独自性の検査に不合格のため --for-docs は使えません: " + " / ".join(failures))
    if for_docs:
        return html
    if re.search(r'<meta\b[^>]*name="robots"', html, re.I):
        html = re.sub(r'<meta\b[^>]*name="robots"[^>]*>', '<meta name="robots" content="noindex,nofollow">', html, flags=re.I)
    else:
        html = html.replace("</head>", '<meta name="robots" content="noindex,nofollow">\n</head>', 1)
    details = "" if not failures else "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in failures) + "</ul>"
    notice = ('<aside id="page-preview-status" role="note" style="padding:16px;background:#fff3cd;color:#453400">'
              '<strong>試作・非公開</strong> — 一般公開前の確認用です。' + details + '</aside>')
    return re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + notice, html, count=1)


# ---------------------------------------------------------------- 部活動専用（旧方式）

def build_bukatsu(html: str, data: dict) -> tuple[str, list[tuple[str, bool]]]:
    removed = []
    for start, tag, label in DROP_SECTIONS:
        html, hit = cut_block(html, start, tag)
        removed.append((label, hit))

    # 同じ7論点を2か所で並べていたので、1枚のカードへ統合してから両方を外す
    html, issue_cards = merge_issue_cards(html, data)
    for start, tag, label in (
        ('<section class="panel conflict-panel"><div class="panel-title"><h2>7つの論点とXの声</h2>',
         "section", "7つの論点とXの声（論点カードへ統合）"),
        ('<section class="panel explainer-section" id="explainer-section">',
         "section", "このテーマを読み解く論点（論点カードへ統合）"),
        ('<div class="explainer-modal" id="explainer-modal"', "div", "図解の拡大表示"),
    ):
        html, hit = cut_block(html, start, tag)
        removed.append((label, hit))

    html, dropped = drop_orphan_scripts(html)
    removed.append((f"取り残されたスクリプト{dropped}本", dropped > 0))

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
    html, n_alert = fix_vote_feedback(html)
    vote = vote.replace('<div id="vote-step1">',
                        '<p id="vote-msg" role="status" aria-live="polite" hidden></p>'
                        '<div id="vote-step1">', 1)
    vote = (f"<style>{VOTE_MSG_CSS}</style>" + vote
            + f"<script>{VOTE_MSG_JS}</script>")
    vote = vote.replace("<span>SNSの声を見る前に</span>",
                        "<span>ここまで読んだうえで</span>")

    rel = '<section class="panel" id="related-topics">'
    if rel not in html:
        raise SystemExit("「次に見るテーマ」が見つかりません")
    html = html.replace(rel, trust + "\n" + rel, 1)

    bg = build_background("bukatsu-chiiki")
    if bg:
        html, old_entry = take_block(html, "<!-- BUKATSU_ENTRY_START -->", "section")
        removed.append(("学校の外へ出した後（台帳から作り直し）", bool(old_entry)))

    section = build_section(split_prototype(render_planet(data)))
    anchor = "<!-- BUKATSU_ENTRY_END -->"
    if anchor not in html:
        raise SystemExit(f"差し込み位置 {anchor} が見つかりません")
    html = html.replace(anchor, bg + "\n" + anchor, 1)
    html = html.replace(anchor, anchor + "\n" + section + "\n" + issue_cards + "\n" + vote, 1)

    for it in data["issues"]:
        tag = f'<div class="extras" id="extras-{it["id"]}">'
        if tag in html:
            html = html.replace(
                tag,
                tag + f'<p style="margin:14px 0 0"><a class="go-card" href="#issue-{it["id"]}">'
                      f'この論点のなかを見る ↓</a></p>', 1)
    return html, removed


# ---------------------------------------------------------------- 汎用（自転車以降）

def build_generic(topic: str, html: str, data: dict) -> tuple[str, list[tuple[str, bool]]]:
    """Replace known visual blocks, preserving all other source content and scripts."""
    removed = []
    ids = ("process-collect", "process-verify", "process-found", "process-table",
           "reread-basis", "elderly-verify", "strongest-arguments", "issue-arena-section")
    for iid in ids:
        match = re.search(r'<section\b[^>]*\bid="' + re.escape(iid) + r'"[^>]*>', html)
        if match:
            html, hit = cut_block(html, match.group(0), "section")
            removed.append((iid, hit))
    html, hit = cut_block(html, '<section class="stats insight-stats"', "section")
    removed.append(("旧注目ポイント", hit))
    # This animation belongs only to the removed process-found section.
    html = re.sub(r'<script\b[^>]*id="process-found-anim"[^>]*>.*?</script>', "", html, flags=re.S)
    section = build_section(split_prototype(render_planet(data)))
    marker = "<!-- RESEARCH_CONDITIONS_END -->"
    if marker not in html:
        raise SystemExit("調査条件の目印が見つかりません")
    html = html.replace(marker, marker + "\n" + section, 1)
    return html, removed


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
    if out.resolve().is_relative_to((ROOT / "docs").resolve()):
        raise SystemExit("見本生成器は docs/ へ書き込みません。quality/prototypes/ を指定してください")
    html = page.read_text(encoding="utf-8")
    source_html = html

    if "<!-- PLANET_SECTION_START -->" in html:
        raise SystemExit("入力ページに山なみが既に入っています（見本ではなく本番の更新です）")

    data = bpd.stabilize(bpd.build(a.topic))
    cfg = bpd.yaml.safe_load((ROOT / "configs/planet" / f"{a.topic}.yaml").read_text())
    failures = bpd.independence_gate(data, cfg)
    if failures:
        data["prototype_only"] = True
        data["gate_failures"] = failures
    # Reject a failing public-mode request before composing or writing any output.
    if failures and a.for_docs:
        apply_preview_policy(html, failures, True)

    if a.topic == "bukatsu-chiiki":
        html, removed = build_bukatsu(html, data)
    else:
        html, removed = build_generic(a.topic, html, data)
    verify_preserved(source_html, html)
    html = apply_preview_policy(html, failures, a.for_docs)

    # 進み具合はページの一番上へ。テンプレート側の paintProgress() が
    # #progress/#pbar/#pnum を前提にしており、無いとJSエラーで山なみごと止まる
    # （テーマを問わず必須。数字はJSが実測して上書きするのでここでは仮置きでよい）。
    bar = ('<div id="progress"><span>読んだところ</span>'
           '<span class="track"><i id="pbar"></i></span><b id="pnum">0</b>'
           '<span class="how">質問に答える・山を押す・クイズに答えると増えます</span></div>')
    html = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + bar, html, count=1)

    # 見本を開いても実サイトのアクセス数に混ざらないよう、計測タグだけ外す。
    # 本番向け（--for-docs）では絶対に外さない。保護タグを落とすと数字が取れなくなる。
    if not a.for_docs:
        html = re.sub(r"<!-- GA_TAG_START -->.*?<!-- GA_TAG_END -->",
                      "<!-- GA_TAG: 見本では外している -->", html, flags=re.DOTALL)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html if a.for_docs else localize_assets(html), encoding="utf-8")
    for label, hit in removed:
        print(("外した  " if hit else "見つからず ") + label)
    try:
        shown = out.relative_to(ROOT)
    except ValueError:
        shown = out
    print(f"wrote {shown}  ({len(html):,} バイト)")


if __name__ == "__main__":
    main()
