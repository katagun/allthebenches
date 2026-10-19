from pathlib import Path

from pipeline.schema import Dataset

TRACES_BENCHMARKS = {'traces_ifr_a', 'traces_ifr_i', 'traces_disclaimer_tax', 'traces_edi_mean'}
TRACES_CONFIGS = {'gpt56_sol_traces_default', 'deepseek_r1_distill_qwen_32b_traces_default', 'llama31_8b_instruct_traces_default'}


def load_dataset() -> Dataset:
    return Dataset.model_validate_json((Path(__file__).parents[1] / 'data/curated/dataset.json').read_text())


def test_traces_panel_hold_is_recorded_as_a_gap_not_silent():
    data = load_dataset()
    gap = next(g for g in data.coverage_gaps if g.id == 'gap_traces_unmapped_panel_rows')
    assert '27' in gap.scope
    sources = {s.id for s in data.sources}
    assert set(gap.source_ids) <= sources


def test_traces_observations_cover_only_exact_identities():
    data = load_dataset()
    cells = [o for o in data.observations if o.benchmark_id in TRACES_BENCHMARKS]
    assert len(cells) == 12
    assert {o.configuration_id for o in cells} == TRACES_CONFIGS
    assert all(o.review_state == 'reviewed' for o in cells)
