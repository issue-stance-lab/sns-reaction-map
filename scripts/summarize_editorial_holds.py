"""Group saved hold reasons without rereading bodies or changing adoption."""
from collections import Counter,defaultdict
import hashlib
from pathlib import Path
from scripts.verify_editorial_hundred import read,sha
from scripts.editorial_work_registry import resolve_source

PATTERNS=[('quote_or_attribution',('引用','見出し','共有','転載','引用元','投稿者自身','帰属')),
          ('context_or_intent',('文脈','皮肉','意図','不明','断定','読み取','曖昧','あいまい')),
          ('multiple_issues',('複数','主論点','主要論点','競合','またが','混在')),
          ('criteria_or_axis',('基準','軸','男系','女系','制度案','定義')),
          ('relevance_or_opinion',('関連','意見','情報紹介','告知','報道'))]
ACTIONS={'quote_or_attribution':'引用元・発言主体を確認し、投稿者の意見と区別する',
 'context_or_intent':'必要な前後文脈だけを確認し、不足なら保留を維持する',
 'multiple_issues':'主要論点を選ぶ優先ルールを整理して同種をまとめる',
 'criteria_or_axis':'テーマの分類基準と軸の混同を点検する',
 'relevance_or_opinion':'関連性と意見有無を分けて確認する',
 'other_or_unmapped':'保存理由を個別に確認して対応を決める'}


def reasons_from_sources(root,private_root,registry,extra_paths=()):
    result={};proofs={}
    def visit(value):
        if isinstance(value,dict):
            reason=value.get('reason')
            if isinstance(reason,str):result[hashlib.sha256(reason.encode()).hexdigest()]=reason
            for v in value.values():visit(v)
        elif isinstance(value,list):
            for v in value:visit(v)
    paths=[resolve_source(s,root,private_root) for s in registry['sources']]+list(map(Path,extra_paths))
    for p in dict.fromkeys(paths):
        if p.suffix!='.json':continue
        before=len(result);visit(read(p))
        if len(result)>before:proofs[str(p)]=sha(p)
    return result,proofs


def summarize(journal,reasons):
    records=[];counts=Counter();modes=Counter();topics=defaultdict(Counter);missing=0
    for row in journal:
        if row['adoption_status']!='hold':continue
        hashes=[h for h in [row.get('reason_sha256'),row.get('independent_reason_sha256'),row.get('supplemental_reason_sha256')] if h]
        available=[reasons[h] for h in hashes if h in reasons];text=' '.join(available)
        labels=[label for label,words in PATTERNS if any(w in text for w in words)]
        primary=labels[0] if labels else 'other_or_unmapped'
        differences=[k for k,v in row.get('proposed',{}).items() if row.get('independent_proposed') is not None and row['independent_proposed'].get(k)!=v]
        mode='supplemental_uncertainty_or_disagreement' if row.get('supplemental_audit_sha256') else 'classification_disagreement' if differences else 'editor_uncertain' if row.get('first_route')=='uncertain' else 'other_uncertainty_or_legacy'
        records.append({'topic':row['topic'],'record_id_hash':row['record_id_hash'],'body_sha256':row['body_sha256'],'classification_sha256':row['classification_sha256'],
                        'hold_mode':mode,'differing_fields':differences,'primary_reason_hint':primary,'reason_hints':labels,'reason_sha256':hashes,
                        'missing_reason_hashes':[h for h in hashes if h not in reasons],'next_action':ACTIONS[primary]})
        counts[primary]+=1;modes[mode]+=1;topics[row['topic']][primary]+=1;missing+=any(h not in reasons for h in hashes)
    return {'schema_version':1,'held_records':len(records),'primary_reason_counts':dict(counts),'hold_modes':dict(modes),'by_topic':dict(topics),
            'records_with_unmapped_reason_evidence':missing,'records':records,
            'scope':'Mechanical first-pass grouping of saved reasons using explicit decision differences and keyword hints; hints are not adjudicated causes. No new body review or adoption change.',
            'new_body_reviews':0,'adoption_changes':0}
