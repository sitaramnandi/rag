"""
Debug helper: for a given question, show where the chunk you expect the
answer to come from actually ranks in the retriever's results.

Usage:
    cd backend
    python scripts/debug_retrieval.py "What is the Compton effect?" --expect "photon" --k 50
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.vectorstore import vector_store  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument(
        "--expect",
        required=True,
        help="substring that should appear in the chunk containing the correct answer",
    )
    parser.add_argument("--k", type=int, default=50, help="how many candidates to pull back")
    args = parser.parse_args()

    results = vector_store.similarity_search_with_score(args.question, k=args.k)

    print(f"Question: {args.question!r}")
    print(f"Retrieved {len(results)} chunks (k={args.k})\n")

    found_rank = None
    for rank, (doc, score) in enumerate(results, start=1):
        matched = args.expect.lower() in doc.page_content.lower()
        if matched and found_rank is None:
            found_rank = rank
        marker = "  <-- EXPECTED CHUNK" if matched else ""
        snippet = doc.page_content[:120].replace("\n", " ")
        print(
            f"#{rank:>2}  score={score:.4f}  "
            f"doc={doc.metadata.get('filename')}  "
            f"chunk={doc.metadata.get('chunk_index')}{marker}"
        )
        print(f"     {snippet}...")

    print()
    if found_rank is None:
        print(f"Chunk containing {args.expect!r} was NOT found in the top {args.k} results at all.")
        print("-> Likely a genuine embedding mismatch (query and chunk are semantically far apart),")
        print("   not just a ranking issue. Try query rewriting or hybrid (keyword + vector) search.")
    elif found_rank <= 5:
        print(f"Chunk containing {args.expect!r} ranked #{found_rank} — within a typical top_k=5.")
        print("-> If your app still isn't using it, check the actual top_k value it's calling with.")
    else:
        print(f"Chunk containing {args.expect!r} ranked #{found_rank} — below a typical top_k=5.")
        print("-> Ranking problem: the chunk is somewhat relevant but not relevant enough by raw")
        print("   embedding similarity alone. Re-ranking the top ~20-30 candidates would likely fix this.")


if __name__ == "__main__":
    main()
