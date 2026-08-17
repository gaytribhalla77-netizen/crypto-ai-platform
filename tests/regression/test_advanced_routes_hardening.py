"""Regression tests for AUDIT_FINDINGS_ROUND1.md #2, #3, #4
(unauthenticated memory write, unauthenticated provider status,
no rate limiting on advanced_routes.py).

These are deliberately source-level checks using `ast`/text search rather
than importing the FastAPI app, so they run without installing fastapi/
pydantic/etc. -- which this environment cannot do (registry access is
blocked). This is weaker evidence than an actual TestClient request
(that would still need a real HTTP-level test once dependencies are
installable), but it is real, executable, and it will fail loudly the
moment someone strips the auth dependency back off during a future edit.

Run: python3 tests/regression/test_advanced_routes_hardening.py
"""
import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
ROUTES_FILE = ROOT / "backend" / "api" / "advanced_routes.py"


def _parse():
    src = ROUTES_FILE.read_text(encoding="utf-8")
    return src, ast.parse(src, filename=str(ROUTES_FILE))


def _find_function(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == name:
            return node
    raise AssertionError(f"could not find async function {name!r} in {ROUTES_FILE}")


def _has_get_current_user_dependency(func_node):
    for arg_default in func_node.args.defaults:
        if isinstance(arg_default, ast.Call) and getattr(arg_default.func, "id", "") == "Depends":
            for call_arg in arg_default.args:
                if isinstance(call_arg, ast.Name) and call_arg.id == "get_current_user":
                    return True
    return False


def test_memory_add_requires_auth():
    src, tree = _parse()
    func = _find_function(tree, "memory_add")
    assert _has_get_current_user_dependency(func), (
        "POST /api/advanced/memory/add must require Depends(get_current_user) -- "
        "this endpoint writes into the shared, unscoped market-memory file that "
        "feeds the AI decision pipeline, and must not be anonymous."
    )


def test_providers_status_requires_auth():
    src, tree = _parse()
    func = _find_function(tree, "provider_status")
    assert _has_get_current_user_dependency(func), (
        "GET /api/advanced/providers/status must require Depends(get_current_user) -- "
        "it discloses whether broker credentials are configured and whether live "
        "trading is enabled."
    )


def test_router_has_rate_limit_dependency():
    src, _tree = _parse()
    assert "dependencies=[Depends(rate_limit(" in src, (
        "advanced_routes.py's APIRouter(...) must declare a shared rate_limit "
        "dependency -- this router previously had zero throttling across all "
        "22 routes, including compute-heavy ones (Monte Carlo, self-learning)."
    )
    assert "from core.rate_limit import rate_limit" in src


if __name__ == "__main__":
    test_memory_add_requires_auth()
    print("PASS: test_memory_add_requires_auth")
    test_providers_status_requires_auth()
    print("PASS: test_providers_status_requires_auth")
    test_router_has_rate_limit_dependency()
    print("PASS: test_router_has_rate_limit_dependency")
