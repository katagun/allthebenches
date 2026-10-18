# Crawlable static detail pages

The Python snapshot build publishes plain HTML model and benchmark references alongside the JSON snapshots. The pages are generated from the curated `Dataset` records and contain only reviewed observations selected for display. Model pages show each reviewed score with its configuration, benchmark variant, evaluator, source, and reported location. Benchmark pages show the reviewed results for that exact variant.

Each page includes links back to the comparison matrix and the interactive entity route. Canonical URLs use `https://allthebenches.com/models/<id>/` and `https://allthebenches.com/benchmarks/<id>/`; IDs are percent-encoded for filesystem paths and URLs. Listing pages live at `/models/` and `/benchmarks/`. The generated sitemap lists all detail and listing pages, and `robots.txt` points crawlers to it.

Missing scores are not represented as zero. Pages explain that no reviewed result means no reviewed result is published, and show an explicit empty state where appropriate. All text and attributes are HTML escaped; source and documentation links are emitted only for valid HTTP or HTTPS URLs. Generation is deterministic for an unchanged dataset.

Call `pipeline.static_pages.build_static_pages(dataset, output)` with the dataset and the same static output directory used for the rest of the published site. The function writes `models/`, `benchmarks/`, `sitemap.xml`, and `robots.txt` under that directory.

`uv run benches build --offline` generates these pages automatically. Generated-file checks and the pre-commit/CI browser suite verify their contents and phone/tablet/desktop page overflow with JavaScript disabled.
