"""Repeated Vals models are distinguished by reviewed tools, never rank or cost."""
from copy import deepcopy
import json

from pipeline import source_adapters as adapters, vals_import


def run_rows(tmp_path, monkeypatch, mutate):
    baseline = json.loads((adapters.ROOT / 'data/expansion/vals-all-source-snapshot-2026-10-18.json').read_text())
    baseline['pages'] = [p for p in baseline['pages'] if p['slug'] == 'web_search']
    baseline['rows'] = [r for r in baseline['rows'] if r['source_slug'] == 'web_search']
    rows = deepcopy(baseline['rows'])
    mutate(rows)
    root = tmp_path / 'data/expansion'
    root.mkdir(parents=True)
    (root / 'vals-all-source-snapshot-2026-10-18.json').write_text(json.dumps(baseline))
    monkeypatch.setattr(adapters, 'ROOT', tmp_path)
    monkeypatch.setattr(vals_import, 'build_expansion', lambda snapshot, dataset: {'sources': [], 'rows': snapshot['rows']})
    headers = baseline['pages'][0]['table_headers']
    html = '<table><tr>' + ''.join(f'<th>{x}</th>' for x in headers) + '</tr>'
    for row in rows:
        html += '<tr>' + ''.join(
            f'<td><a href="{row["model_page_href"]}">{cell}</a></td>' if h == 'Model' else f'<td>{cell}</td>'
            for h, cell in zip(headers, row['cells'], strict=True)) + '</tr>'
    html += '</table>'
    path = tmp_path / 'page.html'
    path.write_text(html)

    class Archive:
        def fetch(self, url):
            return path

    return adapters._vals(Archive(), 'now', {})


def test_distinct_reviewed_tools_survive_reordering_and_price_changes(tmp_path, monkeypatch):
    def mutate(rows):
        rows.reverse()
        rows[0]['cells'][0] = '1'
        rows[0]['cells'][4] = '$999'
        rows[0]['cells'][6] = '1s'
    result, coverage = run_rows(tmp_path, monkeypatch, mutate)
    assert len(result['rows']) == 2
    by_tool = {r['protocol_cells']['Search Tool']: r for r in result['rows']}
    assert by_tool['Exa']['observation_id'] == 'o_vals_web_search_gpt56_sol_3'
    assert by_tool['Exa']['value'] == 45.24
    assert by_tool['Native']['observation_id'] == 'o_vals_web_search_gpt56_sol_4'
    assert by_tool['Native']['value'] == 43.58
    assert by_tool['Native']['protocol_cells']['Cost/Task'] == '$999'
    assert coverage['counts']['candidate_observations'] == 2


def test_duplicate_same_tool_stays_unresolved(tmp_path, monkeypatch):
    result, coverage = run_rows(tmp_path, monkeypatch, lambda rows: rows.append(deepcopy(rows[0])))
    assert [r['protocol_cells']['Search Tool'] for r in result['rows']] == ['Native']
    assert sum(d['status'] == 'unresolved_duplicate_identity' for d in coverage['decisions']) == 2


def test_unreviewed_tool_is_not_guessed_from_model_or_rank(tmp_path, monkeypatch):
    def mutate(rows):
        rows[0]['cells'][2] = 'Unreviewed search tool'
    result, coverage = run_rows(tmp_path, monkeypatch, mutate)
    assert [r['protocol_cells']['Search Tool'] for r in result['rows']] == ['Native']
    assert coverage['decisions'][0]['status'] == 'unresolved_identity'
