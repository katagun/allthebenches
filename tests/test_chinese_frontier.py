import json
from pathlib import Path

from pipeline.schema import Dataset


def test_chinese_frontier_has_reviewed_results_without_version_conflation():
    data = Dataset.model_validate_json((Path(__file__).parents[1] / 'data/curated/dataset.json').read_text())
    frontier = next(p for p in data.presets if p.id == 'frontier_oct2026')
    expected = {'deepseek', 'qwen', 'zai', 'moonshot'}
    models = {m.id: m for m in data.models}
    configs = {c.id: c for c in data.configurations}
    included = [configs[c] for c in frontier.model_configuration_ids]
    assert expected <= {lab for c in included for lab in models[c.model_id].lab_ids}
    for config in included:
        if config.id.endswith('_zai_reported'):
            scores = [o for o in data.observations if o.configuration_id == config.id]
            assert len(scores) == 5
            assert all(o.review_state == 'reviewed' for o in scores)
            assert all(o.benchmark_id in frontier.benchmark_ids for o in scores)
            assert not any(o.benchmark_id in {'terminal_bench_4', 'automationbench_reported', 'agents_last_exam_binary'} for o in scores)
    exported = json.loads((Path(__file__).parents[1] / 'data/presets/frontier_oct2026.json').read_text())
    assert exported['model_configuration_ids'] == frontier.model_configuration_ids
