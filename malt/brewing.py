import yaml

from yaml import YAMLError


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
    also_expected = {}
    optional = {}

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

    def pre_process(self, meta):
        self.raiseBrewError('Pre-processing not implemented.')

    def post_pre_process(self, meta_data):
        self.raiseBrewError('Post-pre-processing not implemented.')

    def process(self, meta):
        self.raiseBrewError('Processing not implemented.')

    def post_process(self, meta):
        self.raiseBrewError('Post-processing not implemented.')

    def ferment(self, meta, data, sugars):
        self.history.append('File has an yeast!')
        self.history.append('type: ' + self.name)
        for key, value in meta.items():
            self.history.append('{}: {}'.format(key, value))

        url = self.pre_process(meta)

        if self.also_expected or self.optional:
            lines = data.split('\n')
            found = False

            for i, line in enumerate(lines):
                if line.strip() == '...':
                    self.history.append('Separator found in line {}.'.format(i + 1))
                    found = True

                    try:
                        meta_data = yaml.load('\n'.join(lines[:i]), Loader=yaml.Loader)
                    except YAMLError as error:
                        self.raiseBrewError('Preamble is not valid YAML: {}'.format(error))
                    self.history.append('Preamble is valid YAML.')

                    if not isinstance(meta_data, dict):
                        self.raiseBrewError('Preamble is not a dictionary.')
                    self.history.append('Preamble is a dictionary.')

                    clean_meta_data = {}
                    for key, type in self.also_expected.items():
                        try:
                            value = meta_data.pop(key)
                        except KeyError:
                            self.raiseBrewError('This yeast requires a value for {}.'.format(key))
                        if not isinstance(value, type):
                            self.raiseBrewError('The value for {} must be of type {}.'.format(key, type.__name__))
                        clean_meta_data[key] = value

                    self.post_pre_process(clean_meta_data)

                    for key, value in meta_data.items():
                        if key in self.optional:
                            type = self.optional[key]
                            if not isinstance(value, type):
                                self.raiseBrewError('The value for {} must be of type {}.'.format(key, type.__name__))
                            try:
                                method = getattr(self, 'process_' + key)
                            except AttributeError:
                                self.raiseBrewError('Processing of {} not implemented.'.format(key))
                            method(value)
                        else:
                            self.raiseBrewError('Unrecognized argument {}.'.format(key))

                    data = '\n'.join(lines[(i + 1):])
                    break

            if not found:
                self.history.append('Separator not found.')
                if self.also_expected:
                    self.raiseBrewError('Separator expected because this yeast requires: {}.'.format(', '.join(self.also_expected)))

        self.process(data)
        self.post_process(sugars)
        return url

    def referment(self, meta, sugars):
        url = self.pre_process(meta)
        self.post_process(sugars)
        return url
