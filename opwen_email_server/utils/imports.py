from importlib import import_module


def can_import(module_name: str) -> bool:
    try:
        import_module(module_name)
    except ImportError:
        return False
    else:
        return True
