"""SkillsLoader: loads scenario guides from the skills/ directory.

Uses progressive disclosure:
- System prompt only injects one-line summaries (get_descriptions).
- Full docs loaded on demand (get_content, called by the load_skill tool).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Skill:
    """Single skill definition.

    Attributes:
        name: Skill name.
        description: Skill description.
        category: Skill category for grouped display.
        body: SKILL.md body text.
        dir_path: Skill directory path (used for on-demand loading of supporting files).
        metadata: Parsed frontmatter metadata.
    """

    name: str
    description: str = ""
    category: str = "other"
    body: str = ""
    dir_path: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def load_support_file(self, filename: str) -> Optional[str]:
        """Load a supporting file on demand.

        Args:
            filename: File name (e.g. examples.md).

        Returns:
            File content or None.
        """
        if not self.dir_path:
            return None
        path = self.dir_path / filename
        if not path.exists():
            return None
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return None


from src.agent.frontmatter import parse_frontmatter as _parse_frontmatter  # shared util


def _extract_markdown_section(body: str, title: str) -> str:
    """Extract a markdown section by heading title."""
    pattern = rf"(?ims)^#+\s*{re.escape(title)}\s*(.*?)(?=^#+\s|\Z)"
    match = re.search(pattern, body)
    return match.group(1).strip() if match else ""


def _extract_bold_keywords(text: str) -> List[str]:
    """Extract bold markdown phrases as activation keywords."""
    keywords: List[str] = []
    seen: set[str] = set()
    for bold in re.findall(r"\*\*(.+?)\*\*", text):
        for part in re.split(r"[/／、,，;；|]+", bold):
            cleaned = part.strip()
            if cleaned and cleaned not in seen:
                keywords.append(cleaned)
                seen.add(cleaned)
    return keywords


def _load_skill_dir(dir_path: Path) -> Optional[Skill]:
    """Load a skill from a directory.

    Args:
        dir_path: Skill directory path (must contain SKILL.md).

    Returns:
        Skill instance or None.
    """
    skill_file = dir_path / "SKILL.md"
    if not skill_file.exists():
        return None
    try:
        text = skill_file.read_text(encoding="utf-8")
    except Exception:
        return None

    meta, body = _parse_frontmatter(text)
    name = meta.get("name", dir_path.name)
    if not name:
        return None
    metadata = dict(meta)
    when_to_activate = _extract_markdown_section(body, "When to Activate")
    if when_to_activate:
        metadata["when_to_activate"] = when_to_activate
        activation_keywords = _extract_bold_keywords(when_to_activate)
        if activation_keywords:
            metadata["activation_keywords"] = activation_keywords

    return Skill(
        name=name,
        description=metadata.get("description", ""),
        category=metadata.get("category", "other"),
        body=body,
        dir_path=dir_path,
        metadata=metadata,
    )


def _load_skill_dir_with_skillkit(dir_path: Path) -> Optional[Skill]:
    """Load a skill directory through skillkit when it is available.

    The local Skill dataclass remains the boundary for the rest of the app, so
    MCP tools, the REST API, and tests keep the same behavior whether skillkit
    is installed or not.
    """
    try:
        import skillkit  # type: ignore[import-not-found]
    except Exception:
        return None

    # skillkit has had a small API surface across releases. Try common loader
    # entry points, then normalize whatever object/dict it returns.
    loaded: Any = None
    for attr in ("load_skill", "load", "read_skill"):
        loader = getattr(skillkit, attr, None)
        if callable(loader):
            try:
                loaded = loader(dir_path)
                break
            except TypeError:
                try:
                    loaded = loader(str(dir_path))
                    break
                except Exception:
                    continue
            except Exception:
                continue

    if loaded is None:
        manager_cls = getattr(skillkit, "SkillManager", None)
        if manager_cls is not None:
            try:
                manager = manager_cls()
                for attr in ("load_skill", "load", "read_skill"):
                    loader = getattr(manager, attr, None)
                    if callable(loader):
                        try:
                            loaded = loader(dir_path)
                            break
                        except TypeError:
                            loaded = loader(str(dir_path))
                            break
            except Exception:
                loaded = None

    if loaded is None:
        return None

    def pick(key: str, default: Any = "") -> Any:
        if isinstance(loaded, dict):
            return loaded.get(key, default)
        return getattr(loaded, key, default)

    name = pick("name") or dir_path.name
    body = pick("body") or pick("content") or pick("instructions") or ""
    metadata = pick("metadata", None) or pick("frontmatter", None) or {}
    if not isinstance(metadata, dict):
        metadata = {}

    # Some skillkit objects expose raw markdown only. Fall back to the local
    # parser for missing body/frontmatter so behavior stays identical.
    if not body:
        try:
            text = (dir_path / "SKILL.md").read_text(encoding="utf-8")
        except Exception:
            return None
        metadata, body = _parse_frontmatter(text)
        name = metadata.get("name", name)

    return Skill(
        name=str(name),
        description=str(pick("description", metadata.get("description", "")) or ""),
        category=str(pick("category", metadata.get("category", "other")) or "other"),
        body=str(body),
        dir_path=dir_path,
        metadata=metadata,
    )


def _load_directory_with_skillkit(directory: Path) -> List[Skill]:
    """Discover skills in a directory using skillkit's SkillManager API."""
    try:
        from skillkit import SkillManager  # type: ignore[import-not-found]
    except Exception:
        return []

    manager = None
    for kwargs in (
        {"project_skill_dir": str(directory)},
        {"skill_dir": str(directory)},
        {"skills_dir": str(directory)},
        {"custom_skill_dirs": [str(directory)]},
    ):
        try:
            manager = SkillManager(**kwargs)
            break
        except TypeError:
            continue
        except Exception:
            return []
    if manager is None:
        try:
            manager = SkillManager()
        except Exception:
            return []

    discover = getattr(manager, "discover", None)
    if callable(discover):
        try:
            discover()
        except TypeError:
            try:
                discover(str(directory))
            except Exception:
                return []
        except Exception:
            return []

    list_skills = getattr(manager, "list_skills", None)
    if not callable(list_skills):
        return []

    try:
        discovered = list_skills()
    except Exception:
        return []

    local_by_name: Dict[str, Skill] = {}
    for skill_file in directory.rglob("SKILL.md"):
        skill = _load_skill_dir(skill_file.parent)
        if skill:
            local_by_name[skill.name] = skill

    out: List[Skill] = []
    for item in discovered or []:
        name = getattr(item, "name", None)
        if isinstance(item, dict):
            name = item.get("name")
        if not name:
            continue

        local = local_by_name.get(str(name))
        if local:
            metadata = dict(local.metadata)
            description = getattr(item, "description", None)
            if isinstance(item, dict):
                description = item.get("description", description)
            if description:
                metadata.setdefault("description", description)
            out.append(Skill(
                name=local.name,
                description=str(description or local.description),
                category=local.category,
                body=local.body,
                dir_path=local.dir_path,
                metadata=metadata,
            ))
            continue

        description = item.get("description", "") if isinstance(item, dict) else getattr(item, "description", "")
        category = item.get("category", "other") if isinstance(item, dict) else getattr(item, "category", "other")
        body = ""
        get_skill = getattr(manager, "get_skill", None)
        if callable(get_skill):
            try:
                full = get_skill(str(name))
                body = getattr(full, "content", "") or getattr(full, "body", "") or getattr(full, "instructions", "")
            except Exception:
                body = ""
        if not body:
            invoke_skill = getattr(manager, "invoke_skill", None)
            if callable(invoke_skill):
                try:
                    body = str(invoke_skill(str(name), ""))
                except Exception:
                    body = ""
        out.append(Skill(
            name=str(name),
            description=str(description or ""),
            category=str(category or "other"),
            body=body,
            dir_path=None,
            metadata={},
        ))
    return out


USER_SKILLS_DIR = Path.home() / ".vibe-trading" / "skills" / "user"


class SkillsLoader:
    """Load skills from bundled skills/ directory and user skills directory.

    Attributes:
        skills: Loaded skill list (bundled + user-created).
    """

    def __init__(self, skills_dir: Optional[Path] = None,
                 user_skills_dir: Optional[Path] = None,
                 use_skillkit: bool = True) -> None:
        """Initialize SkillsLoader.

        Args:
            skills_dir: Bundled skills directory path; defaults to agent/skills/.
            user_skills_dir: User-created skills directory; defaults to ~/.vibe-trading/skills/user/.
        """
        self.skills_dir = skills_dir or Path(__file__).resolve().parents[1] / "skills"
        self._user_skills_dir = user_skills_dir or USER_SKILLS_DIR
        self.use_skillkit = use_skillkit
        self.skills: List[Skill] = []
        self._load()

    def _load(self) -> None:
        """Load all skill subdirectories from user and bundled directories.

        User skills are loaded first so they override bundled skills with the same name
        (e.g. after patch_skill copies and modifies a bundled skill).
        """
        seen_names: set[str] = set()
        for directory in (self._user_skills_dir, self.skills_dir):
            if not directory or not directory.exists():
                continue
            loaded = _load_directory_with_skillkit(directory) if self.use_skillkit else []
            if not loaded:
                for path in sorted(directory.iterdir()):
                    if path.is_dir() and (path / "SKILL.md").exists():
                        skill = None
                        if self.use_skillkit:
                            skill = _load_skill_dir_with_skillkit(path)
                        skill = skill or _load_skill_dir(path)
                        if skill:
                            loaded.append(skill)
            for skill in loaded:
                if skill.name not in seen_names:
                    self.skills.append(skill)
                    seen_names.add(skill.name)

    # Display order for categories (unlisted categories appear at the end).
    _CATEGORY_ORDER = [
        "data-source", "strategy", "analysis", "asset-class",
        "crypto", "flow", "tool", "other",
    ]
    _MATCH_STOPWORDS = {
        "分析", "帮我", "一下", "一个", "这个", "那个", "用户", "需要", "看看",
        "研究", "数据", "市场", "股票", "交易", "投资", "策略", "工具",
    }
    _MATCH_SYNONYMS = {
        "走强": {"强势", "强势股", "领涨"},
        "强势": {"走强", "强势股", "领涨"},
        "题材": {"题材归因", "热点", "概念"},
        "热点": {"题材", "题材归因", "概念"},
    }

    def get_descriptions(self) -> str:
        """Return skills grouped by category for the system prompt.

        Returns:
            Grouped skill list with category headers.
        """
        if not self.skills:
            return "(no skills)"

        groups: Dict[str, List[Skill]] = {}
        for skill in self.skills:
            groups.setdefault(skill.category, []).append(skill)

        ordered_cats = [c for c in self._CATEGORY_ORDER if c in groups]
        ordered_cats += [c for c in sorted(groups) if c not in ordered_cats]

        lines: List[str] = []
        for cat in ordered_cats:
            lines.append(f"\n### {cat}")
            for skill in groups[cat]:
                lines.append(f"  - {skill.name}: {skill.description}")
        return "\n".join(lines)

    @staticmethod
    def _activation_text(skill: Skill) -> str:
        """Return compact searchable text for automatic skill matching."""
        chunks = [skill.name, skill.description]
        triggers = (
            skill.metadata.get("activation_keywords")
            or skill.metadata.get("triggers")
            or skill.metadata.get("keywords")
            or skill.metadata.get("tags")
        )
        if isinstance(triggers, list):
            chunks.extend(str(item) for item in triggers)
        elif isinstance(triggers, str):
            chunks.append(triggers)

        when_to_activate = skill.metadata.get("when_to_activate", "")
        if isinstance(when_to_activate, str) and when_to_activate:
            chunks.append(when_to_activate)
        else:
            chunks.append(skill.body[:1200])
        return "\n".join(chunk for chunk in chunks if chunk)

    @staticmethod
    def _terms(text: str) -> set[str]:
        """Extract rough searchable terms across English, Chinese, and tickers."""
        lowered = text.lower()
        terms = set(re.findall(r"[a-z][a-z0-9_-]{1,}|[0-9]{5,6}(?:\.(?:sh|sz|bj))?", lowered))
        for token in re.findall(r"[\u4e00-\u9fff]{2,}", text):
            if token not in SkillsLoader._MATCH_STOPWORDS:
                terms.add(token)
            for size in (2, 3, 4):
                if len(token) >= size:
                    terms.update(
                        part
                        for i in range(0, len(token) - size + 1)
                        if (part := token[i:i + size]) not in SkillsLoader._MATCH_STOPWORDS
                    )
        expanded = set(terms)
        for term in terms:
            expanded.update(SkillsLoader._MATCH_SYNONYMS.get(term, set()))
        terms = expanded
        return terms

    def match_skills(self, user_message: str, max_results: int = 3) -> List[Skill]:
        """Return skills whose activation text matches the user's message.

        This is intentionally conservative: it only returns skills with direct
        lexical overlap against the skill name, description, frontmatter hints,
        or a "When to Activate" section. Full skill docs are still loaded by the
        LLM via the `load_skill` tool.
        """
        query_terms = self._terms(user_message)
        if not query_terms:
            return []
        has_ashare_code = bool(re.search(r"\b(?:[0368]\d{5}|[0368]\d{5}\.(?:sh|sz|bj))\b", user_message.lower()))

        scored: List[tuple[int, Skill]] = []
        for skill in self.skills:
            activation = self._activation_text(skill)
            activation_terms = self._terms(activation)
            overlap = query_terms & activation_terms
            if not overlap:
                continue
            score = len(overlap)
            if skill.name.lower() in user_message.lower():
                score += 5
            if any(term in skill.description.lower() for term in query_terms if len(term) >= 2):
                score += 2
            if has_ashare_code and any(marker in activation for marker in ("A股", "个股", "沪深")):
                score += 3
            if str(skill.metadata.get("origin", "")).lower() == "custom":
                score += 2
            if score >= 4:
                scored.append((score, skill))

        scored.sort(key=lambda item: (-item[0], item[1].name))
        return [skill for _, skill in scored[:max_results]]

    def get_content(self, name: str) -> str:
        """Return the full documentation for a skill (used by the load_skill tool).

        Falls back to disk lookup for user skills created mid-session.

        Args:
            name: Skill name.

        Returns:
            XML-wrapped full skill document, or an error message.
        """
        for skill in self.skills:
            if skill.name == name:
                return f'<skill name="{name}">\n{skill.body}\n</skill>'

        # Fallback: check user skills directory on disk (mid-session created skills)
        if self._user_skills_dir:
            skill = _load_skill_dir(self._user_skills_dir / name)
            if skill:
                self.skills.append(skill)
                return f'<skill name="{name}">\n{skill.body}\n</skill>'

        available = ", ".join(s.name for s in self.skills)
        return f"Error: Unknown skill '{name}'. Available: {available}"
