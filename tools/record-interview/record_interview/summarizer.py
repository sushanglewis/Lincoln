from __future__ import annotations

import abc
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

from record_interview.config import Config


CLAUDE_CLI_TIMEOUT_SECONDS = 300


class Summarizer(abc.ABC):
    @abc.abstractmethod
    def summarize(self, context: str, instruction: str) -> str:
        raise NotImplementedError


class ClaudeSummarizer(Summarizer):
    def __init__(self, model: str | None = None) -> None:
        if shutil.which("claude") is None:
            raise RuntimeError("claude CLI not found in PATH")
        self._model = model

    def summarize(self, context: str, instruction: str) -> str:
        prompt = f"{instruction}\n\n{context}"
        cmd = ["claude", "--print"]
        if self._model:
            cmd.extend(["--model", self._model])
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=CLAUDE_CLI_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            raise RuntimeError("claude CLI failed")
        return result.stdout


class FileBasedClaudeSummarizer(ClaudeSummarizer):
    """Claude summarizer that passes file paths via --file."""

    def summarize(self, context: str, instruction: str) -> str:
        fd, name = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        os.chmod(name, stat.S_IRUSR | stat.S_IWUSR)
        context_path = Path(name)
        try:
            context_path.write_text(context, encoding="utf-8")
            cmd = ["claude", "--print", "--file", str(context_path)]
            if self._model:
                cmd.extend(["--model", self._model])
            result = subprocess.run(
                cmd,
                input=instruction,
                capture_output=True,
                text=True,
                timeout=CLAUDE_CLI_TIMEOUT_SECONDS,
            )
            if result.returncode != 0:
                raise RuntimeError("claude CLI failed")
            return result.stdout
        finally:
            context_path.unlink(missing_ok=True)


class OpenAISummarizer(Summarizer):
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini") -> None:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError("openai package is not installed") from e
        self._client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self._model = model

    def summarize(self, context: str, instruction: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": context},
            ],
            timeout=CLAUDE_CLI_TIMEOUT_SECONDS,
        )
        return response.choices[0].message.content or ""


class AnthropicSummarizer(Summarizer):
    def __init__(self, api_key: str | None = None, model: str = "claude-3-5-sonnet-latest") -> None:
        try:
            from anthropic import Anthropic
        except ImportError as e:
            raise ImportError("anthropic package is not installed") from e
        self._client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self._model = model

    def summarize(self, context: str, instruction: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=instruction,
            messages=[{"role": "user", "content": context}],
            timeout=CLAUDE_CLI_TIMEOUT_SECONDS,
        )
        return response.content[0].text if response.content else ""


def build_summarizer(config: Config) -> Summarizer:
    if config.summarization is None:
        raise ValueError("summarization configuration is missing")
    provider = config.summarization.provider
    if provider == "claude":
        return ClaudeSummarizer(model=config.summarization.model)
    if provider == "openai":
        return OpenAISummarizer(
            api_key=config.summarization.openai_api_key,
            model=config.summarization.model or "gpt-4o-mini",
        )
    if provider == "anthropic":
        return AnthropicSummarizer(
            api_key=config.summarization.anthropic_api_key,
            model=config.summarization.model or "claude-3-5-sonnet-latest",
        )
    raise ValueError(f"unknown summarization provider: {provider}")
