"""FastAPI review server for corpus-mining proposals.

Serves:
- GET /                       → review.html
- GET /api/proposals/{phase}  → flattened proposals for that phase
- GET /api/decisions/{phase}  → previously submitted decisions (for resume)
- POST /api/decisions/{phase} → append one decision

Decision JSON shape (submitted by viewer.js):
{
    "proposal_id": str,          # unique id within the phase
    "dimension": str | null,
    "status": "approved" | "edited" | "rejected" | "deferred",
    "name": str | null,
    "definition": str | null,
    "rationale": str | null,
    "timestamp": iso-8601 str
}

Usage:
    uv run packages/ontology/mining/scripts/review_server.py --port 8766
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Any

MINING_ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY_ROOT = MINING_ROOT.parent
PROPOSALS = MINING_ROOT / "proposals"
DECISIONS = MINING_ROOT / "decisions"
VIEWER = MINING_ROOT / "viewer"
VOCAB_DIR = ONTOLOGY_ROOT / "schemas" / "vocabularies"

DECISIONS.mkdir(parents=True, exist_ok=True)
PROPOSALS.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Ontology Mining Review")

# Load existing mechanism seed vocabulary at startup
_mechanism_seed_vocab: list[dict] | None = None


def _load_mechanism_vocab() -> list[dict]:
    global _mechanism_seed_vocab
    if _mechanism_seed_vocab is None:
        enums_path = VOCAB_DIR / "enums.json"
        if enums_path.exists():
            enums = json.loads(enums_path.read_text())
            _mechanism_seed_vocab = enums.get("mechanism_seed_vocabulary", {}).get("values", [])
        else:
            _mechanism_seed_vocab = []
    return _mechanism_seed_vocab


class Decision(BaseModel):
    proposal_id: str
    dimension: str | None = None
    status: str  # approved | edited | rejected | deferred
    name: str | None = None
    definition: str | None = None
    rationale: str | None = None


def _flatten_distribution_proposals(raw: dict) -> list[dict]:
    """distribution-gaps-v0.json has proposals grouped by dimension. Flatten
    into one list with a synthetic stable id so the viewer can iterate."""
    out: list[dict] = []
    by_dim = raw.get("proposals_by_dimension") or {}
    for dim, proposals in by_dim.items():
        for i, p in enumerate(proposals or []):
            pid = f"{dim}:{p.get('proposed_id') or i}"
            out.append({
                "proposal_id": pid,
                "dimension": dim,
                "proposed_id": p.get("proposed_id"),
                "proposed_name": p.get("proposed_name"),
                "definition": p.get("definition"),
                "supporting_action_ids": p.get("supporting_action_ids") or [],
                "external_vocab_match": p.get("external_vocab_match"),
                "alternative": p.get("alternative"),
                "raw": p,
            })
    return out


def _flatten_mechanism_proposals(raw: Any) -> list[dict]:
    """mechanisms-v0.json (future) — expected to be a flat list."""
    if not isinstance(raw, list):
        return []
    out = []
    for i, p in enumerate(raw):
        pid = p.get("cluster_id") or p.get("proposed_id") or f"mech:{i}"
        out.append({
            "proposal_id": str(pid),
            "dimension": "mechanism",
            "proposed_id": p.get("proposed_id") or p.get("cluster_id"),
            "proposed_name": p.get("proposed_name") or p.get("canonical_name"),
            "definition": p.get("definition") or p.get("proposed_definition"),
            "examples": p.get("examples") or [],
            "cluster_size": p.get("cluster_size"),
            "external_vocab_match": p.get("external_vocab") or p.get("external_vocab_match"),
            "ambiguities": p.get("ambiguities") or [],
            "raw": p,
        })
    return out


def _flatten_plan_proposals(raw: dict) -> list[dict]:
    """plan-properties-v0.json has properties and relationships arrays."""
    out: list[dict] = []

    # Properties
    for i, p in enumerate(raw.get("properties", [])):
        pid = f"prop:{p.get('property_id', i)}"
        out.append({
            "proposal_id": pid,
            "dimension": "plan_property",
            "proposed_id": p.get("property_id"),
            "proposed_name": p.get("property_name"),
            "definition": p.get("definition"),
            "examples": [{"text": str(ex)} for ex in (p.get("examples") or [])],
            "data_type": p.get("data_type"),
            "required": p.get("required"),
            "notes": p.get("notes"),
            "raw": p,
        })

    # Relationships
    for i, r in enumerate(raw.get("relationships", [])):
        pid = f"rel:{r.get('relationship_type', i)}"
        out.append({
            "proposal_id": pid,
            "dimension": "plan_relationship",
            "proposed_id": r.get("relationship_type"),
            "proposed_name": r.get("relationship_type"),
            "definition": r.get("definition"),
            "target_entity": r.get("target_entity"),
            "cardinality": r.get("cardinality"),
            "notes": r.get("notes"),
            "raw": r,
        })

    return out


def _proposals_path(phase: str) -> Path:
    name = {
        "distribution": "distribution-gaps-v0.json",
        "mechanisms": "mechanisms-v0.json",
        "plans": "plan-properties-v0.json"
    }.get(phase)
    if not name:
        raise HTTPException(400, f"unknown phase: {phase}")
    return PROPOSALS / name


def _decisions_path(phase: str) -> Path:
    return DECISIONS / f"{phase}-decisions.json"


@app.get("/api/proposals/{phase}")
def get_proposals(phase: str) -> list[dict]:
    path = _proposals_path(phase)
    if not path.exists():
        raise HTTPException(404, f"proposals not found at {path}")
    raw = json.loads(path.read_text())
    if phase == "distribution":
        return _flatten_distribution_proposals(raw)
    if phase == "mechanisms":
        return _flatten_mechanism_proposals(raw)
    if phase == "plans":
        return _flatten_plan_proposals(raw)
    raise HTTPException(400, f"unknown phase: {phase}")


@app.get("/api/decisions/{phase}")
def get_decisions(phase: str) -> list[dict]:
    path = _decisions_path(phase)
    if not path.exists():
        return []
    return json.loads(path.read_text())


@app.post("/api/decisions/{phase}")
def post_decision(phase: str, decision: Decision) -> dict:
    if decision.status not in {"approved", "edited", "rejected", "deferred"}:
        raise HTTPException(400, f"bad status: {decision.status}")
    path = _decisions_path(phase)
    existing: list[dict] = json.loads(path.read_text()) if path.exists() else []
    # Replace any prior decision for the same proposal_id
    existing = [d for d in existing if d.get("proposal_id") != decision.proposal_id]
    record = decision.model_dump()
    record["timestamp"] = datetime.now(timezone.utc).isoformat()
    existing.append(record)
    path.write_text(json.dumps(existing, indent=2))
    return record


@app.delete("/api/decisions/{phase}/{proposal_id}")
def delete_decision(phase: str, proposal_id: str) -> dict:
    path = _decisions_path(phase)
    if not path.exists():
        return {"removed": 0}
    existing = json.loads(path.read_text())
    before = len(existing)
    existing = [d for d in existing if d.get("proposal_id") != proposal_id]
    path.write_text(json.dumps(existing, indent=2))
    return {"removed": before - len(existing)}


@app.get("/api/vocab/mechanism-seed")
def get_mechanism_seed_vocab() -> list[dict]:
    """Return the existing mechanism seed vocabulary for reference during review."""
    return _load_mechanism_vocab()


# Serve viewer files
app.mount("/viewer", StaticFiles(directory=VIEWER), name="viewer")


@app.get("/")
def index() -> FileResponse:
    html = VIEWER / "review.html"
    if not html.exists():
        raise HTTPException(500, f"viewer HTML missing at {html}")
    return FileResponse(html)


def main() -> int:
    import uvicorn

    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8769)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    print(f"Review server at http://{args.host}:{args.port}  (phases: distribution, mechanisms, plans)")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
