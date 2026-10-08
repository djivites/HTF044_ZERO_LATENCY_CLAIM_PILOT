import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.services.document_service import process_document
from backend.services.gemma_service import extract_claims, extract_evidence, extract_events
from backend.services.vector_service import store_document_embeddings, store_evidence_embeddings
from backend.services.evidence_service import create_evidence_graph
from backend.services.timeline_service import build_timeline


def run_pipeline(file_path: str = "uploads/sample_document.txt"):
    print("=" * 70)
    print("CLAIM PILOT - BACKEND END-TO-END MANUAL TEST PIPELINE")
    print("=" * 70)

    # 1. Document Processing
    print("\n[STEP 1] Document Processing (document_service.py)")
    print("-" * 50)
    processed_doc = process_document(file_path, filename=Path(file_path).name, document_id="doc_test_001")
    print(f"Status       : {processed_doc.get('status')}")
    print(f"Document ID  : {processed_doc.get('document_id')}")
    print(f"Filename     : {processed_doc.get('filename')}")
    print(f"Extracted Text:\n{processed_doc.get('text')}\n")

    # 2. Gemma AI Extraction
    print("[STEP 2] Gemma Extraction (gemma_service.py)")
    print("-" * 50)
    
    print("-> Extracting Claims...")
    claims = extract_claims(processed_doc)
    print(f"Extracted {len(claims)} claim(s):")
    print(json.dumps(claims, indent=2))

    print("\n-> Extracting Evidence...")
    evidence = extract_evidence(processed_doc)
    print(f"Extracted {len(evidence)} evidence item(s):")
    print(json.dumps(evidence, indent=2))

    print("\n-> Extracting Events...")
    events = extract_events(processed_doc)
    print(f"Extracted {len(events)} event(s):")
    print(json.dumps(events, indent=2))

    # 3. Vector Database Storage
    print("\n[STEP 3] Vector Database Storage (vector_service.py)")
    print("-" * 50)
    
    print("-> Storing Document Embeddings...")
    doc_vec_res = store_document_embeddings(processed_doc)
    print(json.dumps(doc_vec_res, indent=2))

    print("\n-> Storing Evidence Embeddings...")
    ev_vec_res = store_evidence_embeddings(evidence)
    print(json.dumps(ev_vec_res, indent=2))

    # 4. Evidence Graph Creation
    print("\n[STEP 4] Creating Evidence Graph (evidence_service.py)")
    print("-" * 50)
    graph = create_evidence_graph(
        processed_document=processed_doc,
        claims=claims,
        evidence=evidence,
        events=events
    )
    print(f"Graph Nodes Count        : {len(graph['nodes'])}")
    print(f"Graph Relationships Count: {len(graph['relationships'])}")
    print("Graph Structure:")
    print(json.dumps(graph, indent=2))

    # 5. Timeline Building
    print("\n[STEP 5] Building Timeline (timeline_service.py)")
    print("-" * 50)
    timeline = build_timeline(events)
    print(f"Built chronological timeline with {len(timeline)} event(s):")
    print(json.dumps(timeline, indent=2))

    print("\n" + "=" * 70)
    print("MANUAL PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    sample_file = sys.argv[1] if len(sys.argv) > 1 else "uploads/sample_document.txt"
    run_pipeline(sample_file)
