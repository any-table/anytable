#!/usr/bin/env python3

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

FOUNDATIONAL = ROOT / "FOUNDATIONAL.md"
CARD = ROOT / "CARD.md"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"

CARD_START = "<!-- card:start -->"
CARD_END = "<!-- card:end -->"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: Path) -> str:
    if not path.exists():
        fail(f"Required file is missing: {path.relative_to(ROOT)}")

    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def extract_between(text: str, start: str, end: str, source: str) -> str:
    if text.count(start) != 1:
        fail(f"{source} must contain exactly one {start!r} marker.")

    if text.count(end) != 1:
        fail(f"{source} must contain exactly one {end!r} marker.")

    before, remainder = text.split(start, 1)
    body, after = remainder.split(end, 1)

    if before is None or after is None:
        fail(f"Could not extract marked section from {source}.")

    return body.strip()


def extract_version(pattern: str, text: str, source: str) -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)

    if not match:
        fail(f"Could not find version in {source}.")

    return match.group(1)


def check_card() -> None:
    foundational = read(FOUNDATIONAL)
    card = read(CARD)

    canonical = extract_between(
        foundational,
        CARD_START,
        CARD_END,
        "FOUNDATIONAL.md",
    )

    portable = extract_between(
        card,
        CARD_START,
        CARD_END,
        "CARD.md",
    )

    if canonical != portable:
        print("ERROR: CARD.md does not match the card in FOUNDATIONAL.md.")
        print()
        print("The text between the card markers must be identical.")
        raise SystemExit(1)

    print("OK: CARD.md matches FOUNDATIONAL.md")


def check_versions() -> str:
    foundational = read(FOUNDATIONAL)
    readme = read(README)
    changelog = read(CHANGELOG)

    foundational_version = extract_version(
        r"\*\*Version\.\*\*\s+(\d+\.\d+\.\d+)\b",
        foundational,
        "FOUNDATIONAL.md",
    )

    readme_version = extract_version(
        r"FOUNDATIONAL\.md\*\*:\s+the full text,\s+version\s+(\d+\.\d+\.\d+)",
        readme,
        "README.md",
    )

    changelog_version = extract_version(
        r"^##\s+(\d+\.\d+\.\d+)\s+\(",
        changelog,
        "CHANGELOG.md",
    )

    versions = {
        "FOUNDATIONAL.md": foundational_version,
        "README.md": readme_version,
        "CHANGELOG.md": changelog_version,
    }

    if len(set(versions.values())) != 1:
        fail(
            "Version mismatch: "
            + ", ".join(f"{name}={version}" for name, version in versions.items())
        )

    print(f"OK: document version is {foundational_version}")

    return foundational_version


def check_tag(version: str) -> None:
    ref_type = os.environ.get("GITHUB_REF_TYPE")
    ref_name = os.environ.get("GITHUB_REF_NAME")

    if ref_type != "tag":
        return

    if not ref_name or not ref_name.startswith("v"):
        fail(f"Release tag must use v<version>; got {ref_name!r}")

    tag_version = ref_name.removeprefix("v")

    if tag_version != version:
        fail(
            f"Tag {ref_name} does not match document version {version}."
        )

    print(f"OK: tag {ref_name} matches document version")


def check_required_files() -> None:
    required = [
        "CARD.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "FOUNDATIONAL.md",
        "GOVERNANCE.md",
        "LICENSE",
        "NOTICE.md",
        "READING.md",
        "README.md",
    ]

    missing = [name for name in required if not (ROOT / name).exists()]

    if missing:
        fail("Missing required files: " + ", ".join(missing))

    print("OK: required files exist")


def main() -> None:
    check_required_files()
    check_card()
    version = check_versions()
    check_tag(version)

    print("All document integrity checks passed.")


if __name__ == "__main__":
    main()
