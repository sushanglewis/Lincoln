#!/usr/bin/env python3
"""Lincoln recall precheck.

Given a task description, scores knowledge base documents by keyword overlap
(and optionally by embedding similarity) and returns the top-K matches.
Designed to be called from on-session-start.sh before injecting context.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

DEFAULT_KNOWLEDGE_DIR = "knowledge"
DEFAULT_TOP_K = 5


def _tokenize(text: str) -> set[str]:
    """Extract lowercase alphanumeric tokens."""
    return set(re.findall(r"[a-zA-Z0-9一-鿿]+", text.lower()))


def _load_documents(knowledge_dir: Path) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    if not knowledge_dir.exists():
        return docs
    for path in sorted(knowledge_dir.rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
            docs.append(
                {
                    "path": str(path.relative_to(knowledge_dir)),
                    "tokens": _tokenize(text),
                    "title": path.stem,
                    "_text": text[:2000],
                }
            )
        except Exception:
            continue
    return docs


def _score_by_keywords(query_tokens: set[str], doc: dict[str, Any]) -> float:
    if not query_tokens:
        return 0.0
    doc_tokens = doc["tokens"]
    if not doc_tokens:
        return 0.0
    overlap = len(query_tokens & doc_tokens)
    return overlap / max(len(query_tokens), len(doc_tokens))


def _try_embedding_score(query: str, docs: list[dict[str, Any]]) -> list[float] | None:
    """Attempt embedding-based scoring if sentence-transformers is installed."""
    try:
        from sentence_transformers import SentenceTransformer, util  # type: ignore

        model = SentenceTransformer("all-MiniLM-L6-v2")
        query_embedding = model.encode(query, convert_to_tensor=True)
        doc_texts = [doc.get("_text", "") for doc in docs]
        doc_embeddings = model.encode(doc_texts, convert_to_tensor=True)
        scores = util.cos_sim(query_embedding, doc_embeddings)[0].tolist()
        return list(scores)
    except Exception:
        return None


def recall(
    query: str,
    knowledge_dir: Path | None = None,
    top_k: int = DEFAULT_TOP_K,
    use_embedding: bool = True,
) -> dict[str, Any]:
    """Return top-K knowledge documents for a query."""
    knowledge_dir = knowledge_dir or Path(DEFAULT_KNOWLEDGE_DIR)
    docs = _load_documents(knowledge_dir)
    query_tokens = _tokenize(query)

    if use_embedding:
        embedding_scores = _try_embedding_score(query, docs)
    else:
        embedding_scores = None

    results = []
    for idx, doc in enumerate(docs):
        keyword_score = _score_by_keywords(query_tokens, doc)
        if embedding_scores is not None:
            score = 0.5 * keyword_score + 0.5 * embedding_scores[idx]
        else:
            score = keyword_score
        results.append(
            {
                "path": doc["path"],
                "title": doc["title"],
                "score": round(score, 4),
                "method": "embedding+keywords" if embedding_scores else "keywords",
            }
        )

    results.sort(key=lambda r: r["score"], reverse=True)
    return {
        "query": query,
        "top_k": top_k,
        "docs": [r for r in results[:top_k] if r["score"] > 0],
        "method": "embedding+keywords" if embedding_scores else "keywords",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recall relevant knowledge documents")
    parser.add_argument("--query", required=True)
    parser.add_argument("--knowledge-dir", type=Path, default=None)
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--no-embedding", action="store_true", default=False)
    args = parser.parse_args(argv)

    result = recall(
        query=args.query,
        knowledge_dir=args.knowledge_dir,
        top_k=args.top_k,
        use_embedding=not args.no_embedding,
    )

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"# 相关知识（{result['method']}）\n")
        if result["docs"]:
            for doc in result["docs"]:
                print(f"- [{doc['title']}]({doc['path']}) — score {doc['score']}")
        else:
            print("_未找到相关知识。_")
    return 0


if __name__ == "__main__":
    sys.exit(main())