#!/usr/bin/env python3
"""Pure-stdlib regression checks for the remaining Round 1 findings."""
from pathlib import Path
import ast
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))


def test_compose_has_no_redis():
    text = (ROOT / 'docker-compose.yml').read_text()
    assert '\n  redis:' not in text
    assert 'depends_on: [postgres, redis]' not in text
    assert 'depends_on: [postgres]' in text


def test_memory_isolation():
    from memory.market_memory import MarketMemory, MemoryRecord

    with tempfile.TemporaryDirectory() as tmp:
        old = MarketMemory.BASE_DIR
        MarketMemory.BASE_DIR = Path(tmp)
        try:
            a = MarketMemory(101)
            b = MarketMemory(202)
            record = MemoryRecord(1.0, 'BTCUSDT', 'bull', 'buy', 0.9, {'x': 1}, 0.12, True, 'user A')
            a.add(record)
            assert a.digest({'x': 1})['matches'] == 1
            assert b.digest({'x': 1})['matches'] == 0
            assert a.path.name == '101.jsonl'
            assert b.path.name == '202.jsonl'
            assert not (Path(tmp).parent / 'market_memory.jsonl').exists()
        finally:
            MarketMemory.BASE_DIR = old


def test_api_memory_routes_are_authenticated_and_user_scoped():
    tree = ast.parse((ROOT / 'backend/api/advanced_routes.py').read_text())
    routes = {}
    for node in tree.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name in {'memory_add', 'memory_similar'}:
            routes[node.name] = node
    assert set(routes) == {'memory_add', 'memory_similar'}
    for name, node in routes.items():
        source = ast.get_source_segment((ROOT / 'backend/api/advanced_routes.py').read_text(), node)
        assert 'Depends(get_current_user)' in source, f'{name} must require authentication'
        assert 'user.id' in source, f'{name} must use authenticated user id'
        assert 'MarketMemory(user.id)' in source, f'{name} must use per-user memory'


def test_no_live_redis_dependency():
    for path in (ROOT / 'backend').rglob('*.py'):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name != 'redis' and not alias.name.startswith('redis.') for alias in node.names), path
            elif isinstance(node, ast.ImportFrom):
                assert node.module != 'redis' and not (node.module or '').startswith('redis.'), path
    req = (ROOT / 'backend/requirements.txt').read_text().lower()
    assert '\nredis' not in req


if __name__ == '__main__':
    tests = [v for k, v in globals().items() if k.startswith('test_')]
    for test in tests:
        test()
        print(f'PASS {test.__name__}')
    print(f'PASS {len(tests)} Round 2 regression checks')
