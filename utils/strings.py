import unicodedata


def normalize_caseless(s):
    """
    :type s: str
    :rtype: str

    """
    if not isinstance(s, str):
        return None

    return unicodedata.normalize('NFKD', s.casefold())
