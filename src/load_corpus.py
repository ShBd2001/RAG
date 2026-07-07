"""
Lit le CSV du corpus et le transforme en liste de dicts {"id", "text", "source"},
la forme attendue par VectorDB._create_collection.
"""

import csv


def load_corpus(csv_path: str) -> list[dict]:
    chunks = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            chunks.append(
                {
                    "id": row["id"],
                    "text": row["text"],
                    "source": row["source"],
                }
            )
    return chunks
