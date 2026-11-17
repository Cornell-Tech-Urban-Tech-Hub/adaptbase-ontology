#!/usr/bin/env python3
"""Build ontology/ontology-v1.9.jsonld from v1.8, and add the enums.round_type block.

Run with: uv run scripts/migrations/v1_9_from_v1_8.py
Re-runnable: the enums block is added once; ontology-v1.9.jsonld and versions.json are
rebuilt from v1.8. Then run scripts/export/build_vocab_jsonld.py for the vocabulary twins.

v1.9 is one decision (Decision 62, Anthony 2026-11-16): the company directory. A Supplier
gets a short profile, OFFERS the kinds of solution it sells, is LOCATED_IN the jurisdiction
of its headquarters, and a funding round is a FundingAllocation that FUNDS the Supplier
and is PROVIDED_BY each investor.
"""

import json
from copy import deepcopy
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ONT = REPO / "ontology"
SRC = ONT / "ontology-v1.8.jsonld"
DST = ONT / "ontology-v1.9.jsonld"
ENUMS = ONT / "vocabularies" / "enums.json"
VERSION = "v1.9"
DATE = "2026-11-16"
UPDATED = "2026-11-16T18:00:00.000Z"

D = "v1.9 (Decision 62)."

ROUND_TYPE = {
    "_source": "v1.9 (Decision 62)",
    "_usage": "FundingAllocation.round_type",
    "_note": (
        "Only on an allocation that FUNDS a Supplier. The kind of round as the source names it; "
        "not_stated when a source says only that the investor backs the company."
    ),
    "values": [
        {"id": "pre_seed", "name": "Pre-seed", "description": "A pre-seed or angel round."},
        {"id": "seed", "name": "Seed", "description": "A seed round."},
        {"id": "series_a", "name": "Series A", "description": "A Series A round."},
        {"id": "series_b", "name": "Series B", "description": "A Series B round."},
        {"id": "series_c_or_later", "name": "Series C or later", "description": "A Series C or any later lettered round."},
        {
            "id": "growth",
            "name": "Growth or private equity",
            "description": "A growth-equity or private-equity investment the source does not give a series letter.",
        },
        {
            "id": "grant",
            "name": "Grant",
            "description": "A grant or award to the company from a public or philanthropic funder ('an SBIR Phase II award').",
        },
        {
            "id": "accelerator_cohort",
            "name": "Accelerator or incubator cohort",
            "description": "The company was taken into an accelerator or incubator cohort. May carry no money.",
        },
        {"id": "debt", "name": "Debt", "description": "A loan or venture debt to the company."},
        {"id": "other", "name": "Other", "description": "A kind of round the source names that is none of the above."},
        {
            "id": "not_stated",
            "name": "Not stated",
            "description": "The source says the investor backs the company and names no round ('one of our portfolio companies').",
        },
    ],
}


def load(p):
    return json.loads(p.read_text())


def dump(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def by_id(items, id):
    return next(x for x in items if x["id"] == id)


def pget(owner, id):
    return next(p for p in owner["properties"] if p["id"] == id)


def rel(rels, id, source, target):
    return next(r for r in rels if r["id"] == id and r["source"] == source and r["target"] == target)


def has(rels, id, source, target):
    return any(r["id"] == id and r["source"] == source and r["target"] == target for r in rels)


def add_round_type_block() -> int:
    e = load(ENUMS)
    if "round_type" not in e:
        out = {}
        for k, v in e.items():
            out[k] = v
            if k == "total_stage":
                out["round_type"] = ROUND_TYPE
        e = out
        dump(ENUMS, e)
    return len(e["round_type"]["values"])


def supplier(o: dict) -> None:
    s = by_id(o["types"], "Supplier")
    s["definition"] = (
        "A company that sells products or services used in adaptation: a vendor, manufacturer, "
        "or service provider. It supplies technology, components, or services for adaptation "
        "actions (SUPPLIES) and offers kinds of solution for sale (OFFERS)."
    )
    new_props = [
        {
            "id": "website",
            "type": "string",
            "required": False,
            "note": (
                f"{D} The company's own website. In the consuming store its registrable domain "
                "is a verified identifier: a Supplier merges on a matching domain or Wikidata QID, "
                "never on its name."
            ),
        },
        {
            "id": "description",
            "type": "string",
            "required": False,
            "note": (
                f"{D} One or two sentences on what the company sells, written by the maintainers "
                "from its sources. Never copied marketing text, and no named people."
            ),
        },
        {
            "id": "founded_year",
            "type": "integer",
            "required": False,
            "note": f"{D} The year the company was founded, when a source states it.",
        },
        {
            "id": "operating_status",
            "type": "enum",
            "required": False,
            "values": ["active", "acquired", "closed"],
            "note": (
                f"{D} As of the latest observation. acquired: bought by another company, whether or "
                "not the name survives; closed: no longer trading. Leave empty when no source says."
            ),
        },
    ]
    have = {p["id"] for p in s["properties"]}
    at = next(i for i, p in enumerate(s["properties"]) if p["id"] == "role") + 1
    s["properties"][at:at] = [p for p in new_props if p["id"] not in have]
    if "Decision 62" not in s["notes"]:
        s["notes"] += (
            f" {D} The company directory: a Supplier carries a short profile, OFFERS the kinds of "
            "solution it sells, is LOCATED_IN the jurisdiction of its headquarters, and a funding "
            "round is a FundingAllocation that FUNDS it. An organization that only invests is a "
            "Stakeholder (its named fund a FundingStream), not a Supplier. Supplier stays a type of "
            "its own; folding it into Stakeholder (review 2026-10-06, item 10) is not taken."
        )
    if "Decision 62" not in s["extract_hint"] and "its own site" not in s["extract_hint"]:
        s["extract_hint"] += (
            " On a company's own site or a description of the company, record its website and "
            "the year it was founded when stated; do not copy its marketing text into description."
        )


def funding_allocation(o: dict) -> None:
    fa = by_id(o["types"], "FundingAllocation")
    fa["definition"] = (
        "One flow of money toward one or more named Actions or CapitalProjects, or into a named "
        "company (a Supplier), as a source states it: an award, an appropriation, a bond draw, a "
        "pledge, a company's funding round, or a bare 'funded through grants'. "
        "The node that carries amount, currency, period, status, and the two comparison axes "
        "source_tier (who pays) and instrument_class (in what form). A sum the source ties to a "
        "purpose and no named project is a FundingTotal (v1.6). Instance type: never merges by "
        "name across documents."
    )
    if not any(p["id"] == "round_type" for p in fa["properties"]):
        at = next(i for i, p in enumerate(fa["properties"]) if p["id"] == "instrument_type") + 1
        fa["properties"].insert(
            at,
            {
                "id": "round_type",
                "type": "enum",
                "required": False,
                "values": [v["id"] for v in ROUND_TYPE["values"]],
                "note": (
                    f"{D} Only on an allocation that FUNDS a Supplier: the kind of round as the "
                    "source names it; not_stated when a source says only that the investor backs "
                    "the company. Set instrument_class as well (private_investment for an equity "
                    "round, grant, debt). The round's year is period_start_year = period_end_year."
                ),
                "vocabulary_binding": {"vocab": "enums", "field": "round_type"},
                "ab:boundToVocabulary": {"@id": "abv:enums-round_type"},
            },
        )
    vb = {"vocab": "enums", "field": "round_type"}
    if vb not in fa["vocabulary_bindings"]:
        fa["vocabulary_bindings"].append(vb)
    if "Decision 62" not in fa["notes"]:
        fa["notes"] += (
            f" {D} A company's funding round is one allocation that FUNDS the Supplier and is "
            "PROVIDED_BY each investor, so its amount is held once however many investors joined. "
            "When a source says only that an investor backs a company, that is one allocation for "
            "that investor and that company with round_type not_stated and no amount; a stated "
            "round found later for the same pair may be the same round, which a reviewer decides. "
            "No sum mixes allocations that FUND a Supplier with allocations that FUND an Action or "
            "CapitalProject: the first is money invested in a company, the second is money spent "
            "on adaptation work. Every reader that adds up amounts filters on the FUNDS target."
        )
    if "funding round" not in fa["extract_hint"]:
        fa["extract_hint"] += (
            " For a company: 'raised a $4M seed round led by X' is one allocation (round_type "
            "seed, amount 4000000) that FUNDS the Supplier and is PROVIDED_BY each named investor; "
            "a portfolio page that says only that the company is in the portfolio is one "
            "allocation with round_type not_stated and no amount."
        )


def new_edges(rels: list) -> None:
    claim_opt = {"id": "claim_ids", "type": "array<uuid>", "required": False}
    is_lead = {
        "id": "is_lead",
        "type": "boolean",
        "required": False,
        "note": (
            f"{D} True when the source says this investor led the round. A fact about one "
            "investor in one round, so it sits on the link."
        ),
    }

    # OFFERS: Supplier -> Solution
    if not has(rels, "OFFERS", "Supplier", "Solution"):
        at = rels.index(rel(rels, "SUPPLIES", "Supplier", "Action")) + 1
        rels.insert(
            at,
            {
                "id": "OFFERS",
                "label": "offers",
                "source": "Supplier",
                "target": "Solution",
                "definition": (
                    "The company sells this kind of solution: a product or service line it offers, "
                    "wherever it is deployed."
                ),
                "properties": [
                    {
                        "id": "product_names",
                        "type": "array<string>",
                        "required": False,
                        "note": (
                            "The company's own names for its products or services of this kind. "
                            "Text only: there is no product node."
                        ),
                    },
                    dict(claim_opt),
                ],
                "cardinality": "many-to-many",
                "notes": (
                    f"{D} A fact about the company, true in every place it sells, so it may sit on "
                    "the shared Solution node. Written only from a source about the company itself: "
                    "its own site, an investor's or accelerator's description of it, a market list. "
                    "Never inferred from one deployment: 'sensors provided by Siemens' in a city's "
                    "plan is SUPPLIES on that Action, which is why v0.8 took SUPPLIES off Solution "
                    "(Decision 33). Reading rule: Jurisdiction ← Action → Solution ← OFFERS ← "
                    "Supplier answers 'who sells this kind of thing', never 'who supplied this "
                    "city'; that question is SUPPLIES."
                ),
                "extract_hint": (
                    "On a company's own page or a description of the company: the kinds of solution "
                    "it sells — 'we build low-cost flood sensors' → OFFERS the flood-sensor class, "
                    "with the product's name in product_names. Prefer a name from the "
                    "solution-concepts vocabulary. Do not emit it from a passage about one project; "
                    "that is SUPPLIES on the Action."
                ),
                "@id": "ab:offers",
                "@type": "owl:ObjectProperty",
                "rdfs:domain": {"@id": "ab:Supplier"},
                "rdfs:range": {"@id": "ab:Solution"},
            },
        )

    # SUPPLIES gains product_names
    sup = rel(rels, "SUPPLIES", "Supplier", "Action")
    if not any(p["id"] == "product_names" for p in sup["properties"]):
        sup["properties"].insert(
            1,
            {
                "id": "product_names",
                "type": "array<string>",
                "required": False,
                "note": f"{D} The supplier's own names for the products or services it provided to this action. Text only.",
            },
        )

    # LOCATED_IN: Supplier -> Jurisdiction; the predicate now has two pairs
    eu = rel(rels, "LOCATED_IN", "ExposureUnit", "Jurisdiction")
    eu["@id"] = "ab:exposureUnitLocatedInJurisdiction"
    eu["rdfs:subPropertyOf"] = {"@id": "ab:locatedIn"}
    if not has(rels, "LOCATED_IN", "Supplier", "Jurisdiction"):
        rels.insert(
            rels.index(rel(rels, "OFFERS", "Supplier", "Solution")) + 1,
            {
                "id": "LOCATED_IN",
                "label": "located in",
                "source": "Supplier",
                "target": "Jurisdiction",
                "definition": "The company's headquarters is in this jurisdiction.",
                "properties": [dict(claim_opt)],
                "cardinality": "many-to-one",
                "notes": (
                    f"{D} Headquarters only, as the company or a public register states it: the city "
                    "when known, otherwise the country. Offices, plants and markets are not "
                    "recorded. Where the company's work is deployed is DEPLOYED_IN on the Action it "
                    "SUPPLIES, never this edge."
                ),
                "extract_hint": (
                    "'Headquartered in Rotterdam', 'a Nairobi-based company', the address on the "
                    "company's own contact page. Not the cities it lists as customers."
                ),
                "@id": "ab:supplierLocatedInJurisdiction",
                "@type": "owl:ObjectProperty",
                "rdfs:subPropertyOf": {"@id": "ab:locatedIn"},
                "rdfs:domain": {"@id": "ab:Supplier"},
                "rdfs:range": {"@id": "ab:Jurisdiction"},
            },
        )

    # FUNDS: FundingAllocation -> Supplier
    if not has(rels, "FUNDS", "FundingAllocation", "Supplier"):
        at = rels.index(rel(rels, "FUNDS", "FundingAllocation", "CapitalProject")) + 1
        rels.insert(
            at,
            {
                "id": "FUNDS",
                "label": "funds",
                "source": "FundingAllocation",
                "target": "Supplier",
                "definition": (
                    "The allocation is money put into this company: a funding round, a grant, an "
                    "accelerator award or a loan."
                ),
                "properties": [{"id": "claim_ids", "type": "array<uuid>", "required": True}],
                "cardinality": "many-to-many",
                "notes": (
                    f"{D} One round is one allocation, PROVIDED_BY each investor, so the amount is "
                    "held once. Never added to allocations that FUND an Action or CapitalProject."
                ),
                "extract_hint": (
                    "'X raised a $4M seed round led by Y' → the allocation FUNDS X. A portfolio "
                    "page that lists X → an allocation with round_type not_stated FUNDS X."
                ),
                "@id": "ab:fundingAllocationFundsSupplier",
                "@type": "owl:ObjectProperty",
                "rdfs:subPropertyOf": {"@id": "ab:funds"},
                "rdfs:domain": {"@id": "ab:FundingAllocation"},
                "rdfs:range": {"@id": "ab:Supplier"},
            },
        )

    # PROVIDED_BY: FundingAllocation -> Supplier, and is_lead on the allocation's pairs
    if not has(rels, "PROVIDED_BY", "FundingAllocation", "Supplier"):
        at = rels.index(rel(rels, "PROVIDED_BY", "FundingAllocation", "FundingStream")) + 1
        rels.insert(
            at,
            {
                "id": "PROVIDED_BY",
                "label": "provided by",
                "source": "FundingAllocation",
                "target": "Supplier",
                "definition": (
                    "The company that provides the money, when the investor is itself a company "
                    "held as a Supplier ('a strategic investment from a pump manufacturer')."
                ),
                "properties": [{"id": "claim_ids", "type": "array<uuid>", "required": True}],
                "cardinality": "many-to-many",
                "notes": (
                    f"{D} Only when the investing company is a Supplier in its own right. An "
                    "investment firm is a Stakeholder; its named fund is a FundingStream."
                ),
                "extract_hint": (
                    "Link to the company the text names as investor when that company also sells "
                    "adaptation products or services."
                ),
                "@id": "ab:fundingAllocationProvidedBySupplier",
                "@type": "owl:ObjectProperty",
                "rdfs:subPropertyOf": {"@id": "ab:providedBy"},
                "rdfs:domain": {"@id": "ab:FundingAllocation"},
                "rdfs:range": {"@id": "ab:Supplier"},
            },
        )
    for target in ("Stakeholder", "FundingStream", "Supplier"):
        r = rel(rels, "PROVIDED_BY", "FundingAllocation", target)
        if not any(p["id"] == "is_lead" for p in r["properties"]):
            r["properties"].insert(0, dict(is_lead))


def main() -> None:
    n_round = add_round_type_block()
    o = deepcopy(load(SRC))
    types, rels = o["types"], o["relationships"]

    supplier(o)
    funding_allocation(o)
    new_edges(rels)

    if not any(v["id"] == "enums.round_type" for v in o["vocabularies"]):
        ts = by_id(o["vocabularies"], "enums.total_stage")
        o["vocabularies"].insert(
            o["vocabularies"].index(ts) + 1,
            {
                "id": "enums.round_type",
                "label": "Round type",
                "type": "internal",
                "url": "",
                "description": "The kind of funding round an allocation to a company is (Decision 62).",
                "bound_to": ["FundingAllocation.round_type"],
                "terms_count": n_round,
                "@id": "abv:enums-round_type",
                "@type": "skos:ConceptScheme",
            },
        )

    md = o["metadata"]
    md["types_count"] = len(types)
    md["relationships_count"] = len(rels)
    md["vocabularies_count"] = len(o["vocabularies"])
    n_pred = len({r["id"] for r in rels})
    summary = (
        f"v1.9 (2026-11-16): the company directory (Decision 62). Supplier profile; OFFERS "
        f"(Supplier → Solution); LOCATED_IN, FUNDS and PROVIDED_BY reach Supplier; round_type on "
        f"FundingAllocation. {len(types)} types, {len(rels)} relationships, {n_pred} predicate ids."
    )
    md["change_history"] = [h for h in md.get("change_history", []) if not h.startswith("v1.9 ")]
    md["change_history"].insert(0, summary)

    o["version"] = VERSION
    o["updated"] = UPDATED
    o["update_note"] = (
        "v1.9 — one decision (Decision 62, 2026-11-16): the company directory. A Supplier gets a "
        "short profile (website, description, founded_year, operating_status), OFFERS the kinds "
        "of solution it sells, and is LOCATED_IN the jurisdiction of its headquarters. A funding "
        "round is a FundingAllocation that FUNDS the Supplier and is PROVIDED_BY each investor; "
        "round_type says what kind of round. No sum mixes money invested in companies with money "
        "spent on adaptation work."
    )
    o["version_notes"] = [n for n in o.get("version_notes", []) if n.get("version") != VERSION]
    o["version_notes"].insert(
        0,
        {
            "version": VERSION,
            "date": DATE,
            "summary": o["update_note"],
            "changes": [
                {"type": "added", "text": "OFFERS (Supplier → Solution) with product_names: the kinds of solution a company sells, written only from sources about the company (Decision 62)"},
                {"type": "added", "text": "FUNDS gains FundingAllocation → Supplier: a company's funding round is one allocation (Decision 62)"},
                {"type": "added", "text": "PROVIDED_BY gains FundingAllocation → Supplier; is_lead on the three FundingAllocation PROVIDED_BY pairs (Decision 62)"},
                {"type": "added", "text": "LOCATED_IN gains Supplier → Jurisdiction (headquarters), many-to-one (Decision 62)"},
                {"type": "added", "text": "FundingAllocation.round_type, bound to the new enums.round_type (11 values) (Decision 62)"},
                {"type": "added", "text": "Supplier properties: website, description, founded_year, operating_status (active | acquired | closed) (Decision 62)"},
                {"type": "added", "text": "SUPPLIES.product_names (Decision 62)"},
                {"type": "changed", "text": "FundingAllocation definition: an allocation can also fund a named company; Supplier definition reworded as a company that sells (Decision 62)"},
                {"type": "changed", "text": "LOCATED_IN (ExposureUnit → Jurisdiction) @id is now ab:exposureUnitLocatedInJurisdiction, a sub-property of ab:locatedIn, as for every predicate with several pairs"},
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
