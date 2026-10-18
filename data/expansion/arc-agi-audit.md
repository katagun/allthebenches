# ARC-AGI coverage

Source: ARC Prize model result pages, visible **Verified scores** tables. The reviewed extraction is `arc-prize-scores.json`; each entry records the URL, retrieval time, raw page SHA-256, and exact displayed table. Re-import with `uv run python scripts/import-arc-prize.py`, then rebuild snapshots.

- ARC-AGI-1 and ARC-AGI-2 use separate semi-private task accuracy rows.
- ARC-AGI-3 uses separate Standard, Provider Adapter, and unspecified-harness rows. Its human-normalized efficiency score is not task accuracy.
- Public task/replay tables below the verified score tables are not the same split and are not aggregated into the verified scores.
- Exact reasoning labels are preserved. Gemini High is not relabeled Max. Unspecified Google-reported comparison configurations are not assigned ARC scores.
- Dashes are missing, not zero. Only exact existing model releases were matched; no results are borrowed for Muse, GLM-5.3 or Qwen3.8-Max from other checkpoints.
- Nine releases are covered initially. Additional verified models, competition systems, public splits and the retired 2025 ARC-AGI-3 Preview are separate collection work; this is not a complete copy of every leaderboard entry.

The [official testing policy](https://arcprize.org/policy) distinguishes the semi-private verified leaderboard from public development tasks and private competition evaluations.
