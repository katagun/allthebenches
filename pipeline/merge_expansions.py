"""Integrate explicitly reviewed fragments without overwriting existing records.

Call only after reviewing a fragment's identities, metric contracts and source audit.
Candidate promotion is explicit; disagreements with an existing ID fail closed.
"""
from copy import deepcopy

from pipeline.schema import Dataset

# Evaluation subsets remain in benchmark names/versions; navigation uses shared
# task categories rather than adding one tab for each evaluator's terminology.
CATEGORY_ALIASES = {
    'knowledge': 'text', 'language': 'text', 'text factuality': 'text',
    'text style control': 'text', 'vision style control': 'vision',
    'document': 'long-context', 'document style control': 'long-context',
    'search factuality': 'search', 'search style control': 'search',
    'webdev': 'coding', 'agentic coding': 'coding', 'design': 'coding',
    'mathematics': 'math', 'data analysis': 'reasoning', 'if': 'reasoning',
    'browser': 'agent', 'research': 'agent', 'long-horizon': 'agent',
}
BENCHMARK_CATEGORIES = {
    'vals_mmlu_pro_unversioned_as_reported': 'reasoning',
    'vals_public_benefits_bench_unversioned_as_reported': 'agent',
}


def canonical_category(item: dict) -> dict:
    result = deepcopy(item)
    result['category'] = BENCHMARK_CATEGORIES.get(item['id'], CATEGORY_ALIASES.get(item['category'], item['category']))
    if item['id'].startswith('arena_hf_') and ' · ' in item['name']:
        family, subset = item['name'].split(' · ', 1)
        result['name'] = family.removesuffix(' Overall') + ' · ' + subset.replace('_', ' ').capitalize()
    return result


ALLOWED_TABLES = {'sources', 'benchmarks', 'configurations', 'series', 'observations', 'external_mappings'}


def merge_fragments(dataset: dict, fragments: list[dict], *, reviewed: bool = False) -> dict:
    merged = deepcopy(dataset)
    merged['benchmarks'] = [canonical_category(b) for b in merged['benchmarks']]
    for fragment in fragments:
        for table, records in fragment.items():
            if table not in ALLOWED_TABLES:
                raise ValueError(f'Unexpected fragment table: {table}')
            index = {item['id']: item for item in merged[table]}
            for record in records:
                item = canonical_category(record) if table == 'benchmarks' else deepcopy(record)
                if table == 'observations' and reviewed and item.get('review_state') == 'candidate':
                    item['review_state'] = 'reviewed'
                old = index.get(item['id'])
                if old is not None:
                    # Schema defaults/serialization are immaterial to record equality.
                    kind = Dataset.model_fields[table].annotation.__args__[0]
                    if kind.model_validate(old) != kind.model_validate(item):
                        raise ValueError(f'Conflicting {table} ID: {item["id"]}')
                    continue
                merged[table].append(item)
                index[item['id']] = item
    Dataset.model_validate(merged)
    return merged
