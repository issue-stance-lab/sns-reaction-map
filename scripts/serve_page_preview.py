#!/usr/bin/env python3
"""ページ見本（山なみ版）を、スマホの実機から開ける形で一時的に配信する。

課題54 段階9 のオーナー確認用。docs/ には一切書き込まない。
docs/ の資産（CSS・JS・画像）へのシンボリックリンクを張った一時ディレクトリを作り、
そこへ --for-docs 付きで組み立てた見本を置いて配信する。

GA4 の測定IDは既定で差し替える。確認のアクセスが実サイトの記録に混ざらないようにするため。

    python3 scripts/serve_page_preview.py

止めるときは Control+C。
"""
from __future__ import annotations

import argparse
import functools
import http.server
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
TOPICS = ("bukatsu-chiiki", "bike-blue-ticket", "elderly-license-revocation")
REAL_GA4 = "G-K10S4YCZFH"
DUMMY_GA4 = "G-0000000000"


def lan_addresses() -> list[str]:
    addrs = []
    for cmd in (["ipconfig", "getifaddr", "en0"], ["ipconfig", "getifaddr", "en1"]):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout.strip()
        except Exception:
            out = ""
        if out and out not in addrs:
            addrs.append(out)
    for ts in ("/Applications/Tailscale.app/Contents/MacOS/Tailscale", "tailscale"):
        try:
            out = subprocess.run([ts, "ip", "-4"], capture_output=True, text=True, timeout=5).stdout.strip()
        except Exception:
            continue
        for line in out.splitlines():
            line = line.strip()
            if line and line not in addrs:
                addrs.append(line)
        if out:
            break
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip not in addrs:
            addrs.append(ip)
    except Exception:
        pass
    return addrs


def build(stage: Path, topics: list[str], keep_ga4: bool) -> None:
    for entry in sorted(DOCS.iterdir()):
        link = stage / entry.name
        if not link.exists():
            link.symlink_to(entry)
    for topic in topics:
        out = stage / f"preview-{topic}.html"
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build_planet_page_preview.py"),
             "--topic", topic, "--for-docs", "--out", str(out)],
            check=True, cwd=str(ROOT), stdout=subprocess.DEVNULL,
        )
        if not keep_ga4:
            html = out.read_text(encoding="utf-8")
            out.write_text(html.replace(REAL_GA4, DUMMY_GA4), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8791)
    ap.add_argument("--topic", action="append", choices=TOPICS, help="既定は3テーマすべて")
    ap.add_argument("--keep-ga4", action="store_true",
                    help="GA4の測定IDを差し替えない（実サイトの記録に混ざるので通常は使わない）")
    args = ap.parse_args()

    topics = args.topic or list(TOPICS)
    stage = Path(tempfile.mkdtemp(prefix="isa-page-preview-"))
    try:
        build(stage, topics, args.keep_ga4)
        print(f"組み立て先: {stage}", flush=True)
        print(f"GA4の測定ID: {'そのまま（実サイトの記録に混ざる）' if args.keep_ga4 else DUMMY_GA4 + ' に差し替え済み'}", flush=True)
        print(flush=True)
        print("スマホの実機で開くURL（Macと同じWi-Fi、またはTailscale経由）:", flush=True)
        for addr in lan_addresses():
            for topic in topics:
                print(f"  http://{addr}:{args.port}/preview-{topic}.html", flush=True)
        print(flush=True)
        print("止めるときは Control+C", flush=True)
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(stage))
        with http.server.ThreadingHTTPServer(("0.0.0.0", args.port), handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n止めました。")
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
