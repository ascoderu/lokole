class DynamicFactory(object):
    def __init__(self, module_or_class):
        self.module_or_class = module_or_class

    def _locate_constructor(self):
        if isinstance(self.module_or_class, type):
            return self.module_or_class

        if isinstance(self.module_or_class, str):
            components = self.module_or_class.split('.')
            module = __import__('.'.join(components[:-1]))
            for component in components[1:]:
                module = getattr(module, component)
            return module

        raise NotImplementedError

    def __call__(self, *args, **kwargs):
        constructor = self._locate_constructor()
        return constructor(*args, **kwargs)
