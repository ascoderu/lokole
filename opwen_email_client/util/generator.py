from typing import Iterable


def length(sequence: Iterable) -> int:
    return sum(1 for _ in sequence)
