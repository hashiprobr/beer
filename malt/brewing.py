class BrewError(Exception):
    def __init__(self, history, message):
        self.history = history
        self.message = message


class YeastError(Exception):
    pass


class Brewer:
    def __init__(self):
        self.history = []

    def raiseBrewError(self, message):
        raise BrewError(self.history, message)


class Yeast(Brewer):
    expected = []

    @classmethod
    def clean(cls, meta):
        clean_meta = {}
        for key, type in cls.expected:
            try:
                value = meta[key]
            except KeyError:
                raise YeastError('expected ' + key)
            if not isinstance(value, type):
                raise YeastError('{} must be {}'.format(key, type.__name__))
            clean_meta[key] = value
        return clean_meta

    def __init__(self, meta, data=None, name=None):
        super().__init__()
        self.meta = meta
        self.data = data
        self.name = name
