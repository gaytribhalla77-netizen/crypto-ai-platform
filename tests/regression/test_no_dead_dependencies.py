"""Regression test for AUDIT_FINDINGS_ROUND1.md #5 (dead dependencies).

redis, python-dotenv, and pydantic-settings were declared in
backend/requirements.txt but never imported by any .py file in the repo.
This test re-derives that fact from the actual source tree (not from
memory of the earlier audit) so it stays correct if the code changes,
and fails if someone re-adds the declaration without ever using it.

Run: python3 tests/regression/test_no_dead_dependencies.py
"""
import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
REQUIREMENTS = ROOT / "backend" / "requirements.txt"

# import-name -> requirements.txt package name
WATCHED = {
    "redis": "redis",
    "dotenv": "python-dotenv",
    "pydantic_settings": "pydantic-settings",
}


def _all_top_level_imports():
    found = set()
    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                found.add(node.module.split(".")[0])
    return found


def _declared_package_names(requirements_text: str) -> set[str]:
    # Only real dependency lines -- ignore comments (which legitimately
    # mention removed package names to explain *why* they were removed)
    # and extras like `uvicorn[standard]`.
    names = set()
    for line in requirements_text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith("-r"):
            continue
        base = line.split("[")[0].strip()
        if base:
            names.add(base.lower())
    return names


def test_watched_packages_still_unused_and_undeclared():
    imports = _all_top_level_imports()
    declared = _declared_package_names(REQUIREMENTS.read_text(encoding="utf-8"))

    for import_name, package_name in WATCHED.items():
        actually_imported = import_name in imports
        still_declared = package_name.lower() in declared
        assert not (still_declared and not actually_imported), (
            f"{package_name!r} is declared in requirements.txt but still not "
            f"imported anywhere -- either use it or remove it again."
        )
        # If it *has* become genuinely used, it must be re-declared -- this
        # branch is what would fire if someone starts using redis etc.
        assert not (actually_imported and not still_declared), (
            f"{import_name!r} is now imported somewhere but {package_name!r} "
            f"is missing from requirements.txt -- add it back."
        )


if __name__ == "__main__":
    test_watched_packages_still_unused_and_undeclared()
    print("PASS: test_watched_packages_still_unused_and_undeclared")
