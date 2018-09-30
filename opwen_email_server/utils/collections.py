from itertools import islice
from typing import Iterable
from typing import Optional
from typing import TypeVar

T = TypeVar('T')


def to_iterable(obj: Optional[T]) -> Iterable[T]:
    if obj:
        yield obj


def chunks(iterable: Iterable[T], chunk_size: int) -> Iterable[Iterable[T]]:
    it = iter(iterable)
    while True:
        chunk = tuple(islice(it, chunk_size))
        if not chunk:
            return
        yield chunk
