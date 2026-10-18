"""Stage exact-model observations from an official Epoch CSV archive, without editing curated data."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import zipfile

URL = 'https://epoch.ai/data/benchmark_data.zip'

# Public CSV primary measures missing from benchmark_metadata.source_file.
# Values remain on the archive's original scale; no guessed percent conversion.
EXTERNAL_MEASURES = {
    # https://evals.futuresearch.ai/#btf3: pooled Brier scale, lower is better.
    'btf3': ('Bench to the Future 3', 'Pooled score', 'reasoning', 'lower'),
    'scicode': ('SciCode', 'Score', 'coding', 'higher'),
    'critpt': ('CritPt', 'Accuracy', 'reasoning', 'higher'),
    'cursorbench': ('CursorBench', 'Score', 'coding', 'higher'),
    'gdp_pdf': ('GDP.pdf', 'GDP.pdf score', 'agent', 'higher'),
    'webdev_arena': ('WebDev Arena', 'Arena Score', 'coding', 'higher'),
    'ale_bench': ('ALE-Bench', 'Performance', 'coding', 'higher'),
    'vending_bench_2': ('Vending-Bench 2', 'Score', 'agent', 'higher'),
    'weirdml_v3': ('WeirdML v3', 'Score', 'coding', 'higher'),
    'blueprint_bench_2': ('BlueprintBench 2', 'Score', 'reasoning', 'higher'),
    'bool_q': ('BoolQ', 'Score', 'text', 'higher'),
    'gbaeval': ('GBAEval', 'Overall score', 'agent', 'higher'),
    'live_bench': ('LiveBench', 'Global average', 'reasoning', 'higher'),
    'enigma_eval': ('EnigmaEval', 'Accuracy', 'reasoning', 'higher'),
    'algotune': ('AlgoTune', 'Score', 'coding', 'higher'),
    'video_mme': ('Video-MME', 'Overall (no subtitles)', 'multimodal', 'higher'),
}


def category_for(filename: str) -> str:
    key = filename.removesuffix('_external.csv').removesuffix('.csv')
    if key in EXTERNAL_MEASURES:
        return EXTERNAL_MEASURES[key][2]
    for category, words in {
        'math': ('math', 'otis', 'gsm8k', 'proofbench'),
        'coding': ('swe', 'code', 'aider', 'weirdml', 'gso', 'posttrain', 'terminal'),
        'agent': ('agent', 'balrog', 'ebr', 'spire', 'furniture', 'osworld', 'metr'),
        'cybersecurity': ('cybench', 'exploit'),
        'long-context': ('fictionlive',),
        'text': ('mmlu', 'trivia', 'simpleqa', 'writing', 'lambada', 'hella', 'wino'),
        'multimodal': ('science_qa', 'cad_eval', 'geo'),
    }.items():
        if any(word in key for word in words):
            return category
    return 'reasoning'



def slug(value: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', value.lower()).strip('_')


def csv_rows(archive: zipfile.ZipFile, filename: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(archive.read(filename).decode('utf-8-sig'))))


def stage(archive_bytes: bytes, mappings: dict, retrieved_at: str) -> tuple[dict, dict]:
    archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
    archive_hash = hashlib.sha256(archive_bytes).hexdigest()
    definitions = {r['source_file']: r for r in csv_rows(archive, 'benchmark_metadata.csv') if r['source_file']}
    fragment = {k: [] for k in ('sources', 'benchmarks', 'configurations', 'series', 'observations')}
    configs, series_ids, observation_ids = set(), set(), set()
    records = []
    for filename in sorted(archive.namelist()):
        if not filename.endswith('.csv') or '/' in filename or filename.endswith('_metadata.csv'):
            continue
        rows = csv_rows(archive, filename)
        definition = definitions.get(filename)
        contract = EXTERNAL_MEASURES.get(filename.removesuffix('_external.csv'))
        if definition is None and contract:
            definition = {'benchmark': contract[0], 'score_column': contract[1]}
        internal = bool(rows and 'mean_score' in rows[0])
        # Three direct suites are not yet listed in benchmark_metadata.csv.
        if internal and definition is None:
            definition = {'benchmark': filename.removesuffix('.csv').replace('_', ' '), 'score_column': 'mean_score', 'release_date': ''}
        field = 'mean_score' if internal else (definition or {}).get('score_column')
        source_id = 'epoch_20261018_' + filename.removesuffix('.csv')
        benchmark_id = 'epoch_' + filename.removesuffix('.csv')
        used = False
        for index, row in enumerate(rows):
            external = row.get('Model version', '')
            item = {'file': filename, 'row': index + 2, 'external_model': external}
            mapping = mappings.get(external)
            if not mapping:
                records.append({**item, 'status': 'unresolved_model'}); continue
            item['model_id'] = mapping['model_id']
            if not field or field not in row:
                records.append({**item, 'status': 'excluded_unreviewed_metric_contract'}); continue
            try:
                raw = float(row[field])
                if not math.isfinite(raw) or (internal and not 0 <= raw <= 1):
                    raise ValueError('invalid score')
            except (ValueError, TypeError):
                records.append({**item, 'status': 'excluded_missing_or_invalid_score'}); continue
            unit, value = ('%', raw * 100) if internal else ('source score', raw)
            efforts = ('none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max')
            effort = external.rsplit('_', 1)[-1]
            reported_efforts = {
                row[key].strip().lower().replace('extra high', 'xhigh')
                for key in ('Reasoning effort', 'Reasoning level', 'Reasoning') if row.get(key)
            }
            reported_efforts &= set(efforts)
            if len(reported_efforts) > 1 or (effort in efforts and reported_efforts and effort not in reported_efforts):
                records.append({**item, 'status': 'excluded_conflicting_reasoning_settings'}); continue
            configuration_id = 'epoch_config_' + slug(external)
            if effort not in efforts and reported_efforts:
                effort = next(iter(reported_efforts))
                configuration_id += '_reported_' + effort
            if configuration_id not in configs:
                known = effort in efforts
                fragment['configurations'].append({'id': configuration_id, 'model_id': mapping['model_id'],
                    'reasoning_label': effort if known else 'not stated (Epoch)',
                    'mode': ('disabled' if effort == 'none' else 'enabled') if known else 'unknown'})
                configs.add(configuration_id)
            identity = row.get('id') or hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()[:20]
            observation_id = f'{benchmark_id}_{slug(identity)}'
            if observation_id in observation_ids:
                records.append({**item, 'status': 'duplicate_run', 'observation_id': observation_id}); continue
            observation_ids.add(observation_id)
            series_id = benchmark_id + '_archive_series'
            if series_id not in series_ids:
                fragment['series'].append({'id': series_id, 'benchmark_id': benchmark_id,
                    'evaluator': 'Epoch AI' if internal else 'External evaluator via Epoch AI',
                    'protocol': f'Epoch archive {filename}, column {field}; per-run settings and original links retained in setup.',
                    'comparability_status': 'unknown', 'comparability': 'Do not assume the same settings across archive rows; inspect each run.'})
                series_ids.add(series_id)
            uncertainty = None
            if internal and row.get('stderr'):
                try:
                    se = float(row['stderr'])
                except ValueError:
                    se = float('nan')
                if math.isfinite(se) and se >= 0:
                    uncertainty = {'standard_error': se * 100, 'unit': '%', 'source_field': 'stderr'}
            fragment['observations'].append({'id': observation_id, 'configuration_id': configuration_id,
                'benchmark_id': benchmark_id, 'series_id': series_id, 'value': value, 'unit': unit,
                'source_id': source_id, 'locator': f'{filename}, CSV row {index + 2}, {field}; source run {identity}',
                'evaluator': 'Epoch AI' if internal else 'External evaluator via Epoch AI',
                'reporting_relationship': 'evaluator_measurement' if internal else 'quoted_result',
                'evaluated_at': row.get('Started at') or None,
                'setup': {'source_model_version': external, 'raw_score': raw, 'source_score_column': field,
                          'conversion': 'fraction × 100' if internal else 'none; original source scale',
                          'archive_sha256': archive_hash, 'source_row': row},
                'uncertainty': uncertainty, 'review_state': 'candidate'})
            records.append({**item, 'status': 'staged', 'observation_id': observation_id})
            used = True
        if used:
            fragment['sources'].append({'id': source_id, 'url': URL, 'title': f'Epoch AI benchmark archive: {filename}',
                'publisher': 'Epoch AI', 'retrieved_at': retrieved_at,
                'content_sha256': hashlib.sha256(archive.read(filename)).hexdigest(),
                'license': 'CC BY 4.0' if internal else 'External source terms retained; see original links in each observation',
                'attribution': 'Epoch AI, Capabilities & benchmarking; external results also credit their original publishers.',
                'method': 'CSV extraction from official ZIP', 'locator': filename,
                'version': archive_hash})
            fragment['benchmarks'].append({'id': benchmark_id, 'family_id': benchmark_id.removesuffix('_external'),
                'name': definition['benchmark'] + ' (Epoch)', 'version': 'archive variant: ' + filename.removesuffix('.csv'),
                'category': category_for(filename), 'modality': 'multimodal' if category_for(filename) == 'multimodal' else 'text', 'metric_name': field,
                'unit': '%' if internal else 'source score', 'direction': contract[3] if contract else 'higher',
                'lower_bound': 0 if internal else None, 'upper_bound': 100 if internal else None,
                'owner': 'Epoch AI' if internal else 'Original publisher (via Epoch AI)',
                'documentation_url': 'https://epoch.ai/benchmarks/use-this-data'})
    from collections import Counter
    report = {'source': URL, 'archive_sha256': archive_hash, 'retrieved_at': retrieved_at,
              'scope': 'Primary score column per top-level benchmark CSV; exact reviewed model versions only. Metadata and processed ECI duplicates excluded.',
              'counts': dict(Counter(r['status'] for r in records)), 'records': records}
    return fragment, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--mappings', type=Path, default=Path('data/mappings/epoch_models.json'))
    parser.add_argument('--retrieved-at', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    fragment, report = stage(args.archive.read_bytes(), json.loads(args.mappings.read_text()), args.retrieved_at)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(fragment, indent=2, ensure_ascii=False) + '\n')
    args.output.with_suffix('.coverage.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['counts'])


if __name__ == '__main__':
    main()
