#!/usr/bin/env python3
"""「意見の推移」の折れ線を、単体で配れるPNG画像にする（課題77 案5の画像配布）。

検索（画像検索）と、他のサイトへの埋め込み・引用で使う。ページの節（build_trend_section.py）と同じ
データ（load_rounds の結果）から描くので、数字がページとずれない。更新のたびに adapter.build が作り直す。

画像は貼る場所で使い分ける2種類（build_trend_section.IMAGE_VARIANTS）。
- ひと目版（summary）: Xのタイムラインや記事の本文幅（幅300〜600px）に縮めても読める。見出し1つ・線2本・大きな数字
- 詳細版（detail）: 全項目と各回の動き。資料や数字の確認で、大きく表示する前提

- Pillow だけで描く（GitHub Actions に無い依存を足さない）。3倍で描いて縮小し、線と文字を滑らかにする。保存は256色のPNG（容量を約3分の1に）
- 日本語フォントは macOS のヒラギノ角ゴシック（W3・W6）を使う。無ければ止める（□□□の画像を黙って出さない）
- PNG の Description に、元の数字の指紋（sha256）と最新の収集日を入れる。公開側の検査
  （verify_trend_images.py）が、ページの数字と画像の指紋を突き合わせ、画像の作り直し漏れを止める
- 画像の中に出来事の縦線は入れない（画像だけ切り出されても原因と誤読されないようにする）
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont
from PIL.PngImagePlugin import PngInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_trend_section as trend  # noqa: E402

WIDTH, HEIGHT = 1200, 675
HEADLINE_MIN_SIZE = 34  # ひと目版の見出しの下限。幅350pxに縮めても約10pxで、読める
SCALE = 3  # 3倍で描いて LANCZOS で縮小する

INK = "#0b1d3a"
INK2 = "#26364f"
MUTED = "#66758b"
GRID = "#e4e9f1"
LEADER = "#8795ab"  # 系列名への引き出し線（データの線と区別する灰色の破線）
AXIS = "#cdd7e5"
BLUE = "#315bd8"
PILL = "#eaf1ff"
PILL_GREY = "#f3f6fb"

# (標準, 太字)。最初に両方そろったものを使う。
FONT_CANDIDATES = (
    ("/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc", "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"),
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
)


class LayoutError(RuntimeError):
    """文字が画像に収まらないときは、切れた画像を出さず止める。"""


class FontNotFound(RuntimeError):
    """日本語フォントが無い環境では、画像を作らず止める（文字が□になった画像を出さない）。"""


def find_fonts() -> tuple[str, str]:
    for regular, bold in FONT_CANDIDATES:
        if Path(regular).is_file() and Path(bold).is_file():
            return regular, bold
    raise FontNotFound(
        "日本語フォントが見つかりません。画像は macOS のヒラギノ角ゴシック（または Noto Sans CJK）がある"
        "環境で作ります（scripts/build_trend_images.py の FONT_CANDIDATES）。"
    )


def fonts_available() -> bool:
    try:
        find_fonts()
    except FontNotFound:
        return False
    return True


def series_digest(labels: list[str], rounds: list[dict]) -> str:
    """ページの節に埋めたグラフのデータ（labels と rounds）から作る指紋。画像と照合する。"""
    payload = json.dumps({"labels": labels, "rounds": rounds}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def rounds_for_digest(series: list[dict], labels: list[str]) -> list[dict]:
    return [
        {
            "d": item["date"], "n": item["n"],
            "v": [item["shares"][label] for label in labels],
            "c": [item["counts"][label] for label in labels],
        }
        for item in series
    ]


# ------------------------------------------------------------ 印（ページのグラフと同じ形）

def shape_points(shape: str) -> list[tuple[float, float]] | None:
    """SHAPE_PATHS（半径1の単位パス。M L H V Z だけ）を点の列にする。円は None。"""
    path = trend.SHAPE_PATHS[shape]
    if path is None:
        return None
    tokens = re.findall(r"([MLHVZ])|(-?\d*\.?\d+)", path)
    points: list[tuple[float, float]] = []
    x = y = 0.0
    command = ""
    numbers: list[float] = []

    def flush() -> None:
        nonlocal x, y
        if command in ("M", "L") and len(numbers) >= 2:
            x, y = numbers[0], numbers[1]
            points.append((x, y))
        elif command == "H" and numbers:
            x = numbers[0]
            points.append((x, y))
        elif command == "V" and numbers:
            y = numbers[0]
            points.append((x, y))

    for cmd, number in tokens:
        if cmd:
            flush()
            command, numbers = cmd, []
        else:
            numbers.append(float(number))
    flush()
    return points


# ------------------------------------------------------------ 描画の道具

def _px(value: float) -> int:
    return int(round(value * SCALE))


def _rgb(color: str) -> tuple[int, int, int]:
    return ImageColor.getrgb(color)


def _blend(color: str, alpha: float) -> tuple[int, int, int]:
    """白の上に alpha で重ねた色（RGB画像には透明がないので、混ぜた色を塗る）。"""
    r, g, b = _rgb(color)
    return tuple(int(round(c * alpha + 255 * (1 - alpha))) for c in (r, g, b))  # type: ignore[return-value]


class Canvas:
    def __init__(self, regular: str, bold: str) -> None:
        self.image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), "white")
        self.draw = ImageDraw.Draw(self.image)
        self._regular, self._bold = regular, bold
        self._cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

    def font(self, size: float, bold: bool = False) -> ImageFont.FreeTypeFont:
        key = (self._bold if bold else self._regular, _px(size))
        if key not in self._cache:
            self._cache[key] = ImageFont.truetype(key[0], key[1], index=0)
        return self._cache[key]

    def text_width(self, text: str, size: float, bold: bool = False) -> float:
        return self.font(size, bold).getlength(text) / SCALE

    def text(self, x: float, y: float, text: str, size: float, color: str, *, bold: bool = False, anchor: str = "ls") -> None:
        self.draw.text((_px(x), _px(y)), text, font=self.font(size, bold), fill=_rgb(color), anchor=anchor)

    def line(self, points: list[tuple[float, float]], color, width: float) -> None:
        pts = [(_px(x), _px(y)) for x, y in points]
        fill = _rgb(color) if isinstance(color, str) else color
        self.draw.line(pts, fill=fill, width=_px(width), joint="curve")

    def dashed(self, start: tuple[float, float], end: tuple[float, float], color: str, width: float, dash: float = 7, gap: float = 6) -> None:
        """破線。データの線と見間違えない、系列名への引き出し線に使う。"""
        length = math.hypot(end[0] - start[0], end[1] - start[1])
        if length == 0:
            return
        ux, uy = (end[0] - start[0]) / length, (end[1] - start[1]) / length
        at = 0.0
        while at < length:
            stop = min(at + dash, length)
            self.line([(start[0] + ux * at, start[1] + uy * at), (start[0] + ux * stop, start[1] + uy * stop)], color, width)
            at += dash + gap

    def rect(self, box: tuple[float, float, float, float], fill: str, radius: float = 0) -> None:
        x0, y0, x1, y1 = (_px(v) for v in box)
        if radius:
            self.draw.rounded_rectangle((x0, y0, x1, y1), radius=_px(radius), fill=_rgb(fill))
        else:
            self.draw.rectangle((x0, y0, x1, y1), fill=_rgb(fill))

    def marker(self, shape: str, cx: float, cy: float, radius: float, color) -> None:
        fill = _rgb(color) if isinstance(color, str) else color
        points = shape_points(shape)
        if points is None:
            r = _px(radius)
            self.draw.ellipse((_px(cx) - r, _px(cy) - r, _px(cx) + r, _px(cy) + r), fill=fill)
        else:
            self.draw.polygon([(_px(cx + x * radius), _px(cy + y * radius)) for x, y in points], fill=fill)

    def finish(self) -> Image.Image:
        return self.image.resize((WIDTH, HEIGHT), Image.LANCZOS)


def _pill(canvas: Canvas, x: float, y: float, text: str, size: float, fg: str, bg: str, *, anchor_right: bool = False) -> float:
    width = canvas.text_width(text, size, True) + 28
    left = x - width if anchor_right else x
    canvas.rect((left, y, left + width, y + size + 18), bg, radius=(size + 18) / 2 if bg == PILL else 12)
    canvas.text(left + 14, y + size + 3, text, size, fg, bold=True)
    return width


def _fit_size(canvas: Canvas, text: str, size: float, max_width: float, minimum: float, bold: bool) -> float:
    while size > minimum and canvas.text_width(text, size, bold) > max_width:
        size -= 1
    return size


# ------------------------------------------------------------ 画像1枚

def image_texts(slug: str, kind: str, series: list[dict]) -> dict:
    """画像に入れる文言。ページの節と同じ見出し・時点・注意書きを使う。"""
    base = trend._theme_base(slug)
    theme = trend.TREND_THEMES[slug]
    spec = trend.KINDS[kind]
    labels = base[spec["labels_key"]]
    info = trend.summary(series, labels)
    axis = "立場別" if kind == "stance" else "主な論点別"
    unit = "意見の投稿に占める割合" if kind == "stance" else "「その他」を除く意見の投稿に占める割合"
    return {
        "labels": labels,
        "title": theme["headings"][kind],
        "asof": f"{trend.jp_date(series[-1]['date'], year=True)}時点",
        "subtitle": f"Xの投稿を{axis}に分類した割合（{unit}）",
        "period": f"{trend.jp_date(series[0]['date'])}〜{trend.jp_date(series[-1]['date'])}の{len(series)}回の収集",
        "notes": [
            "Xの投稿サンプルをAIで分類した構成比です。世論調査ではありません。",
            f"各回の意見は{info['n_min']}〜{info['n_max']}件（最新は{series[-1]['n']}件）で、割合には±{info['median_margin']}ポイント前後のぶれがあります。",
        ],
    }


def render_detail_image(slug: str, kind: str, series: list[dict]) -> Image.Image:
    regular, bold = find_fonts()
    spec = trend.KINDS[kind]
    texts = image_texts(slug, kind, series)
    labels = texts["labels"]
    colors, shapes = spec["colors"][: len(labels)], spec["shapes"][: len(labels)]
    emph = trend.emphasized(series, labels)
    c = Canvas(regular, bold)

    margin_x = 48
    # 上段: 小見出しの丸ラベルと、時点
    _pill(c, margin_x, 34, "SNS上の意見の推移", 18, BLUE, PILL)
    _pill(c, WIDTH - margin_x, 34, texts["asof"], 20, INK2, PILL_GREY, anchor_right=True)
    # 見出し
    size = _fit_size(c, texts["title"], 42, WIDTH - margin_x * 2, 30, True)
    c.text(margin_x, 122, texts["title"], size, INK, bold=True)
    c.text(margin_x, 160, f"{texts['subtitle']}　{texts['period']}", 20, MUTED)

    # 凡例（凡例は2本以上の系列で必ず出す。幅を超えたら折り返す）
    x, y = margin_x, 202
    row_height = 32
    for index, label in enumerate(labels):
        item_width = 40 + 10 + c.text_width(label, 20, True) + 30
        if x + item_width > WIDTH - margin_x and x > margin_x:
            x, y = margin_x, y + row_height
        c.line([(x, y - 7), (x + 34, y - 7)], colors[index], 3)
        c.marker(shapes[index], x + 17, y - 7, 6.5, colors[index])
        c.text(x + 46, y, label, 20, INK2, bold=True)
        x += item_width
    legend_bottom = y

    # 作図領域
    left, right = 104, 1000  # 右に、最新の割合と件数を書く場所を残す
    top, bottom = legend_bottom + 34, 528  # 下に、日付と各回の意見の件数を2段で書く
    max_value = max(v for item in series for v in item["shares"].values() if isinstance(v, (int, float)))
    ceiling = max(10, math.ceil(max_value / 10) * 10)
    first_day = _day(series[0]["date"])
    last_day = _day(series[-1]["date"])

    def x_of(date: str) -> float:
        if last_day == first_day:
            return (left + right) / 2
        return left + (_day(date) - first_day) / (last_day - first_day) * (right - left)

    def y_of(value: float) -> float:
        return bottom - value / ceiling * (bottom - top)

    for value in range(0, ceiling + 1, 10):
        c.line([(left, y_of(value)), (right, y_of(value))], GRID if value else AXIS, 1.2)
        c.text(left - 12, y_of(value) + 6, f"{value}%", 17, MUTED, anchor="rs")
    shown: list[str] = []
    for item in series:
        if not shown or x_of(item["date"]) - x_of(shown[-1]) >= 62:
            shown.append(item["date"])
    if shown[-1] != series[-1]["date"]:
        while len(shown) > 1 and x_of(series[-1]["date"]) - x_of(shown[-1]) < 62:
            shown.pop()
        shown.append(series[-1]["date"])
    n_of = {item["date"]: item["n"] for item in series}
    for date in shown:
        month, day = (int(part) for part in date.split("-")[1:])
        anchor = "ls" if date == series[0]["date"] else ("rs" if date == series[-1]["date"] else "ms")
        c.text(x_of(date), bottom + 27, f"{month}/{day}", 17, MUTED, anchor=anchor)
        c.text(x_of(date), bottom + 47, f"{n_of[date]}件", 14, MUTED, anchor=anchor)
    c.text(left - 12, bottom + 47, "意見数", 14, MUTED, anchor="rs")

    dimmed = lambda s: bool(emph) and s not in emph  # noqa: E731
    for s, label in enumerate(labels):
        points = [(x_of(item["date"]), y_of(item["shares"][label])) for item in series]
        width = 3 if not emph else (2.5 if dimmed(s) else 4)
        c.line(points, _blend(colors[s], 0.5) if dimmed(s) else colors[s], width)
    for s, label in enumerate(labels):
        marker_color = _blend(colors[s], 0.6) if dimmed(s) else colors[s]
        for item in series:
            cx, cy = x_of(item["date"]), y_of(item["shares"][label])
            c.marker(shapes[s], cx, cy, 9.5, "#ffffff")
            c.marker(shapes[s], cx, cy, 6, marker_color)

    # 右端の最新値（重なる行は縦にずらす）
    ends = sorted(((y_of(series[-1]["shares"][label]), s) for s, label in enumerate(labels)))
    placed: list[tuple[float, int]] = []
    for yy, s in ends:
        if placed and yy - placed[-1][0] < 24:
            yy = placed[-1][0] + 24
        placed.append((yy, s))
    for yy, s in placed:
        value = f"{series[-1]['shares'][labels[s]]:.1f}%"
        c.text(right + 18, yy + 7, value, 21, INK, bold=True)
        c.text(right + 18 + c.text_width(value, 21, True) + 9, yy + 7, f"{series[-1]['counts'][labels[s]]}件", 16, MUTED)

    # 足もと: 出典と注意書き
    c.line([(margin_x, 586), (WIDTH - margin_x, 586)], AXIS, 1.2)
    c.text(margin_x, 620, f"出典：SNS反応まっぷ（{trend.SITE_HOST}）", 21, INK, bold=True)
    c.text(margin_x, 647, texts["notes"][0], 16, MUTED)
    c.text(margin_x, 667, texts["notes"][1], 16, MUTED)
    return c.finish()


# ------------------------------------------------------------ ひと目版

def _wrap(canvas: Canvas, text: str, size: float, max_width: float, bold: bool, max_lines: int = 2) -> list[str]:
    """幅で折り返す（日本語なので語の途中でも切る）。max_lines 行目に残りをすべて入れる（文字は欠けない）。"""
    lines: list[str] = []
    current = ""
    for char in text:
        if current and canvas.text_width(current + char, size, bold) > max_width and len(lines) < max_lines - 1:
            lines.append(current)
            current = char
        else:
            current += char
    lines.append(current)
    return lines


def _half_up(value: float) -> int:
    return trend._half_up(value)


def summary_ceiling(max_value: float) -> tuple[int, int]:
    """縦軸の上端と目盛りの間隔。割合なので0から始める（目盛りは多くても4〜6本）。"""
    step = 10 if max_value <= 40 else 20
    return max(step, math.ceil(max_value / step) * step), step


def render_summary_image(slug: str, kind: str, series: list[dict]) -> Image.Image:
    """ひと目版。スマホのタイムライン（幅350px前後）に縮めても、見出しと数字が読めることを基準にする。

    文字は原寸1200pxで24px以上（縮小率0.29で7px。出典と注意書きだけが小さい）、見出しは約50px、数字は52px。
    線は2本だけ。最初と最新の差が大きい2項目（ページの本文が取り上げるのと同じ2項目）を、変化の向きと一緒に見せる。
    """
    regular, bold = find_fonts()
    spec = trend.KINDS[kind]
    base = trend._theme_base(slug)
    labels = base[spec["labels_key"]]
    info = trend.glance(slug, kind, series, labels)
    items = info["items"]
    texts = image_texts(slug, kind, series)
    name = trend.TREND_THEMES[slug]["name"]
    first, last = series[0], series[-1]
    c = Canvas(regular, bold)
    mx = 56

    # 上段: テーマ名つきの小見出しと、時点
    _pill(c, mx, 30, f"{name}｜SNS上の意見の推移", 24, BLUE, PILL)
    _pill(c, WIDTH - mx, 30, texts["asof"], 24, INK2, PILL_GREY, anchor_right=True)

    # 見出し（見出しだけ読んでも、何がどう変わったか分かる）。長い項目名が2つ並ぶ文は文字を縮めて収める。
    size = min(_fit_size(c, line, 54, WIDTH - mx * 2, HEADLINE_MIN_SIZE, True) for line in info["lines"])
    for line in info["lines"]:
        if c.text_width(line, size, True) > WIDTH - mx * 2:
            raise LayoutError(f"ひと目版の見出しが画像の幅に収まりません（{HEADLINE_MIN_SIZE}pxでも）: {line}。項目名を短くするか、build_trend_section.glance_lines の文型を直す")
    for number, line in enumerate(info["lines"]):
        c.text(mx, 142 + number * 66, line, size, INK, bold=True)

    # 説明の行（左: 何の割合か / 右: 回数）
    unit = "意見の投稿に占める割合と件数" if kind == "stance" else "「その他」を除く意見の投稿の割合と件数"
    noun = "立場" if kind == "stance" else "論点"
    caption = f"最初と最新の差が大きい2つ（{unit}）"
    count = f"{len(series)}回の収集"
    cap_size = 24
    while cap_size > 20 and c.text_width(caption, cap_size) + 40 + c.text_width(count, cap_size) > WIDTH - mx * 2:
        cap_size -= 1
    c.text(mx, 260, caption, cap_size, MUTED)
    c.text(WIDTH - mx, 260, count, cap_size, MUTED, anchor="rs")

    # 作図領域（右に、系列名と最新値を直接書く場所を残す）
    left, right = 150, 804
    px_first, px_last = 232, 770
    top, bottom = 296, 536
    colors, shapes = spec["colors"], spec["shapes"]
    ceiling, step = summary_ceiling(max(max(item["start"], item["end"], *(r["shares"][item["label"]] for r in series)) for item in items))
    first_day, last_day = _day(first["date"]), _day(last["date"])

    def x_of(date: str) -> float:
        if last_day == first_day:
            return (px_first + px_last) / 2
        return px_first + (_day(date) - first_day) / (last_day - first_day) * (px_last - px_first)

    def y_of(value: float) -> float:
        return bottom - value / ceiling * (bottom - top)

    for value in range(0, ceiling + 1, step):
        c.line([(left, y_of(value)), (right, y_of(value))], GRID if value else AXIS, 1.6 if value else 2.2)
        c.text(left - 14, y_of(value) + 8, f"{value}%", 24, MUTED, anchor="rs")
    for date, anchor in ((first["date"], "ms"), (last["date"], "ms")):
        month, day = (int(part) for part in date.split("-")[1:])
        c.text(x_of(date), bottom + 36, f"{month}/{day}", 24, MUTED, anchor=anchor)

    # 線（太く）と各回の小さな点。最初の点だけ大きな印にして、形でも見分けられるようにする
    # （右端は、同じ形の印を系列名の横に付けて線でつなぐ。2本が近いと端の印が重なって読めなくなるため）
    for item in items:
        color = colors[item["index"]]
        points = [(x_of(r["date"]), y_of(r["shares"][item["label"]])) for r in series]
        c.line(points, color, 6)
        for point in points[1:-1]:
            c.marker("circle", point[0], point[1], 8, "#ffffff")
            c.marker("circle", point[0], point[1], 5, color)
    for item in items:
        color, shape = colors[item["index"]], shapes[item["index"]]
        c.marker(shape, x_of(first["date"]), y_of(item["start"]), 14, "#ffffff")
        c.marker(shape, x_of(first["date"]), y_of(item["start"]), 10.5, color)

    # 最初の値と件数（高い方は点の上、低い方は点の下）
    ordered = sorted(items, key=lambda item: -item["start"])
    for number, item in enumerate(ordered):
        value, count = f"{_half_up(item['start'])}%", f"{item['start_count']}件"
        y = y_of(item["start"])
        baseline = y - 26 if number == 0 else min(y + 56, bottom - 8)  # 0%の軸に重ならないようにする
        x0 = max(px_first - (c.text_width(value, 36, True) + 10 + c.text_width(count, 22)) / 2, left - 8)  # 縦軸の目盛りの文字に重ねない
        c.text(x0, baseline, value, 36, INK, bold=True)
        c.text(x0 + c.text_width(value, 36, True) + 10, baseline, count, 22, MUTED)

    # 右端: 最新の値と系列名（重なる行は上下に離す）
    label_x = px_last + 52
    name_width = WIDTH - mx - label_x - 6
    blocks = []
    for item in items:
        lines = _wrap(c, item["label"], 28, name_width - 8, True)
        blocks.append({"item": item, "lines": lines, "height": 52 + 8 + 34 * len(lines), "top": y_of(item["end"]) - 26})
    blocks.sort(key=lambda block: block["top"])
    if len(blocks) == 2:
        a, b = blocks
        overlap = (a["top"] + a["height"] + 14) - b["top"]
        if overlap > 0:
            a["top"] -= overlap / 2
            b["top"] += overlap / 2
    for block in blocks:
        block["top"] = min(max(block["top"], top - 22), bottom + 30 - block["height"])
    for block in blocks:
        item = block["item"]
        color, shape = colors[item["index"]], shapes[item["index"]]
        row_y = block["top"] + 26  # 値の行の中心
        c.dashed((px_last + 6, y_of(item["end"])), (label_x - 8, row_y), LEADER, 2.2)
        c.marker(shape, label_x + 12, row_y, 12, color)
        end_value = f"{_half_up(item['end'])}%"
        c.text(label_x + 36, row_y + 19, end_value, 54, INK, bold=True)
        c.text(label_x + 36 + c.text_width(end_value, 54, True) + 12, row_y + 19, f"{item['end_count']}件", 26, MUTED)
        for number, line in enumerate(block["lines"]):
            c.text(label_x, row_y + 26 + 8 + 28 + number * 34, line, 28, INK2, bold=True)

    # 足もと: 出典と注意書き（件数の見方と、意見の合計の件数）
    margin = info["info"]["median_margin"]
    c.line([(mx, 584), (WIDTH - mx, 584)], AXIS, 1.2)
    c.text(mx, 614, f"出典：SNS反応まっぷ（{trend.SITE_HOST}）", 28, INK, bold=True)
    c.text(mx, 641, f"Xの投稿をAIで分類した割合で、世論調査ではありません。割合には±{margin}ポイント前後のぶれがあります。", 21, MUTED)
    c.text(mx, 666, f"件数は、その{noun}の投稿の数です。意見の合計は、最初の回が{first['n']}件、最新の回が{last['n']}件です。", 21, MUTED)
    return c.finish()


def render_image(slug: str, kind: str, series: list[dict], variant: str = "detail") -> Image.Image:
    if variant == "summary":
        return render_summary_image(slug, kind, series)
    if variant == "detail":
        return render_detail_image(slug, kind, series)
    raise ValueError(f"画像の種類が不明です: {variant}")


def _day(date: str) -> int:
    year, month, day = (int(part) for part in date.split("-"))
    import datetime as dt

    return dt.date(year, month, day).toordinal()


def png_metadata(slug: str, kind: str, series: list[dict], variant: str = "detail") -> PngInfo:
    base = trend._theme_base(slug)
    labels = base[trend.KINDS[kind]["labels_key"]]
    texts = image_texts(slug, kind, series)
    digest = series_digest(labels, rounds_for_digest(series, labels))
    info = PngInfo()
    suffix = trend.IMAGE_VARIANTS[variant]["name"]
    info.add_text("Title", f"{texts['title']}（{texts['asof']}・{suffix}）")
    info.add_text("Author", "SNS反応まっぷ")
    info.add_text("Source", trend.page_url(slug))
    info.add_text("Description", f"asof={series[-1]['date']}; kind={kind}; variant={variant}; sha256={digest}")
    return info


def render_for(slug: str, source: Path, outdir: Path) -> dict[tuple[str, str], Path]:
    """全タブ・全種類の画像を outdir に作る。{(kind, variant): パス}。同じ入力なら同じバイト列になる。"""
    base = trend._theme_base(slug)
    outdir.mkdir(parents=True, exist_ok=True)
    result = {}
    for kind in ("stance", "issue"):
        if not base.get(trend.KINDS[kind]["labels_key"]):
            continue
        series = trend.load_rounds(source, base, kind)
        for variant in trend.IMAGE_VARIANTS:
            image = render_image(slug, kind, series, variant)
            path = outdir / trend.image_filename(slug, kind, variant)
            # 256色にして容量を小さくする（毎週の更新でgitの履歴が膨らまないように）。
            indexed = image.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
            indexed.save(path, "PNG", optimize=True, pnginfo=png_metadata(slug, kind, series, variant))
            result[(kind, variant)] = path
    return result


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True, choices=sorted(trend.TREND_THEMES))
    parser.add_argument("--source", type=Path, help="分類済みJSON（省略時はTHEMES.yamlのsample_file）")
    parser.add_argument("--apply", action="store_true", help="docs/images/trend/ へ書き込む（付けなければ一時フォルダへ）")
    args = parser.parse_args()

    import tempfile

    import yaml

    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
    source = args.source or ROOT / themes[args.topic]["sample_file"]
    outdir = ROOT / trend.IMAGE_DIR if args.apply else Path(tempfile.mkdtemp(prefix="trend-images-"))
    for (kind, variant), path in render_for(args.topic, source, outdir).items():
        print(f"{kind}/{variant}: {path} ({path.stat().st_size:,}バイト)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
