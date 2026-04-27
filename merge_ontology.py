#!/usr/bin/env python3
"""
Merge types.json and relationships.json into a complete ontology file.

Usage:
    python merge_ontology.py
"""

import json
from pathlib import Path
from datetime import datetime, timezone

def main():
    ontology_dir = Path(__file__).parent / "ontology"

    # Read types.json
    with open(ontology_dir / "types.json") as f:
        types_data = json.load(f)

    # Read relationships.json
    with open(ontology_dir / "relationships.json") as f:
        rels_data = json.load(f)

    # Merge into complete ontology
    complete_ontology = {
        "version": "0.2",
        "updated": datetime.now(timezone.utc).isoformat(),
        "domains": ["adaptation-planning", "adaptation-solutions"],
        "types": types_data["types"],
        "relationships": rels_data["relationships"],
        "vocabularies": [],
        "metadata": {
            "types_source": types_data.get("source", "extraction-schema-v1.json"),
            "relationships_source": rels_data.get("source", "extraction-schema-v1.json"),
            "types_generated_at": types_data.get("generated_at"),
            "relationships_generated_at": rels_data.get("generated_at"),
            "notes": [
                "Phase 2a complete - Absorbed student ontology governance vocabulary",
                "New: Vulnerability node, REDUCES/IMPROVES relationships, spatial targeting, actor coordination"
            ]
        }
    }

    # Write to draft-v0.json
    output_path = ontology_dir / "draft-v0.json"
    with open(output_path, "w") as f:
        json.dump(complete_ontology, f, indent=2)

    print(f"✅ Merged ontology written to {output_path}")
    print(f"   - {len(complete_ontology['types'])} types")
    print(f"   - {len(complete_ontology['relationships'])} relationships")
    print(f"   - Version: {complete_ontology['version']}")

if __name__ == "__main__":
    main()
