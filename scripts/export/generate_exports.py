# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rdflib>=7.6.0",
# ]
# ///
"""Generate OWL/Turtle/SKOS exports from the JSON-LD ontology source.

Run with: uv run scripts/export/generate_exports.py
Reads ontology/ontology-v1.0.jsonld + ontology/vocabularies/*.jsonld,
writes exports/ontology.ttl, exports/ontology.owl (RDF/XML), and
exports/vocabularies.ttl (combined SKOS).

Note on RDF-star: this file is the ontology *schema* (TBox) -- it describes
classes and properties, not asserted instance edges, so there is nothing
here to reify. `claim_ids` already resolves to `prov:wasDerivedFrom` via
context.jsonld; RDF-star quoted triples become relevant only when the
*instance* knowledge graph (adaptbase-core, Supabase-backed, out of this
repo's scope) is exported with its actual per-edge claim provenance.
"""
import json
from pathlib import Path

from rdflib import Graph

REPO = Path(__file__).resolve().parents[2]
ONTOLOGY_SRC = REPO / "ontology" / "ontology-v1.0.jsonld"
VOCAB_DIR = REPO / "ontology" / "vocabularies"
EXPORTS_DIR = REPO / "exports"


def load_jsonld(path: Path) -> Graph:
    g = Graph()
    # rdflib's json-ld parser resolves a string "@context" as a URL/file path
    # relative to the document's base -- point base at the source file so the
    # "./context.jsonld" / "../context.jsonld" references resolve on disk.
    g.parse(data=path.read_text(), format="json-ld", publicID=path.as_uri())
    return g


def main() -> None:
    EXPORTS_DIR.mkdir(exist_ok=True)

    ontology_graph = load_jsonld(ONTOLOGY_SRC)
    ontology_graph.serialize(destination=EXPORTS_DIR / "ontology.ttl", format="turtle")
    ontology_graph.serialize(destination=EXPORTS_DIR / "ontology.owl", format="xml")
    print(f"ontology.ttl / ontology.owl: {len(ontology_graph)} triples "
          f"from {ONTOLOGY_SRC.relative_to(REPO)}")

    vocab_graph = Graph()
    vocab_files = sorted(VOCAB_DIR.glob("*.jsonld"))
    for vf in vocab_files:
        g = load_jsonld(vf)
        vocab_graph += g
        print(f"  + {vf.relative_to(REPO)}: {len(g)} triples")
    vocab_graph.serialize(destination=EXPORTS_DIR / "vocabularies.ttl", format="turtle")
    print(f"vocabularies.ttl: {len(vocab_graph)} triples combined from {len(vocab_files)} files")


if __name__ == "__main__":
    main()
