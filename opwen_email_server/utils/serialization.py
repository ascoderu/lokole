from json import dumps


def to_json(obj):
    """
    :type obj: object
    :rtype: str

    """
    return dumps(obj, separators=(',', ':'))
