from __future__ import annotations

from pathlib import Path


DEFAULT_KNOWLEDGE_DIR = "docs/knowledge"


def list_knowledge_files(workspace_root: Path) -> list[Path]:
    knowledge_dir = workspace_root / DEFAULT_KNOWLEDGE_DIR
    if not knowledge_dir.is_dir():
        return []
    return sorted(p for p in knowledge_dir.rglob("*.md") if p.is_file())


def _score_document(path: Path, keywords: set[str]) -> int:
    text = path.read_text(encoding="utf-8").lower()
    return sum(1 for keyword in keywords if keyword.lower() in text)


def load_relevant_knowledge(
    workspace_root: Path,
    query: str,
    top_k: int = 3,
) -> list[Path]:
    """Return the most relevant knowledge markdown files for a query.

    Relevance is determined by simple keyword overlap.
    """
    files = list_knowledge_files(workspace_root)
    if not files:
        return []
    keywords = set(query.split())
    scored = [(path, _score_document(path, keywords)) for path in files]
    scored.sort(key=lambda item: item[1], reverse=True)
    return [path for path, score in scored[:top_k] if score > 0]


def build_knowledge_context(workspace_root: Path, query: str, top_k: int = 3) -> str:
    files = load_relevant_knowledge(workspace_root, query, top_k)
    if not files:
        return ""
    parts = ["Relevant knowledge from the repository:"]
    for path in files:
        relative = path.relative_to(workspace_root)
        parts.append(f"\n--- {relative} ---\n")
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)
