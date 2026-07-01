from unittest.mock import MagicMock

import pytest

from record_interview.config import Config, SummarizationConfig
from record_interview.summarizer import (
    AnthropicSummarizer,
    ClaudeSummarizer,
    FileBasedClaudeSummarizer,
    OpenAISummarizer,
    build_summarizer,
)


def test_build_summarizer_claude(mocker):
    mocker.patch("shutil.which", return_value="/usr/bin/claude")
    cfg = Config(summarization=SummarizationConfig(provider="claude"))
    summarizer = build_summarizer(cfg)
    assert isinstance(summarizer, ClaudeSummarizer)


def test_build_summarizer_openai(mocker):
    mocker.patch.dict("sys.modules", {"openai": mocker.MagicMock()})
    cfg = Config(summarization=SummarizationConfig(provider="openai", openai_api_key="sk-key"))
    summarizer = build_summarizer(cfg)
    assert isinstance(summarizer, OpenAISummarizer)


def test_build_summarizer_anthropic(mocker):
    mocker.patch.dict("sys.modules", {"anthropic": mocker.MagicMock()})
    cfg = Config(summarization=SummarizationConfig(provider="anthropic", anthropic_api_key="sk-key"))
    summarizer = build_summarizer(cfg)
    assert isinstance(summarizer, AnthropicSummarizer)


def test_build_summarizer_unknown_provider():
    cfg = Config(summarization=SummarizationConfig(provider="unknown"))
    with pytest.raises(ValueError, match="unknown summarization provider"):
        build_summarizer(cfg)


def test_claude_summarizer_runs_cli(mocker):
    mocker.patch("shutil.which", return_value="/usr/bin/claude")
    run = mocker.patch(
        "subprocess.run",
        return_value=MagicMock(returncode=0, stdout="summary output"),
    )
    summarizer = ClaudeSummarizer()
    result = summarizer.summarize(context="ctx", instruction="instr")
    assert result == "summary output"
    assert run.call_args.kwargs["input"].startswith("instr")


def test_file_based_claude_summarizer(mocker):
    mocker.patch("shutil.which", return_value="/usr/bin/claude")
    run = mocker.patch(
        "subprocess.run",
        return_value=MagicMock(returncode=0, stdout="file summary"),
    )
    summarizer = FileBasedClaudeSummarizer()
    result = summarizer.summarize(context="context text", instruction="summarize")
    assert result == "file summary"
    cmd = run.call_args.args[0]
    assert "--file" in cmd


def test_openai_summarizer(mocker):
    mocker.patch.dict("sys.modules", {"openai": mocker.MagicMock()})
    from openai import OpenAI
    client = OpenAI()
    client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="openai summary"))]
    )
    summarizer = OpenAISummarizer(api_key="sk-key")
    result = summarizer.summarize(context="ctx", instruction="instr")
    assert result == "openai summary"


def test_anthropic_summarizer(mocker):
    mocker.patch.dict("sys.modules", {"anthropic": mocker.MagicMock()})
    from anthropic import Anthropic
    client = Anthropic()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="anthropic summary")]
    )
    summarizer = AnthropicSummarizer(api_key="sk-key")
    result = summarizer.summarize(context="ctx", instruction="instr")
    assert result == "anthropic summary"
