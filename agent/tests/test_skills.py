"""Tests for skill loading, frontmatter parsing, and category grouping."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.agent.skills import Skill, SkillsLoader, _parse_frontmatter


# ---------------------------------------------------------------------------
# _parse_frontmatter
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def test_basic(self) -> None:
        text = "---\nname: test-skill\ndescription: A test\n---\nBody here."
        meta, body = _parse_frontmatter(text)
        assert meta["name"] == "test-skill"
        assert meta["description"] == "A test"
        assert body == "Body here."

    def test_category_field(self) -> None:
        text = "---\nname: foo\ncategory: strategy\n---\nContent"
        meta, body = _parse_frontmatter(text)
        assert meta["category"] == "strategy"

    def test_boolean_values(self) -> None:
        text = "---\nname: foo\nactive: true\narchived: false\n---\nBody"
        meta, _ = _parse_frontmatter(text)
        assert meta["active"] is True
        assert meta["archived"] is False

    def test_list_values(self) -> None:
        text = "---\nname: foo\ntags: [a, b, c]\n---\nBody"
        meta, _ = _parse_frontmatter(text)
        assert meta["tags"] == ["a", "b", "c"]

    def test_empty_list(self) -> None:
        text = "---\nname: foo\ntags: []\n---\nBody"
        meta, _ = _parse_frontmatter(text)
        assert meta["tags"] == []

    def test_no_frontmatter(self) -> None:
        text = "Just plain text, no frontmatter."
        meta, body = _parse_frontmatter(text)
        assert meta == {}
        assert body == text.strip()

    def test_multiline_body(self) -> None:
        text = "---\nname: x\n---\nLine 1\nLine 2\nLine 3"
        _, body = _parse_frontmatter(text)
        assert "Line 1" in body
        assert "Line 3" in body


# ---------------------------------------------------------------------------
# Skill dataclass
# ---------------------------------------------------------------------------


class TestSkill:
    def test_defaults(self) -> None:
        s = Skill(name="test")
        assert s.category == "other"
        assert s.description == ""
        assert s.body == ""
        assert s.metadata == {}

    def test_load_support_file_no_dir(self) -> None:
        s = Skill(name="test")
        assert s.load_support_file("missing.md") is None

    def test_load_support_file(self, tmp_path: Path) -> None:
        (tmp_path / "extra.md").write_text("extra content", encoding="utf-8")
        s = Skill(name="test", dir_path=tmp_path)
        assert s.load_support_file("extra.md") == "extra content"

    def test_load_support_file_missing(self, tmp_path: Path) -> None:
        s = Skill(name="test", dir_path=tmp_path)
        assert s.load_support_file("nope.md") is None

    def test_when_to_activate_metadata(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "alpha"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: alpha\n---\n"
            "# Alpha\n\n"
            "Intro\n\n"
            "## When to Activate\n\n"
            "- Use for momentum\n"
            "- Use for breakouts\n\n"
            "## Workflow\n\n"
            "Steps",
            encoding="utf-8",
        )

        loader = SkillsLoader(tmp_path, user_skills_dir=tmp_path / "empty", use_skillkit=False)
        skill = loader.skills[0]

        assert skill.metadata["when_to_activate"] == "- Use for momentum\n- Use for breakouts"

    def test_when_to_activate_bold_keywords(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "a-stock-data"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: a-stock-data\n---\n"
            "## When to Activate\n\n"
            "- 用户要看**限售解禁日历**\n"
            "- 用户要看**当日强势股 / 题材归因 / 概念热点**\n",
            encoding="utf-8",
        )

        loader = SkillsLoader(tmp_path, user_skills_dir=tmp_path / "empty", use_skillkit=False)
        skill = loader.skills[0]

        assert skill.metadata["activation_keywords"] == [
            "限售解禁日历",
            "当日强势股",
            "题材归因",
            "概念热点",
        ]
        assert [s.name for s in loader.match_skills("查一下限售解禁日历")] == ["a-stock-data"]


# ---------------------------------------------------------------------------
# SkillsLoader
# ---------------------------------------------------------------------------


class TestSkillsLoader:
    @pytest.fixture()
    def empty_user_dir(self, tmp_path_factory: pytest.TempPathFactory) -> Path:
        """Isolated empty user-skills dir so tests don't pick up real user skills."""
        return tmp_path_factory.mktemp("user_skills_empty")

    @pytest.fixture()
    def skills_dir(self, tmp_path: Path) -> Path:
        """Create a minimal skills directory with 3 skills in 2 categories."""
        for name, cat, desc in [
            ("alpha", "strategy", "Alpha strategy"),
            ("beta", "data-source", "Beta source"),
            ("gamma", "strategy", "Gamma strategy"),
        ]:
            d = tmp_path / name
            d.mkdir()
            (d / "SKILL.md").write_text(
                f"---\nname: {name}\ncategory: {cat}\ndescription: {desc}\n---\nBody of {name}.",
                encoding="utf-8",
            )
        return tmp_path

    def test_loads_all_skills(self, skills_dir: Path, empty_user_dir: Path) -> None:
        loader = SkillsLoader(skills_dir, user_skills_dir=empty_user_dir)
        assert len(loader.skills) == 3

    def test_category_assignment(self, skills_dir: Path, empty_user_dir: Path) -> None:
        loader = SkillsLoader(skills_dir, user_skills_dir=empty_user_dir)
        cats = {s.name: s.category for s in loader.skills}
        assert cats["alpha"] == "strategy"
        assert cats["beta"] == "data-source"

    def test_get_descriptions_grouped(self, skills_dir: Path, empty_user_dir: Path) -> None:
        loader = SkillsLoader(skills_dir, user_skills_dir=empty_user_dir)
        desc = loader.get_descriptions()
        # data-source comes before strategy in _CATEGORY_ORDER
        ds_pos = desc.index("data-source")
        st_pos = desc.index("strategy")
        assert ds_pos < st_pos

    def test_get_descriptions_contains_all(self, skills_dir: Path, empty_user_dir: Path) -> None:
        loader = SkillsLoader(skills_dir, user_skills_dir=empty_user_dir)
        desc = loader.get_descriptions()
        assert "alpha" in desc
        assert "beta" in desc
        assert "gamma" in desc

    def test_get_content_existing(self, skills_dir: Path, empty_user_dir: Path) -> None:
        loader = SkillsLoader(skills_dir, user_skills_dir=empty_user_dir)
        content = loader.get_content("alpha")
        assert '<skill name="alpha">' in content
        assert "Body of alpha" in content

    def test_get_content_missing(self, skills_dir: Path, empty_user_dir: Path) -> None:
        loader = SkillsLoader(skills_dir, user_skills_dir=empty_user_dir)
        content = loader.get_content("nonexistent")
        assert "Error" in content
        assert "nonexistent" in content

    def test_match_skills_uses_activation_text(self, tmp_path: Path, empty_user_dir: Path) -> None:
        skill_dir = tmp_path / "a-stock-data"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: a-stock-data\n"
            "category: data-source\n"
            "description: A股行情、估值、研报、资金流数据工具包\n"
            "---\n"
            "## When to Activate\n\n"
            "- 用户要查 A 股个股估值\n"
            "- 用户要看北向资金动向\n",
            encoding="utf-8",
        )
        loader = SkillsLoader(tmp_path, user_skills_dir=empty_user_dir, use_skillkit=False)

        matches = loader.match_skills("帮我分析 600519 的估值和北向资金")

        assert [skill.name for skill in matches] == ["a-stock-data"]

    def test_match_skills_detects_strong_stock_theme_question(self, tmp_path: Path, empty_user_dir: Path) -> None:
        skill_dir = tmp_path / "a-stock-data"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: a-stock-data\n"
            "category: data-source\n"
            "description: A股行情、强势股、题材归因数据工具包\n"
            "---\n"
            "## When to Activate\n\n"
            "- 用户要看当日强势股\n"
            "- 用户要做题材归因\n",
            encoding="utf-8",
        )
        loader = SkillsLoader(tmp_path, user_skills_dir=empty_user_dir, use_skillkit=False)

        matches = loader.match_skills("今天哪些股票走强，主要是什么题材")

        assert [skill.name for skill in matches] == ["a-stock-data"]

    def test_empty_dir(self, tmp_path: Path, empty_user_dir: Path) -> None:
        loader = SkillsLoader(tmp_path, user_skills_dir=empty_user_dir)
        assert loader.skills == []
        assert loader.get_descriptions() == "(no skills)"

    def test_dir_without_skill_md_skipped(self, tmp_path: Path, empty_user_dir: Path) -> None:
        (tmp_path / "empty_skill").mkdir()
        loader = SkillsLoader(tmp_path, user_skills_dir=empty_user_dir)
        assert len(loader.skills) == 0

    def test_nonexistent_dir(self, tmp_path: Path, empty_user_dir: Path) -> None:
        loader = SkillsLoader(tmp_path / "nope", user_skills_dir=empty_user_dir)
        assert loader.skills == []

    def test_skillkit_can_be_disabled(self, skills_dir: Path, empty_user_dir: Path) -> None:
        loader = SkillsLoader(skills_dir, user_skills_dir=empty_user_dir, use_skillkit=False)
        assert {s.name for s in loader.skills} == {"alpha", "beta", "gamma"}

    def test_skillkit_import_failure_falls_back(self, skills_dir: Path, empty_user_dir: Path) -> None:
        with patch.dict("sys.modules", {"skillkit": None}):
            loader = SkillsLoader(skills_dir, user_skills_dir=empty_user_dir)
        assert loader.get_content("alpha").startswith('<skill name="alpha">')

    def test_skillkit_loader_result_is_normalized(self, tmp_path: Path, empty_user_dir: Path) -> None:
        skill_dir = tmp_path / "skillkit-alpha"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: ignored\n---\nFallback body",
            encoding="utf-8",
        )
        fake_skillkit = SimpleNamespace(
            load_skill=lambda path: {
                "name": "skillkit-alpha",
                "description": "Loaded through skillkit",
                "category": "analysis",
                "body": "Skillkit body",
                "metadata": {"source": "skillkit"},
            }
        )

        with patch.dict("sys.modules", {"skillkit": fake_skillkit}):
            loader = SkillsLoader(tmp_path, user_skills_dir=empty_user_dir)

        assert len(loader.skills) == 1
        skill = loader.skills[0]
        assert skill.name == "skillkit-alpha"
        assert skill.description == "Loaded through skillkit"
        assert skill.category == "analysis"
        assert skill.body == "Skillkit body"
        assert skill.metadata == {"source": "skillkit"}

    def test_skillkit_manager_discovery_is_used(self, tmp_path: Path, empty_user_dir: Path) -> None:
        skill_dir = tmp_path / "manager-alpha"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: manager-alpha\ncategory: strategy\ndescription: Local description\n---\nManager body",
            encoding="utf-8",
        )

        class FakeSkillManager:
            def __init__(self, **kwargs: object) -> None:
                self.kwargs = kwargs
                self.discovered = False
                self.directory = Path(str(kwargs["project_skill_dir"]))

            def discover(self) -> None:
                self.discovered = True

            def list_skills(self) -> list[SimpleNamespace]:
                assert self.discovered is True
                if not (self.directory / "manager-alpha" / "SKILL.md").exists():
                    return []
                return [
                    SimpleNamespace(
                        name="manager-alpha",
                        description="Discovered through skillkit",
                    )
                ]

        fake_skillkit = SimpleNamespace(SkillManager=FakeSkillManager)

        with patch.dict("sys.modules", {"skillkit": fake_skillkit}):
            loader = SkillsLoader(tmp_path, user_skills_dir=empty_user_dir)

        assert len(loader.skills) == 1
        skill = loader.skills[0]
        assert skill.name == "manager-alpha"
        assert skill.description == "Discovered through skillkit"
        assert skill.category == "strategy"
        assert skill.body == "Manager body"
