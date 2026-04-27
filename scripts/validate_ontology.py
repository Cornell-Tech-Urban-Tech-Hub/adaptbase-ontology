#!/usr/bin/env python3
"""
Validate ontology v0.3 by LLM-assisted population from real documents.

Usage:
    uv run python scripts/validate_ontology.py --num-docs 5 --output validation/

This script:
1. Samples diverse documents from Supabase
2. Uses LLM to populate ontology from each document
3. Analyzes coverage, gaps, and Phase 2 additions
4. Generates validation reports
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import argparse

# Will need these dependencies
try:
    from anthropic import Anthropic
    from supabase import create_client, Client
except ImportError:
    print("Missing dependencies. Install with:")
    print("  uv add anthropic supabase")
    exit(1)


def load_ontology(ontology_path: Path) -> Dict[str, Any]:
    """Load the complete ontology from draft-v0.json"""
    with open(ontology_path) as f:
        return json.load(f)


def sample_documents(supabase: Client, num_docs: int = 5) -> List[Dict[str, Any]]:
    """
    Sample diverse documents from Supabase.

    Strategy: Get mix of document types, sources, and geographies
    """
    # Try to get diverse sample
    query = """
    SELECT
        id, title, document_type, source_organization,
        city, country, processing_status, pdf_url,
        -- Get text if available (adjust column name as needed)
        COALESCE(full_text, extracted_text, '') as document_text
    FROM documents
    WHERE processing_status = 'complete'
      AND title IS NOT NULL
      AND pdf_url IS NOT NULL
    ORDER BY document_type, source_organization
    LIMIT {num_docs};
    """.format(num_docs=num_docs)

    result = supabase.rpc('execute_sql', {'query': query}).execute()

    if not result.data:
        # Fallback: get any complete documents
        result = supabase.table('documents')\
            .select('id, title, document_type, source_organization, city, country, pdf_url')\
            .eq('processing_status', 'complete')\
            .not_.is_('title', 'null')\
            .limit(num_docs)\
            .execute()

    return result.data


def get_document_text(doc: Dict[str, Any]) -> str:
    """
    Get document text for LLM analysis.

    Priority:
    1. Pre-extracted text from Supabase
    2. Extract from PDF (if extraction pipeline available)
    3. Use first N pages summary
    """
    # Check if text already in doc
    if doc.get('document_text'):
        return doc['document_text']

    # TODO: Implement PDF extraction if needed
    # For now, return placeholder
    return f"[Document text not available for {doc['title']}. Would need PDF extraction.]"


def create_validation_prompt(ontology: Dict[str, Any], document_text: str, doc_metadata: Dict[str, Any]) -> str:
    """Create the LLM prompt for ontology validation"""

    # Extract key ontology info
    node_types = {t['id']: t['definition'] for t in ontology['types']}
    relationships = {r['id']: r['definition'] for r in ontology['relationships']}

    # Highlight Phase 2 additions
    phase2_nodes = ['Vulnerability', 'TimePoint', 'Infrastructure', 'ExposureUnit']
    phase2_rels = ['REDUCES', 'IMPROVES', 'COORDINATES_WITH', 'REPORTS_TO',
                   'PARTICIPATES_IN', 'MONITORS', 'MANAGES', 'STARTED_AT',
                   'ISSUED_AT', 'RECORDED_AT', 'EXPOSES', 'SERVES', 'EXPERIENCES_VULN']

    prompt = f"""Analyze this climate adaptation document and populate the ontology to assess its quality and coverage.

DOCUMENT METADATA:
Title: {doc_metadata.get('title', 'Unknown')}
Type: {doc_metadata.get('document_type', 'Unknown')}
Source: {doc_metadata.get('source_organization', 'Unknown')}

DOCUMENT TEXT:
{document_text[:15000]}  # Limit to ~15k chars to fit in context

ONTOLOGY TO VALIDATE:
We have {len(node_types)} node types and {len(relationships)} relationship types.

NODE TYPES:
{json.dumps(node_types, indent=2)}

RELATIONSHIP TYPES:
{json.dumps(relationships, indent=2)}

PHASE 2 ADDITIONS (FOCUS ON THESE):
Nodes: {', '.join(phase2_nodes)}
Relationships: {', '.join(phase2_rels)}

TASK:
Populate the ontology from this document to validate its design quality.

For EACH node type and relationship type:
1. Identify ALL instances in the document
2. Include direct text quotes as evidence
3. Mark confidence: high (explicitly stated), medium (clearly implied), low (speculative)
4. Note if the concept appears but doesn't fit well

OUTPUT STRUCTURED JSON:
{{
  "document_summary": "1-2 sentence summary of document content",
  "nodes": {{
    "Solution": [
      {{"name": "Green roof installation", "description": "...", "quote": "direct text quote", "confidence": "high"}}
    ],
    "Vulnerability": [...],
    ... (for ALL 19 node types, even if empty array)
  }},
  "relationships": {{
    "REDUCES": [
      {{"source": "Green roofs", "target": "Urban heat vulnerability", "quote": "...", "confidence": "medium"}}
    ],
    "IMPROVES": [...],
    ... (for ALL 30 relationship types, even if empty array)
  }},
  "coverage_assessment": {{
    "expressible_percentage": 85,  # rough estimate: how much of doc fits ontology
    "most_common_patterns": ["Solution-MITIGATES-Hazard appeared 12 times", ...],
    "absent_expected": ["Expected TimePoint for planning cycles but didn't find"]
  }},
  "phase2_validation": {{
    "vulnerability_found": true/false,
    "vulnerability_notes": "how well did Vulnerability node work?",
    "infrastructure_split_clear": true/false,
    "infrastructure_notes": "was Infrastructure vs UrbanSystem distinction clear?",
    "exposure_chain_complete": true/false,
    "exposure_notes": "did Hazard→ExposureUnit→Vulnerability chain work?",
    "temporal_relationships_found": true/false,
    "temporal_notes": "were TimePoints and temporal rels useful?",
    "actor_coordination_found": true/false,
    "actor_notes": "were actor-to-actor relationships present?"
  }},
  "gaps": {{
    "critical_missing": ["concept that can't be expressed at all"],
    "awkward_fits": ["concept that technically fits but feels forced"],
    "unclear_distinctions": ["couldn't tell if OPERATES_ON or IMPROVES"],
    "missing_properties": ["needed property X on node Y"],
    "vocabulary_issues": ["needed value X in vocabulary Y"]
  }},
  "positive_findings": {{
    "worked_well": ["relationship X captured concept perfectly"],
    "validated_phase2": ["Phase 2 addition Y proved necessary"]
  }}
}}

Be CRITICAL - we want to find limitations and gaps in the ontology design!
Focus especially on Phase 2 additions since they're newest.
"""
    return prompt


def call_llm(prompt: str, model: str = "claude-opus-4") -> Dict[str, Any]:
    """Call LLM to analyze document and populate ontology"""
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    message = client.messages.create(
        model=model,
        max_tokens=16000,
        temperature=0,  # Deterministic for analysis
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    # Parse JSON response
    response_text = message.content[0].text
    # Extract JSON from response (may be wrapped in ```json blocks)
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()

    return json.loads(response_text)


def analyze_results(results: List[Dict[str, Any]], output_dir: Path) -> Dict[str, Any]:
    """
    Analyze all LLM outputs to generate summary statistics.

    Returns:
        - Frequency matrix (how often each node/rel appeared)
        - Confidence distribution
        - Aggregated gaps
        - Phase 2 validation summary
    """
    analysis = {
        "node_frequency": {},
        "relationship_frequency": {},
        "confidence_distribution": {"high": 0, "medium": 0, "low": 0},
        "aggregated_gaps": {
            "critical_missing": {},  # count occurrences
            "awkward_fits": {},
            "unclear_distinctions": {}
        },
        "phase2_summary": {
            "vulnerability_docs": 0,
            "infrastructure_split_clear_docs": 0,
            "exposure_chain_complete_docs": 0,
            "temporal_found_docs": 0,
            "actor_coordination_docs": 0
        }
    }

    for result in results:
        # Count nodes
        for node_type, instances in result.get('nodes', {}).items():
            if node_type not in analysis['node_frequency']:
                analysis['node_frequency'][node_type] = {"docs": 0, "total_instances": 0}
            if instances:  # Non-empty
                analysis['node_frequency'][node_type]['docs'] += 1
                analysis['node_frequency'][node_type]['total_instances'] += len(instances)

                # Count confidence
                for instance in instances:
                    conf = instance.get('confidence', 'medium')
                    analysis['confidence_distribution'][conf] = analysis['confidence_distribution'].get(conf, 0) + 1

        # Count relationships
        for rel_type, instances in result.get('relationships', {}).items():
            if rel_type not in analysis['relationship_frequency']:
                analysis['relationship_frequency'][rel_type] = {"docs": 0, "total_instances": 0}
            if instances:
                analysis['relationship_frequency'][rel_type]['docs'] += 1
                analysis['relationship_frequency'][rel_type]['total_instances'] += len(instances)

                # Count confidence
                for instance in instances:
                    conf = instance.get('confidence', 'medium')
                    analysis['confidence_distribution'][conf] = analysis['confidence_distribution'].get(conf, 0) + 1

        # Aggregate gaps
        for gap_type in ['critical_missing', 'awkward_fits', 'unclear_distinctions']:
            for gap in result.get('gaps', {}).get(gap_type, []):
                analysis['aggregated_gaps'][gap_type][gap] = analysis['aggregated_gaps'][gap_type].get(gap, 0) + 1

        # Phase 2 summary
        phase2 = result.get('phase2_validation', {})
        if phase2.get('vulnerability_found'):
            analysis['phase2_summary']['vulnerability_docs'] += 1
        if phase2.get('infrastructure_split_clear'):
            analysis['phase2_summary']['infrastructure_split_clear_docs'] += 1
        if phase2.get('exposure_chain_complete'):
            analysis['phase2_summary']['exposure_chain_complete_docs'] += 1
        if phase2.get('temporal_relationships_found'):
            analysis['phase2_summary']['temporal_found_docs'] += 1
        if phase2.get('actor_coordination_found'):
            analysis['phase2_summary']['actor_coordination_docs'] += 1

    return analysis


def generate_reports(results: List[Dict[str, Any]], analysis: Dict[str, Any],
                     docs_metadata: List[Dict[str, Any]], output_dir: Path):
    """Generate markdown reports from validation results"""

    # Sample selection report
    with open(output_dir / "sample-selection.md", "w") as f:
        f.write("# Sample Selection\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}\n\n")
        f.write(f"**Documents sampled:** {len(docs_metadata)}\n\n")
        f.write("## Selected Documents\n\n")
        for i, doc in enumerate(docs_metadata, 1):
            f.write(f"{i}. **{doc['title']}**\n")
            f.write(f"   - Type: {doc.get('document_type', 'N/A')}\n")
            f.write(f"   - Source: {doc.get('source_organization', 'N/A')}\n")
            f.write(f"   - City/Country: {doc.get('city', 'N/A')}, {doc.get('country', 'N/A')}\n")
            f.write(f"   - URL: {doc.get('pdf_url', 'N/A')}\n\n")

    # Per-document reports
    for i, (result, doc) in enumerate(zip(results, docs_metadata), 1):
        title_slug = doc['title'][:50].lower().replace(' ', '-').replace('/', '-')
        with open(output_dir / f"doc-{i}-{title_slug}.md", "w") as f:
            f.write(f"# Document Analysis: {doc['title']}\n\n")
            f.write(f"**Type:** {doc.get('document_type')}\n")
            f.write(f"**Source:** {doc.get('source_organization')}\n\n")
            f.write(f"## Summary\n{result.get('document_summary', 'N/A')}\n\n")

            # Node coverage
            f.write("## Node Coverage\n\n")
            for node_type, instances in result.get('nodes', {}).items():
                f.write(f"- **{node_type}:** {len(instances)} instances\n")
                if instances:
                    for inst in instances[:2]:  # Show first 2
                        f.write(f"  - {inst.get('name', inst.get('description', 'N/A'))} ({inst.get('confidence')})\n")

            # Relationship coverage
            f.write("\n## Relationship Coverage\n\n")
            for rel_type, instances in result.get('relationships', {}).items():
                if instances:
                    f.write(f"- **{rel_type}:** {len(instances)} instances\n")

            # Gaps
            f.write("\n## Gaps\n\n")
            f.write(json.dumps(result.get('gaps', {}), indent=2))

            # Phase 2 validation
            f.write("\n\n## Phase 2 Validation\n\n")
            f.write(json.dumps(result.get('phase2_validation', {}), indent=2))

    # Synthesis report
    with open(output_dir / "synthesis.md", "w") as f:
        f.write("# Cross-Document Synthesis\n\n")
        f.write(f"**Documents analyzed:** {len(results)}\n\n")

        f.write("## Node Frequency\n\n")
        f.write("| Node Type | Docs | Total Instances |\n")
        f.write("|-----------|------|----------------|\n")
        for node, stats in sorted(analysis['node_frequency'].items(),
                                  key=lambda x: x[1]['total_instances'], reverse=True):
            f.write(f"| {node} | {stats['docs']}/{len(results)} | {stats['total_instances']} |\n")

        f.write("\n## Relationship Frequency\n\n")
        f.write("| Relationship | Docs | Total Instances |\n")
        f.write("|--------------|------|----------------|\n")
        for rel, stats in sorted(analysis['relationship_frequency'].items(),
                                key=lambda x: x[1]['total_instances'], reverse=True):
            f.write(f"| {rel} | {stats['docs']}/{len(results)} | {stats['total_instances']} |\n")

        f.write("\n## Phase 2 Summary\n\n")
        for metric, count in analysis['phase2_summary'].items():
            f.write(f"- {metric}: {count}/{len(results)} documents\n")

        f.write("\n## Aggregated Gaps\n\n")
        f.write(json.dumps(analysis['aggregated_gaps'], indent=2))

    # Recommendations report
    with open(output_dir / "recommendations.md", "w") as f:
        f.write("# Validation Recommendations\n\n")
        f.write("Based on LLM analysis of real documents.\n\n")

        # TODO: Generate smart recommendations based on analysis
        f.write("## Critical Gaps (Can't Express)\n\n")
        for gap, count in sorted(analysis['aggregated_gaps']['critical_missing'].items(),
                                key=lambda x: x[1], reverse=True):
            if count >= 2:  # Appeared in 2+ docs
                f.write(f"- **{gap}** (appeared in {count} docs)\n")

        f.write("\n## Awkward Fits (Forced)\n\n")
        for gap, count in sorted(analysis['aggregated_gaps']['awkward_fits'].items(),
                                key=lambda x: x[1], reverse=True):
            if count >= 2:
                f.write(f"- **{gap}** (appeared in {count} docs)\n")

        f.write("\n## Phase 2 Assessment\n\n")
        # Smart assessment based on frequency
        phase2_nodes = ['Vulnerability', 'TimePoint', 'Infrastructure', 'ExposureUnit']
        for node in phase2_nodes:
            stats = analysis['node_frequency'].get(node, {})
            f.write(f"- **{node}:** Found in {stats.get('docs', 0)}/{len(results)} docs, {stats.get('total_instances', 0)} instances\n")


def main():
    parser = argparse.ArgumentParser(description='Validate ontology against real documents')
    parser.add_argument('--num-docs', type=int, default=5, help='Number of documents to sample')
    parser.add_argument('--output', type=Path, default=Path('validation/'), help='Output directory')
    parser.add_argument('--ontology', type=Path, default=Path('ontology/draft-v0.json'), help='Ontology file')
    args = parser.parse_args()

    # Setup
    output_dir = Path(__file__).parent.parent / args.output
    output_dir.mkdir(exist_ok=True, parents=True)

    ontology_path = Path(__file__).parent.parent / args.ontology
    ontology = load_ontology(ontology_path)

    # Supabase client
    supabase_url = os.environ.get("PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")
    supabase = create_client(supabase_url, supabase_key)

    print(f"Sampling {args.num_docs} documents from Supabase...")
    documents = sample_documents(supabase, args.num_docs)

    print(f"Found {len(documents)} documents")

    # Process each document
    results = []
    for i, doc in enumerate(documents, 1):
        print(f"\nProcessing document {i}/{len(documents)}: {doc['title'][:60]}...")

        # Get text
        doc_text = get_document_text(doc)

        # Create prompt
        prompt = create_validation_prompt(ontology, doc_text, doc)

        # Call LLM
        print(f"  Calling LLM...")
        result = call_llm(prompt)

        # Save raw output
        with open(output_dir / f"llm-output-doc-{i}.json", "w") as f:
            json.dump(result, f, indent=2)

        results.append(result)
        print(f"  ✓ Complete")

    # Analyze results
    print("\nAnalyzing results...")
    analysis = analyze_results(results, output_dir)

    # Save analysis
    with open(output_dir / "analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)

    # Generate reports
    print("Generating reports...")
    generate_reports(results, analysis, documents, output_dir)

    print(f"\n✓ Validation complete! Reports in {output_dir}")
    print(f"  - sample-selection.md")
    print(f"  - doc-1-*.md ... doc-{len(documents)}-*.md")
    print(f"  - synthesis.md")
    print(f"  - recommendations.md")


if __name__ == "__main__":
    main()
