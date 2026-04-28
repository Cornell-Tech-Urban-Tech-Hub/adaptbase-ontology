"""Phase D — Distribution & coverage analysis.

Compares the depth corpus (222 published research narratives for 221 curated
solutions) against the breadth corpus (5,552 CDP-reported adaptation actions)
across shared dimensions: hazards, solution categories, urban systems, and
geographic region.

For each CDP action, we ask an LLM (Haiku via LiteLLM proxy) to map the
free-text action name/description/sectors/hazards onto the controlled
vocabularies already present in packages/ontology/schemas/vocabularies/. The
categorization is checkpointed to parquet so re-runs never re-spend tokens.

Outputs:
- reports/distribution-analysis-v0.md — side-by-side distribution tables
- proposals/distribution-gaps-v0.json — gap candidates for human review

Usage:
    uv run packages/ontology/mining/scripts/phase_d_distribution.py --limit 50
    uv run packages/ontology/mining/scripts/phase_d_distribution.py --all
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

MINING_ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY_ROOT = MINING_ROOT.parent
CORPUS_DEPTH = MINING_ROOT / "corpus" / "depth"
CORPUS_BREADTH = MINING_ROOT / "corpus" / "breadth"
VOCAB_DIR = ONTOLOGY_ROOT / "schemas" / "vocabularies"
REPORTS = MINING_ROOT / "reports"
PROPOSALS = MINING_ROOT / "proposals"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from research.mining.scripts._llm import HAIKU_MODEL, SONNET_MODEL, chat_json  # noqa: E402

# ----------------------------------------------------------------------------
# Vocabulary loading
# ----------------------------------------------------------------------------


def load_vocabs() -> dict:
    """Load hazard / urban-system / solution-category vocabs into compact lists
    suitable for embedding in an LLM prompt."""
    hazards = json.loads((VOCAB_DIR / "hazards.json").read_text())
    usys = json.loads((VOCAB_DIR / "urban-systems.json").read_text())
    cats = json.loads((VOCAB_DIR / "solution-categories.json").read_text())

    hazard_cats = [{"id": c["id"], "name": c["name"]} for c in hazards["categories"]]
    hazard_leaves = []
    for c in hazards["categories"]:
        for h in c.get("hazards", []):
            hazard_leaves.append({"id": h["id"], "name": h["name"], "category": c["id"]})

    urban_sectors = [{"id": s["id"], "name": s["name"]} for s in usys["sectors"]]

    sol_cats = [{"id": c["id"], "name": c["name"]} for c in cats["categories"]]

    return {
        "hazard_categories": hazard_cats,
        "hazard_leaves": hazard_leaves,
        "urban_sectors": urban_sectors,
        "solution_categories": sol_cats,
    }


# ----------------------------------------------------------------------------
# Depth distributions (from extraction_schema JSONB)
# ----------------------------------------------------------------------------


def _extract_value(node):
    """extraction_schema wraps each value as {value, claim_ids, ...}. Pull value."""
    if isinstance(node, dict):
        return node.get("value")
    return node


def _extract_values_list(node):
    """Pull list of .value from an array of {value,...} objects, or plain list."""
    if not node:
        return []
    if isinstance(node, list):
        out = []
        for item in node:
            v = _extract_value(item)
            if v:
                out.append(v)
        return out
    v = _extract_value(node)
    return [v] if v else []


def depth_distributions(sol: pd.DataFrame, rv: pd.DataFrame) -> dict:
    """Tally hazards / solution_categories / urban_systems / mechanisms / actors."""
    dims = {
        "hazards": Counter(),
        "solution_categories": Counter(),
        "urban_systems": Counter(),
        "mechanisms_primary": Counter(),
        "implementing_actors": Counter(),
    }
    for _, row in sol.iterrows():
        es = row.get("extraction_schema")
        if not es:
            continue
        try:
            d = json.loads(es) if isinstance(es, str) else es
        except Exception:
            continue
        dim = d.get("dimensions") or {}

        # hazards_addressed is a list of {value, claim_ids, ...} or {hazard_id, ...}
        hz = (dim.get("hazards") or {}).get("hazards_addressed") or []
        if isinstance(hz, list):
            for h in hz:
                v = None
                if isinstance(h, dict):
                    v = h.get("value") or h.get("hazard_id") or h.get("id")
                elif h:
                    v = str(h)
                if v:
                    dims["hazards"][v] += 1

        # solution_category is a flat dict {category_id, subcategory_id, claim_ids}
        sc = (dim.get("identity") or {}).get("solution_category") or {}
        cat_id = sc.get("category_id") if isinstance(sc, dict) else None
        if cat_id:
            dims["solution_categories"][cat_id] += 1

        # systems_affected is a list of {sector, system_id, claim_ids, relevance_note}
        us = (dim.get("urban_systems") or {}).get("systems_affected") or []
        if isinstance(us, list):
            seen_sectors = set()  # count each sector once per solution
            for u in us:
                if isinstance(u, dict):
                    sector = u.get("sector")
                    if sector and sector not in seen_sectors:
                        dims["urban_systems"][sector] += 1
                        seen_sectors.add(sector)

        # primary_mechanism is {value, claim_ids, description}
        pm = (dim.get("mechanisms") or {}).get("primary_mechanism") or {}
        mech = pm.get("value") if isinstance(pm, dict) else pm
        if mech:
            dims["mechanisms_primary"][mech] += 1

        # implementing_actor_types — list of {value, claim_ids} or similar
        iat = (dim.get("identity") or {}).get("implementing_actor_types") or []
        if isinstance(iat, list):
            for a in iat:
                v = a.get("value") if isinstance(a, dict) else a
                if v:
                    dims["implementing_actors"][v] += 1

    # Fallback hazards from research_versions.hazards if extraction_schema was empty
    if sum(dims["hazards"].values()) == 0:
        for _, row in rv.iterrows():
            hz = row.get("hazards")
            if not hz:
                continue
            try:
                arr = json.loads(hz) if isinstance(hz, str) else hz
            except Exception:
                continue
            if isinstance(arr, list):
                for h in arr:
                    if h:
                        dims["hazards"][str(h)] += 1

    # Geographic region from solutions.loc_id requires a cities join — skipped
    # here; deferred to a later pass if we want geographic gap analysis.
    return dims


# ----------------------------------------------------------------------------
# Breadth (CDP) categorization via LLM
# ----------------------------------------------------------------------------

CDP_CATEGORIZE_SYSTEM = """\
You are a climate-adaptation ontologist. Given a single CDP-reported adaptation \
action (name, description, self-reported sectors, and self-reported hazards), \
map it onto the controlled vocabularies provided. You MUST only use ids from the \
provided vocabularies. If no entry fits, use the literal string "UNMAPPED" for \
that dimension so gaps can be surfaced. Return a JSON object and nothing else.\
"""


def cdp_prompt(row: dict, vocab: dict) -> str:
    # Group leaves under their category for easier prompting.
    leaves_by_cat: dict[str, list[dict]] = {}
    for h in vocab["hazard_leaves"]:
        leaves_by_cat.setdefault(h["category"], []).append(h)
    hazard_block_lines = []
    for c in vocab["hazard_categories"]:
        kids = leaves_by_cat.get(c["id"], [])
        for leaf in kids:
            hazard_block_lines.append(f"- {leaf['id']}: {leaf['name']}  (cat: {c['id']})")
    hazards_vocab = "\n".join(hazard_block_lines)
    urb_sectors = "\n".join(f"- {s['id']}: {s['name']}" for s in vocab["urban_sectors"])
    sol_cats = "\n".join(f"- {c['id']}: {c['name']}" for c in vocab["solution_categories"])

    def clip(s, n=400):
        s = (s or "").strip()
        return s if len(s) <= n else s[:n] + "..."

    return f"""CDP ACTION
- name: {clip(row.get("action_name_en") or row.get("action_name"), 200)}
- description: {clip(row.get("action_description_en") or row.get("action_description"))}
- self-reported sectors: {clip(row.get("action_sectors"), 200)}
- self-reported hazards: {clip(row.get("action_hazards_en") or row.get("action_hazards"), 200)}
- city: {row.get("city_name")}, country: {row.get("country")}

HAZARDS (use leaf ids — the column after the dash; DO NOT invent new ids):
{hazards_vocab}

URBAN SYSTEM SECTORS (use ids — top-level only):
{urb_sectors}

SOLUTION CATEGORIES (use ids — top-level only):
{sol_cats}

Return JSON with this exact shape, using ONLY ids from the vocabularies above (or the literal string "UNMAPPED" when nothing fits):
{{
  "hazards": ["<leaf_id>", ...],
  "solution_category": "<id or UNMAPPED>",
  "urban_sectors": ["<id>", ...],
  "fit_confidence": "high" | "medium" | "low",
  "notes": "<one sentence — only fill if any dimension is UNMAPPED, explaining what would be needed>"
}}"""


def _validate_ids(returned: list, valid: set[str]) -> tuple[list[str], list[str]]:
    """Split a returned id list into (kept, invented). UNMAPPED is preserved in kept."""
    kept, invented = [], []
    for r in returned or []:
        if not isinstance(r, str) or not r:
            continue
        if r == "UNMAPPED" or r in valid:
            kept.append(r)
        else:
            invented.append(r)
    return kept, invented


def categorize_cdp(actions: pd.DataFrame, vocab: dict, model: str, limit: int | None) -> pd.DataFrame:
    ckpt = CORPUS_BREADTH / "cdp_categorized.parquet"
    done_ids: set[int] = set()
    if ckpt.exists():
        prev = pd.read_parquet(ckpt)
        done_ids = set(prev["id"].tolist())
        print(f"  resuming: {len(done_ids):,} already categorized")
    else:
        prev = pd.DataFrame()

    todo = actions[~actions["id"].isin(done_ids)]
    if limit is not None:
        todo = todo.head(limit)
    print(f"  to categorize now: {len(todo):,} (model={model})")

    valid_hazards = {h["id"] for h in vocab["hazard_leaves"]}
    valid_sectors = {s["id"] for s in vocab["urban_sectors"]}
    valid_sol_cats = {c["id"] for c in vocab["solution_categories"]}

    def _call_row(row_dict: dict) -> dict:
        row_id = row_dict["id"]
        try:
            out = chat_json(
                cdp_prompt(row_dict, vocab),
                system=CDP_CATEGORIZE_SYSTEM,
                model=model,
                max_tokens=500,
            )
            haz = out.get("hazards") or out.get("hazard_categories") or []
            kept_haz, inv_haz = _validate_ids(haz, valid_hazards)
            kept_urb, inv_urb = _validate_ids(out.get("urban_sectors") or [], valid_sectors)
            sc = out.get("solution_category") or "UNMAPPED"
            inv_sc = []
            if sc != "UNMAPPED" and sc not in valid_sol_cats:
                inv_sc = [sc]
                sc = "UNMAPPED"
            invented = {"hazards": inv_haz, "urban_sectors": inv_urb, "solution_category": inv_sc}
            return {
                "id": row_id,
                "hazards": json.dumps(kept_haz),
                "solution_category": sc,
                "urban_sectors": json.dumps(kept_urb),
                "fit_confidence": out.get("fit_confidence"),
                "notes": out.get("notes") or "",
                "invented_ids": json.dumps(invented) if any(invented.values()) else None,
            }
        except Exception as e:
            print(f"  ! row {row_id}: {e}", flush=True)
            return {
                "id": row_id,
                "hazards": "[]",
                "solution_category": "ERROR",
                "urban_sectors": "[]",
                "fit_confidence": None,
                "notes": f"ERROR: {e}",
                "invented_ids": None,
            }

    workers = 20
    rows_list = [row.to_dict() for _, row in todo.iterrows()]
    results: list[dict] = []
    buffered_since = time.time()
    start = time.time()
    completed_count = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_call_row, r): r["id"] for r in rows_list}
        for future in as_completed(futures):
            results.append(future.result())
            completed_count += 1
            if time.time() - buffered_since > 60:
                combined = pd.concat([prev, pd.DataFrame(results)], ignore_index=True)
                combined.to_parquet(ckpt, index=False)
                elapsed = time.time() - start
                rate = completed_count / elapsed
                print(
                    f"    ... {completed_count:,}/{len(todo):,}"
                    f"  ({rate:.1f}/s, checkpointed)",
                    flush=True,
                )
                buffered_since = time.time()

    combined = pd.concat([prev, pd.DataFrame(results)], ignore_index=True)
    combined.to_parquet(ckpt, index=False)
    return combined


# ----------------------------------------------------------------------------
# Gap analysis + LLM proposal
# ----------------------------------------------------------------------------


def breadth_distributions(cat: pd.DataFrame) -> dict:
    haz = Counter()
    sol = Counter()
    urb = Counter()
    unmapped = {"hazards": 0, "solution_category": 0, "urban_sectors": 0}
    # Back-compat with older checkpoint: support both "hazards" and "hazard_categories" columns.
    haz_col = "hazards" if "hazards" in cat.columns else "hazard_categories"
    for _, row in cat.iterrows():
        for h in json.loads(row.get(haz_col) or "[]"):
            if h == "UNMAPPED":
                unmapped["hazards"] += 1
            elif h:
                haz[h] += 1
        sc = row["solution_category"]
        if sc == "UNMAPPED":
            unmapped["solution_category"] += 1
        elif sc and sc != "ERROR":
            sol[sc] += 1
        for u in json.loads(row["urban_sectors"] or "[]"):
            if u == "UNMAPPED":
                unmapped["urban_sectors"] += 1
            elif u:
                urb[u] += 1
    return {
        "hazards": haz,
        "solution_categories": sol,
        "urban_systems": urb,
        "unmapped": unmapped,
    }


def fmt_distribution(depth: Counter, breadth: Counter, vocab_index: dict[str, str]) -> str:
    """Render a markdown table: id | name | depth_n | depth_% | breadth_n | breadth_% | delta."""
    all_keys = sorted(set(depth) | set(breadth))
    d_total = sum(depth.values()) or 1
    b_total = sum(breadth.values()) or 1
    rows = []
    rows.append("| id | name | depth | depth % | breadth | breadth % | Δpp |")
    rows.append("| --- | --- | ---: | ---: | ---: | ---: | ---: |")
    for k in all_keys:
        d = depth.get(k, 0)
        b = breadth.get(k, 0)
        dp = 100 * d / d_total
        bp = 100 * b / b_total
        delta = bp - dp
        name = vocab_index.get(k, k)
        rows.append(f"| `{k}` | {name} | {d} | {dp:.1f}% | {b} | {bp:.1f}% | {delta:+.1f} |")
    rows.append(f"| **total** | | **{sum(depth.values())}** | | **{sum(breadth.values())}** | | |")
    return "\n".join(rows)


def top_unmapped_samples(cat: pd.DataFrame, actions: pd.DataFrame, dim: str, n: int = 10) -> list[dict]:
    if dim == "solution_category":
        mask = cat["solution_category"] == "UNMAPPED"
    else:
        if dim == "hazards":
            col = "hazards" if "hazards" in cat.columns else "hazard_categories"
        else:
            col = "urban_sectors"
        mask = cat[col].apply(lambda s: "UNMAPPED" in (s or ""))
    unmapped_ids = cat.loc[mask, "id"].tolist()
    if not unmapped_ids:
        return []
    rows = actions[actions["id"].isin(unmapped_ids)].head(n)
    out = []
    for _, row in rows.iterrows():
        out.append({
            "id": int(row["id"]),
            "city": row.get("city_name"),
            "country": row.get("country"),
            "action_name": (row.get("action_name_en") or row.get("action_name") or "")[:200],
            "action_description": (row.get("action_description_en") or row.get("action_description") or "")[:400],
        })
    return out


def propose_gap_categories(unmapped_samples: list[dict], dimension: str, existing_vocab: list[dict]) -> list[dict]:
    """Use Sonnet to cluster unmapped CDP actions into proposed new categories."""
    if not unmapped_samples:
        return []
    existing = "\n".join(f"- {v['id']}: {v['name']}" for v in existing_vocab)
    items = "\n".join(
        f"[{s['id']}] {s['action_name']} — {s['action_description'][:200]}"
        for s in unmapped_samples
    )
    prompt = f"""The following CDP-reported climate-adaptation actions could not be mapped to any existing entry in our {dimension} vocabulary.

EXISTING VOCABULARY ({dimension}):
{existing}

UNMAPPED ACTIONS:
{items}

Task: Cluster these UNMAPPED actions into 1-4 proposed new {dimension} entries. Only propose a new entry if at least 3 actions would plausibly fit it AND it cannot be represented by any existing entry (if an existing entry fits, say so).

Return JSON of this shape:
{{
  "proposals": [
    {{
      "proposed_id": "<snake_case_id>",
      "proposed_name": "<Human Name>",
      "definition": "<1-2 sentence definition>",
      "supporting_action_ids": [<id int>, ...],
      "external_vocab_match": "<IPCC/CRF/UNDRR term or null>",
      "alternative": "<existing id these could plausibly map to, or null>"
    }}
  ],
  "notes": "<any overall observations>"
}}"""
    out = chat_json(prompt, model=SONNET_MODEL, max_tokens=2000)
    return out.get("proposals") or []


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=200, help="limit CDP actions for this run (default 200 for a cheap first pass)")
    ap.add_argument("--all", action="store_true", help="ignore --limit, categorize all 5,552 actions")
    ap.add_argument("--model", default=HAIKU_MODEL, help="LLM model for CDP categorization")
    ap.add_argument("--skip-propose", action="store_true", help="skip the LLM gap-proposal step")
    args = ap.parse_args()

    if not CORPUS_DEPTH.exists() or not CORPUS_BREADTH.exists():
        sys.exit("corpus not found — run pull_depth_corpus.py and pull_breadth_corpus.py first")

    print("loading depth corpus ...")
    sol = pd.read_parquet(CORPUS_DEPTH / "solutions.parquet")
    rv = pd.read_parquet(CORPUS_DEPTH / "research_versions.parquet")
    print(f"  {len(sol):,} solutions / {len(rv):,} research_versions")

    print("loading breadth corpus ...")
    cdp = pd.read_parquet(CORPUS_BREADTH / "cdp_actions.parquet")
    actions = cdp[cdp["record_type"] == "action"].reset_index(drop=True)
    print(f"  {len(actions):,} CDP actions")

    print("loading vocabularies ...")
    vocab = load_vocabs()
    print(
        f"  {len(vocab['hazard_categories'])} hazard categories, "
        f"{len(vocab['urban_sectors'])} urban sectors, "
        f"{len(vocab['solution_categories'])} solution categories"
    )

    print("computing depth distributions ...")
    depth = depth_distributions(sol, rv)
    for dim, ctr in depth.items():
        print(f"  {dim}: {len(ctr)} distinct values, {sum(ctr.values())} total")

    print(f"categorizing CDP actions (limit={args.limit if not args.all else 'all'}) ...")
    cat = categorize_cdp(actions, vocab, args.model, None if args.all else args.limit)

    # Only evaluate breadth for rows we actually categorized this run (checkpoint-accumulated)
    breadth = breadth_distributions(cat)
    print(f"  breadth rows: {len(cat)}, unmapped summary: {breadth['unmapped']}")

    # --- report ---
    vocab_index = {}
    for c in vocab["hazard_categories"]:
        vocab_index[c["id"]] = c["name"]
    for s in vocab["urban_sectors"]:
        vocab_index[s["id"]] = s["name"]
    for c in vocab["solution_categories"]:
        vocab_index[c["id"]] = c["name"]

    REPORTS.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS / "distribution-analysis-v0.md"
    lines = []
    lines.append("# Phase D — Distribution & Coverage Analysis (v0)\n")
    lines.append(f"_Generated from {len(sol)} depth solutions vs {len(cat)} categorized CDP actions._\n")
    # Build hazard leaf→name and leaf→category indexes
    leaf_to_name = {h["id"]: h["name"] for h in vocab["hazard_leaves"]}
    leaf_to_cat = {h["id"]: h["category"] for h in vocab["hazard_leaves"]}
    cat_to_name = {c["id"]: c["name"] for c in vocab["hazard_categories"]}
    vocab_index.update(leaf_to_name)

    lines.append("## Hazards (leaf level)\n")
    lines.append(fmt_distribution(depth["hazards"], breadth["hazards"], vocab_index))

    # Rolled-up category view
    depth_by_cat = Counter()
    for k, v in depth["hazards"].items():
        c = leaf_to_cat.get(k)
        if c:
            depth_by_cat[c] += v
    breadth_by_cat = Counter()
    for k, v in breadth["hazards"].items():
        c = leaf_to_cat.get(k)
        if c:
            breadth_by_cat[c] += v
    lines.append("\n## Hazards (rolled up to category)\n")
    lines.append(fmt_distribution(depth_by_cat, breadth_by_cat, cat_to_name))
    lines.append("\n## Solution categories\n")
    lines.append(fmt_distribution(depth["solution_categories"], breadth["solution_categories"], vocab_index))
    lines.append("\n## Urban systems (top-level sectors)\n")
    lines.append(fmt_distribution(depth["urban_systems"], breadth["urban_systems"], vocab_index))
    lines.append("\n## Mechanisms (depth only, seed vocab)\n")
    for k, v in depth["mechanisms_primary"].most_common():
        lines.append(f"- `{k}`: {v}")
    lines.append("\n## Implementing actor types (depth only)\n")
    for k, v in depth["implementing_actors"].most_common(15):
        lines.append(f"- `{k}`: {v}")
    lines.append("\n## Unmapped (breadth→vocab)\n")
    lines.append(f"- hazards UNMAPPED: {breadth['unmapped']['hazards']}")
    lines.append(f"- solution_category UNMAPPED: {breadth['unmapped']['solution_category']}")
    lines.append(f"- urban_sectors UNMAPPED: {breadth['unmapped']['urban_sectors']}")

    # Flag invented ids (hallucinated vocab) for quality review
    if "invented_ids" in cat.columns:
        inv_rows = cat[cat["invented_ids"].notna()]
        if len(inv_rows):
            lines.append(f"\n## Invented ids (LLM hallucinations, auto-mapped to UNMAPPED): {len(inv_rows)} rows\n")
            for _, ir in inv_rows.head(10).iterrows():
                lines.append(f"- row {ir['id']}: `{ir['invented_ids']}`")
    report_path.write_text("\n".join(lines))
    print(f"wrote {report_path}")

    # --- proposals ---
    PROPOSALS.mkdir(parents=True, exist_ok=True)
    proposals_path = PROPOSALS / "distribution-gaps-v0.json"
    proposals = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "proposals_by_dimension": {}}

    if not args.skip_propose:
        for dim_vocab_key, dim_col, pretty in [
            ("solution_categories", "solution_category", "solution_category"),
            ("hazard_leaves", "hazards", "hazard"),
            ("urban_sectors", "urban_sectors", "urban_sector"),
        ]:
            samples = top_unmapped_samples(cat, actions, dim_col, n=30)
            if not samples:
                proposals["proposals_by_dimension"][pretty] = []
                continue
            print(f"proposing {pretty} gaps from {len(samples)} unmapped samples ...")
            props = propose_gap_categories(samples, pretty, vocab[dim_vocab_key])
            proposals["proposals_by_dimension"][pretty] = props
    else:
        proposals["proposals_by_dimension"] = {}

    proposals_path.write_text(json.dumps(proposals, indent=2))
    print(f"wrote {proposals_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
