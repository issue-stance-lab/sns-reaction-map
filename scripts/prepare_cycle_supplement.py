"""Freeze supplemental work as soon as a 20-batch chunk has completed gates."""
import argparse
from pathlib import Path
from scripts import supplemental_editorial_audit as supplemental
from scripts.continuous_editorial_review import packet_for
from scripts.editorial_acceptance import assess_batch
from scripts.editorial_work_registry import checked_packet
from scripts.verify_editorial_hundred import read,sha


def prepare(root,run,wave,part):
    root,run=Path(root),Path(run);name=f'wave-{wave:02d}';folder=run/name
    if wave not in [1,2] or part not in [1,2,3]:raise ValueError('invalid wave/part')
    top=read(run/'reservation.json')
    if top!=read(root/'quality/reviews/2026-09-07-cycle-next2000-reservation-v2.json') or sha(folder/'reservation.json')!=top['waves'][name]:raise ValueError('reservation changed')
    batches=[range(1,21),range(21,41),range(41,51)][part-1];journal=[];sources={};editors={}
    for b in batches:
        d=folder/f'batch-{b:02d}';packet=packet_for(folder,b);checked_packet(packet,root)
        editor=read(d/'editor.private.json');audit=read(d/'audit.private.json')
        result=assess_batch(packet,editor,audit,read(d/'quality_gate.private.json'))
        for row in result['journal']:
            row={**row,'batch':b};journal.append(row);raw=packet['records'][row['index']];sources[(b,row['index'])]=(raw,packet['criteria'][raw['topic']])
            if row['adoption_status']=='pending_audit':editors[(b,row['index'])]=next(x for x in editor['reviews'] if x['index']==row['index'])
    out=run/f'supplement-{name}-part-{part:02d}'
    if not editors:return {'records':0,'scope':'no pending audits in completed chunk'}
    return supplemental.prepare(root,out,journal,sources,editor_reviews=editors)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--wave',type=int,required=True);p.add_argument('--part',type=int,required=True);a=p.parse_args();print(prepare(a.root,a.run,a.wave,a.part))
