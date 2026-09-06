#!/usr/bin/env python3
"""Build a single, private repair preview; never promote or mutate its source tree.

Input plan binds every original and reviewed candidate to its SHA-256. This is
a repair-only reproducer, not the general multi-run promotion API of task 59.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import importlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

METADATA = {"fetched_at", "query", "source"}
ADAPTERS = {
    "ai-copyright": "ai_copyright", "elderly-license-revocation": "elderly",
    "takaichi": "takaichi", "school-nickname-ban": "nickname",
    "henoko-student-accident": "henoko",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def source_state(root, themes):
    return {t: sha(root / m["sample_file"]) for t, m in themes.items()}


def inspect_candidate(original, candidate):
    old, new = json.loads(original.read_text()), json.loads(candidate.read_text())
    index = lambda rows: {str(r["tweet_id"]): r for r in rows}
    a, b = index(old), index(new)
    assert len(a) == len(old) and len(b) == len(new), "duplicate IDs"
    assert set(a) <= set(b), "existing IDs removed"
    changed = 0
    for key, row in a.items():
        after = b[key]
        assert {k: v for k, v in row.items() if k not in METADATA} == {
            k: v for k, v in after.items() if k not in METADATA
        }, "existing body/classification changed"
        for field in METADATA:
            if row.get(field):
                assert row[field] == after.get(field), "existing metadata overwritten"
        changed += row != after
    return {"before": len(old), "after": len(new), "added": len(b) - len(a),
            "metadata_repaired": changed}


def snapshot(root):
    paths = [root / "THEMES.yaml", root / "DATA_SHEET.md"]
    for folder in ("docs", "data/public", "data/verification", "configs"):
        paths.extend(p for p in (root / folder).rglob("*") if p.is_file())
    return {str(p.relative_to(root)): sha(p) for p in paths if p.is_file()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--plan", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    assert not out.exists(), "use a new output directory"
    assert out != root and root not in out.parents or ".staging" in out.parts
    plan = json.loads(args.plan.read_text())
    themes = yaml.safe_load((root / "THEMES.yaml").read_text())["themes"]
    before_sources, before_files = source_state(root, themes), snapshot(root)
    assert before_sources == plan["baseline_sha256"], "source tree changed"
    out.mkdir(parents=True)
    preview = out / "preview"
    shutil.copytree(root, preview, ignore=shutil.ignore_patterns(
        ".git", ".staging", "node_modules", "__pycache__"))
    logs = out / "logs"
    logs.mkdir()
    commands = []

    def run(label, command, required=True):
        p = subprocess.run(command, cwd=preview, capture_output=True, text=True)
        (logs / (label + ".log")).write_text(p.stdout + p.stderr)
        commands.append({"label": label, "command": command, "exit": p.returncode})
        dump(out / "commands.json", commands)
        if required and p.returncode:
            raise RuntimeError(f"{label} failed: see {logs / (label + '.log')}")
        return p.returncode

    def py(label, script, *args, required=True):
        return run(label, [sys.executable, script, *args], required)

    sys.path.insert(0, str(root / "scripts"))
    from refresh_topic import _replace_theme_fields
    summaries = {}
    targets = plan["themes"]
    for topic, item in targets.items():
        assert topic in ADAPTERS
        candidate = Path(item["candidate"])
        assert sha(candidate) == item["candidate_sha256"], topic
        original = root / themes[topic]["sample_file"]
        assert sha(original) == item["original_sha256"], topic
        summaries[topic] = inspect_candidate(original, candidate)
        shutil.copy2(candidate, preview / themes[topic]["sample_file"])
        fields = item.get("period_fields", {})
        assert set(fields) <= {"sample_period", "sample_period_source"}
        registry = preview / "THEMES.yaml"
        text = registry.read_text()
        # The ordinary collection helper inserts new fields below refresh_at;
        # unlisted Takaichi has no publication schedule. Anchor provenance to
        # its existing period instead, without inventing a refresh date.
        if "sample_period_source" in fields and "sample_period_source" not in themes[topic]:
            pattern = rf"(^  {re.escape(topic)}:\n.*?^    sample_period:[^\n]*\n)"
            text, n = re.subn(pattern, lambda m: m[1] + "    sample_period_source: " +
                              fields["sample_period_source"] + "\n", text, count=1, flags=re.M | re.S)
            assert n == 1, topic
        registry.write_text(_replace_theme_fields(text, topic, fields))
        if themes[topic].get("verification_file"):
            from verification_data import write_verification_file
            write_verification_file(preview / themes[topic]["sample_file"],
                                    preview / themes[topic]["verification_file"])
    dump(out / "source-checks.json", summaries)
    shutil.copy2(args.plan, out / "input-plan.json")
    # Reviewed source-template fixes travel with the same frozen candidate.
    # Updating this source avoids a one-off HTML edit that the next build loses.
    if plan.get("seo_text_replacements"):
        path = preview / "configs/theme-seo.json"
        text = path.read_text()
        for replacement in plan["seo_text_replacements"]:
            assert text.count(replacement["old"]) == 1
            text = text.replace(replacement["old"], replacement["new"], 1)
        path.write_text(text)

    # All repaired canonical inputs are present before any shared aggregate is built.
    py("registry", "scripts/build_public_registry.py", "--all")
    py("registry-private", "scripts/verify_public_registry.py", "--against-private")
    build_commands = []
    for topic in ("school-nickname-ban", "henoko-student-accident"):
        if topic not in targets:
            continue
        page = themes[topic]["html"]
        script = "scripts/build_nickname_arena.py" if topic == "school-nickname-ban" else "scripts/build_henoko_arena.py"
        cmd = [sys.executable, script, "--input", themes[topic]["sample_file"],
               "--html-template", page, "--output-html", page]
        if topic == "henoko-student-accident":
            cmd += ["--output-data", "docs/henoko-arena-data.js"]
        # Repairing an old wave is not a new collection: do not call _apply_tide.
        run(topic + "-build1", cmd)
        first = snapshot(preview)
        run(topic + "-build2", cmd)
        assert first == snapshot(preview), f"non-idempotent builder: {topic}"
        build_commands.append(cmd)

    for topic in targets:
        adapter = importlib.import_module("refresh_adapters." + ADAPTERS[topic])
        if hasattr(adapter, "finalize"):
            run(topic + "-finalize", [sys.executable, "-c",
                "import sys;sys.path.insert(0,'scripts');from pathlib import Path;from refresh_adapters." + ADAPTERS[topic] +
                " import finalize;finalize(Path.cwd()," + repr(str(themes[topic]["updated_at"])) + ")"])
        py(topic + "-counts", "scripts/sync_issue_counts.py", topic)

    py("trust", "scripts/seo/apply_theme_trust.py")
    # The legacy Takaichi builder does not refresh its research-period block.
    # Render the reviewed period from candidate metadata; keep its review claim.
    from x_embed import period_label
    current_themes = yaml.safe_load((preview / "THEMES.yaml").read_text())["themes"]
    for topic, item in targets.items():
        if not item.get("period_fields"):
            continue
        path = preview / themes[topic]["html"]
        page = path.read_text()
        period = html.escape(period_label(str(current_themes[topic]["sample_period"])))
        page, n = re.subn(r"(取得期間: )([^<]*?)(／)",
                          lambda m: m[1] + period + m[3], page)
        assert n == 1, (topic, "research period anchor", n)
        if item.get("period_note"):
            note = '<p class="repair-period-note" style="max-width:1000px;margin:8px auto 0;font-size:13px;line-height:1.8;">' + html.escape(item["period_note"]) + '</p>'
            page, n = re.subn(r'(<aside class="research-conditions".*?)(</aside>)',
                              lambda m: m[1] + note + "\n" + m[2], page, flags=re.S)
            assert n == 1, (topic, "research note anchor", n)
        path.write_text(page)
    py("portal", "scripts/sync_portal_stats.py")
    py("sitemap", "scripts/seo/generate_seo_assets.py", "--site-url", "https://sns-reaction-map.jp/")
    py("period", "scripts/verify_sample_periods.py", "--generate", required=False)
    py("data-sheet", "scripts/build_data_sheet.py")

    final = snapshot(preview)
    changes = {f: {"before": before_files.get(f), "after": h}
               for f, h in final.items() if h != before_files.get(f)}
    # Current collection/publication dates and every unrelated canonical are fixed.
    after_meta = yaml.safe_load((preview / "THEMES.yaml").read_text())["themes"]
    for topic, meta in themes.items():
        ignored = {"sample_period", "sample_period_source"} if topic in targets else set()
        assert {k:v for k,v in meta.items() if k not in ignored} == {
            k:v for k,v in after_meta[topic].items() if k not in ignored}, topic
        if topic not in targets:
            assert sha(preview / meta["sample_file"]) == before_sources[topic]
    protection = {}
    for topic in targets:
        rel = themes[topic]["html"]
        a, b = (root / rel).read_text(), (preview / rel).read_text()
        adapter = importlib.import_module("refresh_adapters." + ADAPTERS[topic])
        assert adapter.vote_fingerprint(a) == adapter.vote_fingerprint(b), topic
        for token in ("G-K10S4YCZFH", "ca-pub-2542211932832864", "vote-store.js"):
            assert a.count(token) == b.count(token), (topic, token)
        # Preserve exact canonical/OGP/robots tags, not merely presence.
        pattern = r'<(?:link\b[^>]*rel=[\"\']canonical[\"\'][^>]*|meta\b[^>]*(?:property=[\"\']og:[^\"\']+[\"\']|name=[\"\']robots[\"\'])[^>]*)>'
        assert re.findall(pattern, a) == re.findall(pattern, b), topic
        protection[topic] = "vote / analytics / OGP / canonical / robots unchanged"
    dump(out / "protection-checks.json", protection)
    for label, command in (
        ("pages", ["scripts/verify_theme_page.py"]),
        ("numbers", ["scripts/verify_number_provenance.py"]),
        ("top", ["scripts/verify_top_page.py"]),
        ("seo", ["scripts/seo/validate_theme_seo.py"]),
        ("tone", ["scripts/verify_ai_tone.py"]),
        ("registry-final", ["scripts/verify_public_registry.py", "--against-private"]),
    ):
        py(label, *command, required=False)
    assert source_state(root, themes) == before_sources and snapshot(root) == before_files
    dump(out / "manifest.json", {"kind": "repair-preview", "base_commit": plan["base_commit"],
        "generator_sha256": sha(Path(__file__)),
        "code_sha256": {str(p.relative_to(preview)): sha(p)
                        for p in (preview / "scripts").rglob("*")
                        if p.is_file() and p.suffix in {".py", ".js", ".mjs"}},
        "quality_status": "pending_independent_review", "themes": summaries,
        "canonical_files": {themes[t]["sample_file"]: {
            "before": before_sources[t], "after": sha(preview / themes[t]["sample_file"])
        } for t in targets},
        "inputs": targets, "files": changes, "checks": commands,
        "note": "Private preview only. No collection dates advanced. No promotion token."})
    print(json.dumps({"preview": str(preview), "counts": summaries,
                      "changed_files": len(changes), "failed_checks": [c["label"] for c in commands if c["exit"]]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
