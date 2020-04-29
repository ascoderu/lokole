from functools import wraps
from typing import Dict
from typing import Optional

from flask import request
from flask import session


class Session(object):
    _current_language_key = 'current_language'
    _last_visited_url_key = 'last_visited_url'

    @classmethod
    def _session(cls) -> Dict[str, str]:
        return session

    @classmethod
    def store_last_visited_url(cls):
        cls._session()[cls._last_visited_url_key] = request.url

    @classmethod
    def get_last_visited_url(cls) -> Optional[str]:
        return cls._session().get(cls._last_visited_url_key)

    @classmethod
    def store_current_language(cls, language: str):
        cls._session()[cls._current_language_key] = language

    @classmethod
    def get_current_language(cls) -> str:
        return cls._session().get(cls._current_language_key)


def track_history(func):
    @wraps(func)
    def history_tracker(*args, **kwargs):
        Session.store_last_visited_url()
        return func(*args, **kwargs)

    return history_tracker
