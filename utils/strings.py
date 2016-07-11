import unicodedata


def _normalize_caseless(s):
    return unicodedata.normalize('NFKD', s.casefold())


def istreq(s1, s2):
    if s1 is None and s2 is None:
        return True

    if s1 is None or s2 is None:
        return False

    if not isinstance(s1, str) or not isinstance(s2, str):
        return False

    return _normalize_caseless(s1) == _normalize_caseless(s2)
