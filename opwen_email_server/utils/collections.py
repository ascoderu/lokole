def to_iterable(obj):
    """
    :type obj: T|None
    :rtype: collection.Iterable[T]

    """
    if obj:
        yield obj
