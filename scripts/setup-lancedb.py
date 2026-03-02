"""
Setup script for LanceDB collections.
Run this once to initialize the 4 domain collections + cross-domain index.

Usage:
    pip install lancedb pyarrow
    python scripts/setup-lancedb.py --db-path /data/lancedb
"""

import argparse
import lancedb
import pyarrow as pa

DOMAIN_SCHEMA = pa.schema([
    pa.field("id", pa.string()),
    pa.field("doi", pa.string()),
    pa.field("title", pa.string()),
    pa.field("authors", pa.string()),
    pa.field("year", pa.int32()),
    pa.field("journal", pa.string()),
    pa.field("citation_count", pa.int32()),
    pa.field("study_type", pa.string()),
    pa.field("chunk_type", pa.string()),
    pa.field("chunk_text", pa.string()),
    pa.field("vector", pa.list_(pa.float32(), 1024)),
    pa.field("domain", pa.string()),
    pa.field("keywords", pa.list_(pa.string())),
    pa.field("methodology_tags", pa.list_(pa.string())),
    pa.field("open_access", pa.bool_()),
    pa.field("source", pa.string()),
    pa.field("collected_date", pa.string()),
    pa.field("quality_score", pa.float32()),
])

CROSS_DOMAIN_SCHEMA = pa.schema([
    pa.field("concept", pa.string()),
    pa.field("domains_present", pa.list_(pa.string())),
    pa.field("description", pa.string()),
    pa.field("vector", pa.list_(pa.float32(), 1024)),
    pa.field("related_concepts", pa.list_(pa.string())),
    pa.field("ols_relevance", pa.string()),
])

COLLECTIONS = [
    "psychology_papers",
    "sociology_papers",
    "environmentalism_papers",
    "neuroscience_papers",
]


def setup(db_path: str):
    db = lancedb.connect(db_path)
    existing = db.table_names()

    for collection in COLLECTIONS:
        if collection in existing:
            print(f"  Collection '{collection}' already exists, skipping")
        else:
            # Create empty table with schema
            empty_table = pa.table(
                {field.name: pa.array([], type=field.type) for field in DOMAIN_SCHEMA},
                schema=DOMAIN_SCHEMA,
            )
            db.create_table(collection, empty_table)
            print(f"  Created collection: {collection}")

    if "cross_domain_index" in existing:
        print("  Collection 'cross_domain_index' already exists, skipping")
    else:
        empty_table = pa.table(
            {field.name: pa.array([], type=field.type) for field in CROSS_DOMAIN_SCHEMA},
            schema=CROSS_DOMAIN_SCHEMA,
        )
        db.create_table("cross_domain_index", empty_table)
        print("  Created collection: cross_domain_index")

    print(f"\nAll collections ready. Tables: {db.table_names()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize LanceDB collections")
    parser.add_argument("--db-path", default="/data/lancedb", help="Path to LanceDB directory")
    args = parser.parse_args()

    print(f"Initializing LanceDB at {args.db_path}")
    setup(args.db_path)
    print("Done.")
