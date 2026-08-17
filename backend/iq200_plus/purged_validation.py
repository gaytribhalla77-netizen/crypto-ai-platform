from dataclasses import dataclass
from typing import Sequence

@dataclass(frozen=True)
class Fold:
    train: list[int]
    test: list[int]
    purged: list[int]
    embargoed: list[int]

def purged_walk_forward(n: int, n_splits: int = 5, purge: int = 0, embargo: int = 0) -> list[Fold]:
    if n <= 0 or n_splits < 2 or n_splits > n:
        raise ValueError("invalid sample/split configuration")
    step = n // n_splits
    out = []
    for k in range(n_splits):
        test_start = k * step
        test_end = n if k == n_splits - 1 else (k + 1) * step
        test = list(range(test_start, test_end))
        purge_start = max(0, test_start - purge)
        purge_end = min(n, test_end + purge)
        purged = list(range(purge_start, purge_end))
        train = [i for i in range(n) if i not in purged]
        emb_start, emb_end = test_end, min(n, test_end + embargo)
        embargoed = list(range(emb_start, emb_end))
        train = [i for i in train if i not in embargoed]
        out.append(Fold(train, test, purged, embargoed))
    return out

def leakage_check(train: Sequence[int], test: Sequence[int], embargoed: Sequence[int] = ()) -> bool:
    return not (set(train) & set(test) or set(train) & set(embargoed))
