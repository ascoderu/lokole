from pathlib import Path
from typing import Optional


def get_extension(path: Optional[str]) -> str:
    return ''.join(Path(path).suffixes) if path else ''
