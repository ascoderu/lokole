from json import dumps


def to_json(obj: object) -> str:
    return dumps(obj, separators=(',', ':'))
