#!/usr/bin/env python3
"""Reproducible presentation pass. Leaves source text, datasets and controls intact."""
from pathlib import Path
import json
import re
import shutil

ROOT=Path(__file__).resolve().parents[1]
THEMES=('ai-copyright','bike-blue-ticket','constitutional-amendment','elderly-license-revocation','school-nickname-ban','henoko-student-accident','fukushuto','koshitsu-tenpakai','consumption-tax-cut')
HEAD='<!-- THEME_DESIGN_START -->\n<link rel="stylesheet" href="theme-design.css?v=1">\n<script defer src="theme-design.js?v=1"></script>\n<!-- THEME_DESIGN_END -->'

def transform(text,slug):
    text=re.sub(r'<!-- THEME_DESIGN_START -->.*?<!-- THEME_DESIGN_END -->\s*','',text,flags=re.S)
    text=text.replace('</head>',HEAD+'\n</head>',1)
    def body(m):
        tag=m[0]
        tag=re.sub(r' data-renew-theme="[^"]*"','',tag)
        if re.search(r'class="',tag):
            tag=re.sub(r'class="([^"]*)"',lambda c:'class="'+ ' '.join(dict.fromkeys(c[1].split()+['site-renewal']))+'"',tag,count=1)
        else:tag=tag[:-1]+' class="site-renewal">'
        return tag[:-1]+f' data-renew-theme="{slug}">'
    text=re.sub(r'<body\b[^>]*>',body,text,count=1)
    text=re.sub(r'<!-- THEME_COUNT_START -->.*?<!-- THEME_COUNT_END -->','',text,flags=re.S)
    if slug!='henoko-student-accident':
        match=re.search(r'window.PLANET_DATA\s*=\s*(\{.*?\});',text,re.S)
        if match:
            data=json.loads(match[1]); count=data['totals']['opinions']
            stamp=f'<!-- THEME_COUNT_START --><aside class="renew-count" aria-label="分析したSNSの意見 {count}件"><span>SNSの意見</span><strong>{count:,}<small>件</small></strong><span>収集した投稿のうち、意見を含むもの</span></aside><!-- THEME_COUNT_END -->'
            text=re.sub(r'(<h1\b[^>]*>.*?</h1>)',lambda m:stamp+m[0],text,count=1,flags=re.S)
    return text

def finish(root):
    root=Path(root); targets={}
    config=root/"configs/theme-design.json"
    if not config.exists() or not json.loads(config.read_text()).get("enabled"):return targets
    for ext in ('css','js'):
        dst=root/'docs'/f'theme-design.{ext}'
        shutil.copyfile(root/'scripts/theme_design'/f'site.{ext}',dst)
        targets[dst.relative_to(root)]=dst
    for slug in THEMES:
        p=root/'docs'/f'{slug}-reaction-map.html'
        if p.exists():
            old=p.read_text(); new=transform(old,slug)
            if old!=new:p.write_text(new)
            targets[p.relative_to(root)]=p
    return targets
if __name__=='__main__':
    finish(ROOT)
