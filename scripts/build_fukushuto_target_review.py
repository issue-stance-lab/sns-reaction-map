#!/usr/bin/env python3
"""Build an auditable, non-publishing review from full-text manual judgments.

No classification by keywords; no canonical or docs writes. Output has counts,
reviewer paraphrases and hashed evidence only. It is NOT a public-data payload.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import html
import json
from pathlib import Path

LABELS = ('肯定', '否定', '条件付き', '判断保留', '未表明', '判定保留')
ISSUES = ('定義・中身', '候補地', '防災・災害', '都構想・維新', '費用・財源', '優先順位', 'その他')
SCOPES = ('法案・成立法（版未確定）', '制度設計・運用（対象案未確定）', '別案・追加提案', '附帯決議・同日選の制限')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def counts(values):
    c = Counter(values)
    return {k: c[k] for k in LABELS}

def compile_review(baseline, review):
    rows = review['records']
    if not baseline or len(rows) != len(baseline):
        raise ValueError('全件の本文確認が必要')
    if sorted(r['index'] for r in rows) != list(range(len(baseline))):
        raise ValueError('確認位置が重複・欠落')
    if len({str(p['tweet_id']) for p in baseline}) != len(baseline):
        raise ValueError('原本に投稿ID重複')
    for r in rows:
        src = baseline[r['index']]
        if r['post_key'] != digest(str(src['tweet_id']).encode()) or r['text_sha256'] != digest(src['text'].encode()):
            raise ValueError('確認記録と原文が不一致')
        if not r.get('read_at') or not r.get('reason'):
            raise ValueError('確認日時・根拠が欠落')
        if r['decision'] not in ('include', 'exclude', 'hold') or r['main_issue'] not in ISSUES:
            raise ValueError('未知の採否・論点')
        if any(r[k] not in LABELS for k in ('concept', 'law')):
            raise ValueError('未知の評価')
        if r['law_scope'] not in (*SCOPES, '未表明'):
            raise ValueError('未知の制度対象')
        if (r['law'] == '未表明') != (r['law_scope'] == '未表明'):
            raise ValueError('制度対象と評価が不整合')
        if len({x['name'] for x in r['locations']}) != len(r['locations']):
            raise ValueError('地域の重複')
        if any(not x['name'] or x['stance'] not in LABELS or x['stance'] == '未表明' for x in r['locations']):
            raise ValueError('地域評価が不正')
        if r['decision'] == 'exclude' and (r['concept'] != '未表明' or r['law'] != '未表明' or r['locations']):
            raise ValueError('除外投稿に評価を付与')
    included = [r for r in rows if r['decision'] == 'include']
    old = [p for p in baseline if p['classification'].get('is_relevant') and p['classification'].get('is_opinion')]
    transition = Counter(('意見' if baseline[r['index']]['classification'].get('is_relevant') and baseline[r['index']]['classification'].get('is_opinion') else '非意見', r['decision']) for r in rows)
    locations = defaultdict(list)
    for r in included:
        for loc in r['locations']:
            locations[loc['name']].append(loc['stance'])
    old_issues = Counter(p['classification']['main_issue'] for p in old)
    new_issues = Counter(r['main_issue'] for r in included)
    moves = Counter((baseline[r['index']]['classification']['main_issue'], r['main_issue']) for r in included if baseline[r['index']]['classification'].get('is_relevant') and baseline[r['index']]['classification'].get('is_opinion'))
    pending = [r for r in rows if r['decision'] == 'hold' or '判定保留' in [r['concept'], r['law'], *[l['stance'] for l in r['locations']]]]
    text_counts = Counter(digest(p['text'].encode()) for p in baseline)
    return {
        'schema': 'fukushuto-target-review-v1', 'status': 'draft_not_for_publication',
        'can_publish': False, 'independent_review': False,
        'classification_body_read': len(rows), 'editorial_bucket_reread': 0,
        'original_total': len(baseline), 'old_opinions': len(old), 'candidate_opinions': len(included),
        'decisions': dict(Counter(r['decision'] for r in rows)),
        'adoption_transition': {old: {new: transition[(old,new)] for new in ('include','exclude','hold')} for old in ('意見','非意見')},
        'old_stances': dict(Counter(p['classification']['stance'] for p in old)),
        'issues': [{'name': i, 'before': old_issues[i], 'after': new_issues[i], 'delta': new_issues[i]-old_issues[i]} for i in ISSUES],
        'retained_issue_changed_posts': sum(n for (a,b),n in moves.items() if a != b),
        'issue_moves_retained': [{'from': a, 'to': b, 'count': n} for (a,b),n in sorted(moves.items())],
        'concept': counts(r['concept'] for r in included),
        'law_by_scope': {s: counts(r['law'] for r in included if r['law_scope'] == s) for s in SCOPES},
        'law_unexpressed': sum(r['law'] == '未表明' for r in included),
        'locations': [{'name': name, 'posts': len(v), 'counts': counts(v)} for name,v in sorted(locations.items(), key=lambda x:(-len(x[1]),x[0]))],
        'location_evaluating_posts': sum(bool(r['locations']) for r in included),
        'no_target_stance_posts': sum(r['concept'] == r['law'] == '未表明' and not r['locations'] for r in included),
        'pending_posts': len(pending),
        'pending': [{k:r[k] for k in ('post_key','text_sha256','decision','reason')} for r in pending],
        'same_text': {'distinct_texts': len(text_counts), 'repeated_text_groups': sum(n>1 for n in text_counts.values()), 'posts_in_repeated_groups': sum(n for n in text_counts.values() if n>1)},
        'caveats': ['同じ投稿を仕分け直した結果であり、世論の変化ではありません。', '収集した投稿サンプルの件数です。人の数や世論全体の支持率ではありません。', '対象間・地域間には同じ投稿の重複があるため、件数を合計しません。', '法案の版や対象案を特定できないものは、その限界を区分名に残します。別案の支持を現行法への支持に数えません。', '未表明は中立票ではありません。判断保留は本人が迷っている場合、判定保留は読み手が文脈を確定できない場合です。', '投稿中の法律・災害・財源の主張の正しさを認定するものではありません。', '分類の本文確認と、山なみの理由を作る編集再読・独立監査は別工程です。'],
        'records': [{k:r[k] for k in ('post_key','text_sha256','read_at','decision','main_issue','concept','law','law_scope','locations','reason')} for r in rows],
    }

def markdown(d):
    n=d['candidate_opinions']; old=d['old_opinions']; tr=d['adoption_transition']
    lines=['# 副首都：全1,733投稿の対象別点検・数値変更案', '',
      '**分類の本文確認は全件完了。新ページは未完成・未公開です。**',
      '20件比較の分け方で進めるオーナー指示を受け、全文を読んで対象ごとの評価を記録しました。これは担当者の候補で、独立監査は未実施です。', '',
      f'意見として採用する案は **{old:,} → {n:,}件（{n-old:+,}件）**。全体の収集件数は{d["original_total"]:,}件のままです。',
      f'旧意見から除外{tr["意見"]["exclude"]}件・保留{tr["意見"]["hold"]}件、旧非意見から追加{tr["非意見"]["include"]}件。残りの旧非意見は除外{tr["非意見"]["exclude"]}件・保留{tr["非意見"]["hold"]}件です。',
      '**AIが同じ投稿を仕分け直したために動く数字です。世論が変わったのではありません。**', '',
      '## 意見の採否', '', '|旧区分|採用案|除外案|保留|','|---|---:|---:|---:|']
    for k,v in tr.items(): lines.append(f'|{k}|{v["include"]}|{v["exclude"]}|{v["hold"]}|')
    lines+=['','## 論点の対照表', '',f'一投稿につき主論点は一つ。旧母数{old:,}件、新しい案の母数{n:,}件。割合は各母数に対する比率。', '', '|論点|変更前|変更案|差|','|---|---:|---:|---:|']
    for x in d['issues']:lines.append(f'|{x["name"]}|{x["before"]}（{x["before"]/old:.1%}）|{x["after"]}（{x["after"]/n:.1%}）|{x["delta"]:+}|')
    lines+=['',f'旧・新とも意見に残す投稿のうち、主論点を変更したのは{d["retained_issue_changed_posts"]}件です。これは採否の追加・除外と別の変更です。', '', '## 立場の対照表', '',f'旧表示は{old:,}件を一つの立場へ分類していました。新しい案では、以下を別々に読むため、旧ラベルとの一対一の増減率は出しません。', '', '|旧ラベル|旧件数|', '|---|---:|']
    for k,v in d['old_stances'].items():lines.append(f'|{k}|{v}（{v/old:.1%}）|')
    lines+=['',f'新しい案の採用母数は{n:,}件。構想は全{n:,}件、制度は区分内の件数、候補地は各地域について評価した投稿を下表で数えます。未表明を中立として加えません。', '', '|新しい対象|肯定・擁護|否定・批判|条件付き|本人の判断保留|読取の判定保留|記録件数|','|---|---:|---:|---:|---:|---:|---:|']
    def row(name,c):return '|'+name+'|'+'|'.join(str(c[k]) for k in ('肯定','否定','条件付き','判断保留','判定保留'))+'|'+str(sum(v for k,v in c.items() if k!='未表明'))+'|'
    lines.append(row('構想',d['concept']))
    for k,v in d['law_by_scope'].items():lines.append(row(k,v))
    lines += ['',f'構想への未表明は{d["concept"]["未表明"]:,}件。法案・制度すべてへの未表明は{d["law_unexpressed"]:,}件。制度の区分を合算して「法案賛成率」にしないでください。別案・追加提案の肯定には、投稿者自身の提案も含まれます。', '', '|地域の表記|肯定・擁護|否定・批判|条件付き|本人の判断保留|読取の判定保留|記録件数|','|---|---:|---:|---:|---:|---:|---:|']
    for x in d['locations'][:12]:lines.append(row(x['name'],x['counts']))
    lines += ['',f'地域の評価がある投稿は{d["location_evaluating_posts"]:,}件。地域は原文に表れた単位で保持し、福岡市と北九州市、大阪と関西などを自動で合算しません。全地域は画面案で選択できます。三つの対象に賛否を示していない意見は{d["no_target_stance_posts"]:,}件あり、主に優先順位・政治姿勢・説明を求める意見などとして残します。', '', '## 読み方と品質上の残り', '']
    lines += ['- '+x for x in d['caveats']]
    lines += [f'- 投稿全体の採否を保留した{d["decisions"]["hold"]}件に加え、一部地域の記号を確定できない投稿が1件。未解決は合計{d["pending_posts"]}投稿です。未解決を無理に賛否へ割り振りません。',f'- 同一本文の繰り返しは{d["same_text"]["repeated_text_groups"]}組、該当{d["same_text"]["posts_in_repeated_groups"]}投稿。投稿IDは全件一意で、同文の別投稿を黙って削除していません。', '- 10件を対象に始めたHermes試験は、最初の処理で判断理由の空欄が3回続き、有効な出力を得られず不採用。全件を担当者が本文から直接点検しました。', '- 先に確認した20例は、対象評価・採否とも今回の記録と一致しています。質問だけの投稿を本人の判断保留とする読み過ぎは原文で再確認し修正しました。', '- 原本・公開JSON・公開ページ・21の投票選択肢は未変更です。', '', '## 次の作業', '', 'この数値案を確認した後、未解決の文脈確認、理由別の編集再読と独立監査、山なみ生成器への接続を進めます。画面案は対象別表示の確認用で、山なみの完成版ではありません。', '', '数字の採用と本番公開は別です。公開前には分類・編集再読・ページ検査を満たす必要があります。', '']
    return '\n'.join(lines)

def render_preview(d, examples, template):
    payload={k:v for k,v in d.items() if k not in ('records','pending','issue_moves_retained')}
    payload['examples']=[x for x in examples if x['number'] in (1,2,5,7,8,18)]
    body='<table><caption>旧表示の立場（母数 '+str(d['old_opinions'])+'件）</caption><thead><tr><th>立場</th><th>件数</th></tr></thead><tbody>'
    body+=''.join('<tr><td>'+html.escape(k)+'</td><td>'+str(v)+'</td></tr>' for k,v in d['old_stances'].items())
    body+='</tbody></table><table><caption>論点別の変更前後</caption><thead><tr><th>論点</th><th>前</th><th>案</th><th>差</th></tr></thead><tbody>'
    body+=''.join('<tr><td>'+html.escape(x['name'])+'</td><td>'+str(x['before'])+'</td><td>'+str(x['after'])+'</td><td>'+format(x['delta'],'+')+'</td></tr>' for x in d['issues'])
    body+='</tbody></table>'
    encoded=json.dumps(payload,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    return template.replace('__DATA__',encoded).replace('__STATIC_TABLES__',body)

def main():
    a=argparse.ArgumentParser();a.add_argument('--baseline',type=Path,required=True);a.add_argument('--review',type=Path,required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args()
    if 'docs' in args.output.parts or ('data' in args.output.parts and 'public' in args.output.parts):
        a.error('公開領域には出力できません')
    raw=args.baseline.read_bytes(); evidence=args.review.read_bytes()
    d=compile_review(json.loads(raw),json.loads(evidence));d['provenance']={'baseline_sha256':digest(raw),'review_sha256':digest(evidence),'builder_sha256':digest(Path(__file__).read_bytes())}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.with_suffix('.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    args.output.with_suffix('.md').write_text(markdown(d))
    root=Path(__file__).resolve().parents[1]
    examples=json.loads((root/'quality/reviews/2026-09-12-fukushuto-20-comparison.json').read_text())
    if isinstance(examples,dict): examples=examples['items']
    template=(root/'quality/prototypes/fukushuto-target-review.template.html').read_text()
    (root/'quality/prototypes/fukushuto-target-review.html').write_text(render_preview(d,examples,template))
    print(json.dumps({k:d[k] for k in ('original_total','candidate_opinions','decisions','pending_posts','can_publish')},ensure_ascii=False))
if __name__=='__main__':main()
