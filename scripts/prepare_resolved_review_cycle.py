"""Reserve one <=1000-record cycle from the resolved scope; never auto-credit aliases."""
import json
import shutil
import time
from collections import Counter
from pathlib import Path

import yaml
from scripts.resolve_remaining_review_scope import load_resolution
from scripts.prepare_editorial_continuation import build_criteria
from scripts.editorial_work_registry import load_registry, checked_packet, fingerprint
from scripts.verify_editorial_hundred import read, sha, dump


def select_ordinary(scope, raw, criteria, used, quotas):
    selected = []
    for topic, quota in sorted(quotas.items()):
        if topic in {'koshitsu-tenpakai','takaichi'}:raise ValueError('paused or private topic forbidden')
        candidates = [r for r in scope['records'] if r['topic'] == topic and
                      r['route'] == 'new_body_review' and (topic,r['record_id_hash']) not in used]
        if len(candidates) < quota: raise ValueError('not enough ordinary unreserved inputs: '+topic)
        for r in candidates[:quota]:
            row = raw[(topic,r['record_id_hash'])]
            if any(row[k] != r[k] for k in ('body_sha256','classification_sha256')) or fingerprint(criteria[topic]) != r['criteria_sha256']:
                raise ValueError('scope input or criteria changed')
            selected.append({**row, 'scope_route':r['route'], 'scope_input_job_key':r['input_job_key']})
    wanted=sum(quotas.values())
    if len({(r['topic'],r['record_id_hash']) for r in selected}) != wanted or len({r['scope_input_job_key'] for r in selected}) != wanted:
        raise ValueError('duplicate selected ID or input')
    return selected


def prepare(root, private, run, quotas, worktrees, prior_runs=()):
    root, private, run = (Path(p).resolve() for p in (root, private, run))
    if run.exists() or not run.is_relative_to(private) or run.is_relative_to(root):
        raise ValueError('new private run required')
    if set(worktrees) != {'editor_a', 'editor_b', 'auditor'} or len(set(worktrees.values())) != 3:
        raise ValueError('three separate actors/worktrees required')
    if any(not Path(p).is_dir() for p in worktrees.values()):
        raise ValueError('assigned worktree missing')
    if sum(quotas.values()) != 1000 or any(n <= 0 or n % 20 for n in quotas.values()):
        raise ValueError('this writer requires one 1000-record cycle in single-topic twenties')
    if set(quotas) & {'koshitsu-tenpakai', 'takaichi'}:
        raise ValueError('paused or private topic forbidden')
    scope_summary = read(root/'data/verification/editorial-review-scope.json')
    scope = load_resolution(scope_summary, private)
    inv_path = private/'body-review-inventory/20260908-finish5134/inventory.private.json'
    if sha(inv_path) != scope['provenance']['inventory_sha256']:
        raise ValueError('inventory version changed')
    raw = {(r['topic'], r['record_id_hash']): r for r in read(inv_path)['raw_remaining']}
    metadata = yaml.safe_load((root/'THEMES.yaml').read_text())['themes']
    for topic, expected in scope['provenance']['canonical_sha256'].items():
        if sha(root/metadata[topic]['sample_file']) != expected:
            raise ValueError('canonical version changed')
    criteria = build_criteria(root)
    work = load_registry(root/'data/verification/editorial-work.json', root, private)
    completed = {(r['topic'], r['record_id_hash']) for r in work['records'] if r['state'] != 'attempted'}
    used = set(completed)
    prior_hashes = {}
    for previous in map(Path, prior_runs):
        top = read(previous/'reservation.json')
        prior_hashes[str(previous.relative_to(private))] = sha(previous/'reservation.json')
        for name, digest in top['waves'].items():
            wave = previous/name
            if sha(wave/'reservation.json') != digest: raise ValueError('prior reservation changed')
            for rel, expected in read(wave/'reservation.json')['packet_hashes'].items():
                path = wave/rel
                if sha(path) != expected: raise ValueError('prior packet changed')
                for row in read(path)['records']: used.add((row['topic'],row['record_id_hash']))
    selected=select_ordinary(scope,raw,criteria,used,quotas)
    run.mkdir(parents=True)
    wave = run/'wave-01'; wave.mkdir()
    for name, rel in [('work','editorial-work'),('adoption','editorial-adoption-current')]:
        shutil.copy2(root/f'data/verification/{rel}.json',run/f'{name}-before.private.json')
    policy = {}
    for name in ('CYCLE_2000_RUNBOOK.md','POLICY_STANCE_MAPPING_V3.md'):
        source = root/'quality/designs/body-review'/name
        shutil.copy2(source,run/name);policy[name]=sha(source)
    packets = {}
    for b in range(1,51):
        rows=selected[(b-1)*20:b*20];topic=rows[0]['topic']
        assert {r['topic'] for r in rows} == {topic}
        packet={'schema_version':1,'state':'prepared_not_reviewed','records':rows,
                'criteria':{topic:criteria[topic]},'input_sha256':fingerprint(rows),
                'automatic_reread_credit':0,'additional_model_calls':0,
                'instructions':'Read each body individually under the frozen v3 policy; independent values before comparison. No canonical/adoption/public changes.'}
        checked_packet(packet,root)
        path=wave/f'batch-{b:02d}'/'packet.private.json';dump(path,packet);packets[str(path.relative_to(wave))]=sha(path)
    reservation={'schema_version':1,'prepared_epoch':time.time(),'new_records':1000,'packet_hashes':packets,
                 'writer_sha256':sha(root/'scripts/continuous_editorial_review.py'),'cycle_writer_sha256':sha(root/'scripts/editorial_cycle.py'),
                 'assignments':{'editor':{'editor_a':list(range(1,51,2)),'editor_b':list(range(2,51,2))},'audit':{'auditor':list(range(1,51))}},
                 'worktrees':worktrees,'model':'parent-configured model','reasoning_effort':'inherited'}
    dump(wave/'reservation.json',reservation)
    top={'schema_version':1,'prepared_epoch':time.time(),'new_records':1000,'waves':{'wave-01':sha(wave/'reservation.json')},
         'scope_resolution_sha256':scope_summary['resolution_sha256'],'prior_runs':prior_hashes,'topic_counts':dict(Counter(r['topic'] for r in selected)),
         'baseline_work_sha256':sha(run/'work-before.private.json'),'baseline_work_records':len(work['records']),
         'baseline_adoption_sha256':sha(run/'adoption-before.private.json'),'canonical_hashes':scope['provenance']['canonical_sha256'],
         'policy_sha256':policy,'koshitsu_paused':782,'non_koshitsu_target':4352,'status':'reserved_not_reviewed','registered_reread_increment':0,
         'activity_check':'Only current editor_a/editor_b/auditor are assigned; prior task actors completed; parent confirmed live status before dispatch.'}
    dump(run/'reservation.json',top)
    return top
