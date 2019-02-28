from urllib.parse import quote


def is_lowercase(string: str) -> bool:
    return string.lower() == string


def urlsafe(urlpart: str) -> str:
    return quote(urlpart, safe='')
