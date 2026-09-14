"""Publish the approved candidate and fail closed on unreviewed future inputs."""
from pathlib import Path
import hashlib
import json
import re
import yaml

ROOT=Path(__file__).resolve().parents[1]
TOPIC='koshitsu-tenpakai'
BASE=ROOT/'quality/candidates'/TOPIC

def verify_inputs(source=None):
    manifest=json.loads((BASE/'manifest.json').read_text())
    themes=yaml.safe_load((ROOT/'THEMES.yaml').read_text())
    canonical=ROOT/themes['themes'][TOPIC]['sample_file']
    if hashlib.sha256(canonical.read_bytes()).hexdigest()!=manifest['private_candidate_sha256']:
        raise ValueError('皇室の正典が承認候補と異なります。追加・変更分の再読と監査が必要です')
    if source and json.loads(Path(source).read_text())!=json.loads(canonical.read_text()):
        raise ValueError('皇室の更新候補に未監査の変更があります')
    expected=json.loads((BASE/'inputs/data/public/themes'/f'{TOPIC}.json').read_text())
    actual=json.loads((ROOT/'data/public/themes'/f'{TOPIC}.json').read_text())
    # Publication metadata can change; all semantic aggregates must match.
    for field in ('opinion_count','collected_count','issues','stances'):
        if actual.get(field)!=expected.get(field):raise ValueError('皇室の公開集計が監査候補と異なります: '+field)


def render():
    verify_inputs()
    text=(ROOT/'quality/prototypes/koshitsu-tenpakai-page-preview.html').read_text()
    original=(BASE/'original-page.html').read_text()
    text=re.sub(r'<aside\b[^>]*(?:class="candidate-note"|id="page-preview-status")[^>]*>.*?</aside>','',text,flags=re.S)
    text=re.sub(r'<meta\b[^>]*name="robots"[^>]*>','',text)
    text=text.replace('../../docs/','')
    for tag in ('GA_TAG','ADSENSE_TAG'):
        block=re.search('<!-- '+tag+'_START -->.*?<!-- '+tag+'_END -->',original,re.S)[0]
        text=re.sub('<!-- '+tag+'_START -->.*?<!-- '+tag+'_END -->',lambda m:block,text,flags=re.S)
        if block not in text:text=text.replace('</head>',block+'\n</head>',1)
    text=text.replace('<script>window.SNS_VOTE_CONFIG={};</script>','<script src="vote-config.js?v=1"></script>')
    text=text.replace("var STORAGE_KEY='sns_preview_vote_'","var STORAGE_KEY='sns_vote_'")
    text=text.replace('この確認用ページの回答はブラウザー内だけに保存されます。本番へ送信されません。','回答と、24時間の重複防止用に一方向変換した接続元情報をサーバーに保存します。')
    text=text.replace('従来の非意見323件','従来の情報共有などの投稿323件')
    text=text.replace('追加分の確認はAI編集者によるもので、別の担当者による監査はまだ行っていません。','追加分はAI編集者が確認し、公開前に別のAI担当者が本文と判断根拠を照合しました。')
    from refresh_adapters.koshitsu import vote_fingerprint
    assert vote_fingerprint(original)==vote_fingerprint(text)
    assert 'sns_preview_vote_' not in text and 'noindex' not in text
    return text


def build(check=False,source=None,output=None):
    verify_inputs(source)
    out=Path(output) if output else ROOT/'docs'/f'{TOPIC}-reaction-map.html'
    text=render();changed=not out.exists() or out.read_text()!=text
    if not check:out.write_text(text)
    return ['皇室典範：監査済み山なみを生成（未監査入力は拒否）'],changed
