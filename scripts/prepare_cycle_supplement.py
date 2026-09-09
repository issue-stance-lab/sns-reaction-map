"""Freeze supplemental work from a completed, reserved cycle range.

The source run is read-only. A new private output directory is required for
every invocation so an earlier run or saved decision is never overwritten.
"""
import argparse
import re
import sys
from pathlib import Path

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import supplemental_editorial_audit as supplemental
from scripts.continuous_editorial_review import packet_for
from scripts.editorial_acceptance import assess_batch
from scripts.editorial_work_registry import checked_packet
from scripts.verify_editorial_hundred import read, sha


PACKET_KEY = re.compile(r'^batch-(\d+)/packet\.private\.json$')


def _available_batches(reservation):
    batches = []
    for key in reservation.get('packet_hashes', {}):
        match = PACKET_KEY.fullmatch(key)
        if match:
            batches.append(int(match.group(1)))
    batches = sorted(batches)
    if not batches or batches != list(range(1, len(batches) + 1)):
        raise ValueError('source wave has invalid packet reservation')
    return batches


def prepare(root, run, wave, out, batch_start=1, batch_end=None):
    root, run, out = Path(root), Path(run), Path(out)
    if type(wave) is not int or wave < 1:
        raise ValueError('wave must be a positive integer')
    name = f'wave-{wave:02d}'
    folder = run / name
    top_path, wave_path = run / 'reservation.json', folder / 'reservation.json'
    top, wave_reservation = read(top_path), read(wave_path)
    top_sha, wave_sha = sha(top_path), sha(wave_path)
    if name not in top.get('waves', {}) or wave_sha != top['waves'][name]:
        raise ValueError('source wave reservation changed')
    if out.resolve().is_relative_to(run.resolve()):
        raise ValueError('supplement output must not be inside the source run')

    available = _available_batches(wave_reservation)
    if batch_end is None:
        batch_end = available[-1]
    if (type(batch_start) is not int or type(batch_end) is not int or
            batch_start < 1 or batch_end < batch_start or batch_end > available[-1]):
        raise ValueError('invalid source batch range')
    batches = list(range(batch_start, batch_end + 1))

    journal, sources, editors = [], {}, {}
    for batch in batches:
        directory = folder / f'batch-{batch:02d}'
        packet = packet_for(folder, batch)
        checked_packet(packet, root)
        editor = read(directory / 'editor.private.json')
        audit = read(directory / 'audit.private.json')
        gate = read(directory / 'quality_gate.private.json')
        result = assess_batch(packet, editor, audit, gate)
        for row in result['journal']:
            row = {**row, 'batch': batch}
            journal.append(row)
            raw = packet['records'][row['index']]
            sources[(batch, row['index'])] = (raw, packet['criteria'][raw['topic']])
            if row['adoption_status'] == 'pending_audit':
                editors[(batch, row['index'])] = next(
                    review for review in editor['reviews'] if review['index'] == row['index'])

    if not editors:
        return {'records': 0, 'scope': 'no pending audits in completed range'}
    if sha(top_path) != top_sha or sha(wave_path) != wave_sha:
        raise ValueError('source reservation changed during preparation')
    provenance = {
        'source_run': str(run.resolve()),
        'source_top_reservation_sha256': top_sha,
        'source_wave': name,
        'source_wave_reservation_sha256': wave_sha,
        'source_batches': batches,
    }
    return supplemental.prepare(
        root, out, journal, sources, editor_reviews=editors,
        source_provenance=provenance)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--wave', type=int, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--batch-start', type=int, default=1)
    parser.add_argument('--batch-end', type=int)
    args = parser.parse_args()
    print(prepare(args.root, args.run, args.wave, args.out,
                  args.batch_start, args.batch_end))
