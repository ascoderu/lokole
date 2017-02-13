def length(sequence):
    """
    :type sequence: collections.Iterable
    :rtype: int

    """
    return sum(1 for _ in sequence)
