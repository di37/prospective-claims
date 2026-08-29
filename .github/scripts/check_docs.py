"""Documentation checks that can run before any research code exists.

Five checks, all of which catch things that rot silently: relative links pointing
at files that were renamed, anchor links pointing at headings that were reworded,
a CITATION.cff that stopped parsing, a guidelines version that drifted between the
change log and the record schema, and hard-wrapped prose.

Run locally with `python .github/scripts/check_docs.py`. Exits non-zero on failure.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARKDOWN = sorted(p for p in ROOT.rglob("*.md") if "bin" not in p.parts and ".github" not in p.parts)

FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^\s*#{1,6}\s+(.*)$")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
HTML_SRC = re.compile(r'(?:src|srcset|href)="([^"]+)"')
SKIP_PROSE = re.compile(r"^\s*(#{1,6}\s|\||[-*+]\s|\d+[.)]\s|>|<|\[.+\]:)|^ {4,}\S|^\s*$")


def anchor(text: str) -> str:
    """Convert a heading into the anchor GitHub generates for it.

    Args:
        text: Raw heading text, without the leading hashes.

    Returns:
        The anchor slug.
    """
    text = re.sub(r"[`*_]", "", text).strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s+", "-", text)


def outside_fences(path: Path) -> list[tuple[int, str]]:
    """Return numbered lines that sit outside fenced code blocks.

    Args:
        path: Markdown file.

    Returns:
        List of (line number, line) pairs.
    """
    out, fenced = [], False
    for i, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            out.append((i, line))
    return out


def check_links(fail) -> None:
    """Check that relative links and same-file anchors resolve.

    Args:
        fail: Callback taking a message string.

    Returns:
        None.
    """
    for path in MARKDOWN:
        lines = outside_fences(path)
        anchors = {anchor(m.group(1)) for _, l in lines if (m := HEADING.match(l))}
        for number, line in lines:
            for target in LINK.findall(line) + HTML_SRC.findall(line):
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                where = f"{path.relative_to(ROOT)}:{number}"
                if target.startswith("#"):
                    if target[1:] not in anchors:
                        fail(f"{where}  anchor {target} matches no heading")
                else:
                    resolved = (path.parent / target.split("#")[0]).resolve()
                    if not resolved.exists():
                        fail(f"{where}  link {target} points at a missing file")


def check_citation(fail) -> None:
    """Check that CITATION.cff parses and carries the fields GitHub needs.

    Args:
        fail: Callback taking a message string.

    Returns:
        None.
    """
    path = ROOT / "CITATION.cff"
    if not path.exists():
        fail("CITATION.cff is missing")
        return
    try:
        import yaml
    except ImportError:
        print("  note: PyYAML absent, CITATION.cff parsed structurally only")
        text = path.read_text(encoding="utf-8")
        for key in ("cff-version", "title", "authors", "license"):
            if not re.search(rf"^{key}:", text, re.M):
                fail(f"CITATION.cff missing required key: {key}")
        return
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for key in ("cff-version", "title", "authors", "license"):
        if key not in data:
            fail(f"CITATION.cff missing required key: {key}")


def check_guidelines_version(fail) -> None:
    """Check the guidelines version agrees between the schema block and change log.

    Args:
        fail: Callback taking a message string.

    Returns:
        None.
    """
    path = ROOT / "annotation-guidelines.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")

    in_schema = re.search(r'"guidelines_version":\s*"([\d.]+)"', text)
    entries = re.findall(r"^\|\s*(\d+\.\d+)\s*\|", text, re.M)
    if not in_schema:
        fail("annotation-guidelines.md: no guidelines_version in the record schema")
        return
    if not entries:
        fail("annotation-guidelines.md: no change-log entries found")
        return
    newest = max(entries, key=lambda v: tuple(int(x) for x in v.split(".")))
    if in_schema.group(1) != newest:
        fail(
            f"annotation-guidelines.md: schema says v{in_schema.group(1)} but the "
            f"newest change-log entry is v{newest}"
        )


def check_no_hard_wrapping(fail) -> None:
    """Check that prose paragraphs are not hard-wrapped.

    Args:
        fail: Callback taking a message string.

    Returns:
        None.
    """
    for path in MARKDOWN:
        previous, in_comment = None, False
        for number, line in outside_fences(path):
            if "<!--" in line and "-->" not in line:
                in_comment = True
            if in_comment:
                if "-->" in line:
                    in_comment = False
                previous = None
                continue
            is_prose = not SKIP_PROSE.match(line)
            if is_prose and previous is not None:
                fail(f"{path.relative_to(ROOT)}:{previous}  paragraph is hard-wrapped")
                previous = None
                continue
            previous = number if is_prose else None


def main() -> int:
    """Run every check and return a process exit code.

    Returns:
        0 if all checks passed, 1 otherwise.
    """
    failures: list[str] = []
    checks = [
        ("links and anchors resolve", check_links),
        ("CITATION.cff is valid", check_citation),
        ("guidelines version is consistent", check_guidelines_version),
        ("prose is not hard-wrapped", check_no_hard_wrapping),
    ]
    for name, check in checks:
        before = len(failures)
        check(failures.append)
        found = len(failures) - before
        print(("FAIL  " if found else "PASS  ") + name)
        for message in failures[before:]:
            print(f"        {message}")

    print(f"\n{len(checks)} checks run, {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
