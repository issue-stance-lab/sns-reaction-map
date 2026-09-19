#!/usr/bin/env python3
"""公開済みの山なみページ（docs/{topic}-reaction-map.html）を、最新の正典データで作り直す。

初回の切り替え（build_planet_page_preview.py --for-docs）は「旧デザイン→山なみ」の
1回きりの変換で、既に山なみが入っているページに使うと安全装置が拒否する
（この課題54・63の反映作業で実際に発生し、この専用スクリプトを新設した）。

このスクリプトは <!-- PLANET_SECTION_START --> 〜 <!-- PLANET_SECTION_END --> の
区間を、最新の正典データから作り直した内容へ置き換える。区間の外では
テーマ別に登録された冒頭・調査条件の件数説明も更新する。ヘッダー・フッター・
投票・SNS投稿サンプル・関連テーマ・広告枠・OGP・進捗バーの入れ物は変更しない。

同じ入力で2回実行しても差分が出ない（課題34の冪等性）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_planet_data as bpd  # noqa: E402
from build_planet_page_preview import build_section, render_planet, split_prototype  # noqa: E402
from issue_card_counts import card_counts, load_records, other_count  # noqa: E402
from sync_issue_counts import apply_lead, apply_note  # noqa: E402

START = "<!-- PLANET_SECTION_START -->"
END = "<!-- PLANET_SECTION_END -->"


def _sync_lead_and_note(html: str, topic: str, themes: dict) -> str:
    """sync_issue_counts.py の lead/note を、山なみページにも適用する。

    sync_theme() は「論点カード同期は対象外」として山なみ全体を早期returnし、
    lead・noteもろとも素通りしていた。しかしlead・noteは論点カードの構造に
    依存しない単純な文字列置換で、card_counts()自体は山なみでも問題なく計算できる
    （実際に部活動のconfigsは issue_counts.sync=["lead"] のまま）。ここだけ、
    既存の apply_lead / apply_note を直接呼んで正しく揃える。
    """
    config_path = ROOT / "configs" / f"{topic}-reaction-map.json"
    if not config_path.is_file():
        return html
    config = json.loads(config_path.read_text(encoding="utf-8"))
    sync = [str(name) for name in ((config.get("issue_counts") or {}).get("sync") or [])]
    if not sync:
        return html
    theme_data = themes[topic]
    sample_file = theme_data.get("verification_file") or theme_data.get("sample_file")
    cards = card_counts(topic, config, sample_file)
    # bike-blue-ticketは以前ここで論点カード（explainer-card）の件数も揃えていたが、
    # 起承転結の再構成（課題69）でカードを山なみの論点パネルへ一本化したため不要になった。
    if "lead" in sync:
        html = apply_lead(html, topic, cards, other_count(topic, config, sample_file))
    if "note" in sync:
        block = config.get("issue_counts") or {}
        block_source = str(block.get("source") or sample_file or "")
        html = apply_note(html, topic, len(load_records(block_source)))
    return html


def _inject_bukatsu_go_cards(block: str, data: dict) -> str:
    """build_bukatsu() が本文中に足す「この論点のなかを見る」リンクを再現する。

    build_section() 自体は作らない（build_planet_page_preview.py:build_bukatsu の
    セクション挿入後の一手間）。ここを飛ばすと、初回変換時に足された既存のリンクが
    再生成のたびに消える（課題47と同じ失われ方）。bukatsu-chiiki専用（他テーマの
    build_generic() には無い一手間のため、他テーマでは呼ばない）。
    """
    for it in data["issues"]:
        tag = f'<div class="extras" id="extras-{it["id"]}">'
        if tag in block and f'href="#issue-{it["id"]}"' not in block:
            block = block.replace(
                tag,
                tag + f'<p style="margin:14px 0 0"><a class="go-card" href="#issue-{it["id"]}">'
                      f'この論点のなかを見る ↓</a></p>', 1)
    return block


METHOD_TEXT_RE = re.compile(r"(重複を除いた累計)([\d,]+)(件を分類し、意見と判定した)([\d,]+)(件を論点分析に使用しています)")


BUKATSU_RESEARCH_CONDITIONS_RE = re.compile(
    r"(Yahooリアルタイム検索で取得した公開投稿 )[\d,]+(件<br>\s*\n\s*（取得期間: )[^／<]+"
)


def _sync_bukatsu_method_text(html: str, data: dict) -> str:
    """「調査条件」内の集計方法テキスト（累計N件・意見M件）と、収集件数・取得期間を揃える。

    このテキストはbuild_bukatsu_arena.py・sync_issue_counts.pyのどちらの生成対象にも
    入っておらず（山なみ移行前からの静的文で、山なみ判定によるスキップの対象にすら
    なっていない）、初回変換以来だれも更新していなかった。bukatsu-chiiki専用。
    2026-09-15、課題69の定期収集で「収集した公開投稿N件」「取得期間」も同じ理由で
    未更新のまま残っていたと判明し、あわせて揃えるようにした（自転車の
    _sync_bike_method_text と同じパターン）。
    """
    collected, opinions = data["totals"]["collected"], data["totals"]["opinions"]
    new_html, n = METHOD_TEXT_RE.subn(
        lambda m: f"{m.group(1)}{collected:,}{m.group(3)}{opinions:,}{m.group(5)}", html, count=1
    )
    if n != 1:
        raise SystemExit("調査条件の集計方法テキストが見つからないか複数あります（bukatsu-chiiki）")
    new_html, n = BUKATSU_RESEARCH_CONDITIONS_RE.subn(
        lambda m: f"{m.group(1)}{collected:,}{m.group(2)}{data['sample_period']}", new_html, count=1
    )
    if n != 1:
        raise SystemExit("調査条件の取得件数・取得期間が見つからないか複数あります（bukatsu-chiiki）")
    return _sync_bukatsu_issue_card_counts(new_html, data)


def _sync_bukatsu_issue_card_counts(html: str, data: dict) -> str:
    """「論点ごとに、なかを見る」（#issue-cards）にある論点カードの件数を揃える。

    このセクションは build_planet_page_preview.py の merge_issue_cards() が
    初回の山なみ変換時にだけ作る静的HTMLで、PLANET_SECTION_END より後ろ
    （山なみ区間の外）にある。update_bukatsu_tide.py・build_bukatsu_arena.py・
    sync_issue_counts.py のどの山なみ判定にも掛からず、refresh_planet_section.py も
    今まで山なみ区間の中しか書き換えていなかったため、初回変換以来だれも
    更新していなかった（verify_number_provenance.py だけがこの残存を検出する。
    verify_theme_page.py の「論点カードのデータ整合」検査対象には入っていない）。
    bukatsu-chiiki専用。
    """
    counts = {it["id"]: it["count"] for it in data["issues"]}
    for issue_id, count in counts.items():
        pattern = re.compile(
            rf'(<article class="ic" id="issue-{re.escape(issue_id)}">.*?<span class="cnt">)'
            r'[\d,]+(<small>件</small></span>)', re.S)
        html, n = pattern.subn(lambda m: f"{m.group(1)}{count:,}{m.group(2)}", html, count=1)
        if n != 1:
            raise SystemExit(f"論点カード「{issue_id}」の件数表示が見つかりません（bukatsu-chiiki #issue-cards）")
    return html


ELDERLY_OPINION_COUNT_RE = re.compile(r"(意見と判定した)([\d,]+)(件)")


def _sync_elderly_method_text(html: str, data: dict) -> str:
    """本文中に3か所ある「意見と判定したN件」（lead文・データ出典・調査条件）を揃える。

    configs/elderly-license-revocation-reaction-map.json に issue_counts.sync が
    無いため sync_issue_counts.py の apply_lead/apply_note は素通りし、かつ
    そのLEAD_RE/NOTE_REが探す定型文（「分析対象となった意見N件を...」等）とも
    文言が違って一致しない。3か所とも山なみ区間の外にあり、build_section()の
    再生成対象にも入らないため、初回変換以来だれも更新していなかった
    （部活動の「調査条件」文と同じ失われ方）。elderly-license-revocation専用。
    """
    opinions = data["totals"]["opinions"]
    new_html, n = ELDERLY_OPINION_COUNT_RE.subn(
        lambda m: f"{m.group(1)}{opinions:,}{m.group(3)}", html
    )
    if n != 3:
        raise SystemExit(f"「意見と判定したN件」の想定箇所数(3)と一致しません（elderly-license-revocation）: {n}件")
    return new_html


def _sync_bike_method_text(html: str, data: dict) -> str:
    """山なみ化後に旧ビルダが飛ばす冒頭・調査条件の母数を揃える。"""
    collected = data["totals"]["collected"]
    opinions = data["totals"]["opinions"]
    other = next(issue["count"] for issue in data["issues"] if issue["key"] == "その他")
    patterns = [
        (r'(<p class="lead">収集したSNS投稿)[\d,]+(件のうち、分析対象の意見)[\d,]+(件をAIで整理し、主要5論点)[\d,]+(件に分類し、残る)[\d,]+',
         lambda m: f"{m[1]}{collected}{m[2]}{opinions}{m[3]}{opinions - other}{m[4]}{other}"),
        (r'(収集した)[\d,]+(件のうち意見と判定した)[\d,]+(件を論点分析の対象にしています)',
         lambda m: f"{m[1]}{collected}{m[2]}{opinions}{m[3]}"),
    ]
    for pattern, replacement in patterns:
        html, count = re.subn(pattern, replacement, html)
        if count != 1:
            raise SystemExit(f"自転車の母数説明が想定箇所数(1)と一致しません: {count}件")
    html, count = re.subn(
        r'(このマップの元データ:</strong> Yahooリアルタイム検索で取得した公開投稿 )[\d,]+(件<br>\s*（取得期間: )[^／<]+',
        lambda m: f"{m[1]}{collected}{m[2]}{data['sample_period']}", html)
    if count != 1:
        raise SystemExit(f"自転車の冒頭の調査条件が想定箇所数(1)と一致しません: {count}件")
    return html


def _sync_henoko_method_text(html: str, data: dict) -> str:
    """「SNS投稿の収集方法」段落の集計件数を揃える。

    「編集・分析情報」内の静的文で、build_section()の再生成対象（山なみ区間の外）
    にも sync_issue_counts.py の LEAD_RE/NOTE_RE（探す定型文が違う）にも掛からず、
    初回変換以来だれも更新していなかった（他テーマと同じ失われ方。2026-09-16、
    課題69の辺野古1回目で発覚）。henoko-student-accident専用。
    """
    collected = data["totals"]["collected"]
    opinions = data["totals"]["opinions"]
    pattern = re.compile(r"(収集した)[\d,]+(件のうち意見と判定した)[\d,]+(件を論点分析に表示しています)")
    new_html, n = pattern.subn(lambda m: f"{m[1]}{collected:,}{m[2]}{opinions:,}{m[3]}", html)
    if n != 1:
        raise SystemExit(f"「収集したN件のうち意見と判定したM件」の想定箇所数(1)と一致しません（henoko-student-accident）: {n}件")
    return new_html


# consumption-tax-cutの論点ごとの図解画像。slugはファイル名の接尾辞、labelはalt文字列用
# （h2はアイコン付きなのでここは別に持つ）。「その他」は図解を持たない。
CTC_LANDING_IMAGE_BY_ISSUE_ID = {
    "consumption-tax-cut-political-trust": ("kouyaku", "公約・政治不信"),
    "consumption-tax-cut-scope": ("taishou", "対象範囲"),
    "consumption-tax-cut-effect": ("kouka", "減税の効果"),
    "consumption-tax-cut-finance-welfare": ("zaigen", "財源・社会保障"),
    "consumption-tax-cut-alternatives": ("kyufu", "給付との比較"),
    "consumption-tax-cut-business-burden": ("jigyousha", "事業者の負担"),
}


# bike-blue-ticketの論点ごとの図解画像（consumption-tax-cutと同じ形）。「その他」は図解を持たない。
BIKE_LANDING_IMAGE_BY_ISSUE_ID = {
    "bike-blue-ticket-enforcement-support": ("torishimari", "取締り強化賛成"),
    "bike-blue-ticket-infrastructure-first": ("infra", "インフラ整備優先"),
    "bike-blue-ticket-road-safety": ("sharido", "車道走行への不安"),
    "bike-blue-ticket-license-requirement": ("menkyo", "免許制要求"),
    "bike-blue-ticket-rule-ambiguity": ("ambiguity", "ルール曖昧・不信"),
}


def _landing_image_html(topic: str, slug: str, label: str) -> str:
    path = f"images/topics/{topic}/{topic}-infographic-wide-{slug}.webp"
    return (
        f'<div class="explainer-card landing-image" data-img="{path}" data-alt="{label}">'
        f'<img src="{path}" alt="論点図解：{label}" loading="lazy"></div>'
    )


def _inject_landing_images(block: str, data: dict, topic: str, images: dict, js_prefix: str) -> str:
    """論点ごとの図解画像を、山なみ再生成後のブロックへ差し戻す。

    render_planet()（build_planet_page_preview.py、10テーマ共通）はテーマ専用の画像を
    知らないため、refresh()がPLANET_SECTION全体を作り直すたびにこの画像が消える。
    無JS用フォールバック（#fallback配下のlanding-panel）と、実際の操作画面を作るJS
    （drawPanel相当）の両方に差し戻す。もとは「このテーマを読み解く、N つの論点」
    という別建てのカードだったが、山なみの各論点パネルと内容が重複するため、起承転結の
    再構成（課題69、fukushutoのapply_landing_images()と同型）でこちらへ一本化した。
    js_prefix はJS変数名の接頭辞（既存ページの出力を変えないためテーマごとに固定）。
    """
    def add_to_fallback(m: re.Match) -> str:
        issue_id, heading = m.group(1), m.group(0)
        found = images.get(issue_id)
        if not found:
            return heading
        slug, label = found
        return heading + _landing_image_html(topic, slug, label)

    block, n = re.subn(
        rf'<section class="landing-panel" id="fb-({re.escape(topic)}-[a-z-]+)"[^>]*>\s*<h2>[^<]*</h2>',
        add_to_fallback,
        block,
    )
    expected_panels = len(data["issues"])
    if n != expected_panels:
        raise SystemExit(
            f"論点画像(フォールバック側): landing-panelが{expected_panels}件必要です（{n}件、{topic}）"
        )

    slug_map_js = ",".join(f'"{k}":"{v[0]}"' for k, v in images.items())
    v_slug, v_path, v_html = f"{js_prefix}ImgSlug", f"{js_prefix}ImgPath", f"{js_prefix}ImgHtml"
    old_draw_panel_head = (
        "  const it = issues[st.landed];\n"
        "  const n = m.counts[it.id];\n"
        "  let h = '<h2>'+it.icon+' '+it.label+'</h2>'"
    )
    # 画像パスは先に1つの変数へ組み立ててから src / data-img へ埋め込む。
    # "images/…-" のように末尾が結合前で切れた断片を直接 src="…" の形で書くと、
    # validate_theme_seo.py の参照チェック（href|src="…"の正規表現）が実在しない
    # パスとして誤検知する（fukushutoの起承転結の再構成で発見、課題69）。
    new_draw_panel_head = (
        "  const it = issues[st.landed];\n"
        "  const n = m.counts[it.id];\n"
        f"  const {v_slug} = {{" + slug_map_js + "}[it.id];\n"
        f"  const {v_path} = {v_slug} ? ('images/topics/{topic}/{topic}-infographic-wide-'+{v_slug}+'.webp') : '';\n"
        f"  const {v_html} = {v_slug} ? ('<div class=\"explainer-card landing-image\" data-img=\"'+{v_path}+'\" data-alt=\"'+it.label+'\">'\n"
        f"    +'<img src=\"'+{v_path}+'\" alt=\"論点図解：'+it.label+'\" loading=\"lazy\"></div>') : '';\n"
        f"  let h = '<h2>'+it.icon+' '+it.label+'</h2>' + {v_html}"
    )
    if old_draw_panel_head not in block:
        raise SystemExit(f"論点画像(drawPanel側): JSテンプレートの差し込み位置が見つかりません（{topic}）")
    block = block.replace(old_draw_panel_head, new_draw_panel_head, 1)
    return block


def _inject_ctc_landing_images(block: str, data: dict) -> str:
    return _inject_landing_images(
        block, data, "consumption-tax-cut", CTC_LANDING_IMAGE_BY_ISSUE_ID, "ctc"
    )


def _inject_bike_landing_images(block: str, data: dict) -> str:
    return _inject_landing_images(
        block, data, "bike-blue-ticket", BIKE_LANDING_IMAGE_BY_ISSUE_ID, "bike"
    )


TOPIC_ENRICH = {
    "bukatsu-chiiki": _inject_bukatsu_go_cards,
    "consumption-tax-cut": _inject_ctc_landing_images,
    "bike-blue-ticket": _inject_bike_landing_images,
}
TOPIC_METHOD_TEXT = {
    "bukatsu-chiiki": _sync_bukatsu_method_text,
    "elderly-license-revocation": _sync_elderly_method_text,
    "bike-blue-ticket": _sync_bike_method_text,
    "henoko-student-accident": _sync_henoko_method_text,
}


def refresh(topic: str) -> tuple[str, str, list[str]]:
    page = ROOT / "docs" / f"{topic}-reaction-map.html"
    html = page.read_text(encoding="utf-8")
    if START not in html or END not in html:
        raise SystemExit(
            f"「{topic}」はまだ山なみ形式ではありません。"
            "初回切り替えは build_planet_page_preview.py --for-docs を使うこと"
        )
    i = html.index(START)
    j = html.index(END) + len(END)

    data = bpd.build(topic)
    cfg = bpd.yaml.safe_load((ROOT / "configs/planet" / f"{topic}.yaml").read_text())
    failures = bpd.independence_gate(data, cfg)
    data = bpd.stabilize(data)

    prototype_html = render_planet(data)
    parts = split_prototype(prototype_html)
    new_block = build_section(parts)
    enrich = TOPIC_ENRICH.get(topic)
    if enrich:
        new_block = enrich(new_block, data)

    new_html = html[:i] + new_block + html[j:]
    themes = bpd.yaml.safe_load((ROOT / "THEMES.yaml").read_text())["themes"]
    new_html = _sync_lead_and_note(new_html, topic, themes)
    method_text = TOPIC_METHOD_TEXT.get(topic)
    if method_text:
        new_html = method_text(new_html, data)
    return html, new_html, failures


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--topic", required=True)
    ap.add_argument("--for-docs", action="store_true", help="docs/ へ実際に書き込む（既定は見本のみ）")
    a = ap.parse_args()

    old_html, new_html, failures = refresh(a.topic)
    if failures and a.for_docs:
        print("独自性の検査に不合格のため docs/ へは書けません:")
        for x in failures:
            print(f"  - {x}")
        raise SystemExit(1)

    changed = new_html != old_html
    if a.for_docs:
        if changed:
            (ROOT / "docs" / f"{a.topic}-reaction-map.html").write_text(new_html, encoding="utf-8")
        print(("UPDATE" if changed else "OK") + f". Lines: {len(old_html.splitlines())} → {len(new_html.splitlines())}")
    else:
        out = ROOT / "quality/prototypes" / f"{a.topic}-section-refresh-preview.html"
        out.write_text(new_html, encoding="utf-8")
        print(f"見本を書き出しました（docs/は未変更）: {out}")
        print(("差分あり" if changed else "差分なし") + f". Lines: {len(old_html.splitlines())} → {len(new_html.splitlines())}")


if __name__ == "__main__":
    main()
