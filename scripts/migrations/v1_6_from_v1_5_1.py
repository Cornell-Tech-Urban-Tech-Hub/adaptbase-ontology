#!/usr/bin/env python3
"""Build ontology/ontology-v1.6.jsonld from v1.5.1.

Run with: uv run scripts/migrations/v1_6_from_v1_5_1.py
Re-runnable: ontology-v1.6.jsonld and versions.json are rebuilt from v1.5.1.

v1.6 is one decision (Decision 59, Anthony 2026-10-29, ontology#30): a stated
total of money a source attributes to a purpose ("nearly $12 billion in capital
projects that address flood risk") is a FundingTotal, kept apart from
FundingAllocation so no sum can mix totals with the project lines inside them.
"""

import json
from copy import deepcopy
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ONT = REPO / "ontology"
SRC = ONT / "ontology-v1.5.1.jsonld"
DST = ONT / "ontology-v1.6.jsonld"
VERSION = "v1.6"
DATE = "2026-10-29"
UPDATED = "2026-10-29T18:00:00.000Z"

D = "v1.6 (Decision 59)."
CLAIM_IDS = {"id": "claim_ids", "type": "array<uuid>", "required": True}


def load(p):
    return json.loads(p.read_text())


def dump(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def by_id(items, id):
    return next(x for x in items if x["id"] == id)


def pget(owner, id):
    return next(p for p in owner["properties"] if p["id"] == id)


def funding_total(fa: dict, alt_names: dict) -> dict:
    """The FundingTotal type. Money fields are copied from FundingAllocation so
    the base-units note (Decision 58) and the amount_qualifier binding stay one."""
    return {
        "id": "FundingTotal",
        "label": "Funding Total",
        "definition": (
            "A stated total of money that a source attributes to a purpose, a hazard, a system or "
            "a vulnerability, without naming the projects it pays for: 'nearly $12 billion in "
            "capital projects that address flood risk', '$46.5 billion in contributing elements'. "
            "A total is never added to another total, or to the allocations it includes: totals "
            "overlap (a project tagged for both flooding and heat sits in both) and a sum would "
            "count the same money twice. Instance type: never merges across documents; next "
            "year's report gives a new node."
        ),
        "properties": [
            {
                "id": "label",
                "type": "string",
                "required": False,
                "note": "The source's own wording for the total ('capital projects that address flood risk').",
            },
            deepcopy(pget(fa, "amount")),
            deepcopy(pget(fa, "currency")),
            deepcopy(pget(fa, "amount_qualifier")),
            {
                "id": "period_start_year",
                "type": "integer",
                "required": False,
                "note": "First year the total covers (a fiscal year, or the start of a ten-year plan). A single-year total has start = end.",
            },
            {"id": "period_end_year", "type": "integer", "required": False},
            {
                "id": "scope_basis",
                "type": "enum",
                "required": False,
                "values": ["purpose", "contributing_elements", "other"],
                "note": (
                    "How the source drew the total. purpose: money spent for the purpose "
                    "('projects that address flood risk'); contributing_elements: money in projects "
                    "with an element that contributes to it, though the project's main purpose may "
                    "be another ('$46.5 billion in contributing elements'); other: any other basis "
                    "the source states."
                ),
            },
            {
                "id": "attribution_method",
                "type": "string",
                "required": False,
                "note": "The source's own method for tagging money to the purpose, when it names one ('Climate Budgeting').",
            },
            deepcopy(alt_names),
        ],
        "vocabulary_bindings": [{"vocab": "enums", "field": "amount_qualifier"}],
        "notes": (
            f"{D} Kept apart from FundingAllocation so that no sum of allocations can mix in a "
            "total. Points at its purposes with FOR_PURPOSE (a total for two hazards points at both; "
            "there is no overlap edge between totals), at the government whose budget it reports "
            "with BUDGETED_BY, and at the allocations or smaller totals the text says sit inside it "
            "with INCLUDES. The untraced remainder (amount minus the allocations it includes) is "
            "computed when read, never stored."
        ),
        "extract_hint": (
            "Look for a sum of money tied to a purpose and no single project: 'nearly $12 billion "
            "in capital projects that address flood risk', '$2 billion for heat', 'over $200 million "
            "in heat-vulnerable neighbourhoods'. Record amount (full base units), currency and years "
            "as stated; link FOR_PURPOSE to each hazard, system, solution or vulnerability named and "
            "BUDGETED_BY to the government whose budget it is. If the text names the project the "
            "money pays for, it is a FundingAllocation, not a total."
        ),
        "@id": "ab:FundingTotal",
        "@type": "owl:Class",
    }


def edge(id, label, target, definition, cardinality, notes, hint, at_id, parent=None, props=None):
    r = {
        "id": id,
        "label": label,
        "source": "FundingTotal",
        "target": target,
        "definition": definition,
        "properties": props if props is not None else [dict(CLAIM_IDS)],
        "cardinality": cardinality,
        "notes": notes,
        "extract_hint": hint,
        "@id": at_id,
        "@type": "owl:ObjectProperty",
    }
    if parent:
        r["rdfs:subPropertyOf"] = {"@id": parent}
    r["rdfs:domain"] = {"@id": "ab:FundingTotal"}
    r["rdfs:range"] = {"@id": f"ab:{target}"}
    return r


def new_edges(rels: list) -> list:
    fp_notes = (
        f"{D} A total for two purposes points at both ('$1 billion that addresses both flooding "
        "and heat' → Flooding and Extreme heat). No edge records that two totals overlap; they "
        "are never added together."
    )
    fp_hint = "Link each purpose the text attaches the total to: the hazard, system, solution or vulnerability it is 'for' or 'addresses'."
    out = []
    for target, what, example in (
        ("Hazard", "climate hazard", "flood risk"),
        ("Solution", "kind of solution", "green infrastructure"),
        ("UrbanSystem", "urban system", "the stormwater system"),
        ("Vulnerability", "vulnerability", "heat vulnerability"),
    ):
        out.append(
            edge(
                "FOR_PURPOSE",
                "for purpose",
                target,
                f"The source attributes the total to this {what} ('{example}').",
                "many-to-many",
                fp_notes,
                fp_hint,
                f"ab:fundingTotalForPurpose{target}",
                "ab:forPurpose",
            )
        )
    out.append(
        edge(
            "BUDGETED_BY",
            "budgeted by",
            "Jurisdiction",
            "The government whose budget or capital programme the total reports.",
            "many-to-one",
            f"{D} The place, not the paying organisation: a funder the text names is PROVIDED_BY a Stakeholder or FundingStream.",
            "Usually the document's own city for a city budget report; state it when the text names another government.",
            "ab:budgetedBy",
        )
    )
    inc_notes = (
        f"{D} Many-to-many: one allocation can sit inside a flood total and a heat total. "
        "Only when the text states the containment ('of which $1.2 billion is the "
        "East Side Coastal Resiliency project'). Most totals will have none at first. The traced "
        "share is the sum of the included allocations, computed when read."
    )
    inc_hint = "Link the allocations or smaller totals the text says are part of this total. Never infer containment from matching purposes."
    for target, what in (("FundingAllocation", "allocation"), ("FundingTotal", "smaller total")):
        out.append(
            edge(
                "INCLUDES",
                "includes",
                target,
                f"The source states that this {what} is part of the total.",
                "many-to-many",
                inc_notes,
                inc_hint,
                f"ab:fundingTotalIncludes{target}",
                "ab:includes",
            )
        )
    for target in ("Stakeholder", "FundingStream"):
        base = next(r for r in rels if r["id"] == "PROVIDED_BY" and r["source"] == "FundingAllocation" and r["target"] == target)
        r = deepcopy(base)
        r["source"] = "FundingTotal"
        r["definition"] = {
            "Stakeholder": "The organisation that provides the money in the total, at the organisation grain ('federal funds from FEMA').",
            "FundingStream": "The named pot of money the total is drawn from ('City capital funds', 'the General Fund').",
        }[target]
        r["notes"] = f"{D} Same meaning as PROVIDED_BY on a FundingAllocation. Present only when the text names the {target.lower() if target == 'Stakeholder' else 'stream'}."
        r["@id"] = f"ab:fundingTotalProvidedBy{target}"
        r["rdfs:domain"] = {"@id": "ab:FundingTotal"}
        out.append(r)
    return out


def main() -> None:
    o = deepcopy(load(SRC))
    types, rels = o["types"], o["relationships"]
    fa = by_id(types, "FundingAllocation")
    alt = pget(by_id(types, "FundingStream"), "alternative_names")

    if not any(t["id"] == "FundingTotal" for t in types):
        types.insert(types.index(fa) + 1, funding_total(fa, alt))

    # Decision 59: FundingAllocation is narrowed to lines that name what they fund.
    fa["definition"] = (
        "One flow of money toward one or more named Actions or CapitalProjects, as a source states "
        "it: an award, an appropriation, a bond draw, a pledge, or a bare 'funded through grants'. "
        "The node that carries amount, currency, period, status, and the two comparison axes "
        "source_tier (who pays) and instrument_class (in what form). A sum the source ties to a "
        "purpose and no named project is a FundingTotal (v1.6). Instance type: never merges by "
        "name across documents."
    )
    if "Decision 59" not in fa["notes"]:
        fa["notes"] += (
            f" {D} An allocation names what it pays for; a stated total for a purpose "
            "('$12 billion for flood risk') is a FundingTotal, which no allocation sum includes."
        )

    if not any(r["source"] == "FundingTotal" for r in rels):
        anchor = max(i for i, r in enumerate(rels) if r["source"] == "FundingAllocation")
        rels[anchor + 1 : anchor + 1] = new_edges(rels)

    aq = by_id(o["vocabularies"], "enums.amount_qualifier")
    if "FundingTotal.amount_qualifier" not in aq["bound_to"]:
        aq["bound_to"].append("FundingTotal.amount_qualifier")
        aq["description"] = "How an allocation or total amount is stated (Decisions 43, 59)."

    md = o["metadata"]
    md["types_count"] = len(types)
    md["relationships_count"] = len(rels)
    n_pred = len({r["id"] for r in rels})
    summary = (
        f"v1.6 (2026-10-29): FundingTotal — a stated total of money for a purpose, kept apart "
        f"from FundingAllocation (Decision 59). New FOR_PURPOSE, BUDGETED_BY, INCLUDES; PROVIDED_BY "
        f"gains FundingTotal. {len(types)} types, {len(rels)} relationships, {n_pred} predicate ids."
    )
    md["change_history"] = [h for h in md.get("change_history", []) if not h.startswith("v1.6 ")]
    md["change_history"].insert(0, summary)

    o["version"] = VERSION
    o["updated"] = UPDATED
    o["update_note"] = (
        "v1.6 — one decision (Decision 59, 2026-10-29): a stated total of money a source "
        "attributes to a purpose is a FundingTotal, a type of its own so no sum mixes totals "
        "with the allocations inside them. It points at its purposes (FOR_PURPOSE), the "
        "government whose budget it reports (BUDGETED_BY), the allocations or totals the text "
        "says it includes (INCLUDES) and its funder (PROVIDED_BY). FundingAllocation is narrowed "
        "to lines that name what they fund."
    )
    o["version_notes"] = [n for n in o.get("version_notes", []) if n.get("version") != VERSION]
    o["version_notes"].insert(
        0,
        {
            "version": VERSION,
            "date": DATE,
            "summary": o["update_note"],
            "changes": [
                {"type": "added", "text": "FundingTotal type: label, amount, currency, amount_qualifier, period_start_year, period_end_year, scope_basis, attribution_method, alternative_names; instance type (Decision 59)"},
                {"type": "added", "text": "FOR_PURPOSE (FundingTotal → Hazard | Solution | UrbanSystem | Vulnerability) (Decision 59)"},
                {"type": "added", "text": "BUDGETED_BY (FundingTotal → Jurisdiction), many-to-one (Decision 59)"},
                {"type": "added", "text": "INCLUDES (FundingTotal → FundingAllocation | FundingTotal), only where the text states it (Decision 59)"},
                {"type": "added", "text": "PROVIDED_BY gains FundingTotal → Stakeholder | FundingStream (Decision 59)"},
                {"type": "changed", "text": "FundingAllocation definition narrowed to lines that name the Action or CapitalProject they fund (Decision 59)"},
            ],
        },
    )
    dump(DST, o)
    print(f"wrote {DST.name}: {len(types)} types, {len(rels)} edges, {n_pred} predicate ids")
    vs = load(ONT / "versions.json")
    if vs[0]["value"] != VERSION:
        vs.insert(0, {"path": f"../ontology/ontology-{VERSION}.jsonld", "label": VERSION, "value": VERSION})
        dump(ONT / "versions.json", vs)


if __name__ == "__main__":
    main()
