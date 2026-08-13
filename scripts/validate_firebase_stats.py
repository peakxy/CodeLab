#!/usr/bin/env python3
"""Validate immutable Firebase statistics IDs for blog articles."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


FIELD_RE = re.compile(
    r"^firebaseStatsId\s*[:=]\s*(?:\"([^\"]+)\"|'([^']+)'|([^\s#]+))\s*$",
    re.MULTILINE,
)
LEGACY_FIELD_RE = re.compile(r"^firebaseStatsPath\s*[:=]", re.MULTILINE)
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._/-]*$")
LANGUAGE_SUFFIX_RE = re.compile(r"\.[a-z]{2}(?:-[a-z0-9]+)?$")


def front_matter(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] not in {"---", "+++"}:
        return ""

    delimiter = lines[0]
    try:
        end = lines[1:].index(delimiter) + 1
    except ValueError:
        return ""
    return "\n".join(lines[1:end])


def article_group(path: Path, content_dir: Path) -> str:
    relative = path.relative_to(content_dir)
    stem = LANGUAGE_SUFFIX_RE.sub("", relative.stem)
    return str(relative.with_name(stem))


def validate(content_dir: Path) -> list[str]:
    errors: list[str] = []
    group_ids: dict[str, str] = {}
    firestore_ids: dict[str, tuple[str, Path]] = {}
    articles = sorted(
        path
        for path in (content_dir / "blog").rglob("*.md")
        if not path.name.startswith("_index")
    )

    for path in articles:
        metadata = front_matter(path)
        relative = path.relative_to(content_dir)
        if LEGACY_FIELD_RE.search(metadata):
            errors.append(f"{relative}: replace firebaseStatsPath with firebaseStatsId")

        match = FIELD_RE.search(metadata)
        if not match:
            errors.append(f"{relative}: missing firebaseStatsId")
            continue

        stats_id = next(value for value in match.groups() if value is not None)
        if not ID_RE.fullmatch(stats_id) or "//" in stats_id or ".." in stats_id.split("/"):
            errors.append(f"{relative}: invalid firebaseStatsId {stats_id!r}")
            continue

        group = article_group(path, content_dir)
        normalized = stats_id.replace("/", "-")
        previous_group_id = group_ids.setdefault(group, normalized)
        if previous_group_id != normalized:
            errors.append(f"{relative}: translations of {group} must share one firebaseStatsId")

        previous = firestore_ids.setdefault(normalized, (group, relative))
        if previous[0] != group:
            errors.append(
                f"{relative}: firebaseStatsId collides with {previous[1]} after '/' normalization"
            )

    if not articles:
        errors.append("content/blog: no article files found")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-dir", type=Path, default=Path("content"))
    args = parser.parse_args()

    errors = validate(args.content_dir)
    if errors:
        print("Firebase statistics ID validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Firebase statistics IDs are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
