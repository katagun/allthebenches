#!/usr/bin/env python3
"""Audit every third-party package locked in uv.lock against OSV.

This script intentionally does not install project dependencies. It passes
exact locked versions to a pinned pip-audit tool with dependency resolution
disabled, so platform-marked lock entries are audited as well as the current
platform's packages. Audit/network failures propagate as a non-zero exit.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path


PIP_AUDIT_VERSION = "2.10.1"


def normalized_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    lock_path = root / "uv.lock"
    project_path = root / "pyproject.toml"

    with project_path.open("rb") as stream:
        project = tomllib.load(stream)
    with lock_path.open("rb") as stream:
        lock = tomllib.load(stream)

    project_name = project.get("project", {}).get("name")
    if not project_name:
        raise ValueError(f"missing [project].name in {project_path}")
    root_name = normalized_name(project_name)

    packages = lock.get("package")
    if not isinstance(packages, list):
        raise ValueError(f"missing package entries in {lock_path}")

    pinned: set[tuple[str, str]] = set()
    for package in packages:
        if not isinstance(package, dict):
            raise ValueError(f"invalid package entry in {lock_path}: {package!r}")
        name = package.get("name")
        version = package.get("version")
        if not isinstance(name, str) or not isinstance(version, str):
            raise ValueError(f"lock entry must have string name and version: {package!r}")
        source = package.get("source") or {}
        if not isinstance(source, dict):
            raise ValueError(f"invalid source in lock entry for {name}: {source!r}")
        if normalized_name(name) == root_name or source.get("editable") == ".":
            continue
        pinned.add((name, version))

    if not pinned:
        raise ValueError(f"no third-party package versions found in {lock_path}")

    with tempfile.TemporaryDirectory(prefix="allthebenches-python-audit-") as temporary:
        temp_path = Path(temporary)
        requirements = temp_path / "locked-requirements.txt"
        requirements.write_text(
            "".join(f"{name}=={version}\n" for name, version in sorted(pinned)),
            encoding="utf-8",
        )

        command = [
            "uvx",
            "--from",
            f"pip-audit=={PIP_AUDIT_VERSION}",
            "pip-audit",
            "--requirement",
            str(requirements),
            "--no-deps",
            "--disable-pip",
            "--strict",
            "--vulnerability-service",
            "osv",
        ]
        print(
            f"Auditing {len(pinned)} locked third-party packages with "
            f"pip-audit {PIP_AUDIT_VERSION} against OSV.",
            flush=True,
        )
        try:
            result = subprocess.run(command, cwd=root, check=False)
        except FileNotFoundError as error:
            print(f"Could not start uvx for the dependency audit: {error}", file=sys.stderr)
            return 1
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
