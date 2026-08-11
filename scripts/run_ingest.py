"""
scripts/run_ingest.py
Ingest all documents in the data/ directory and print a summary report.
Run from the project root: python scripts/run_ingest.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path regardless of working directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.pipeline import ingest_documents

DATA_DIR = PROJECT_ROOT / "data"
SUPPORTED = {".pdf", ".html", ".htm", ".md"}


def main() -> None:
    doc_files = sorted(
        f for f in DATA_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED
    )

    print("=" * 60)
    print(f"RAG Ingestion — data/ folder: {len(doc_files)} files")
    print("=" * 60)
    for f in doc_files:
        print(f"  {f.suffix.upper()[1:]:4s}  {f.name}")
    print()

    result = ingest_documents(doc_files)

    print()
    print("=" * 60)
    print("  INGESTION COMPLETE")
    print("=" * 60)
    print(f"  Files processed  : {result.files_processed}")
    print(f"  Chunks added     : {result.chunks_added}")
    print(f"  Chunks skipped   : {result.chunks_skipped}")
    print(f"  FAISS index size : {result.faiss_size}  vectors")
    print(f"  SQLite row count : {result.sqlite_count}  rows")
    total = result.chunks_added + result.chunks_skipped
    if total > 0:
        pct = 100 * result.chunks_skipped // total
        print(f"  Skip rate        : {pct}%  ({result.chunks_skipped}/{total})")
    print("=" * 60)

    # Quick consistency check
    if result.faiss_size != result.sqlite_count:
        print()
        print(f"  [WARN] FAISS size ({result.faiss_size}) != "
              f"SQLite count ({result.sqlite_count}) — stores are out of sync!")
    else:
        print(f"  [OK]  FAISS and SQLite agree: {result.faiss_size} vectors/rows")
    print("=" * 60)


if __name__ == "__main__":
    main()
