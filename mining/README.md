# Corpus Mining Pipeline

Grounds the ontology in real corpus data. See
`packages/ontology/plans/ONTOLOGY-FUTURE-EXPANSION-CORPUS-MINING.md` for the
full plan and `/Users/anthonytownsend/.claude/plans/mellow-hugging-melody.md`
for the implementation plan this pipeline follows.

## Layout

```
mining/
├── scripts/              # CLI entrypoints (all `uv run ...`)
├── corpus/               # local parquet cache (gitignored)
├── proposals/            # LLM-generated proposals (JSON, reviewable)
├── decisions/            # human review outcomes (JSON)
├── reports/              # generated analysis reports
└── viewer/               # review UI (HTML + JS, served by FastAPI)
```

## End-to-end flow

```bash
# 1. Pull corpora (idempotent; re-runs within 7 days are no-ops)
uv run packages/ontology/mining/scripts/pull_depth_corpus.py --stats
uv run packages/ontology/mining/scripts/pull_breadth_corpus.py --stats

# 2. Phase D — distribution & coverage analysis.
#    --limit N bounds cost for a first-pass run. Re-running adds N more.
uv run packages/ontology/mining/scripts/phase_d_distribution.py --limit 500

# 3. Start the review server
uv run packages/ontology/mining/scripts/review_server.py   # → http://localhost:8769

# 4. Apply approved decisions back to vocabularies
uv run packages/ontology/mining/scripts/apply_decisions.py --phase distribution --dry-run
uv run packages/ontology/mining/scripts/apply_decisions.py --phase distribution
```

## Corpus

| Corpus | Source | Rows | Purpose |
|---|---|---|---|
| **Depth** | `research_versions WHERE published=true` + claims + documents | 222 versions / 221 solutions / ~5.3K claims / ~1.3K docs | Rich semantic signal. Used for depth distributions and (later) mechanism clustering. |
| **Breadth** | `catalog_cdp_adaptation` | 11,842 (5,552 actions, 3,629 goals, 2,661 projects) | Coverage signal. LLM-categorized against vocabularies; unmapped rows surface ontology gaps. |

Claims are joined to research_versions via `solution_id` (not `run_id` — `run_id` here marks import batches, not per-research-session IDs).

## Review UI

- Port `8769` (picks one above the legacy `8765` static viewer that may still be running).
- Keyboard: `←` / `→` navigate, `a` approve, `r` reject (rationale required), `d` defer (rationale required).
- Decisions persist to `decisions/{phase}-decisions.json`. Re-opening skips already-reviewed items; the "Clear" button on a prior-decision banner lets you redo one.

## LLM proxy

Uses LiteLLM proxy via OpenAI-compatible client (`OPENAI_API_BASE`, `OPENAI_API_KEY` from repo `.env`).
- Haiku (cheap categorization): `anthropic.claude-4.5-haiku`
- Sonnet (proposal generation): `anthropic.claude-4.5-sonnet`

## Vocabulary write-back

`apply_decisions.py --phase distribution` routes approved proposals by dimension:
- `solution_category` → `schemas/vocabularies/solution-categories.json`
- `hazard` → `schemas/vocabularies/hazards.json` (added to a temporary `emergent_from_mining` category for later reparenting)
- `urban_sector` → `schemas/vocabularies/urban-systems.json`
- `mechanism` → `schemas/vocabularies/mechanisms.json` (created on first run) and patches `ontology/ontology-v0.1.json` Mechanism entity

All new entries carry a `"source": "corpus_mining_<phase>_v0"` tag for traceability.

Rejected and deferred decisions are appended to `packages/ontology/decisions-log.md` with their rationale.
