"""Tests for load_skill tool observability."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.agent.skills import SkillsLoader
from src.tools.load_skill_tool import LoadSkillTool


def test_load_skill_logs_loaded_skill_name(tmp_path: Path, caplog, capsys) -> None:
    skill_dir = tmp_path / "alpha"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: alpha\ndescription: Alpha skill\n---\nBody",
        encoding="utf-8",
    )
    loader = SkillsLoader(tmp_path, user_skills_dir=tmp_path / "empty-user", use_skillkit=False)
    tool = LoadSkillTool(loader)

    with caplog.at_level(logging.INFO, logger="src.tools.load_skill_tool"):
        result = json.loads(tool.execute(name="alpha"))

    assert result["status"] == "ok"
    assert "Skill loaded: alpha" in caplog.text
    assert "Skill loaded: alpha" in capsys.readouterr().out
