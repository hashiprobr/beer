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

    def clean(self, meta):
        clean_meta = {}
        for key in self.expected:
            try:
                value = meta[key]
            except KeyError:
                raise YeastError('expected ' + key)
            if not isinstance(value, str):
                raise YeastError(key + ' must be a string')
            clean_meta[key] = value
        return clean_meta
