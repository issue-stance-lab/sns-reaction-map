#!/usr/bin/env python3
"""Regression tests for protecting the current top page from legacy generation."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INDEX = PROJECT_ROOT / "docs" / "index.html"
RUN_PIPELINE = PROJECT_ROOT / "scripts" / "run_pipeline.py"
BUILD_PORTAL = PROJECT_ROOT / "scripts" / "build_site_portal.py"

CURRENT_THEME_PAGES = (
    "ai-copyright-reaction-map.html",
    "bike-blue-ticket-reaction-map.html",
    "bukatsu-chiiki-reaction-map.html",
    "constitutional-amendment-reaction-map.html",
    "consumption-tax-cut-reaction-map.html",
    "elderly-license-revocation-reaction-map.html",
    "fukushuto-reaction-map.html",
    "henoko-student-accident-reaction-map.html",
    "koshitsu-tenpakai-reaction-map.html",
    "school-nickname-ban-reaction-map.html",
)


def index_digest() -> str:
    return hashlib.sha256(INDEX.read_bytes()).hexdigest()


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class PortalOverwriteSafetyTest(unittest.TestCase):
    def test_pipeline_dry_run_does_not_schedule_legacy_portal(self) -> None:
        before = index_digest()
        result = run(
            str(RUN_PIPELINE),
            "--topic",
            "ai-copyright",
            "--skip-fetch",
            "--skip-classify",
            "--dry-run",
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("build_site_portal.py", result.stdout + result.stderr)
        self.assertEqual(index_digest(), before)

    def test_pipeline_execution_does_not_change_current_top_page(self) -> None:
        before = index_digest()
        result = run(
            str(RUN_PIPELINE),
            "--topic",
            "ai-copyright",
            "--skip-fetch",
            "--skip-classify",
            "--skip-build",
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(index_digest(), before)

    def test_legacy_portal_rejects_every_spelling_of_current_top_page(self) -> None:
        before = index_digest()
        protected_outputs = (
            "docs/index.html",
            "./docs/index.html",
            str(INDEX),
        )

        for output in protected_outputs:
            with self.subTest(output=output):
                result = run(str(BUILD_PORTAL), "--output", output)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("protected current top page", result.stderr)
                self.assertEqual(index_digest(), before)

    def test_legacy_portal_can_generate_explicit_tmp_preview(self) -> None:
        before = index_digest()
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp_dir:
            preview = Path(tmp_dir) / "legacy-portal-preview.html"
            result = run(str(BUILD_PORTAL), "--output", str(preview))

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(preview.is_file())
            self.assertIn("<!doctype html>", preview.read_text(encoding="utf-8").lower())
        self.assertEqual(index_digest(), before)

    def test_current_top_page_keeps_design_and_all_eleven_themes(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        self.assertIn("home-story.css", html)
        self.assertIn('id="hero-map"', html)
        self.assertIn("公開中のテーマ</", html)
        self.assertIn("<strong>10</strong>", html)
        for page in CURRENT_THEME_PAGES:
            with self.subTest(page=page):
                self.assertIn(f'href="{page}"', html)


if __name__ == "__main__":
    unittest.main()
