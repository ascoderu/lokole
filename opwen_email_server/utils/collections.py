from typing import Iterable
from typing import Optional
from typing import TypeVar

T = TypeVar('T')


def to_iterable(obj: Optional[T]) -> Iterable[T]:
    if obj:
        yield obj
