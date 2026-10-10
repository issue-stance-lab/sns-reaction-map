#!/usr/bin/env python3
"""Render the reviewed redesign after the existing verified article build.

Creates a self-contained preview or release bundle; never overwrites docs.
The legacy builder remains the data/editorial source until rollout is approved.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from bs4 import BeautifulSoup, Comment

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "scripts/bukatsu_redesign"
PAGE = "bukatsu-chiiki-reaction-map.html"
PRINT_PAGE = "bukatsu-chiiki-classroom.html"
REVIEW_INPUTS = (
    "data/bukatsu-chiiki_teacher-reread.json",
    "data/bukatsu-chiiki_cost-receiver-reread.json",
    "data/verification/bukatsu-chiiki-plan-child-subissues.json",
)
# These source sections supply the prose frozen in the reviewed editorial template.
EDITORIAL_SELECTORS = (
    ".classroom-section", "#bukatsu-background", "#detail-data",
    ".sources-pane", ".post-link",
)

def fingerprint(source, root=ROOT):
    soup = BeautifulSoup(source, "html.parser")
    parts = [str(n) for sel in EDITORIAL_SELECTORS for n in soup.select(sel)]
    parts += [(root / path).read_text() for path in REVIEW_INPUTS]
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()

def finalize(markup, source, mode):
    s = BeautifulSoup(markup, "html.parser")
    src = BeautifulSoup(source, "html.parser")
    # The prototype had two descriptions; retain the canonical source metadata only.
    for name in ("description",):
        nodes = s.select('meta[name="' + name + '"]')
        for node in nodes[:-1]:
            node.decompose()
    s.title.string = src.title.get_text()
    s.head.append(s.new_tag("meta",attrs={"name":"bukatsu-layout","content":"redesign-v1"}))
    for node in s.select(".preview"):
        node.decompose()
    banner = s.new_tag("div", attrs={"class": "preview"})
    if mode == "preview":
        banner.string = "公開前の確認用ページ"
        s.body.insert(0, banner)
    else:
        for node in s.select('meta[name="robots"]'):
            node.decompose()
        # Preserve the exact production integrations and their existing host restrictions.
        for start, end in (("GA_TAG_START", "GA_TAG_END"), ("ADSENSE_TAG_START", "ADSENSE_TAG_END")):
            match = re.search(r"<!-- " + start + r" -->.*?<!-- " + end + r" -->", source, re.S)
            if not match:
                raise ValueError("Missing protected integration: " + start)
            s.head.append(BeautifulSoup(match.group(), "html.parser"))
    for node in s.select(".issue-heading .eyebrow"):
        node["class"] = node.get("class", []) + ["redesign-issue-count"]
    for node in s.select(".reason-detail>.eyebrow"):
        node["class"] = node.get("class", []) + ["redesign-reason-count"]
    for node in s.select(".reason-index>.fine,.reason-menu>.fine"):
        if "再読済み" in node.get_text():
            node["class"] = node.get("class", []) + ["redesign-coverage"]
    # Preserve the public data contract used by the existing publication validators.
    # It contains aggregate/verified public information only, copied from the public source.
    contract = src.select_one("#planet-data")
    if contract is None:
        raise ValueError("Missing verified PLANET_DATA")
    s.body.append(BeautifulSoup(str(contract), "html.parser"))
    caution = src.select_one("#caution")
    if caution is None:
        raise ValueError("Missing research conditions")
    map_section = s.select_one("#map")
    map_section.insert_before(Comment(" PLANET_SECTION_START "))
    overview = map_section.select_one(".overview")
    conditions = BeautifulSoup(str(caution), "html.parser")
    overview.insert_before(Comment(" RESEARCH_CONDITIONS_START "))
    overview.insert_before(conditions)
    overview.insert_before(Comment(" RESEARCH_CONDITIONS_END "))
    s.select_one("#reading").insert_after(Comment(" PLANET_SECTION_END "))
    # Same public config and client as the existing site; activate only at its canonical host.
    store = s.select_one('script[src="assets/vote-store.js"]')
    store["src"] = "vote-store.js"
    config = s.new_tag("script", src="vote-config.js")
    guard = s.new_tag("script")
    guard.string = ("window.SNS_REDESIGN_PRODUCTION=" +
                    ("location.hostname==='sns-reaction-map.jp'" if mode == "release" else "false") +
                    ";if(!window.SNS_REDESIGN_PRODUCTION)window.SNS_VOTE_CONFIG={};")
    store.insert_before(config)
    store.insert_before(guard)
    for script in s.select("script:not([src])"):
        if script.string and "sns_vote_preview_" in script.string:
            script.string = script.string.replace(
                "'sns_vote_preview_'+TOPIC+'_my'",
                "(window.SNS_REDESIGN_PRODUCTION?'sns_vote_':'sns_vote_preview_')+TOPIC+'_my'",
            )
    for a in s.select('a[href="classroom-print.html"]'):
        a["href"] = PRINT_PAGE
    full_link=s.new_tag('a',href='bukatsu-chiiki-full.html',attrs={'class':'full-reading-link'})
    full_link.string='全文・印刷版'
    s.select_one('.contents').append(full_link)
    fallback=s.select_one('noscript')
    if fallback:
        fallback.clear()
        note=s.new_tag('p');note.string='論点を切り替えられない場合は、全文・印刷版ですべての意見と資料を読めます。'
        link=s.new_tag('a',href='bukatsu-chiiki-full.html');link.string='全文・印刷版を開く'
        fallback.append(note);fallback.append(link)
    # Keep historical links working without restoring the removed UI flow.
    aliases = {"planet-block": "map", "stance-map-section": "map", "issue-cards": "reading",
               "classroom-title": "classroom", "detail-data": "method",
               "bukatsu-background": "background", "editorial": "editorial-notes",
               "ocean": "source-only", "bukatsu-chiiki-audit": "reading"}
    for issue in s.select(".issue-panel"):
        aliases["issue-" + issue["id"]] = issue["id"]
        aliases["fb-" + issue["id"]] = issue["id"]
    alias_script = s.new_tag("script")
    alias_script.string = """(()=>{const aliases=""" + json.dumps(aliases) + """;
function resolve(){const target=aliases[location.hash.slice(1)];if(target)location.replace('#'+target);}
addEventListener('hashchange',resolve);resolve();})();"""
    s.body.append(alias_script)
    text = str(s).replace("この試作には掲載していません。", "このページには掲載していません。")
    text = text.replace("現行ページの論点図解。", "この論点の図解。")
    # Do not call this UI "current" once it is itself the published page.
    text = text.replace("現行ページの確認事項を読む", "地域の確認事項を読む")
    text = text.replace("各資料の確認時点は、現行ページの記載を引き継いでいます。", "各資料の確認時点もあわせて記載しています。")
    text = text.replace('7<small>つの論点</small>', '6<small>つの論点＋その他</small>')
    text = text.replace('7つの論点を見渡す', '論点の全体像を見渡す')
    text = text.replace('7つの論点の山並み', '6つの論点とその他の山並み')
    text = text.replace('7論点の山並み', '6つの論点とその他の山並み')
    return text

def build(source_page, output_dir, mode="preview", root=ROOT):
    source_page, output_dir = Path(source_page).resolve(), Path(output_dir).resolve()
    if output_dir == (root / "docs").resolve() or (root / "docs").resolve() in output_dir.parents:
        raise ValueError("公開先docsへ直接出力できません。公開候補用の別フォルダを指定してください。")
    source = source_page.read_text()
    resources = root / "scripts/bukatsu_redesign"
    review = json.loads((resources / "editorial-review.json").read_text())
    if fingerprint(source, root) != review["editorial_sha256"]:
        raise ValueError("参照本文か理由分類が変わりました。説明・引用・資料を確認し、editorial-review.jsonを更新してください。出力は変更していません。")
    with tempfile.TemporaryDirectory(prefix="bukatsu-redesign-") as temp:
        stage = Path(temp)
        shutil.copytree(resources, stage / ".build", ignore=shutil.ignore_patterns("__pycache__"))
        (stage / "evidence").mkdir()
        env = dict(os.environ, BUKATSU_BUILD_ROOT=str(stage), BUKATSU_REPO_ROOT=str(root))
        subprocess.run([sys.executable, str(stage / ".build/build.py"),
                        "--source-page", str(source_page)], check=True, env=env, cwd=root)
        page = finalize((stage / "index.html").read_text(), source, mode)
        (stage / PAGE).write_text(page)
        from scripts.bukatsu_redesign_readable import READ_PAGE, readable
        (stage / READ_PAGE).write_text(readable(page, PAGE))
        print_page = (stage / "classroom-print.html").read_text().replace("index.html#", PAGE + "#").replace(" — ", "：")
        (stage / PRINT_PAGE).write_text(print_page)
        for name in ("vote-store.js", "vote-config.js"):
            shutil.copy2(root / "docs" / name, stage / name)
        # Preview and release use the same body, graph data, voting identifiers and assets.
        manifest = {"mode": mode, "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                    "files": {}}
        files = [stage / PAGE, stage / PRINT_PAGE, stage / READ_PAGE, stage / "vote-store.js", stage / "vote-config.js",
                 *sorted((stage / "images").rglob("*")), *sorted((stage / "evidence").glob("*.json"))]
        output_dir.mkdir(parents=True, exist_ok=True)
        for path in files:
            if not path.is_file():
                continue
            relative = path.relative_to(stage)
            target = output_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(target.suffix + ".tmp")
            shutil.copy2(path, temporary)
            temporary.replace(target)
            manifest["files"][str(relative)] = hashlib.sha256(path.read_bytes()).hexdigest()
        (output_dir / "build-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-page", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("preview", "release"), default="preview")
    args = parser.parse_args()
    if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
    from scripts.bukatsu_layout import source_for_refresh
    result = build(args.source_page or source_for_refresh(ROOT), args.output_dir, args.mode)
    print(f"Built {len(result['files'])} files ({args.mode}); no deployment performed.")

if __name__ == "__main__":
    main()
