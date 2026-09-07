"""Attach saved-reason triage without changing editorial adoption."""
from collections import Counter,defaultdict
from scripts.verify_editorial_hundred import read,sha
from scripts.summarize_editorial_holds import ACTIONS


def merge_triage(summary,input_path,output_path):
    source=read(input_path);result=read(output_path)
    if result['source_sha256']!=sha(input_path):raise ValueError('triage input changed')
    labels=result['records']
    if len(labels)!=len(source['records']) or sorted(r['index'] for r in labels)!=list(range(len(labels))):raise ValueError('triage coverage mismatch')
    bykey={}
    for label in labels:
        if label['category'] not in source['categories'] or not isinstance(label.get('brief_basis'),str) or not label['brief_basis'].strip():raise ValueError('invalid triage label')
        raw=source['records'][label['index']];bykey[(raw['topic'],raw['record_id_hash'])]=(raw,label)
    records=[];counts=Counter();methods=Counter();topics=defaultdict(Counter);applied=0
    for row in summary['records']:
        found=bykey.get((row['topic'],row['record_id_hash']))
        if found:
            raw,label=found
            if raw['reason_sha256']!=row['reason_sha256']:raise ValueError('triage reason version mismatch')
            group=label['category'];method='individual_saved_reason_triage';applied+=1
        else:group=row['primary_reason_hint'];method='keyword_hint_only'
        actions={**ACTIONS,'negative_not_support':'批判・嫌悪と政策への賛否を区別する','disagreement_only':'食い違った分類項目と両者の根拠を比較する'}
        records.append({**row,'reason_group':group,'grouping_method':method,'next_action':actions[group]});counts[group]+=1;methods[method]+=1;topics[row['topic']][group]+=1
    if applied!=len(labels):raise ValueError('triage contains records outside hold summary')
    return {**summary,'records':records,'reason_group_counts':dict(counts),'grouping_methods':dict(methods),'reason_groups_by_topic':dict(topics),
            'triage_input_sha256':sha(input_path),'triage_output_sha256':sha(output_path),'triage_scope':'201 previously uncategorized saved reasons reviewed individually; other entries remain explicitly labeled keyword hints. No body reread or adoption change.'}
