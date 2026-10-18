"""Generate crawlable HTML reference pages from reviewed dataset records."""
from __future__ import annotations

from html import escape
from pathlib import Path
from urllib.parse import quote

from .build import select_observations
from .schema import Dataset

SITE = "https://allthebenches.com"
GENERATOR_MARKER = '<meta name="generator" content="allthebenches-static-pages">'
DISCLAIMER = ("Scores are reported for the exact configurations and benchmark variants shown. "
              "Missing scores mean no reviewed result is published here; they do not mean zero.")


def _e(value: object) -> str:
    return escape(str(value), quote=True)


def _url(value: str | None) -> str | None:
    if not value:
        return None
    from urllib.parse import urlsplit
    try:
        parsed = urlsplit(value)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            return None
        return value
    except ValueError:
        return None


def _link(url: str | None, label: str) -> str:
    safe = _url(url)
    if safe is None:
        return _e(label)
    return f'<a href="{_e(safe)}" rel="noopener noreferrer">{_e(label)}</a>'


def _document(title: str, description: str, canonical: str, body: str) -> str:
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
{GENERATOR_MARKER}<title>{_e(title)} | All the Benches</title><meta name="description" content="{_e(description)}">
<link rel="canonical" href="{_e(canonical)}"><style>
:root{{color-scheme:light;--ink:#17202a;--muted:#586573;--line:#d9e0e6;--surface:#fff;--wash:#f4f7f9;--accent:#245b79}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--wash);color:var(--ink);font:16px/1.55 system-ui,-apple-system,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:1.25rem}}header,section,.notice{{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:1rem;margin:1rem 0}}
h1{{line-height:1.2}}h2{{font-size:1.25rem}}a{{color:var(--accent);overflow-wrap:anywhere}}nav{{display:flex;gap:1rem;flex-wrap:wrap}}.muted{{color:var(--muted)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,290px),1fr));gap:.8rem}}.card{{border:1px solid var(--line);border-radius:8px;padding:.8rem;min-width:0}}
dl{{display:grid;grid-template-columns:minmax(8rem,auto) 1fr;gap:.25rem .75rem}}dt{{color:var(--muted)}}dd{{margin:0;overflow-wrap:anywhere}}
table{{width:100%;border-collapse:collapse}}th,td{{text-align:left;vertical-align:top;padding:.6rem;border-bottom:1px solid var(--line)}}.scroll{{overflow-x:auto}}
@media(max-width:600px){{main{{padding:.65rem}}dl{{grid-template-columns:1fr}}dt{{font-weight:600}}dd{{margin-bottom:.45rem}}th,td{{padding:.45rem}}}}
</style></head><body><main>{body}</main></body></html>'''


def _prune_stale_pages(directory: Path, current_slugs: set[str]) -> None:
    """Remove only our marked stale index files; retain directories and assets."""
    for entry in directory.iterdir():
        if entry.name in current_slugs or entry.is_symlink() or not entry.is_dir():
            continue
        index = entry / "index.html"
        if not index.is_file():
            continue
        try:
            generated = GENERATOR_MARKER in index.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            generated = False
        if generated:
            index.unlink()
            try:
                entry.rmdir()
            except OSError:
                pass


def _cell_status(state: str) -> str:
    return {"disputed": "Disputed reports", "agreed": "Agreed reports"}.get(state, "Reviewed report")


def _nav(kind: str | None = None, entity: str | None = None, entity_id: str | None = None) -> str:
    links = [f'<a href="{SITE}/#/">Comparison matrix</a>',
             f'<a href="{SITE}/models/">Models</a>', f'<a href="{SITE}/benchmarks/">Benchmarks</a>']
    if kind and entity_id:
        links.append(f'<a href="{SITE}/#/{kind}/{quote(entity_id, safe="")}">Open interactive {entity} page</a>')
    return "<nav>" + "".join(links) + "</nav>"


def _source_refs(ids: list[str], sources: dict) -> str:
    items = []
    for source_id in sorted(set(ids)):
        source = sources.get(source_id)
        if source:
            items.append(_link(source.url, source.title or source.id))
    return ", ".join(items) if items else '<span class="muted">No source link available</span>'


def _config_label(config) -> str:
    labels = [config.reasoning_label, config.mode if config.mode != "unknown" else None,
              f"{config.reasoning_budget_tokens} reasoning tokens" if config.reasoning_budget_tokens is not None else None,
              config.precision]
    return ", ".join(_e(v) for v in labels if v) or "Configuration details unknown"


def _benchmark_label(benchmark) -> str:
    parts = [benchmark.version, benchmark.subset, benchmark.split, benchmark.metric_name]
    return " · ".join(_e(v) for v in parts if v)


def build_static_pages(dataset: Dataset, output: Path) -> None:
    """Write deterministic model and benchmark detail pages and crawler metadata."""
    if any(item.id in {".", "..", ""} for item in [*dataset.models, *dataset.benchmarks]):
        raise ValueError("Invalid static page identifier")
    output.mkdir(parents=True, exist_ok=True)
    models = {item.id: item for item in dataset.models}
    configs = {item.id: item for item in dataset.configurations}
    benchmarks = {item.id: item for item in dataset.benchmarks}
    sources = {item.id: item for item in dataset.sources}
    labs = {item.id: item for item in dataset.labs}
    cells = select_observations(dataset)
    published_ids = {oid for cell in cells for oid in cell["observation_ids"]}
    observations = {o.id: o for o in dataset.observations if o.review_state == "reviewed" and o.id in published_ids}
    pages: list[str] = []

    model_dir = output / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_slugs = {quote(item.id, safe="") for item in dataset.models}
    _prune_stale_pages(model_dir, model_slugs)
    for model in sorted(dataset.models, key=lambda item: item.id):
        slug = quote(model.id, safe="")
        directory = model_dir / slug
        directory.mkdir(parents=True, exist_ok=True)
        lab_names = [labs[i].name for i in model.lab_ids if i in labs]
        own_scores = []
        for cell in cells:
            config = configs.get(cell["configuration_id"])
            if config is None or config.model_id != model.id:
                continue
            benchmark = benchmarks.get(cell["benchmark_id"])
            if benchmark is None:
                continue
            for oid in cell["observation_ids"]:
                obs = observations.get(oid)
                if obs is None:
                    continue
                own_scores.append((benchmark.name, _benchmark_label(benchmark), config, obs, cell["state"]))
        score_cards = []
        for name, variant, config, obs, state in sorted(own_scores, key=lambda row: (row[0], row[1], row[2].id, row[3].id)):
            source = sources.get(obs.source_id)
            source_label = source.title if source else obs.source_id
            score_cards.append(f'<article class="card"><h3>{_e(name)}</h3><p><strong>{_e(obs.value)} {_e(obs.unit)}</strong></p>'
                f'<p class="muted">{_cell_status(state)}</p>'
                f'<dl><dt>Variant and metric</dt><dd>{variant}</dd><dt>Configuration</dt><dd>{_config_label(config)}</dd>'
                f'<dt>Evaluator</dt><dd>{_e(obs.evaluator)}</dd><dt>Source</dt><dd>{_link(source.url if source else None, source_label)}</dd>'
                f'<dt>Reported location</dt><dd>{_e(obs.locator or "Not specified")}</dd></dl></article>')
        body = (_nav("models", "model", model.id) + f'<header><h1>{_e(model.name)}</h1><p class="muted">{_e(model.id)}</p>'
                f'<p>{_e(", ".join(lab_names) or "Organization unknown")}</p><p>{DISCLAIMER}</p></header>'
                f'<section><h2>Reviewed benchmark results</h2><div class="grid">{"".join(score_cards) if score_cards else "<p>No reviewed scores are published for this model.</p>"}</div></section>')
        (directory / "index.html").write_text(_document(model.name, f"Reviewed benchmark results for {model.name}.", f"{SITE}/models/{slug}/", body), encoding="utf-8")
        pages.append(f"{SITE}/models/{slug}/")

    model_items = "".join(f'<li><a href="{quote(m.id, safe="")}/">{_e(m.name)}</a></li>' for m in sorted(dataset.models, key=lambda item: (item.name.casefold(), item.id)))
    (model_dir / "index.html").write_text(_document("Models", "Reviewed model releases and benchmark results.", f"{SITE}/models/", _nav() + f'<header><h1>Models</h1><p>{DISCLAIMER}</p></header><section><ul>{model_items}</ul></section>'), encoding="utf-8")

    benchmark_dir = output / "benchmarks"
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    benchmark_slugs = {quote(item.id, safe="") for item in dataset.benchmarks}
    _prune_stale_pages(benchmark_dir, benchmark_slugs)
    for benchmark in sorted(dataset.benchmarks, key=lambda item: item.id):
        slug = quote(benchmark.id, safe="")
        directory = benchmark_dir / slug
        directory.mkdir(parents=True, exist_ok=True)
        rows = []
        for cell in cells:
            if cell["benchmark_id"] != benchmark.id:
                continue
            config = configs.get(cell["configuration_id"])
            model = models.get(config.model_id) if config else None
            if not config or not model:
                continue
            for oid in cell["observation_ids"]:
                obs = observations.get(oid)
                if obs is None:
                    continue
                source = sources.get(obs.source_id)
                rows.append((model.name, model.id, config, obs, source, cell["state"]))
        result_rows = "".join(f'<tr><td><a href="{SITE}/models/{quote(mid, safe="")}/">{_e(name)}</a></td><td>{_config_label(config)}</td>'
            f'<td>{_cell_status(state)}</td>'
            f'<td>{_e(obs.value)} {_e(obs.unit)}</td><td>{_e(obs.evaluator)}</td><td>{_link(source.url if source else None, source.title if source else obs.source_id)}</td></tr>'
            for name, mid, config, obs, source, state in sorted(rows, key=lambda row: (row[0].casefold(), row[2].id, row[3].id)))
        details = [f"<dt>Version</dt><dd>{_e(benchmark.version)}</dd>", f"<dt>Metric</dt><dd>{_e(benchmark.metric_name)} ({_e(benchmark.unit)})</dd>",
                   f"<dt>Category</dt><dd>{_e(benchmark.category)}</dd>", f"<dt>Direction</dt><dd>{_e(benchmark.direction)}</dd>"]
        for label, value in (("Subset", benchmark.subset), ("Split", benchmark.split), ("Task", benchmark.task), ("Scorer version", benchmark.scorer_version)):
            if value:
                details.append(f"<dt>{label}</dt><dd>{_e(value)}</dd>")
        if benchmark.documentation_url:
            details.append(f"<dt>Documentation</dt><dd>{_link(benchmark.documentation_url, benchmark.documentation_url)}</dd>")
        body = (_nav("benchmarks", "benchmark", benchmark.id) + f'<header><h1>{_e(benchmark.name)}</h1><p class="muted">{_e(benchmark.id)}</p><p>{DISCLAIMER}</p></header>'
                f'<section><h2>Benchmark variant</h2><dl>{"".join(details)}</dl></section><section><h2>Reviewed scores</h2><div class="scroll"><table><thead><tr><th>Model</th><th>Configuration</th><th>Evidence status</th><th>Score</th><th>Evaluator</th><th>Source</th></tr></thead><tbody>{result_rows}</tbody></table></div>'
                f'{"" if result_rows else "<p>No reviewed scores are published for this benchmark.</p>"}</section>')
        (directory / "index.html").write_text(_document(benchmark.name, f"Reviewed results for {benchmark.name}.", f"{SITE}/benchmarks/{slug}/", body), encoding="utf-8")
        pages.append(f"{SITE}/benchmarks/{slug}/")
    benchmark_items = "".join(f'<li><a href="{quote(b.id, safe="")}/">{_e(b.name)} — {_benchmark_label(b)}</a></li>' for b in sorted(dataset.benchmarks, key=lambda item: (item.name.casefold(), item.id)))
    (benchmark_dir / "index.html").write_text(_document("Benchmarks", "Reviewed benchmark variants and results.", f"{SITE}/benchmarks/", _nav() + f'<header><h1>Benchmarks</h1><p>{DISCLAIMER}</p></header><section><ul>{benchmark_items}</ul></section>'), encoding="utf-8")
    (output / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{_e(url)}</loc></url>\n" for url in sorted(pages + [f"{SITE}/models/", f"{SITE}/benchmarks/"])) + "</urlset>\n", encoding="utf-8")
    (output / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
