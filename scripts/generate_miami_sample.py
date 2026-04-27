# /// script
# dependencies = [
#   "openai>=1.0",
#   "PyPDF2>=3.0",
# ]
# ///
"""Generate per-solution sample ontology data for Miami from Supabase + PDF."""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from openai import OpenAI
from PyPDF2 import PdfReader


def load_env(env_path: Path) -> dict:
    env = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip("\"'")
    return env


def query_supabase(url: str, key: str, endpoint: str) -> list:
    req = Request(
        f"{url}/rest/v1/{endpoint}",
        headers={"apikey": key, "Authorization": f"Bearer {key}"},
    )
    return json.loads(urlopen(req).read())


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages.append(f"--- PAGE {i + 1} ---\n{text}")
    return "\n\n".join(pages)


def build_ontology_context(ontology: dict) -> str:
    lines = ["# Ontology Schema\n"]

    lines.append("## Types\n")
    for t in ontology["types"]:
        props = []
        for p in t.get("properties", []):
            pid = p.get("name", p.get("id", "?"))
            req = " (required)" if p.get("required") else ""
            enum = f" enum={p['enum_values']}" if "enum_values" in p else ""
            props.append(f"  - {pid}{req}{enum}")
        lines.append(f"### {t['id']}\n{t['definition']}\nProperties:")
        lines.extend(props)
        lines.append("")

    lines.append("## Relationships\n")
    for r in ontology["relationships"]:
        rprops = []
        for p in r.get("properties", []):
            pid = p.get("name", p.get("id", "?"))
            rprops.append(pid)
        pstr = f" [properties: {', '.join(rprops)}]" if rprops else ""
        lines.append(f"- {r['id']}: {r['source']} --{r['label']}--> {r['target']}{pstr}")
        if r.get("definition"):
            lines.append(f"  {r['definition']}")

    return "\n".join(lines)


def build_per_solution_prompt(
    ontology_context: str,
    pdf_text: str,
    solution: dict,
    city: dict,
) -> tuple[str, str]:
    c = solution.get("crawler", {})

    system = f"""You are an ontology extraction engine. Given a climate adaptation plan and ONE specific solution identified in that plan, extract all entities (nodes) and relationships (edges) connected to that solution according to the ontology schema below.

{ontology_context}

## Output Format

Return a JSON object with two arrays: "nodes" and "edges".

Each node:
{{
  "id": "<type_prefix>_<n>",
  "type": "<ontology type ID>",
  "properties": {{ ... }}
}}

Each edge:
{{
  "id": "e_<n>",
  "type": "<relationship ID>",
  "source": "<node id>",
  "target": "<node id>",
  "properties": {{ ... }}
}}

## Rules
1. The Solution node MUST have id "solution" and include the supabase_id in its properties. The Solution "name" property MUST be a concise human-readable title (5-10 words) that summarizes the intervention — NOT the raw quote from the plan. Example: "Building Energy Performance Benchmarking Program" instead of pasting the quote.
2. The Plan node (the climate plan document this solution comes from) MUST have id "plan". A Plan is NOT a Solution — it is the document that prescribes the solution.
3. The Location node for Miami MUST have id "location".
4. Extract all other entity types connected to THIS solution: Hazards it mitigates, UrbanSystems it operates on, Mechanisms it works by, Stakeholders involved, Vulnerabilities it reduces, ExposureUnits it protects, Barriers it faces, EnablingConditions it requires, ResilienceGoals it contributes to, Outcomes it produces, Indicators, FinancingSources, FinancialInstruments, Suppliers.
5. Create relationships between nodes wherever the PDF provides evidence. Include a "claim_quote" property on each edge with the supporting text snippet (max 200 chars).
6. Link the Plan to the Solution via PRESCRIBES. Link the Plan to its ResilienceGoals via SETS_GOAL.
7. Be thorough but precise — only extract entities that relate to THIS specific solution.
8. Return ONLY valid JSON, no markdown fences or explanation."""

    user = f"""## Climate Adaptation Plan (Full Text)

{pdf_text}

## The Solution to Extract For

Supabase ID: {solution['id']}
Category: {c.get('category', '?')}
Subcategory: {c.get('subcategory', '?')}
Quote from plan: {c.get('quote', '')}
Context from plan: {c.get('context', '')}

## Location Context
City: {city['name']}
Latitude: {city['latitude']}, Longitude: {city['longitude']}
Population: {city['population']}

Extract all ontology entities and relationships connected to THIS specific solution. The solution is an action or intervention described in the plan — the plan itself is a separate Plan node that PRESCRIBES this solution."""

    return system, user


def extract_for_solution(
    env: dict,
    ontology: dict,
    pdf_text: str,
    solution: dict,
    city: dict,
    sol_index: int,
) -> dict:
    c = solution.get("crawler", {})
    sol_name = c.get("quote", "")[:80]
    print(f"\n  [{sol_index + 1}] Extracting for: {sol_name}...")

    ontology_context = build_ontology_context(ontology)
    system_prompt, user_prompt = build_per_solution_prompt(
        ontology_context, pdf_text, solution, city
    )

    client = OpenAI(
        api_key=env["OPENAI_API_KEY"],
        base_url=env["OPENAI_API_BASE"],
    )

    response = client.chat.completions.create(
        model=env.get("LLM_MODEL", "anthropic.claude-4.5-sonnet"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        max_tokens=16000,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
        raw = re.sub(r"\n?```\s*$", "", raw)

    result = json.loads(raw)
    llm_nodes = result.get("nodes", [])
    llm_edges = result.get("edges", [])

    # Use LLM-generated solution title if available, fall back to quote
    llm_sol = next((n for n in llm_nodes if n["id"] == "solution"), {})
    llm_name = llm_sol.get("properties", {}).get("name", "")
    sol_name_final = llm_name if llm_name else c.get("quote", "")[:100]

    sol_node = {
        "id": "solution",
        "type": "Solution",
        "properties": {
            "name": sol_name_final,
            "description": c.get("context", ""),
            "quote": c.get("quote", ""),
            "category_id": c.get("category", ""),
            "subcategory_id": c.get("subcategory", ""),
            "supabase_id": solution["id"],
        },
    }

    loc_node = {
        "id": "location",
        "type": "Location",
        "properties": {
            "name": city["name"],
            "location_type": "city",
            "country": "USA",
            "region": "Southeast Florida",
            "loc_id": city["loc_id"],
            "geometry": {
                "type": "Point",
                "coordinates": [city["longitude"], city["latitude"]],
            },
        },
    }

    # Merge: keep LLM nodes but override solution and location with ours
    nodes = [sol_node, loc_node]
    seen_ids = {"solution", "location"}
    for n in llm_nodes:
        if n["id"] in seen_ids:
            continue
        if n["type"] == "Solution" and n["id"] != "solution":
            continue
        nodes.append(n)
        seen_ids.add(n["id"])

    # Ensure IMPLEMENTED_IN edge exists
    impl_edge = {
        "id": "e_implemented_in",
        "type": "IMPLEMENTED_IN",
        "source": "solution",
        "target": "location",
        "properties": {"deployment_context": "City of Miami"},
    }

    edges = [impl_edge]
    seen_edge_ids = {"e_implemented_in"}
    for e in llm_edges:
        if e["id"] in seen_edge_ids:
            continue
        if e["source"] in seen_ids and e["target"] in seen_ids:
            edges.append(e)
            seen_edge_ids.add(e["id"])

    # Count dangling edges (for diagnostics)
    dangling = sum(
        1 for e in llm_edges
        if e["source"] not in seen_ids or e["target"] not in seen_ids
    )

    type_counts = {}
    for n in nodes:
        type_counts[n["type"]] = type_counts.get(n["type"], 0) + 1
    rel_counts = {}
    for e in edges:
        rel_counts[e["type"]] = rel_counts.get(e["type"], 0) + 1

    print(f"      Nodes: {len(nodes)} ({', '.join(f'{t}:{c}' for t, c in sorted(type_counts.items()))})")
    print(f"      Edges: {len(edges)} ({', '.join(f'{t}:{c}' for t, c in sorted(rel_counts.items()))})")
    if dangling:
        print(f"      ({dangling} dangling edges dropped)")

    return {
        "source": {
            "plan": "Miami Forever Climate Ready 2020",
            "pdf": "miami-forever-climate-ready-2020-strategy.pdf",
            "supabase_solution_id": solution["id"],
            "supabase_loc_id": city["loc_id"],
            "ontology_version": ontology.get("version", "0.1"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "solution_summary": {
            "category": c.get("category", ""),
            "subcategory": c.get("subcategory", ""),
            "quote": c.get("quote", ""),
        },
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "node_counts": type_counts,
            "edge_counts": rel_counts,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        },
    }


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:60]


def main():
    parser = argparse.ArgumentParser(description="Generate per-solution Miami ontology samples")
    parser.add_argument(
        "--pdf",
        type=Path,
        default=Path.home() / "Downloads" / "miami-forever-climate-ready-2020-strategy.pdf",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "extractions" / "miami",
    )
    parser.add_argument(
        "--ontology",
        type=Path,
        default=Path(__file__).parent.parent / "ontology" / "ontology-v0.1.json",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(__file__).resolve().parents[3] / ".env",
    )
    args = parser.parse_args()

    if not args.pdf.exists():
        print(f"ERROR: PDF not found at {args.pdf}")
        sys.exit(1)
    if not args.ontology.exists():
        print(f"ERROR: Ontology not found at {args.ontology}")
        sys.exit(1)

    env = load_env(args.env_file)
    with open(args.ontology) as f:
        ontology = json.load(f)

    # Query Supabase
    url = env["PUBLIC_SUPABASE_URL"]
    key = env["SUPABASE_SERVICE_ROLE_KEY"]

    print("Querying Supabase...")
    cities = query_supabase(url, key, "cities?name=eq.Miami&select=id,name,loc_id,latitude,longitude,population")
    if not cities:
        print("ERROR: Miami not found")
        sys.exit(1)
    city = cities[0]
    print(f"  City: {city['name']} (loc_id={city['loc_id']})")

    solutions = query_supabase(url, key, "solutions?loc_id=eq.76&select=id,publication,crawler,taxonomy")
    published = [
        s for s in solutions
        if s.get("publication", {}).get("status") == "published"
        or s.get("publication", {}).get("visibility") == "public"
    ]
    print(f"  Published solutions: {len(published)}")

    # Extract PDF
    pdf_text = extract_pdf_text(args.pdf)
    print(f"  PDF: {len(pdf_text)} chars from {len(PdfReader(str(args.pdf)).pages)} pages")

    # Process each solution
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_files = []

    print(f"\nExtracting {len(published)} solutions...")
    for i, sol in enumerate(published):
        result = extract_for_solution(env, ontology, pdf_text, sol, city, i)

        slug = slugify(sol["crawler"].get("category", "unknown"))
        filename = f"miami-{i + 1:02d}-{slug}.json"
        outpath = args.output_dir / filename

        with open(outpath, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            f.write("\n")

        output_files.append(filename)
        print(f"      Written: {outpath}")

    # Write index file
    index = {
        "plan": "Miami Forever Climate Ready 2020",
        "city": "Miami",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": output_files,
    }
    with open(args.output_dir / "index.json", "w") as f:
        json.dump(index, f, indent=2)
        f.write("\n")

    print(f"\nDone. {len(output_files)} files in {args.output_dir}/")


if __name__ == "__main__":
    main()
