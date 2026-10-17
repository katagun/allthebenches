import json

import httpx

from pipeline.collectors import _records, collect, mapping_queue_rows
from pipeline.reconcile import candidate_openrouter_ids, create_reconciliation_proposal


class FailedClient:
    headers = {}
    def get(self, url):
        request = httpx.Request("GET", url)
        return httpx.Response(503, request=request)


def test_all_feed_failure_preserves_previous_staged_data(tmp_path):
    original = {"source":"openrouter", "retrieved_at":"2026-01-01T00:00:00Z", "status":"ok",
                "feeds":[{"url":"https://openrouter.ai/api/v1/models", "status":"ok", "data":{"data":[{"id":"x/model","name":"Model"}]}}]}
    path = tmp_path / "openrouter.json"
    path.write_text(json.dumps(original))
    result = collect("openrouter", tmp_path, FailedClient())
    assert result["status"] == "stale"
    assert result["feeds"][0]["data"]["data"][0]["id"] == "x/model"
    assert json.loads((tmp_path / "openrouter-mapping-queue.json").read_text())[0]["external_id"] == "x/model"


def test_success_stages_raw_and_unresolved_queue(tmp_path):
    class SuccessClient:
        headers = {}
        def get(self, url):
            return httpx.Response(200, request=httpx.Request("GET", url), json={"data":[{"id":"x/model", "name":"Model"}]})
    result = collect("openrouter", tmp_path, SuccessClient())
    assert result["status"] == "ok"
    queue = json.loads((tmp_path / "openrouter-mapping-queue.json").read_text())
    assert queue[0]["external_id"] == "x/model"
    assert queue[0]["status"] == "unresolved"


def test_repeated_partial_failures_keep_stale_feed_and_original_as_of(tmp_path):
    class PartialClient:
        headers = {}
        def get(self, url):
            if url.endswith("/models"):
                return httpx.Response(503, request=httpx.Request("GET", url))
            return httpx.Response(200, request=httpx.Request("GET", url), json={"data":[]})
    path = tmp_path / "openrouter.json"
    path.write_text(json.dumps({"source":"openrouter", "retrieved_at":"2026-01-01T00:00:00Z", "status":"ok",
        "feeds":[{"url":"https://openrouter.ai/api/v1/models", "status":"ok", "retrieved_at":"2025-12-01T00:00:00Z", "data":{"data":[{"id":"x/model"}]}},
                  {"url":"https://openrouter.ai/api/v1/datasets/rankings-daily", "status":"ok", "data":{"data":[]}}]}))
    collect("openrouter", tmp_path, PartialClient())
    second = collect("openrouter", tmp_path, PartialClient())
    stale_feed = next(f for f in second["feeds"] if f["url"].endswith("/models"))
    assert stale_feed["status"] == "stale"
    assert stale_feed["data"]["data"][0]["id"] == "x/model"
    assert stale_feed["retrieved_at"] == "2025-12-01T00:00:00Z"
    queue = json.loads((tmp_path / "openrouter-mapping-queue.json").read_text())
    assert any(row["external_id"] == "x/model" and row["feed_status"] == "stale" for row in queue)


def test_record_parser_handles_real_source_wrappers_and_keyed_catalogs():
    labs = list(_records({"labs":[{"id":"lab-openai","name":"OpenAI"}]}))
    models = list(_records({"models":[{"id":"atlas-id","source_id":"openai/gpt-6-astra","name":"GPT-6 Astra"}]}))
    catalog = list(_records({"openai/gpt-6-astra":{"id":"openai/gpt-6-astra","name":"GPT-6 Astra"}}))
    assert labs[0][0] == "lab-openai"
    assert models[0][0] == "openai/gpt-6-astra"
    assert catalog[0][0] == "openai/gpt-6-astra"
    rankings = {"feeds":[{"url":"rankings-daily","status":"ok","data":{"data":[
        {"model_permaslug":"openai/gpt-6-astra","date":"2026-10-16","total_tokens":"12"},
        {"model_permaslug":"other","date":"2026-10-16","total_tokens":"34"}]}}]}
    queue = mapping_queue_rows("openrouter", rankings)
    assert len(queue) == 1
    assert queue[0]["external_id"] == "openai/gpt-6-astra@2026-10-16"


def test_reconciliation_requires_exact_id_and_excludes_benchmark_metadata(tmp_path):
    staging = tmp_path / "staging"
    staging.mkdir()
    curated = tmp_path / "dataset.json"
    curated.write_text(json.dumps({"models":[{"id":"model-x","name":"Example Model"}],"labs":[]}))
    def envelope(feeds): return {"retrieved_at":"2026-10-17T00:00:00Z","feeds":feeds}
    (staging / "peacefulcoexistance.json").write_text(json.dumps(envelope([
        {"url":"https://peacefulcoexistance.com/models.json","sha256":"atlas-hash","retrieved_at":"2026-10-17T00:00:00Z","data":{"models":[{"id":"atlas-model-x","source_id":"vendor/example-model","name":"Example Model","source_metadata":{"name":"Example Model","release_date":"2026-01-01","benchmarks":[{"name":"invented?"}]}}]}},
        {"url":"https://peacefulcoexistance.com/models-dev.json","data":{"models":[]}},
        {"url":"https://peacefulcoexistance.com/labs.json","data":{"labs":[]}},
    ])))
    (staging / "models.dev.json").write_text(json.dumps(envelope([
        {"url":"https://models.dev/models.json?type=all","sha256":"models-hash","retrieved_at":"2026-10-17T00:00:01Z","data":{"vendor/example-model":{"id":"vendor/example-model","name":"Example Model","release_date":"2026-01-01","benchmarks":[{"score":100}]}}},
    ])))
    (staging / "openrouter.json").write_text(json.dumps(envelope([
        {"url":"https://openrouter.ai/api/v1/models","sha256":"or-hash","retrieved_at":"2026-10-17T00:00:02Z","data":{"data":[{"id":"vendor/example-model","name":"Example Model","pricing":{"prompt":"0.000001","completion":"0.000002"}}]}},
    ])))
    (staging / "openrouter-endpoints.json").write_text(json.dumps({"endpoints":{"vendor/example-model":{"status":"ok","data":{"data":{"id":"vendor/example-model","endpoints":[{"provider_name":"Vendor","pricing":{"prompt":"0.000003","completion":"0.000004"}}]}}}}}))
    ids = candidate_openrouter_ids(curated, staging)
    assert ids == ["vendor/example-model"]
    proposal = create_reconciliation_proposal(curated, staging)
    model = proposal["models"][0]
    assert model["models_dev"]["external_id"] == "vendor/example-model"
    assert "benchmarks" not in model["models_dev"]["metadata"]
    assert "benchmarks" not in model["atlas"]["source_metadata"]
    assert model["openrouter"]["endpoints"][0]["pricing"]["usd_per_million_tokens"]["input"] == "3.000000"
