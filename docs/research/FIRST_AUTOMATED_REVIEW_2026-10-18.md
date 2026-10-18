# First automated source proposals: review and resolution

Reviewed PRs #22–#26 against their archived, SHA-256-verified source bytes and the
published catalog. All **5,690 verified results were already published**. The site
retains **6,538 observations**; this review adds no duplicate scores and deletes none.

| Source | Verified existing results | Resolution |
| --- | ---: | --- |
| Epoch (#23) | 925 | Preserve published observations and their original archive provenance |
| Vals (#25) | 533 | Restore two tool-specific rows to collector coverage; both already published |
| AA (#22) | 1,082 | Preserve original extracted-payload provenance; new capture is full HTML |
| Arena (#26) | 2,564 | Reuse original Arena configurations; suppress identical replays |
| LiveBench (#24) | 586 | Reuse original LiveBench configurations; fix source CSV/category URLs |

## Why apparent additions were not new results

Arena's 1,343 apparently new IDs and LiveBench's 196 apparently new IDs pointed to
configurations from other evaluators with matching model/effort. Their underlying
source row values and other payload fields were unchanged. Repeated imports now
reuse the evaluator's exact upstream identity, model and reasoning setting. Unknown
setups create source-specific configurations; conflicting existing mappings fail.
Arena replay also compares the count fields actually stored in observations, and
uses the exact source snapshot rather than an arbitrary same-date observation.
Changed scores or vote/session/observation counts continue to require review.

Vals had excluded both GPT-5.6 Sol web-search rows as duplicate identities. The
reviewed Search Tool column distinguishes Exa (45.24%) and Native (43.58%). Matching
now includes that protocol field, never row position, price, latency or rank.
Duplicate rows for the same tool and unreviewed tools remain unresolved.

Epoch's archive changed only country ordering for an out-of-catalog model in two
CSV members. Every admitted source row remains identical. Preserve the original
`archive_sha256` for existing observations; the new archive is separately retained
under `data/automation/epoch/raw/`.

AA's former hash identified a decoded Flight payload, whereas the proposal archives
full HTML containing that payload. All 1,082 scores remain identical. Neither a
fresh retrieval timestamp nor a different capture representation is a new result.

Both LiveBench CSV hashes are unchanged. Their published links mistakenly used
hyphenated dates; the verified download paths use underscores. Correct the source
URL and category locator while retaining the original capture date and score history.

## Coverage limits

- Epoch: 925 admitted, 6,175 unresolved models, 8 unreviewed metric contracts and
  1 conflicting reasoning setting. No guessed mappings were promoted.
- Vals: 3,177 rows accounted for: 533 verified, 2,625 unresolved identities and
  19 ambiguous duplicate identities. This accounting differs from the older audit's
  exclusion labels but preserves the same 533 published results.
- AA: 704 source model records inspected; 1,082 existing verified metric observations
  under reviewed field contracts. Estimates and unsupported metrics stay excluded.
- Arena: 30,387 scored records: 2,564 verified and 27,823 unresolved/out-of-catalog.
- LiveBench: 1,976 numeric cells: 586 verified and 1,390 unresolved/out-of-catalog.

The two URL/locator corrections are recorded field-by-field in
`data/corrections/livebench-source-links-2026-10-18.json`; original capture hashes and
retrieval dates remain unchanged.

## Reproduce

The original proposal commits retain their archived evidence. At this review commit,
`data/automation/` contains those proposals; later refresh PRs may replace the working
files, while Git history preserves the originals. The corrected adapters
can audit them offline, checking the original proposal hashes, raw captures, exact
published observation equality, and expected coverage totals:

```sh
uv run --group collectors python scripts/audit-source-proposals.py \
  --output /tmp/first-source-review.json
```

The machine-readable review is `FIRST_AUTOMATED_REVIEW_2026-10-18.json`. New collection
runs use the corrected adapters; old proposal reports remain records of what was
actually proposed. No candidate is marked reviewed merely because its JSON validates.
