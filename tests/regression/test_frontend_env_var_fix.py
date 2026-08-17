"""Regression test for AUDIT_FINDINGS_ROUND1.md #1 (frontend env var mismatch).

page.tsx used to read NEXT_PUBLIC_API_URL, which nothing else in the repo
ever sets, so the dashboard silently fell back to localhost:8000 in every
deployed environment. This is a plain source-text check (no fastapi/next
install required) so it can actually run in restricted environments.

Run: python3 tests/regression/test_frontend_env_var_fix.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
PAGE_TSX = ROOT / "apps" / "web" / "app" / "page.tsx"
API_TS = ROOT / "apps" / "web" / "app" / "lib" / "api.ts"
ENV_EXAMPLE = ROOT / "apps" / "web" / ".env.local.example"


def _non_comment_lines(src: str):
    # Strip full-line `//` comments so explanatory comments that mention
    # the old (broken) var name for documentation purposes don't trip the
    # check -- only actual code references matter here.
    return "\n".join(
        line for line in src.splitlines() if not line.strip().startswith("//")
    )


def test_page_and_api_client_use_the_same_env_var():
    page_src = PAGE_TSX.read_text(encoding="utf-8")
    page_code = _non_comment_lines(page_src)
    api_src = API_TS.read_text(encoding="utf-8")
    env_src = ENV_EXAMPLE.read_text(encoding="utf-8")

    assert "process.env.NEXT_PUBLIC_API_URL" not in page_code, (
        "page.tsx still reads process.env.NEXT_PUBLIC_API_URL in actual code, "
        "which is never set anywhere in the repo -- this is the regression "
        "this test guards."
    )
    assert "NEXT_PUBLIC_API_BASE" in page_src, "page.tsx should read NEXT_PUBLIC_API_BASE."
    assert "NEXT_PUBLIC_API_BASE" in api_src, "lib/api.ts should still read NEXT_PUBLIC_API_BASE."
    assert "NEXT_PUBLIC_API_BASE" in env_src, ".env.local.example should still document NEXT_PUBLIC_API_BASE."

    # duplicate-line regression: the example file used to declare the same
    # var twice.
    occurrences = env_src.count("NEXT_PUBLIC_API_BASE=")
    assert occurrences == 1, f"expected exactly one NEXT_PUBLIC_API_BASE= line, found {occurrences}"


if __name__ == "__main__":
    test_page_and_api_client_use_the_same_env_var()
    print("PASS: test_page_and_api_client_use_the_same_env_var")
