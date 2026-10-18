import importlib.util
import json
from pathlib import Path

import pytest
from pipeline.schema import Dataset

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('arc_import', ROOT / 'scripts/import-arc-prize.py')
arc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arc)


def test_arc_score_missing_is_not_zero_and_unknown_format_fails():
    assert arc.score('—') is None
    assert arc.score('0.0%') == 0
    with pytest.raises(ValueError):
        arc.score('not tested')
    with pytest.raises(ValueError):
        arc.score('101%')


def test_all_arc_generations_and_harnesses_are_distinct_and_sourced():
    data = Dataset.model_validate_json((ROOT / 'data/curated/dataset.json').read_text())
    ids = {v[0] for v in arc.HEADERS.values()}
    for name in ['arc_agi', 'frontier_oct2026', 'all_models_oct2026']:
        preset = next(p for p in data.presets if p.id == name)
        assert ids <= set(preset.benchmark_ids)
    observations = [o for o in data.observations if o.id.startswith('o_arc_')]
    snapshot = json.loads((ROOT / 'data/expansion/arc-prize-scores.json').read_text())
    expected = sum(arc.score(score) is not None for model in snapshot for row in model['table'][1:] for score in row[1:])
    assert len(observations) == expected
    assert all(o.reporting_relationship == 'evaluator_measurement' and o.review_state == 'reviewed' for o in observations)
    assert all(o.setup['split'] == 'semi-private' for o in observations)
    assert {o.value for o in observations if o.configuration_id == 'gpt61_sol_max' and o.benchmark_id == 'arc_agi_3_standard'} == {52.7}
    assert {o.value for o in observations if o.configuration_id == 'gpt61_sol_max' and o.benchmark_id == 'arc_agi_3_provider_adapter'} == {96.2}
    assert not any(o.benchmark_id == 'arc_agi_3_standard' and o.setup['reasoning_effort'] == 'high' and o.source_id == 'arc_prize_gemini4_argon' for o in observations)
