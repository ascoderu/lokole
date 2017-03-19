from importlib import import_module


def can_import(module: str) -> bool:
    try:
        import_module(module)
    except ImportError:
        return False
    else:
        return True
