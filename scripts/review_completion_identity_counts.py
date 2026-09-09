"""Body-free duplicate accounting; a bare global ID is reference, not exclusion.

An exact global ID/body/classification repeat blocks even across different themes.

Call after validating completion journals. This helper grants no review credit.
The baseline must be the frozen work-before registry, never the current registry.
"""
from collections import Counter, defaultdict

from scripts.editorial_work_registry import STATES


POST = ('topic', 'record_id_hash')
VERSION = (*POST, 'body_sha256', 'classification_sha256')
GLOBAL_VERSION = ('record_id_hash', 'body_sha256', 'classification_sha256')


def identity_counts(journals, scope, baseline):
    """Accept journal lists, resolved scope and frozen baseline dictionaries.

``blocking`` counts must all be zero. ``reference`` deliberately includes old
attempts, distinct IDs sharing text, and global IDs recurring across themes.
Duplicate counts mean excess rows; baseline overlap counts mean affected rows.
Criteria come from scope because completed journals omit that field.
"""
    rows = [row for journal in journals for row in journal]
    key = lambda row, fields: tuple(row[field] for field in fields)
    scoped = {key(row, POST): row for row in scope['records']}
    if len(scoped) != len(scope['records']):
        raise ValueError('duplicate scope topic/post identity')
    for row in rows:
        original = scoped.get(key(row, POST))
        if original is None or key(original, VERSION) != key(row, VERSION):
            raise ValueError('completed identity/version differs from scope')
        if 'criteria_sha256' in row and row['criteria_sha256'] != original['criteria_sha256']:
            raise ValueError('completed criteria differs from scope')
    if any(row['state'] not in STATES for row in baseline['records']):
        raise ValueError('unknown baseline work state')
    completed = [row for row in baseline['records'] if row['state'] != 'attempted']
    attempts = [row for row in baseline['records'] if row['state'] == 'attempted']
    baseline_posts = {key(row, POST) for row in completed}
    baseline_versions = {key(row, VERSION) for row in completed}
    baseline_global_versions = {key(row, GLOBAL_VERSION) for row in completed}
    attempt_versions = {key(row, VERSION) for row in attempts}
    versioned = [(*key(row, VERSION), scoped[key(row, POST)]['criteria_sha256']) for row in rows]
    baseline_versioned = {key(row, (*VERSION, 'criteria_sha256')) for row in completed}
    post_counts = Counter(key(row, POST) for row in rows)
    version_counts = Counter(key(row, VERSION) for row in rows)
    global_version_counts = Counter(key(row, GLOBAL_VERSION) for row in rows)
    global_topics, baseline_global_topics = defaultdict(set), defaultdict(set)
    for row in rows:
        global_topics[row['record_id_hash']].add(row['topic'])
    for row in completed:
        baseline_global_topics[row['record_id_hash']].add(row['topic'])
    recurring = sorted(set(global_topics) & set(baseline_global_topics))
    aliases = [row for row in rows if scoped[key(row, POST)]['route'].startswith('verify_distinct_id_')]
    return {
        'records': len(rows),
        'blocking': {
            'topic_id_duplicate_excess_rows': sum(n - 1 for n in post_counts.values()),
            'topic_id_body_classification_duplicate_excess_rows': sum(n - 1 for n in version_counts.values()),
            'topic_id_body_classification_criteria_duplicate_excess_rows': len(versioned) - len(set(versioned)),
            'global_id_body_classification_duplicate_excess_rows': sum(n - 1 for n in global_version_counts.values()),
            'previously_completed_topic_id_rows': sum(key(row, POST) in baseline_posts for row in rows),
            'previously_completed_topic_id_body_classification_rows': sum(key(row, VERSION) in baseline_versions for row in rows),
            'previously_completed_full_version_rows': sum(value in baseline_versioned for value in versioned),
            'previously_completed_global_id_body_classification_rows': sum(key(row, GLOBAL_VERSION) in baseline_global_versions for row in rows),
        },
        'reference': {
            'baseline_completed_records': len(completed),
            'baseline_attempted_records': len(attempts),
            'resumed_attempted_version_rows': sum(key(row, VERSION) in attempt_versions for row in rows),
            'distinct_id_verification_rows': len(aliases),
            'global_id_distinct_count': len(global_topics),
            'global_id_across_theme_recurrences': [
                {'record_id_hash': post, 'topics': sorted(topics)}
                for post, topics in sorted(global_topics.items()) if len(topics) > 1],
            'global_id_reappears_in_baseline_completed_count': len(recurring),
            'global_id_reappears_in_baseline_completed': [
                {'record_id_hash': post, 'current_topics': sorted(global_topics[post]),
                 'baseline_topics': sorted(baseline_global_topics[post])} for post in recurring],
        },
    }
