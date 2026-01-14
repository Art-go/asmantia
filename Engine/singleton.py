from functools import wraps


class Singleton:
    _instance = None
    initialized = False
    _custom_init = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self.initialized or self._custom_init:
            return
        self.initialized = True

    @staticmethod
    def check_init(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.initialized:
                raise RuntimeError("Instance wasn't initialized. Perhaps, you forgot to call .init()?")
            method(self, *args, **kwargs)

        return wrapper
