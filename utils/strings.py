import unicodedata

from bleach import ALLOWED_TAGS, clean

_HEADERS = ['h%d' % i for i in range(1, 7)]
_KEEP_TAGS = ALLOWED_TAGS + _HEADERS + ['u']


def make_all_safe(items, keep_case=False):
    """
    :type items: list[str]
    :type keep_case: bool
    :rtype: list[str]

    """
    return [make_safe(item, keep_case) for item in items] if items else items


def make_safe(data, keep_case=False):
    """
    :type data: str
    :type keep_case: bool
    :rtype: str

    """
    data = clean(data, strip=True, tags=_KEEP_TAGS)

    if not keep_case:
        data = normalize_caseless(data)
    return data


def normalize_caseless(s):
    """
    :type s: str
    :rtype: str

    """
    if not isinstance(s, str):
        return None

    return unicodedata.normalize('NFKD', s.casefold())
