import csv
import io
import json
import zipfile
from pathlib import Path

from pipeline.epoch_import import stage
from pipeline.schema import Dataset


def archive(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as z:
        for name, rows in files.items():
            stream = io.StringIO()
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
            z.writestr(name, stream.getvalue())
    return buffer.getvalue()


def test_exact_identity_zero_missing_and_mean_not_best():
    payload = archive({
        'benchmark_metadata.csv': [{'source_file': 'gpqa_diamond.csv', 'benchmark': 'GPQA', 'score_column': 'Best score (across scorers)'}],
        'gpqa_diamond.csv': [
            {'Model version': m, 'mean_score': score, 'Best score (across scorers)': '1', 'stderr': 'bad', 'id': str(i)}
            for i, (m, score) in enumerate([('exact_high', '0'), ('exact_high', '.5'), ('exact_high', ''), ('exact_high', 'nan'), ('similar', '.8')])
        ],
    })
    result, audit = stage(payload, {'exact_high': {'model_id': 'canonical'}}, '2026-10-18T00:00:00Z')
    assert [o['value'] for o in result['observations']] == [0, 50]
    assert all(o['uncertainty'] is None and o['review_state'] == 'candidate' for o in result['observations'])
    assert result['configurations'][0]['reasoning_label'] == 'high'
    assert audit['counts'] == {'staged': 2, 'excluded_missing_or_invalid_score': 2, 'unresolved_model': 1}


def test_external_lower_is_better_keeps_raw_scale_and_unknown_effort():
    payload = archive({
        'benchmark_metadata.csv': [{'source_file': '', 'benchmark': '', 'score_column': ''}],
        'btf3_external.csv': [{'Model version': 'exact_unknown', 'Pooled score': '.135', 'Harness': 'FutureSearch agent'}],
    })
    result, _ = stage(payload, {'exact_unknown': {'model_id': 'canonical'}}, '2026-10-18T00:00:00Z')
    assert result['benchmarks'][0]['direction'] == 'lower'
    assert result['observations'][0]['value'] == .135
    assert result['observations'][0]['setup']['source_row']['Harness'] == 'FutureSearch agent'
    assert result['configurations'][0]['mode'] == 'unknown'


def test_staged_epoch_references_validate_without_duplicate_import():
    root = Path(__file__).resolve().parents[1]
    curated = json.loads((root / 'data/curated/dataset.json').read_text())
    fragment = json.loads((root / 'data/expansion/epoch-2026-10-18.json').read_text())
    for key, rows in fragment.items():
        existing = {r['id'] for r in curated[key]}
        curated[key].extend(row for row in rows if row['id'] not in existing)
    Dataset.model_validate(curated)


def test_conflicting_reasoning_is_excluded_but_explicit_row_setting_is_used():
    payload = archive({
        'benchmark_metadata.csv': [{'source_file': '', 'benchmark': '', 'score_column': ''}],
        'scicode_external.csv': [
            {'Model version': 'exact_max', 'Score': '.5', 'Reasoning effort': 'medium'},
            {'Model version': 'exact_unknown', 'Score': '.6', 'Reasoning effort': 'high'},
        ],
    })
    result, audit = stage(payload, {v: {'model_id': 'canonical'} for v in ['exact_max', 'exact_unknown']}, '2026-10-18T00:00:00Z')
    assert audit['counts'] == {'excluded_conflicting_reasoning_settings': 1, 'staged': 1}
    assert result['configurations'][0]['reasoning_label'] == 'high'
    assert result['observations'][0]['setup']['source_model_version'] == 'exact_unknown'
