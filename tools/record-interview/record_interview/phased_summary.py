from __future__ import annotations

from pathlib import Path

from record_interview.knowledge_loader import build_knowledge_context
from record_interview.metadata import add_phase_summary, read_metadata, write_metadata
from record_interview.summarizer import Summarizer


PHASE_SUMMARY_PROMPT = """You are a product management assistant.
Summarize the following interview transcript segment into a concise phase summary.
Include key decisions, open questions, and action items.
If relevant knowledge is provided, reference it explicitly with the file path.

{context}
"""

FINAL_SUMMARY_PROMPT = """You are a product management assistant.
Synthesize the following phase summaries into a final meeting minutes document.
Include attendees (if known), key topics, decisions, open questions, and action items.
If relevant knowledge is provided, reference it explicitly with the file path.

{context}
"""


def _phase_summary_path(session_dir: Path, index: int) -> Path:
    return session_dir / f"phase-summary-{index:02d}.md"


def _read_phased_summaries(session_dir: Path) -> list[Path]:
    return sorted(session_dir.glob("phase-summary-*.md"))


def _format_transcript(transcript_segments: list[tuple[float, float, str, str]]) -> str:
    lines = []
    for start, end, speaker, text in transcript_segments:
        lines.append(f"[{start:.1f}s - {end:.1f}s] {speaker}: {text}")
    return "\n".join(lines)


class PhasedSummaryGenerator:
    def __init__(
        self,
        workspace_root: Path,
        session_id: str,
        summarizer: Summarizer,
        phase_interval_seconds: int = 600,
    ) -> None:
        self.workspace_root = workspace_root
        self.session_id = session_id
        self.summarizer = summarizer
        self.phase_interval_seconds = phase_interval_seconds
        self._session_dir = workspace_root / "interviews" / session_id
        self._phase_index = 0

    @property
    def session_dir(self) -> Path:
        return self._session_dir

    def generate_phase_summary(
        self,
        transcript_segments: list[tuple[float, float, str, str]],
        start_time: str,
        end_time: str,
    ) -> Path:
        self._phase_index += 1
        path = _phase_summary_path(self._session_dir, self._phase_index)
        transcript = _format_transcript(transcript_segments)
        knowledge = build_knowledge_context(
            self.workspace_root,
            query=transcript,
            top_k=3,
        )
        context = f"{knowledge}\n\nTranscript:\n{transcript}".strip()
        content = self.summarizer.summarize(
            context=context,
            instruction=PHASE_SUMMARY_PROMPT.format(context=context),
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self._update_metadata(path, start_time, end_time)
        return path

    def _update_metadata(self, path: Path, start_time: str, end_time: str) -> None:
        metadata = read_metadata(self.workspace_root, self.session_id) or {}
        metadata = add_phase_summary(
            metadata,
            index=self._phase_index,
            file=str(path.relative_to(self.workspace_root)),
            start_time=start_time,
            end_time=end_time,
        )
        write_metadata(self.workspace_root, self.session_id, metadata)

    def generate_final_summary(self) -> Path:
        summary_path = self._session_dir / "summary.md"
        phase_paths = _read_phased_summaries(self._session_dir)
        parts = []
        for phase_path in phase_paths:
            parts.append(f"\n--- {phase_path.name} ---\n")
            parts.append(phase_path.read_text(encoding="utf-8"))
        context = "\n".join(parts).strip()
        knowledge = build_knowledge_context(self.workspace_root, query=context, top_k=3)
        if knowledge:
            context = f"{knowledge}\n\n{context}"
        content = self.summarizer.summarize(
            context=context,
            instruction=FINAL_SUMMARY_PROMPT.format(context=context),
        )
        summary_path.write_text(content, encoding="utf-8")
        return summary_path
