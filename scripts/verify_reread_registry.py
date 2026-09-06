#!/usr/bin/env python3
"""本文を含まない共通再読台帳と継承元の版を検査する。"""
import argparse
import json
import yaml
from pathlib import Path
from reread_registry import validate_manifest, assess
from manage_reread_registry import check_sources, canonical
ROOT = Path(__file__).resolve().parents[1]


def check(root=ROOT, against_private=False):
    failures=[]
    paths = set((root/'data/verification/reread').glob('*.json'))
    for config in (root/'configs/planet').glob('*.yaml'):
        if (yaml.safe_load(config.read_text()) or {}).get('reread_registry'):
            paths.add(root/'data/verification/reread'/f'{config.stem}.json')
    for path in sorted(paths):
        try:
            manifest=json.loads(path.read_text())
            validate_manifest(manifest)
            if manifest['topic'] != path.stem:
                raise ValueError('テーマと台帳名が一致しません')
            check_sources(root,manifest)
            if against_private:
                _,rows=canonical(root,path.stem)
                result=assess(manifest,rows)
                reviewed={r['post_key'] for r in manifest['records'] if r['review']}
                stale={'removed','body_changed','issue_changed','opinion_changed'}
                if any(r['post_key'] in reviewed and stale.intersection(r['statuses']) for r in result['records']):
                    raise ValueError('再読済み投稿が原本から変化しています')
        except (ValueError,KeyError,TypeError,OSError) as exc:
            failures.append(f'{path.stem}: {exc}')
    return failures


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--against-private',action='store_true')
    args=parser.parse_args()
    failures=check(against_private=args.against_private)
    for failure in failures:print('NG',failure)
    print(f'再読共通台帳: NG {len(failures)}件')
    return bool(failures)

if __name__=='__main__':raise SystemExit(main())
