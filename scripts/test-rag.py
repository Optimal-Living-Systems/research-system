"""
Quick test script to verify RAG retrieval is working.
Run after data collection and embedding to validate.

Usage:
    pip install lancedb sentence-transformers
    python scripts/test-rag.py --query "intrinsic motivation volunteer retention"
"""

import argparse
import json
import lancedb
from sentence_transformers import SentenceTransformer


def test_query(db_path: str, query: str, domains: list, top_k: int = 5):
    print(f"Loading embedding model...")
    model = SentenceTransformer("BAAI/bge-m3")
    query_vector = model.encode(query)

    db = lancedb.connect(db_path)

    print(f"\nQuery: '{query}'")
    print(f"Searching domains: {domains}")
    print(f"Top-K: {top_k}\n")

    all_results = []

    for domain in domains:
        table_name = f"{domain}_papers"
        if table_name not in db.table_names():
            print(f"  [SKIP] Collection '{table_name}' not found")
            continue

        table = db.open_table(table_name)
        results = table.search(query_vector).limit(top_k).to_list()

        print(f"  [{domain.upper()}] Found {len(results)} results")
        for r in results:
            r["search_domain"] = domain
            all_results.append(r)

    # Sort by distance (lower = more relevant)
    all_results.sort(key=lambda x: x.get("_distance", 999))

    print(f"\n{'='*80}")
    print(f"TOP {top_k} RESULTS ACROSS ALL DOMAINS")
    print(f"{'='*80}\n")

    for i, r in enumerate(all_results[:top_k]):
        print(f"[{i+1}] (dist: {r.get('_distance', 'N/A'):.4f}) [{r['search_domain']}]")
        print(f"    Title: {r.get('title', 'N/A')}")
        print(f"    Year: {r.get('year', 'N/A')} | Journal: {r.get('journal', 'N/A')}")
        print(f"    Chunk: {r.get('chunk_type', 'N/A')}")
        print(f"    Text: {r.get('chunk_text', '')[:200]}...")
        print()

    return all_results[:top_k]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test RAG retrieval")
    parser.add_argument("--db-path", default="/data/lancedb")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--domains", nargs="+",
                       default=["psychology", "sociology", "environmentalism", "neuroscience"])
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    test_query(args.db_path, args.query, args.domains, args.top_k)
