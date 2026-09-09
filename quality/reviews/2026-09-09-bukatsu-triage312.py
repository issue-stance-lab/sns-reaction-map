#!/usr/bin/env python3
"""部活動の未解決312件をA/B/Cへ振り分ける（本文なし・判定台帳は読むだけ）。

出発点は作業台帳 data/verification/editorial-work.json の bukatsu-chiiki 411件。
採用状態は「現在の採用台帳 > 波別ジャーナル」の優先順、さらに 2026-09-09 の
修正候補41件の最終判定で上書きする。新しい本文確認・再分類・採用適用はしない。

使い方:
  python3 quality/reviews/2026-09-09-bukatsu-triage312.py \
      --root . --private-root /Volumes/HD-LE-B/issue-stance-private-backups/data-repairs \
      --out quality/reviews/2026-09-09-bukatsu-triage312.json
"""
import argparse
import collections
import json
import os
from pathlib import Path

TOPIC = 'bukatsu-chiiki'
FIELDS = ('is_relevant', 'is_opinion', 'main_issue', 'stance')
TRIAGE_FILES = (
    'quality/reviews/2026-09-07-cycle3000-hold-reasons.json',
    'quality/reviews/2026-09-07-cycle4000-hold-reasons.json',
    'quality/reviews/2026-09-07-cycle-holds-triaged.json',
)
# 2026-09-09 の最終判定で保留になった15件。md の「保留15件」節が挙げた原因ごとに分ける。
FINAL41_RULE = {
    40: 'B2', 28: 'B2', 33: 'B2',
    29: 'B3', 30: 'B3',
    4: 'B4', 21: 'B4', 31: 'B4', 32: 'B4', 37: 'B4', 38: 'B4',
    18: 'C4', 19: 'C4', 22: 'C4', 23: 'C4',
}


def load(root, rel):
    return json.loads((Path(root) / rel).read_text(encoding='utf-8'))


def build(root, private_root):
    work = load(root, 'data/verification/editorial-work.json')
    records = {r['record_id_hash']: r for r in work['records'] if r['topic'] == TOPIC}

    journal = {}
    for source in work['sources']:
        if source['storage'] == 'repository' and source['kind'] == 'journal':
            for row in load(root, source['path']).get('journal', []):
                if row.get('topic') == TOPIC:
                    journal[row['record_id_hash']] = (source['path'], row)

    adoption = {r['record_id_hash']: r
                for r in load(root, 'data/verification/editorial-adoption-current.json')['records']
                if r['topic'] == TOPIC}
    final41 = {r['record_id_hash']: r
               for r in load(root, 'quality/reviews/2026-09-09-bukatsu-final41-results.json')['records']}

    triage = {}
    for path in TRIAGE_FILES:
        for row in load(root, path)['records']:
            if row['topic'] == TOPIC:
                triage[row['record_id_hash']] = (path, row)

    opinions = {r['record_id_hash'] for r in load(root, f'data/verification/{TOPIC}.json')
                if r['classification'].get('is_opinion')}

    gates = {}
    for key, row in records.items():
        for evidence in row['evidence']:
            if evidence.endswith('packet.private.json'):
                batch = os.path.dirname(evidence)
                path = Path(private_root) / batch / 'quality_gate.private.json'
                gates[key] = (batch, json.loads(path.read_text(encoding='utf-8')) if path.is_file() else None)

    out = []
    for key, row in records.items():
        if key not in journal:
            continue  # 判定を持たない attempted 1件は対象外
        source, entry = journal[key]
        status = adoption[key]['adoption_status'] if key in adoption else entry.get('adoption_status', '-')
        basis = adoption[key].get('adoption_basis') if key in adoption else entry.get('adoption_basis', '-')
        final = final41.get(key)
        if final is not None:
            if final['decision'] != 'hold':
                continue  # 2026-09-09 に判定確定（未解決ではない）
            status, basis = 'hold', 'final41_hold'
        elif status == 'accepted':
            continue  # 採用台帳で確定済み

        proposed = entry.get('proposed')
        independent = entry.get('independent_proposed')
        checked = bool(entry.get('independently_checked')) and independent is not None
        differing = sorted(f for f in FIELDS if checked and independent.get(f) != proposed.get(f))
        batch, gate = gates.get(key, (None, None))
        hint = triage.get(key)

        if basis == 'final41_hold':
            bucket_group = FINAL41_RULE[final['id']]
        elif basis == 'criteria_issue':
            bucket_group = 'B1'
        elif basis == 'insufficient_or_conflicting_reason':
            bucket_group = 'C3'
        elif not checked:
            bucket_group = 'C2'
        elif differing:
            bucket_group = 'C1'
        else:
            bucket_group = 'C1b'

        out.append({
            'record_id_hash': key,
            'body_sha256': row['body_sha256'],
            'in_current_opinions': key in opinions,
            'bucket': bucket_group[0],
            'group': bucket_group,
            'adoption_status': status,
            'adoption_basis': basis,
            'route': entry['route'],
            'independently_checked': checked,
            'differing_fields': differing,
            'evidence': {
                'journal': source,
                'work_evidence': row['evidence'],
                'reason_sha256': entry.get('reason_sha256'),
                'independent_reason_sha256': entry.get('independent_reason_sha256'),
                'quality_gate_batch': batch,
                'gate_systemic_criteria_issue': None if gate is None else gate['systemic_criteria_issue'],
                'reason_group_hint': None if hint is None else {
                    'source': hint[0], 'group': hint[1]['reason_group'],
                    'method': hint[1]['grouping_method'], 'next_action': hint[1]['next_action'],
                },
                'final41_id': None if final is None else final['id'],
                'final41_pending_fields': None if final is None else final.get('pending_fields'),
            },
        })
    out.sort(key=lambda r: (r['group'], r['record_id_hash']))
    return work, out


GROUP_LABEL = {
    'B1': '論点（main_issue）体系に不足があり、組ごと停止している',
    'B2': '廃止要求・批判を全体の賛否へ変換するかが未定',
    'B3': '期待・称賛を移行支持に数えるかが未定',
    'B4': '肯定を含む要求・願い・問題指摘を支持と条件付きのどちらへ置くかが未定',
    'C1': '編集担当と独立監査で分類項目が食い違ったまま',
    'C1b': '両者一致だが編集担当が保留を選び、理由が確定していない',
    'C2': '独立監査が無いまま保留',
    'C3': '保存理由に矛盾がある',
    'C4': '発言者・引用元・前後文脈が欠ける',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--private-root', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()

    work, rows = build(args.root, args.private_root)
    counts = collections.Counter(r['bucket'] for r in rows)
    groups = collections.Counter(r['group'] for r in rows)
    result = {
        'schema_version': 1,
        'scope': 'Routing of unresolved records only; no canonical, adoption, page or public change.',
        'topic': TOPIC,
        'work_registry_records': sum(1 for r in work['records'] if r['topic'] == TOPIC),
        'resolved_excluded': sum(1 for r in work['records'] if r['topic'] == TOPIC) - 1 - len(rows),
        'unresolved': len(rows),
        'bucket_counts': dict(sorted(counts.items())),
        'group_counts': dict(sorted(groups.items())),
        'group_labels': GROUP_LABEL,
        'in_current_opinions': sum(1 for r in rows if r['in_current_opinions']),
        'not_in_current_opinions': sum(1 for r in rows if not r['in_current_opinions']),
        'new_body_reviews': 0,
        'canonical_changes': 0,
        'adoption_ledger_changes': 0,
        'public_changes': 0,
        'records': rows,
    }
    if args.out:
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    summary = {k: v for k, v in result.items() if k != 'records' and k != 'group_labels'}
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
