class MockResponses:
    def __init__(self, responses):
        self._i = 0
        self._responses = responses

    def __call__(self, *args, **kwargs):
        try:
            status, headers, body = self._responses[self._i]
        except ValueError:
            body = self._responses[self._i]
            status = 200
            headers = {}

        self._i += 1

        return status, headers, body


def throw(exception):
    # noinspection PyUnusedLocal
    def throws(*args, **kwargs):
        raise exception

    return throws
