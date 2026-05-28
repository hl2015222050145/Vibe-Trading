"""Tests for per-message automatic skill matching."""

from __future__ import annotations

import logging
from pathlib import Path

from src.agent.context import ContextBuilder
from src.agent.memory import WorkspaceMemory
from src.agent.skills import SkillsLoader
from src.agent.tools import ToolRegistry


def test_build_messages_injects_auto_selected_skill_prompt(tmp_path: Path) -> None:
    skill_dir = tmp_path / "a-stock-data"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: a-stock-data\n"
        "category: data-source\n"
        "description: A股行情、估值、研报、资金流数据工具包\n"
        "---\n"
        "## When to Activate\n\n"
        "- 用户要查 A 股个股估值\n",
        encoding="utf-8",
    )
    loader = SkillsLoader(tmp_path, user_skills_dir=tmp_path / "empty-user", use_skillkit=False)
    context = ContextBuilder(ToolRegistry(), WorkspaceMemory(), skills_loader=loader)

    messages = context.build_messages("分析 600519 的估值")

    user_content = messages[-1]["content"]
    assert "<auto-selected-skills>" in user_content
    assert "MUST call load_skill" in user_content
    assert 'load_skill("a-stock-data")' in user_content
    assert "分析 600519 的估值" in user_content


def test_build_messages_logs_auto_selected_skill(tmp_path: Path, caplog, capsys) -> None:
    skill_dir = tmp_path / "a-stock-data"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: a-stock-data\n"
        "category: data-source\n"
        "description: A股行情、估值、资金流数据工具包\n"
        "---\n"
        "## When to Activate\n\n"
        "- 用户要查 A 股个股估值\n",
        encoding="utf-8",
    )
    loader = SkillsLoader(tmp_path, user_skills_dir=tmp_path / "empty-user", use_skillkit=False)
    context = ContextBuilder(ToolRegistry(), WorkspaceMemory(), skills_loader=loader)

    with caplog.at_level(logging.INFO, logger="src.agent.context"):
        context.build_messages("分析 600519 的估值")

    assert "Skill auto-selected: a-stock-data" in caplog.text
    assert "Skill auto-selected: a-stock-data" in capsys.readouterr().out
