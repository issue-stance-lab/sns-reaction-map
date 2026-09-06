#!/usr/bin/env python3
"""Read-only mechanical audit; ID-bearing evidence is written only to --output."""
import argparse, collections, hashlib, json, shutil, subprocess, tarfile
from pathlib import Path

def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_bytes())
def ids(rows): return {str(r['tweet_id']) for r in rows}
def safeids(rows): return {'sha256:'+sha(('tweet:'+str(r['tweet_id'])).encode()) for r in rows}
def stats(rows):
    c=[r.get('classification',r) for r in rows]
    op=[r for r in c if r.get('is_relevant') and r.get('is_opinion')]
    return {'collected':len(rows),'relevant':sum(bool(r.get('is_relevant')) for r in c),'opinions':len(op),'issues':dict(collections.Counter(r.get('main_issue') for r in op)),'stances':dict(collections.Counter(r.get('stance') for r in op))}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path.cwd());ap.add_argument('--output',type=Path,required=True);ap.add_argument('--backup-dir',type=Path,required=True);ap.add_argument('--shared-root',type=Path,required=True);a=ap.parse_args();root=a.root.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);e=out/'evidence';e.mkdir(exist_ok=True)
    def git(*args):return subprocess.check_output(['git','-C',str(root),*args])
    canon='social-samples/constitutional_amendment_hermes_arena_classified.json';wave='social-samples/updates/constitutional-amendment/2026-08-08';vf='data/verification/constitutional-amendment.json'
    before=read(root/canon);records=read(root/wave/'classified.json');raw=read(root/wave/'raw.json');wi=ids(records);wh=safeids(records);ci=ids(before)
    source_files=[canon,*[wave+'/'+f for f in ('raw.json','classified.json','report.json')],vf,'data/verification/updates/constitutional-amendment/2026-08-08/classified.json','data/constitutional-amendment_claim_posts.json','data/verification/constitutional-amendment-claims.json','configs/topics/constitutional.yaml','scripts/classify_constitutional_arena_hermes.py','scripts/refresh_adapters/constitutional.py','configs/prompts/claude-code/20260808_constitutional-amendment-opinion.md']
    fingerprints={}
    for rel in source_files:
        p=root/rel;dest=e/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);fingerprints[rel]=sha(p.read_bytes())
    histories=[]
    for commit in git('log','--all','--format=%H','--',vf).decode().splitlines():
        try:b=git('show',commit+':'+vf);rows=json.loads(b)
        except subprocess.CalledProcessError:continue
        overlap=wh&{r['record_id_hash'] for r in rows};histories.append({'commit':commit,'rows':len(rows),'target_overlap':len(overlap),'sha256':sha(b)});(e/('canonical-summary-'+commit[:12]+'.json')).write_bytes(b)
    for commit in ('5afcb76','d5ece93','633278c','004ba5d','5037b65','fe2c632'):
        (e/('git-'+commit+'.txt')).write_bytes(git('show','--format=fuller','--stat',commit))
    archives=[]
    for p in sorted(a.backup_dir.glob('private-data-*.tar.gz')):
        found=False
        with tarfile.open(p,'r|gz') as t:
            for member in t:
                if member.name.lstrip('./')==canon:
                    b=t.extractfile(member).read();rows=json.loads(b);archives.append({'archive':p.name,'rows':len(rows),'target_overlap':len(wi&ids(rows)),'canonical_sha256':sha(b)});found=True;break
        if not found:archives.append({'archive':p.name,'canonical_absent':True})
    waves=[]
    for p in sorted((root/'social-samples/updates/constitutional-amendment').glob('*/classified.json')):
        r=read(p);waves.append({'date':p.parent.name,**stats(r),'target_overlap':len(wi&ids(r)),'canonical_overlap':len(ci&ids(r)),'sha256':sha(p.read_bytes())})
    claim=read(root/'data/constitutional-amendment_claim_posts.json');claimids={str(v) for c in claim['claims'] for v in c['tweet_ids']}
    checks={'raw_classified_ids_equal':ids(raw)==wi,'raw_count_227':len(raw)==len(records)==len(wi)==227,'raw_preserved_in_classified':all({k:v for k,v in r.items() if k!='classification'}==next(x for x in raw if str(x['tweet_id'])==str(r['tweet_id'])) for r in records),'current_unique':len(ci)==len(before),'all_227_outside_current':len(wi-ci)==227,'public_wave_hashes_match':wh=={r['record_id_hash'] for r in read(root/'data/verification/updates/constitutional-amendment/2026-08-08/classified.json')},'shared_canonical_hash_matches':sha((root/canon).read_bytes())==sha((a.shared_root/canon).read_bytes()),'no_target_in_git_canonical_history':all(r['target_overlap']==0 for r in histories),'no_target_in_backup_canonicals':all(r.get('target_overlap',0)==0 for r in archives)}
    report={'baseline_commit':git('rev-parse','HEAD').decode().strip(),'before':stats(before),'after':stats(before),'wave':stats(records),'checks':checks,'fingerprints':fingerprints,'git_canonical_history':histories,'backup_canonical_history':archives,'waves':waves,'claim_audit':{'claims':len(claim['claims']),'post_references':sum(len(c['tweet_ids']) for c in claim['claims']),'unique_posts':len(claimids),'target_overlap':len(wi&claimids)},'treatment_counts':{'unadopted_candidate_current_reason_unknown':len(wi-ci),'already_adopted':len(wi&ci),'confirmed_omission':0,'confirmed_exclusion':0,'classification_change_required_confirmed':0},'limitations':['No semantic reread performed; adopted/excluded decisions require review of all 227 candidate posts.','Historical model identifier is not recorded in run report; current configuration is not evidence of historical runtime.','Git and retained backup snapshots cannot prove transient unrecorded local states.']}
    decisions=[{'tweet_id':str(r['tweet_id']),'status':'unadopted_candidate_current_reason_unknown','initial_staging_reason':'Explicit no-promotion instruction while page_update_mode=migration','later_nonadoption_reason':'unknown','current_action':'hold_pending_semantic_review_and_adoption_decision','reason':'20260808 opinion prompt required --promote absent and canonical 646-only reclassification; run 20260808_183218 validated candidate 873 only. No target membership in retained canonical snapshots. Permanent exclusion and later reason for not promoting are unconfirmed.','evidence':['configs/prompts/claude-code/20260808_constitutional-amendment-opinion.md:31-33,269','git:633278c','git:d5ece93','report.json:run_id=20260808_183218','summary.json:git_canonical_history,backup_canonical_history'],'semantic_review':'not_performed','existing_classification':r['classification'],'text_sha256':sha(r['text'].encode())} for r in records]
    (out/'decisions.private.json').write_text(json.dumps(decisions,ensure_ascii=False,indent=2)+'\n');(out/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');shutil.copyfile(root/canon,out/'candidate-unchanged.json');shutil.copyfile(root/wave/'classified.json',out/'held-wave.private.json')
    checks['candidate_byte_identical']=sha((out/'candidate-unchanged.json').read_bytes())==fingerprints[canon]
    (out/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['before','wave','checks','claim_audit','treatment_counts']},ensure_ascii=False,indent=2));print('git snapshots',len(histories),'backup snapshots',len(archives));assert all(checks.values())
if __name__=='__main__':main()
