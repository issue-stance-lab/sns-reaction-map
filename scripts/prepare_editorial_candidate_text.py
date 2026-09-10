"""Reviewed copy-only text adjustment when AI topic's leading issue changes."""
import json
import re
from pathlib import Path
from scripts.verify_editorial_candidate_pair import counts


def prepare_conclusion(tree):
    tree=Path(tree);config_path=tree/'configs/ai-copyright-reaction-map.json';config=json.loads(config_path.read_text())
    canonical=tree/'social-samples/ai-copyright_hermes_classified.json'
    totals=counts(json.loads(canonical.read_text()))['issues'];block=config['issue_counts']
    card_totals={c['slug']:sum(totals.get(k,0) for k in c['main_issue']) for c in block['cards']}
    current=block['conclusion'];top=max(card_totals,key=card_totals.get)
    if card_totals[current]>=card_totals[top]:return []
    if current!='gakushu' or top!='moraru':raise ValueError('unreviewed leading issue requires editorial copy')
    page_path=tree/'docs/ai-copyright-reaction-map.html';page=page_path.read_text()
    pattern=r'(<li class="conclusion-focus"><span class="conclusion-count"><b>)[0-9,]+(</b>件</span>)<strong>学習データの無断利用を、どこまで認めるのか</strong><span class="conclusion-detail">許諾なしの学習は権利侵害か、合法な技術利用かに議論が集中しています。</span>'
    page,n=re.subn(pattern,lambda m:m[1]+str(card_totals[top])+m[2]+'<strong>AI生成物の使い方や表示・二次利用をどう考えるか</strong><span class="conclusion-detail">この収集サンプルでは、利用者モラル・倫理に分類された意見が最多です。</span>',page)
    if n!=1:raise ValueError('unrecognized conclusion copy')
    # Ordinal 1 is also interpreted as a largest-issue claim by the verifier.
    page,n=re.subn(r'(<span class="axis-kicker">)論点[1-6](?:・最大勢力)?([^<]*</span>)',r'\1論点\2',page)
    if n!=6:raise ValueError('unrecognized issue badges')
    page,n=re.subn(r'(<article class="issue-block" id="issue-moraru">\s*<div class="issue-head"><span class="axis-kicker">)論点(</span>)',r'\1論点・最大勢力\2',page)
    if n!=1:raise ValueError('missing new leading badge')
    block['conclusion']=top
    config_path.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n');page_path.write_text(page)
    return [{'theme':'ai-copyright','from':current,'to':top,'count':card_totals[top],'scope':'isolated candidate only'}]


def sync_bukatsu_summary(tree):
    """Refresh existing summary numbers after the arena builder; no collection wave."""
    tree=Path(tree);p=tree/'docs/bukatsu-chiiki-reaction-map.html';page=p.read_text()
    if '<!-- PLANET_SECTION_START -->' in page:
        # 課題54段階3で本番差し替え済み。この関数が同期する4つの注目ポイント・
        # SNS反応マップ・アリーナのISSUES配列は、山なみ形式ではどれも存在しない
        # （#planet-blockが役目を引き継いだ）。書くものが無いので何もしない。
        return
    rows=json.loads((tree/'social-samples/bukatsu-chiiki_hermes_classified.json').read_text());data=counts(rows)
    if max(data['stances'],key=data['stances'].get)!='移行支持' or max(data['issues'],key=data['issues'].get)!='教員の働き方':
        raise ValueError('bukatsu leading interpretation needs editorial review')
    relevant=sum(bool((r.get('classification') or {}).get('is_relevant',r.get('is_relevant',False))) for r in rows)
    pattern=r'(<strong class="insight-value">)[0-9]+(<small>件</small></strong>\s*<p class="insight-note">関連)[0-9]+(件から)'
    page,n=re.subn(pattern,lambda m:m[1]+str(data['opinions'])+m[2]+str(relevant)+m[3],page)
    if n!=1:raise ValueError('missing bukatsu opinion/relevance summary')
    teacher=data['issues'].get('教員の働き方',0);pct=round(teacher*100/data['opinions']) if data['opinions'] else 0
    page,n=re.subn(r'(<strong class="insight-value">教員の働き方 )[0-9]+(<small>件</small></strong>)',lambda m:m[1]+str(teacher)+m[2],page)
    if n!=1:raise ValueError('missing bukatsu leading issue summary')
    page,n=re.subn(r'(data-tone="topic"[^>]*>.*?<i style="width:)[0-9]+(%")',lambda m:m[1]+str(pct)+m[2],page,count=1,flags=re.S)
    if n!=1:raise ValueError('missing bukatsu leading issue meter')
    for label,stance,tone in [('移行支持','移行支持','debate'),('改善条件あり','条件付き・改善要求','option')]:
        value=data['stances'].get(stance,0);pct=round(value*100/data['opinions']) if data['opinions'] else 0
        pattern=r'(<strong class="insight-value">'+re.escape(label)+r' )[0-9]+(%</strong>\s*<p class="insight-note">)[0-9]+(件)'
        page,n=re.subn(pattern,lambda m:m[1]+str(pct)+m[2]+str(value)+m[3],page)
        if n!=1:raise ValueError('missing bukatsu stance summary')
        pattern=r'(data-tone="'+tone+r'"[^>]*>.*?<i style="width:)[0-9]+(%")'
        page,n=re.subn(pattern,lambda m:m[1]+str(pct)+m[2],page,count=1,flags=re.S)
        if n!=1:raise ValueError('missing bukatsu stance meter')
    from scripts.update_bukatsu_tide import sm_raw
    from scripts.public_registry_common import is_opinion_record
    page,n=re.subn(r'const SM_RAW = \[.*?\n\];',lambda _:sm_raw([r for r in rows if is_opinion_record(r)]),page,flags=re.S)
    if n!=1:raise ValueError('missing bukatsu map records')
    page,n=re.subn(r'(<h2>SNS反応マップ</h2><span>)意見[0-9]+(件 \| セクター=)',lambda m:m[1]+'意見'+str(data['opinions'])+m[2],page)
    if n!=1:raise ValueError('missing bukatsu map caption')
    pattern=r'const ISSUES=\[.*?\n  \];';blocks=list(re.finditer(pattern,page,re.S))
    if len(blocks)!=1:raise ValueError('unexpected bukatsu arena issue blocks')
    block=blocks[0].group()
    for label in ['費用・家庭負担','受け皿・指導者','教員の働き方','教育的意義・機会','地域格差','制度・移行プロセス','その他']:
        block,n=re.subn(r'(k:[\'\"]'+re.escape(label)+r'[\'\"],\s*n:)\d+',lambda m:m[1]+str(data['issues'].get(label,0)),block)
        if n!=1:raise ValueError('missing bukatsu arena issue')
    page=page[:blocks[0].start()]+block+page[blocks[0].end():];p.write_text(page)
