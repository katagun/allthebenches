# Google Gemini 4 Argon evaluation table audit

Reviewed 17 October 2026 against [Google’s Gemini 4 Argon model card](https://deepmind.google/models/model-cards/gemini-4-argon/) and the [Google DeepMind evaluation PDF](https://storage.googleapis.com/deepmind-media/gemini/gemini_4_argon_model_evaluation.pdf). The model card publishes the results table (HTML rows 188–209); the PDF’s fifth page is the rendered results page, and pp. 2–4 specify methods. Google’s announcement is [here](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-argon/).

The table below records the four columns in the source order: Gemini 4 Argon, GPT-6 Astra, Claude Fable 5.1, Claude Opus 5.5. A dash is stored as an explicit `not_reported` missing cell; it never becomes zero. Values retain the reported percentage precision.

| Benchmark row | Argon | Astra | Fable 5.1 | Opus 5.5 |
| --- | ---: | ---: | ---: | ---: |
| Vals Index | 68.9 | 63.1 | 65.8 | 67.0 |
| AutomationBench | 51.3 | 41.4 | 31.4 | 42.5 |
| Vals Finance Agent v2 | 65.4 | 53.5 | 58.9 | 58.6 |
| Harvey’s Legal Agent Benchmark | 19.6 | 5.4 | 6.7 | 3.8 |
| DeepSWE v1.1 | 77.9 | 74.1 | 67.4 | 74.2 |
| FrontierSWE v2 | 55.0 | 65.5 | 56.3 | 62.3 |
| Vibe Code Bench | 91.9 | 89.6 | 90.3 | 90.3 |
| Terminal-Bench 4.0 | 57.4 | 58.2 | 57.9 | 66.4 |
| PostTrainBench v1.1 | 45.3 | 44.3 | 40.2 | 49.3 |
| Terminal-Bench Science 0.1 | 57.6 | 68.1 | 52.6 | 63.3 |
| LABBench 2 | 88.8 | 85.4 | 68.6 | 73.1 |
| RiemannBench | 76.0 | 72.0 | 65.6 | 69.6 |
| GraphWalks, up to 128k, BFS F1 | 99.7 | 98.7 | 91.4 | 90.6 |
| GraphWalks, 256k–1M, BFS F1 | 84.2 | 71.8 | 65.0 | 66.8 |
| Agent’s Last Exam, binary pass rate | 39.5 | 34.2 | — | 38.2 |
| OSWorld 2.0, offline subset partial score | 69.2 | 72.6 | — | — |
| Chartography | 71.6 | 71.0 | 46.2 | 66.3 |
| LVBench | 91.7 | 87.5 | 79.7 | 83.7 |
| CWE-bench v1 | 68.0 | 68.0 | 58.0 | 67.0 |

Method and provenance notes from the PDF:

- Unless otherwise specified, Argon scores are pass@1, run through Gemini API at its highest thinking setting. “Single attempt” means no majority voting or parallel test-time compute. Google averages multiple trials for smaller benchmarks. The table does not disclose exact effort labels for every result.
- For non-Gemini models, Google uses provider self-reported numbers unless a row says otherwise. It defaults to maximum thinking/reasoning settings, but uses the best available result when a maximum-setting result is unavailable. The report does not identify exact effort labels for each row. Curated competitor configurations therefore retain a source-selected label with exact effort unresolved.
- Vals Index, Vals Finance Agent v2 and Harvey’s Legal Agent Benchmark are sourced from Vals AI. AutomationBench uses its private set and the official Zapier public leaderboard.
- DeepSWE: Argon was computed with a mini-swe agent harness; Astra came from its official public leaderboard; Fable and Opus from their system cards. Reported effort selection follows the highest scoring thinking level on DataCurve’s main leaderboard.
- FrontierSWE comes from Proximal’s official public leaderboard; Vibe Code Bench from Vals AI’s public leaderboard. Terminal-Bench 4 Argon is self-computed; peers are from its official public leaderboard, using the highest scoring thinking level reported by its authors.
- PostTrainBench v1.1 was self-computed for all four models using OpenCode, a 10-hour budget and one NVIDIA H100 GPU. The result is a weighted aggregate across four base models and seven benchmarks.
- Terminal-Bench Science Argon was self-computed with a six-times verifier timeout; peer results come from the official public leaderboard. LABBench 2 was self-computed for all four with a Linux terminal, preinstalled bioinformatics tools, Python, R and internet access. RiemannBench comes from Surge’s official public leaderboard.
- GraphWalks was self-computed for all four. The up-to-128k subset has 650 items; the 256k–1M subset has 200 items.
- Agent’s Last Exam Argon uses default ALE-Claw with a five-hour window and safety filters enabled. Filtered responses are empty strings and the episode can continue. The report provides binary pass rate; Astra and Opus are from the official leaderboard; Fable is absent there.
- OSWorld 2.0 Argon is the maximum score across three single-attempt runs on the offline subset, with safety filters. Google uses the official Docker and evaluator, default 1080p, 500-step maximum, Gemini CUA harness with parallel batch calls, compaction, pyautogui and screenshot-only observation, plus the official 08.08 patch. GPT-6 Astra is quoted from an official blog post, per Google’s methodology. Anthropic only publishes the combined online/offline score, so both cells are omitted.
- Chartography is from Surge’s official public leaderboard without tools. LVBench is self-computed without tools; frame sampling differs because of API limits: 1 FPS for Gemini, 800 frames for Astra, 300 for Fable and 600 for Opus. CWE-bench v1 is from the official public leaderboard and ranks by pass@1, with pass@4 breaking ties.

Because the report combines self-computed results, provider/system-card scores and leaderboard values, its table series is marked heterogeneous. Benchmark-level setup detail is retained with each observation; no common-harness ranking is inferred.
