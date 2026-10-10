"""Single source for prototype figures, with fail-closed editorial review."""
from pathlib import Path
import argparse, hashlib, json, re
from bs4 import BeautifulSoup

ISSUES=['bukatsu-chiiki-'+x for x in ['kyoin','seido','kyoiku','ukezara','hiyo','sonota','kakusa']]
def digest(text): return hashlib.sha256(text.encode()).hexdigest()
def parse_page(text):
    soup=BeautifulSoup(text,'html.parser')
    node=soup.select_one('#planet-data')
    if not node: raise ValueError('更新元に planet-data がありません')
    data=json.loads(node.get_text().split('=',1)[1].strip().rstrip(';'))
    if [i['id'] for i in data['issues']] != ISSUES: raise ValueError('論点の追加・並び替えがあります。見出し・色・説明の対応を確認してください')
    total=data['totals']['opinions']
    if sum(i['count'] for i in data['issues'])!=total or sum(s['count'] for s in data['stances'])!=total: raise ValueError('意見総数・論点・立場の合計が一致しません')
    for issue in data['issues']:
        items=issue['sub'].get('items',[])
        if items and sum(x['count'] for x in items)!=issue['count']: raise ValueError('理由の合計が論点の件数と一致しません: '+issue['id'])
    card=soup.select_one('.trend-card script')
    trends=json.loads(re.search(r'const panels = (.*?);\n',card.string).group(1))
    for panel in trends.values():
        rounds=panel['rounds']
        dates=[r['d'] for r in rounds]
        if not dates or dates!=sorted(set(dates)): raise ValueError('推移の日付が空、重複、または逆順です')
        if dates[-1]!=data['updated_at']: raise ValueError('集計と推移の最終日が一致しません')
        for r in rounds:
            if len(r['v'])!=len(panel['labels']) or len(r['c'])!=len(panel['labels']): raise ValueError('推移の系列数が一致しません')
    return data,trends

def load_inputs(root,main):
    ap=argparse.ArgumentParser(description='公開候補HTMLから試作を更新。本文の再確認が必要な変更は停止します。')
    ap.add_argument('--source-page',type=Path,default=main/'docs/bukatsu-chiiki-reaction-map.html')
    ap.add_argument('--output',type=Path,default=root/'index.html')
    args=ap.parse_args()
    text=args.source_page.read_text();data,trends=parse_page(text)
    review=json.loads((root/'.build/editorial-review.json').read_text())
    fingerprint=digest(json.dumps(data,ensure_ascii=False,sort_keys=True))
    report={'source':str(args.source_page),'source_sha256':digest(text),'data_sha256':fingerprint,'snapshot':data['snapshot_id'],'opinions':data['totals']['opinions'],'updated_at':data['updated_at'],'rounds':{k:len(v['rounds']) for k,v in trends.items()},'editorial_review_required':fingerprint!=review['data_sha256'],'review_items':['7論点の説明と4理由の説明','比較欄の意見抜粋','論点別の投稿例・主張と一次資料','制度の内容・確認日・背景・授業用の説明']}
    (root/'evidence/refresh-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    if report['editorial_review_required']: raise ValueError('データが変わりました。evidence/refresh-check.json の確認項目を読み直し、editorial-review.json に確認記録を保存してから再生成してください。現在のページは保持しました。')
    return data,text,args.output
