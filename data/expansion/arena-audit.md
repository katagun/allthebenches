# Arena leaderboard expansion audit

Research checkpoint: 17 October 2026. Arena has several different public evaluations under the same leaderboard interface. This import keeps each leaderboard and metric in its own dated benchmark variant. It does not interpret an Arena rating as an accuracy score.

## Included data

- Text Arena Overall: Bradley–Terry rating points for four exact model/configuration matches (Muse Wonder Max, Claude Fable 5.1 Max, GPT-6.1 Sol Max, GPT-6 Astra Max), published 15 October 2026.
- Vision Arena Overall: Bradley–Terry rating points for three exact matches (GPT-6.1 Sol Max, Claude Fable 5.1 Max, GPT-6 Astra Max), published 9 October 2026.
- Search Arena Overall: Bradley–Terry rating points for two exact matches (GPT-6.1 Sol Max, GPT-6 Astra Max), published 13 October 2026.
- Code Arena: WebDev Overall: Bradley–Terry rating points for four exact matches (Claude Opus 5.5 Max, GPT-6 Astra Max, GPT-6.1 Sol Max, Claude Fable 5.1 Max), published 16 October 2026.
- Agent Arena Overall: Net Improvement and five distinct signal columns for four exact matches (Claude Opus 5.5 Max, GPT-6 Astra Max, Claude Fable 5.1 Max, GPT-6.1 Sol Max), published 16 October 2026.

The source rows retain displayed vote/session counts and the displayed ± interval as uncertainty. The retrieved leaderboard table does not state a confidence level for the displayed interval, so `confidence_level` is left null. A rating is higher-is-better within its own dated Arena category. Ratings are relative human preference, not accuracy or benchmark pass rate, and should not be compared between categories or dates. Tool Hallucination is lower-is-better; Agent Arena signal metrics remain separate from the overall Net Improvement score.

## Source audit

- `https://arena.ai/leaderboard/chat/text` — Text Arena overall table and exact displayed rows; the page states 8,834,211 votes and 416 models as of 15 October.
- `https://arena.ai/leaderboard/chat/vision` — Vision Arena overall table; 1,462,389 votes and 165 models as of 9 October.
- `https://arena.ai/leaderboard/chat/search` — Search Arena overall table; 1,437,508 votes and 42 models as of 13 October.
- `https://arena.ai/leaderboard/code/webdev` — WebDev overall table; 891,922 votes and 145 models as of 16 October.
- `https://arena.ai/leaderboard/agent` — Agent Arena overall table; 2,534,501 sessions and 52 models as of 16 October.
- `https://arena.ai/resources/agent-arena-signals` — Arena definitions for confirmed success, praise versus complaint, steerability, bash reliability, and tool hallucinations. The signal measures derive from user confirmations, explicit sentiment, corrections, or tool traces in real sessions.
- `https://arena.ai/blog/ranking-method` — Arena documents confidence intervals and rank spread. The interval shown on the accessed tables is retained as published without assigning an unstated confidence level.
- `https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset` — Arena-published historical leaderboard dataset card, which documents per-arena subsets and schema for rating bounds, votes, and agent signal scores. It also documents Bradley–Terry ratings and separate Agent Arena signal exports. This card was used to check source semantics and coverage, not to fill missing observations.

## Configuration matching and scope

Only rows whose Arena model label exactly matches a curated model release and reasoning configuration were imported. A similar model name with a different or absent effort label was not assigned to the nearest local configuration. For example, Muse Spark 1.3 remains distinct from Muse Spark base, and GPT-6.1 Sol Max was not mapped to the unknown-reasoning configuration.

This is a reviewed, partial snapshot rather than a full mirror of Arena. Explicit coverage gaps record the Text category leaderboards and remaining image/video/document modalities, and note that Arena ratings are not cross-category or cross-date comparable. Search, Vision, and WebDev have overall snapshots only; their narrower categories are not inferred. Agent Code, Chat, and Work slices are also not inferred from Agent Overall.

The source is dynamic. Refreshes should use Arena's historical `leaderboard-dataset` snapshots or recapture the public leaderboard with its published date, rather than silently replacing the dated observations in this snapshot.


## Additional exact Agent Arena matches

The 16 October Overall leaderboard also contains exact local configuration matches for Muse Wonder (Max), Muse Spark 1.3 (Max), and Grok 4.7 (xHigh). Their six values and displayed ± intervals were transcribed from the corresponding rows and retained in the same six benchmark series; session counts are 7,690, 73,912, and 15,127 respectively. The primary table identifies the metrics in order as Net Improvement, Confirmed Success, Praise vs Complaint, Steerability, Bash Reliability, and Tool Hallucination. Tool Hallucination remains lower-is-better. These 18 observations bring the integrated Arena snapshot to 55 observations across eight exact configurations. The Arena preset includes both added configurations.
