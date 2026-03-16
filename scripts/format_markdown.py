#!/usr/bin/env python3
"""Normalize Markdown for the CSC rulebook."""

from __future__ import annotations

import re
import sys
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
HR_RE = re.compile(r"^ {0,3}([-*_])(?:\s*\1){2,}\s*$")
BULLET_RE = re.compile(r"^(\s*)-\s+(.*)$")
NUMBERED_RULE_RE = re.compile(r"^\*\*(\d+(?:\.\d+)+)\*\*&emsp;(.*)$")
SAME_FILE_FRAGMENT_RE = re.compile(r"\]\(#([^)]+)\)")
BARE_URL_RE = re.compile(r"(?<!\]\()(?<!<)(https?://[^\s)>]+)(?!>)")


def iter_markdown_paths(args: list[str]) -> list[Path]:
    if args:
        candidates = [Path(arg) for arg in args]
    else:
        candidates = [Path(".")]

    paths: set[Path] = set()
    for candidate in candidates:
        if candidate.is_dir():
            for path in candidate.rglob("*.md"):
                if "node_modules" not in path.parts and ".git" not in path.parts:
                    paths.add(path)
            continue

        if candidate.is_file() and candidate.suffix.lower() == ".md":
            paths.add(candidate)

    return sorted(path.resolve() for path in paths)


def slugify_fragment(fragment: str) -> str:
    slug = fragment.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    return slug.strip("-")


def normalize_heading_levels(lines: list[str]) -> list[str]:
    levels = []
    for line in lines:
        match = HEADING_RE.match(line)
        if match:
            levels.append(len(match.group(1)))

    non_h1_levels = [level for level in levels if level > 1]
    shift = max(0, min(non_h1_levels, default=2) - 2)

    normalized: list[str] = []
    previous_level = 0
    for line in lines:
        match = HEADING_RE.match(line)
        if not match:
            normalized.append(line)
            continue

        level = len(match.group(1))
        title = match.group(2).strip()

        if level > 1 and shift:
            level = max(2, level - shift)

        if previous_level and level > previous_level + 1:
            level = previous_level + 1

        normalized.append(f"{'#' * level} {title}")
        previous_level = level

    return normalized


def normalize_bullets(lines: list[str]) -> list[str]:
    normalized: list[str] = []
    previous_source_indent: int | None = None
    previous_formatted_indent: int | None = None
    previous_text = ""
    previous_kind: str | None = None
    bullet_gap = True

    for line in lines:
        match = BULLET_RE.match(line)
        if not match:
            normalized.append(line)
            bullet_gap = True
            continue

        current_indent = len(match.group(1))
        text = match.group(2).lstrip()

        numbered = NUMBERED_RULE_RE.match(text)
        if numbered:
            depth = max(0, numbered.group(1).count(".") - 2)
            indent = depth * 4
            kind = "numbered"
        elif current_indent == 0 and not bullet_gap and previous_formatted_indent is not None:
            kind = "plain"
            if previous_kind == "numbered":
                indent = previous_formatted_indent + 4
            elif previous_formatted_indent == 0 and not previous_text.rstrip().endswith((".", "!", "?")):
                indent = 4
            elif previous_formatted_indent > 0:
                if previous_kind == "plain" and not previous_text.rstrip().endswith(":"):
                    indent = previous_formatted_indent
                else:
                    indent = previous_formatted_indent + 4
            else:
                indent = 0
        elif current_indent == 0:
            indent = 0
            kind = "plain"
        else:
            kind = "plain"
            if previous_source_indent is None or previous_formatted_indent is None:
                indent = max(4, round(current_indent / 4) * 4)
            elif current_indent > previous_source_indent:
                if previous_kind == "plain" and not previous_text.rstrip().endswith(":"):
                    indent = previous_formatted_indent
                else:
                    indent = previous_formatted_indent + 4
            elif current_indent == previous_source_indent:
                indent = previous_formatted_indent
            else:
                indent = max(4, round(current_indent / 4) * 4)

        normalized.append(f"{' ' * indent}- {text}")
        previous_source_indent = current_indent
        previous_formatted_indent = indent
        previous_text = text
        previous_kind = kind
        bullet_gap = False

    return normalized


def normalize_special_text(line: str) -> str:
    line = line.replace("\t", "    ").rstrip()
    line = SAME_FILE_FRAGMENT_RE.sub(
        lambda match: f"](#${slugify_fragment(match.group(1))})".replace("#$", "#"),
        line,
    )
    line = BARE_URL_RE.sub(r"<\1>", line)
    return line


def normalize_spacing(lines: list[str]) -> list[str]:
    output: list[str] = []
    blank_pending = False

    def flush_blank() -> None:
        nonlocal blank_pending
        if blank_pending and output and output[-1] != "":
            output.append("")
        blank_pending = False

    for line in lines:
        stripped = line.strip()
        is_blank = stripped == ""
        is_special = stripped == "&emsp;" or HEADING_RE.match(line) or HR_RE.match(line)

        if is_blank:
            blank_pending = True
            continue

        if is_special:
            if output and output[-1] != "":
                output.append("")
            output.append(stripped if stripped == "&emsp;" else line)
            blank_pending = True
            continue

        flush_blank()
        output.append(line)

    while output and output[-1] == "":
        output.pop()

    return output


def format_markdown(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [normalize_special_text(line) for line in text.split("\n")]
    lines = normalize_heading_levels(lines)
    lines = normalize_bullets(lines)
    lines = normalize_spacing(lines)
    return "\n".join(lines) + "\n"


def main() -> int:
    paths = iter_markdown_paths(sys.argv[1:])
    if not paths:
        return 0

    changed = False
    for path in paths:
        original = path.read_text(encoding="utf-8")
        formatted = format_markdown(original)
        if formatted != original:
            path.write_text(formatted, encoding="utf-8")
            changed = True

    if not sys.stdout.isatty() and changed:
        print(f"Formatted {len(paths)} Markdown file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
