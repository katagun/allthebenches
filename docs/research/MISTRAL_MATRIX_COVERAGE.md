# Mistral Large 4: model-page versus matrix coverage

Snapshot `49c4bb68f3b1d696` contains 171 published observations across 166 exact benchmark variants and seven configurations for Mistral Large 4.

The default Frontier view selects 22 benchmark variants and the `mistral_large4_unknown` configuration. That configuration has scores on three of those variants: Lakera B3, DeepSWE v1.1, and Terminal-Bench 4.0. Across all seven Mistral configurations, five Frontier variants have results: the other two are Vals Index and Vibe Code Bench. Terminal-Bench also has separate Vals and Artificial Analysis reports with different scores and setups.

Most of the remaining observations concern other benchmark variants, including 71 Arena rating observations and eight signed Agent Arena IPS observations. They are not scores for the missing Frontier rows. Neither matching model names nor matching benchmark family names establishes identical evaluation conditions.

The model-page matrix link previously selected only the most-covered configuration while selecting every benchmark variant. This made real results from other configurations disappear behind empty cells. It now selects all configurations backing the model page's published observations. Empty cells with numeric results under other setups show the reported score or min–max range, marked †, and open the evidence panel, where the user can switch to those exact setups. These previews stay neutral and do not affect sorting or winner highlighting. Saturation-filtered views do not show alternate-setup previews.

Detail pages now round score labels to two decimal places (scientific notation preserves tiny nonzero values). Full precision remains in evidence and archival data. Rating points, fractions, signed IPS, index points, and source-defined scores are labeled separately; they are not all percentages. Source-defined scores are not rescaled without a verified unit contract.
