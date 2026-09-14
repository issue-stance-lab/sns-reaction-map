#!/usr/bin/env python3
"""課題54の皇室典範・非公開候補を、隔離した集計入力から組み立てる。

--stage-root は候補の THEMES/configs/data/scripts を持つ非公開作業領域。
公開中の docs/・THEMES.yaml・公開JSONを書き換えない。独自性検査は省略しない。
"""
from __future__ import annotations
import argparse
import hashlib
import html as h
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPIC = 'koshitsu-tenpakai'
sys.path.insert(0, str(ROOT / 'scripts'))
from build_planet_page_preview import cut_block
from refresh_adapters.koshitsu import vote_fingerprint
from koshitsu_issue_media import restore_issue_media
from koshitsu_background_detail import expand_background


def prepare_template(source: str, public: dict) -> str:
    text = source
    for iid in ('stance-map-section', 'explainer-section', 'koshitsu-audit', 'detail-data'):
        match = re.search(r'<section\b[^>]*\bid="'+iid+r'"[^>]*>', text)
        if match:
            text, _ = cut_block(text, match.group(0), 'section')
    for cls in ('update-dashboard', 'panel conflict-panel'):
        while True:
            match = re.search(r'<section\b[^>]*\bclass="'+cls+r'"[^>]*>', text)
            if not match: break
            text, _ = cut_block(text, match.group(0), 'section')
    text, _ = cut_block(text, '<div class="thirty-summary"', 'div')
    text = re.sub(r'<script\b[^>]*>.*?</script>',
                  lambda m: '' if any(token in m[0] for token in ('const SM_RAW', "const ISSUES=", 'getElementById("koshitsu-tenpakai-tide-widget")')) else m[0],
                  text, flags=re.S)
    n = public['opinion_count']; total = public['collected_count']
    text = re.sub(r'<p class="question-line">.*?</p>', '<p class="question-line">皇族の人数と、皇位を継ぐ資格。二つを分けて読む。</p>', text, count=1, flags=re.S)
    text = re.sub(r'<p class="lead">.*?</p>', f'<p class="lead">世論調査ではありません。収集した{total:,}件から、意見を含む{n:,}件を整理しました。今回の改正への評価と、女性天皇・女系天皇への考えを分けてたどります。</p>', text, count=1, flags=re.S)
    text = text.replace('1,282件', f'{n:,}件').replace('1282件',f'{n}件')
    text = re.sub(r'<ul class="article-trust-observations">.*?</ul>',
        '<ul class="article-trust-observations"><li>旧分類の「男系維持／女系容認」と改正全体への賛否を分離しました。政党の採決行動への批判だけで法案内容全体への反対とは判定していません。</li>'
        '<li>旧意見1,282件のうち、782件は以前の編集・監査記録を引き継ぎ、残る500件を本文確認しました。判断が分かれた43件と追加1件も再確認しています。引用だけの投稿など37件を意見の集計から外しました。</li>'
        '<li>従来の非意見323件は今回の再読対象外です。追加分の確認はAI編集者によるもので、別の担当者による監査はまだ行っていません。</li></ul>', text, count=1, flags=re.S)
    # Move the editorial notice out of the voting form without deleting its content.
    trust = re.search(r'<!-- ARTICLE_TRUST_START -->.*?<!-- ARTICLE_TRUST_END -->',text,re.S)
    if trust:
        text=text[:trust.start()]+text[trust.end():]
        text=text.replace('<section class="panel" id="related-topics"',trust[0]+'\n<section class="panel" id="related-topics"',1)
    text=text.replace("iss.desc+'。同じ論点", "(iss.desc||iss.k)+'。同じ論点")
    columns=[s['label'] for s in public['issues'][0]['stances']]
    header=''.join('<th scope="col">'+h.escape(c)+'</th>' for c in columns)
    rows=''.join('<tr><th scope="row">'+h.escape(i['label'])+'</th><td>'+str(i['count'])+'</td>'+''.join('<td>'+str(v['count'])+'</td>' for v in i['stances'])+'</tr>' for i in public['issues'])
    details=f'<section class="panel details-panel" id="detail-data"><div class="panel-title"><h2>詳細データ</h2></div><details><summary>論点ごとの件数と、今回案全体への評価</summary><div style="overflow-x:auto"><table><caption>意見{n:,}件。人数・世論の割合ではありません。</caption><thead><tr><th scope="col">論点</th><th scope="col">計</th>{header}</tr></thead><tbody>{rows}</tbody></table></div><p>「未表明」は中立の意味ではありません。表現強度は従来のAI分類を引き継いでおり、今回再判定していません。</p></details></section>'
    text=text.replace('<section class="panel" id="related-topics"',details+'\n<section class="panel" id="related-topics"',1)
    assert vote_fingerprint(source)==vote_fingerprint(text), '投票24選択肢の意味が変化'
    return text


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage-root',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=ROOT/'quality/prototypes/koshitsu-tenpakai-page-preview.html')
    args=ap.parse_args();stage=args.stage_root.resolve();out=args.out.resolve()
    if out.is_relative_to((ROOT/'docs').resolve()):raise SystemExit('候補生成器はdocsへ書き込めません')
    if stage==ROOT or stage.is_relative_to(ROOT):raise SystemExit('集計入力はリポジトリ外の非公開領域を指定してください')
    public=json.loads((stage/'data/public/themes'/f'{TOPIC}.json').read_text())
    source=(ROOT/'quality/candidates'/TOPIC/'original-page.html').read_text()
    manifest=json.loads((ROOT/'quality/candidates'/TOPIC/'manifest.json').read_text())
    if hashlib.sha256(source.encode()).hexdigest()!=manifest['original_html_sha256']:
        raise SystemExit('元ページが候補作成時から変わっています。差分確認してから再生成してください')
    template=stage/'candidate-template.html';template.write_text(prepare_template(source,public))
    # Require the real gate before invoking the common preview assembler.
    subprocess.run([sys.executable,'-c',"import sys;sys.path.insert(0,sys.argv[1]);import build_planet_data as b,yaml;d=b.build('koshitsu-tenpakai');f=b.independence_gate(d,yaml.safe_load((b.ROOT/'configs/planet/koshitsu-tenpakai.yaml').read_text()));assert not f,f;print('独自性検査: OK')",str(stage/'scripts')],check=True)
    subprocess.run([sys.executable,str(stage/'scripts/build_planet_page_preview.py'),'--topic',TOPIC,'--page',str(template),'--out',str(out)],check=True)
    text=expand_background(restore_issue_media(out.read_text(), public))
    # The common static fallback still displays the older smoothed height.
    # Match its visible percentage to the raw ratio used by the interactive graph.
    for issue in public['issues']:
        high=next(v['count'] for v in issue['intensities'] if v['id']=='high')
        pct=round(100*high/issue['count'],1) if issue['count'] else 0.0
        pattern=r'(<section[^>]+id="fb-'+re.escape(issue['id'])+r'".*?山の高さ：強い表現)[0-9.]+(%)'
        text,n=re.subn(pattern,lambda m:m[1]+str(pct)+m[2],text,count=1,flags=re.S)
        if n!=1:raise ValueError('静的表示の高さを確認できません: '+issue['id'])
    text=text.replace('（薄いほど意見が割れています）','（各立場の件数は内訳に表示）')
    text=text.replace('資料にあるのに、SNSにないこと','資料から補う、投稿では少なかった話')
    text=text.replace('資料にしかない話を見る','資料から補う話を見る')
    text=text.replace('人が一次資料を読んで見つけた','編集時に一次資料を読んで確認した')
    text=text.replace('SNSでよく見る主張','投稿が事実として示す主張')
    text=text.replace('SNSの声を見る前に','読んだあとのあなたの考え')
    text=text.replace('<dt>最終更新日</dt>','<dt>公開元の最終更新日</dt>')
    text=text.replace('／更新 2026-09-01','／収集データの更新 2026-09-01')
    text=text.replace('山を押すと、その論点の図解と、賛成・反対それぞれの投稿が読めます','山を押すと理由の内訳が開き、論点ごとの図解とX投稿へ進めます')
    # Explain the color axis before the reader reaches the graph.
    note_axis='<p class="axis-note" style="margin:16px 0;padding:16px;background:#eef3f8;border-left:4px solid #73869a"><strong>色は「今回案全体」への評価です。</strong>女性天皇への希望や養子制度への意見だけで、改正全体への賛否は決めていません。<strong>未表明は、中立や無関心の意味ではありません。</strong></p>'
    text=text.replace('<div class="modes"',note_axis+'<div class="modes"',1)
    text=text.replace('語られていない争点 — 一次資料では争点なのに、集めた投稿にほとんど無いもの','一次資料と、関連する投稿を照らす')
    text=text.replace('ここから下は集計ではありません。編集部が一次資料を読んで確かめたことだけを置いています。','一次資料の記載に、関連する投稿の確認件数を添えています。言い換えを網羅した集計ではありません。')
    note=('<aside class="candidate-note" style="margin:18px auto;padding:16px;max-width:1120px;background:#fff4d6;border:1px solid #caa65b;border-radius:12px">'
          '<strong>確認用ページ・未公開（2026年9月13日作成）</strong> — 分類基準を見直した候補です。追加分の独立監査は未実施です。下の投票はこの画面だけの動作見本で、サイトへ送信されません。</aside>')
    text=re.sub(r'(<body[^>]*>)',lambda m:m[0]+note,text,count=1)
    # Use the existing local fallback. No production requests or saved votes in a preview.
    text=re.sub(r'<script\b[^>]*src="[^"]*vote-config\.js[^"]*"[^>]*></script>','<script>window.SNS_VOTE_CONFIG={};</script>',text)
    text=text.replace("var STORAGE_KEY='sns_vote_'", "var STORAGE_KEY='sns_preview_vote_'")
    text=re.sub(r'<script\b[^>]*src="https://pagead2\.googlesyndication\.com[^"]*"[^>]*></script>','<!-- 広告配信: 確認用ページでは停止 -->',text)
    text=text.replace('回答と、24時間の重複防止用に一方向変換した接続元情報をサーバーに保存します。','この確認用ページの回答はブラウザー内だけに保存されます。本番へ送信されません。')
    assert vote_fingerprint(source)==vote_fingerprint(text)
    assert '改正賛成（女系容認）' not in text and '改正反対（男系維持）' not in text
    assert 'prototype_only' not in text or '"prototype_only": true' not in text
    text=re.sub(r'^[ \t]+$','',text,flags=re.M)
    out.write_text(text)
    print(f'候補完成: {out}')

if __name__=='__main__':main()
