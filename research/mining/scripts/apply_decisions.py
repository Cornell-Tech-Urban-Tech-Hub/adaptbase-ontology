"""Apply reviewed corpus-mining decisions to the canonical ontology files.

Reads decisions/<phase>-decisions.json and:
- approved/edited → append to the appropriate vocabulary file(s), tagged with
  source="corpus_mining_<phase>_v0"
- rejected/deferred → append a dated entry to decisions-log.md with rationale

Supports --dry-run so the user can preview the diff before writing anything.

Usage:
    uv run packages/ontology/mining/scripts/apply_decisions.py --phase distribution --dry-run
    uv run packages/ontology/mining/scripts/apply_decisions.py --phase distribution
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

MINING_ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY_ROOT = MINING_ROOT.parent
DECISIONS_DIR = MINING_ROOT / "decisions"
VOCAB_DIR = ONTOLOGY_ROOT / "schemas" / "vocabularies"
ONTOLOGY_FILE = ONTOLOGY_ROOT / "ontology" / "ontology-v0.1.1.json"
LOG_FILE = ONTOLOGY_ROOT / "decisions-log.md"


# ----------------------------------------------------------------------------
# Routing: which dimension → which vocab file
# ----------------------------------------------------------------------------

VOCAB_ROUTES = {
    # phase "distribution"
    "solution_category": VOCAB_DIR / "solution-categories.json",
    "hazard": VOCAB_DIR / "hazards.json",
    "urban_sector": VOCAB_DIR / "urban-systems.json",
    # phase "mechanisms"
    "mechanism": VOCAB_DIR / "mechanisms.json",
}


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


def load_json(path: Path):
    return json.loads(path.read_text())


def save_json(path: Path, data, dry_run: bool) -> None:
    body = json.dumps(data, indent=2) + "\n"
    if dry_run:
        print(f"[dry-run] would write {path} ({len(body):,} bytes)")
    else:
        path.write_text(body)


def snake_id(name: str) -> str:
    return (
        "".join(c.lower() if c.isalnum() else "_" for c in (name or ""))
        .strip("_")
        .replace("__", "_")
    )


def entry_exists(vocab: dict, dim: str, id_: str) -> bool:
    """Check both top-level categories and nested leaves for an existing id."""
    if dim == "hazard":
        for cat in vocab.get("categories", []):
            if cat.get("id") == id_:
                return True
            for h in cat.get("hazards", []):
                if h.get("id") == id_:
                    return True
        return False
    if dim == "solution_category":
        for cat in vocab.get("categories", []):
            if cat.get("id") == id_:
                return True
        return False
    if dim == "urban_sector":
        for s in vocab.get("sectors", []):
            if s.get("id") == id_:
                return True
        return False
    if dim == "mechanism":
        for m in vocab.get("mechanisms", []):
            if m.get("id") == id_:
                return True
        return False
    return False


# ----------------------------------------------------------------------------
# Appliers
# ----------------------------------------------------------------------------


def apply_solution_category(vocab: dict, decision: dict, source_tag: str) -> bool:
    new_id = decision.get("name") and snake_id(decision["name"])
    new_id = decision.get("proposal_id", "").split(":", 1)[-1] or new_id
    if not new_id:
        return False
    if entry_exists(vocab, "solution_category", new_id):
        return False
    vocab.setdefault("categories", []).append({
        "id": new_id,
        "name": decision.get("name") or new_id,
        "definition": decision.get("definition") or "",
        "subcategories": [],
        "source": source_tag,
    })
    return True


def apply_hazard(vocab: dict, decision: dict, source_tag: str) -> bool:
    """For first-pass simplicity, emergent hazards go into a new 'emergent' category.
    A human can reparent them during ontology review."""
    new_id = snake_id(decision.get("name") or decision.get("proposal_id", ""))
    if not new_id or entry_exists(vocab, "hazard", new_id):
        return False
    # Ensure emergent bucket exists
    emergent = next((c for c in vocab.get("categories", []) if c.get("id") == "emergent_from_mining"), None)
    if emergent is None:
        emergent = {
            "id": "emergent_from_mining",
            "name": "Emergent (corpus-mining proposals, awaiting reparenting)",
            "hazard_source": "corpus_mining",
            "rcc_shocks": [],
            "hazards": [],
            "source": source_tag,
        }
        vocab.setdefault("categories", []).append(emergent)
    emergent["hazards"].append({
        "id": new_id,
        "name": decision.get("name") or new_id,
        "definition": decision.get("definition") or "",
        "undrr_terms": [],
        "source": source_tag,
    })
    return True


def apply_urban_sector(vocab: dict, decision: dict, source_tag: str) -> bool:
    new_id = snake_id(decision.get("name") or decision.get("proposal_id", ""))
    if not new_id or entry_exists(vocab, "urban_sector", new_id):
        return False
    vocab.setdefault("sectors", []).append({
        "id": new_id,
        "name": decision.get("name") or new_id,
        "description": decision.get("definition") or "",
        "subsectors": [],
        "source": source_tag,
    })
    return True


def apply_mechanism(vocab: dict, decision: dict, source_tag: str) -> bool:
    new_id = snake_id(decision.get("name") or decision.get("proposal_id", ""))
    if not new_id or entry_exists(vocab, "mechanism", new_id):
        return False
    vocab.setdefault("mechanisms", []).append({
        "id": new_id,
        "name": decision.get("name") or new_id,
        "definition": decision.get("definition") or "",
        "source": source_tag,
    })
    return True


def apply_plan_property(onto: dict, decision: dict, source_tag: str) -> bool:
    """Add property to Plan entity in ontology. onto is the full ontology dict."""
    plan_entity = next((t for t in onto.get("types", []) if t.get("id") == "Plan"), None)
    if plan_entity is None:
        return False

    prop_id = decision.get("proposal_id") or decision.get("name", "")
    prop_id = prop_id.replace("prop:", "")  # Strip prefix if present

    # Check if property already exists
    existing = plan_entity.get("properties", [])
    if any(p.get("id") == prop_id for p in existing):
        return False

    # Extract from raw decision or reconstruct
    raw = decision.get("raw") or decision
    plan_entity.setdefault("properties", []).append({
        "id": prop_id,
        "label": decision.get("name") or raw.get("property_name") or prop_id,
        "type": raw.get("data_type", "string"),
        "required": raw.get("required", False),
        "definition": decision.get("definition") or raw.get("definition") or "",
        "notes": raw.get("notes") or f"Added by {source_tag}",
    })
    return True


def apply_plan_relationship(onto: dict, decision: dict, source_tag: str) -> bool:
    """Add relationship to ontology. onto is the full ontology dict."""
    rel_type = decision.get("proposal_id") or decision.get("name", "")
    rel_type = rel_type.replace("rel:", "")  # Strip prefix if present

    # Check if relationship already exists
    existing = onto.get("relationships", [])
    if any(r.get("id") == rel_type for r in existing):
        return False

    # Extract from raw decision or reconstruct
    raw = decision.get("raw") or decision
    onto.setdefault("relationships", []).append({
        "id": rel_type,
        "label": rel_type.replace("_", " ").title(),
        "source_entity": "Plan",
        "target_entity": raw.get("target_entity", "Entity"),
        "cardinality": raw.get("cardinality", "many"),
        "definition": decision.get("definition") or raw.get("definition") or "",
        "notes": raw.get("notes") or f"Added by {source_tag}",
    })
    return True


APPLIERS = {
    "solution_category": apply_solution_category,
    "hazard": apply_hazard,
    "urban_sector": apply_urban_sector,
    "mechanism": apply_mechanism,
    # Plan properties/relationships are handled separately (operate on ontology file not vocab files)
}


# ----------------------------------------------------------------------------
# decisions-log.md append
# ----------------------------------------------------------------------------


def append_log_entries(phase: str, rejected_or_deferred: list[dict], dry_run: bool) -> None:
    if not rejected_or_deferred:
        return
    today = date.today().isoformat()
    lines = [
        "",
        f"## Corpus mining {phase} — rejected/deferred ({today})",
        "",
        f"_Applied from decisions/{phase}-decisions.json._",
        "",
    ]
    for d in rejected_or_deferred:
        dim = d.get("dimension") or "?"
        pid = d.get("proposal_id") or "?"
        status = d.get("status") or "?"
        rationale = (d.get("rationale") or "").replace("\n", " ")
        name = d.get("name") or ""
        lines.append(f"- **[{status}]** `{dim}` / `{pid}` — {name}")
        if rationale:
            lines.append(f"  - Rationale: {rationale}")
    chunk = "\n".join(lines) + "\n"
    if dry_run:
        print(f"[dry-run] would append {len(chunk):,} bytes to {LOG_FILE}")
        print(chunk)
    else:
        with LOG_FILE.open("a") as f:
            f.write(chunk)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["distribution", "mechanisms", "plans"])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    decisions_path = DECISIONS_DIR / f"{args.phase}-decisions.json"
    if not decisions_path.exists():
        sys.exit(f"no decisions file at {decisions_path}")
    decisions = json.loads(decisions_path.read_text())
    if not decisions:
        sys.exit(f"decisions file is empty: {decisions_path}")

    source_tag = f"corpus_mining_{args.phase}_v0"
    print(f"loaded {len(decisions)} decisions from {decisions_path}")

    # Group decisions
    approved = [d for d in decisions if d.get("status") in ("approved", "edited")]
    rejected_or_deferred = [d for d in decisions if d.get("status") in ("rejected", "deferred")]
    print(f"  approved/edited: {len(approved)}, rejected/deferred: {len(rejected_or_deferred)}")

    # Preload all vocabulary files we may need
    touched: set[Path] = set()
    vocab_cache: dict[Path, dict] = {}
    for path in set(VOCAB_ROUTES.values()):
        if path.exists():
            vocab_cache[path] = load_json(path)

    # Apply approved
    added_counts: dict[str, int] = {}
    skipped_counts: dict[str, int] = {}

    # Special handling for plans phase (operates on ontology file)
    if args.phase == "plans":
        ontology = load_json(ONTOLOGY_FILE)
        ontology_modified = False
        for d in approved:
            dim = d.get("dimension")
            if dim == "plan_property":
                if apply_plan_property(ontology, d, source_tag):
                    added_counts[dim] = added_counts.get(dim, 0) + 1
                    ontology_modified = True
                else:
                    skipped_counts[dim] = skipped_counts.get(dim, 0) + 1
            elif dim == "plan_relationship":
                if apply_plan_relationship(ontology, d, source_tag):
                    added_counts[dim] = added_counts.get(dim, 0) + 1
                    ontology_modified = True
                else:
                    skipped_counts[dim] = skipped_counts.get(dim, 0) + 1
            else:
                print(f"  ! unknown dimension {dim!r} for plans phase, skipping")

        if ontology_modified:
            # Update Plan entity notes
            plan_entity = next((t for t in ontology.get("types", []) if t.get("id") == "Plan"), None)
            if plan_entity:
                plan_entity["notes"] = f"Properties and relationships expanded by {source_tag} ({date.today().isoformat()})."
            touched.add(ONTOLOGY_FILE)
            save_json(ONTOLOGY_FILE, ontology, args.dry_run)
    else:
        # Vocabulary-based phases (distribution, mechanisms)
        for d in approved:
            dim = d.get("dimension")
            applier = APPLIERS.get(dim)
            if not applier:
                print(f"  ! unknown dimension {dim!r} on proposal {d.get('proposal_id')}, skipping")
                continue
            vocab_path = VOCAB_ROUTES[dim]
            if vocab_path not in vocab_cache:
                # Bootstrap a new vocab file if needed (e.g. mechanisms.json doesn't exist yet)
                if dim == "mechanism":
                    vocab_cache[vocab_path] = {
                        "_source": "Corpus-mining-derived mechanism taxonomy (Phase A).",
                        "_usage": "mechanisms.primary_mechanism and secondary_mechanisms.",
                        "mechanisms": [],
                    }
                else:
                    sys.exit(f"vocab file not found and no bootstrap for {dim}: {vocab_path}")
            if applier(vocab_cache[vocab_path], d, source_tag):
                touched.add(vocab_path)
                added_counts[dim] = added_counts.get(dim, 0) + 1
            else:
                skipped_counts[dim] = skipped_counts.get(dim, 0) + 1

        # Write all touched vocab files
        for path in touched:
            save_json(path, vocab_cache[path], args.dry_run)

    # Bump Mechanism entity in ontology-v0.1.json if we touched mechanisms.json
    mech_path = VOCAB_ROUTES["mechanism"]
    if mech_path in touched:
        ontology = load_json(ONTOLOGY_FILE)
        for t in ontology.get("types", []):
            if t.get("id") == "Mechanism":
                t["vocabulary_bindings"] = list({*(t.get("vocabulary_bindings") or []), "schemas/vocabularies/mechanisms.json"})
                t.setdefault("notes", "")
                if source_tag not in (t.get("notes") or ""):
                    t["notes"] = (t.get("notes") or "").rstrip() + f"\n\nUpdated by {source_tag} ({date.today().isoformat()})."
                break
        save_json(ONTOLOGY_FILE, ontology, args.dry_run)

    # Append rejected/deferred to decisions-log.md
    append_log_entries(args.phase, rejected_or_deferred, args.dry_run)

    print("\nSummary")
    print(f"  added:   {added_counts or '{}'}")
    print(f"  skipped: {skipped_counts or '{}'}")
    print(f"  touched files: {sorted(p.name for p in touched)}")
    if args.dry_run:
        print("\n(dry-run — no files modified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
