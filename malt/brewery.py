import yaml

from yaml import YAMLError

from .brewing import YeastError, Brewer
from .enzymes import EnzymeError, ZipEnzyme, TarEnzyme
from .yeasts import CourseYeast


ENZYMES = [
    ZipEnzyme(),
    TarEnzyme(),
]

YEASTS = {
    'course': CourseYeast,
}


class GypsyBrewer(Brewer):
    def __init__(self, history):
        self.history = history


class Grower(GypsyBrewer):
    def grow(self, content, Yeasts):
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            self.history.append('File seems to be binary.')
            return None
        self.history.append('File does not seem to be binary.')

        lines = text.split('\n')

        for i, line in enumerate(lines):
            if line.strip() == '...':
                self.history.append('Separator found in line {}.'.format(i + 1))

                try:
                    meta = yaml.load('\n'.join(lines[:i]), Loader=yaml.Loader)
                except YAMLError as error:
                    self.history.append('Preamble is not valid YAML: {}'.format(error))
                    return None
                self.history.append('Preamble is valid YAML.')

                if not isinstance(meta, dict):
                    self.history.append('Preamble is not a dictionary.')
                    return None
                self.history.append('Preamble is a dictionary.')

                try:
                    type = meta.pop('type')
                except KeyError:
                    self.history.append('Preamble does not have a type.')
                    return None
                self.history.append('Preamble has a type.')

                try:
                    Yeast = Yeasts[type]
                except KeyError:
                    self.history.append('Preamble type {} does not exist.'.format(type))
                    return None
                self.history.append('Preamble type {} exists.'.format(type))

                yeast = Yeast()

                try:
                    clean_meta = yeast.clean(meta)
                except YeastError as error:
                    self.history.append('Preamble does not describe a valid {}: {}'.format(type, error))
                    return None
                self.history.append('Preamble describes a valid {}.'.format(type))

                return yeast, clean_meta, '\n'.join(lines[(i + 1):])

        self.history.append('Separator not found.')
        return None


class Primer(GypsyBrewer):
    def prime(self, meta, sugars, Yeasts):
        try:
            type = meta.pop('view_name')
        except KeyError:
            self.raiseBrewError('Page not found.')

        try:
            Yeast = Yeasts[type]
        except KeyError:
            self.raiseBrewError('File does not have an yeast and page is not editable.')

        yeast = Yeast()

        try:
            clean_meta = yeast.clean(meta)
        except YeastError as error:
            self.raiseBrewError('Page not valid.')

        return yeast.referment(clean_meta, sugars)


class Brewery(Brewer):
    def brew(self, files, meta, enzymes=ENZYMES, Yeasts=YEASTS, Grower=Grower, Primer=Primer):
        grower = Grower(self.history)
        primer = Primer(self.history)

        if len(files) != 1:
            self.raiseBrewError('One file is expected and this file cannot have more than 25MB.')

        try:
            file = files['file']
        except KeyError:
            self.raiseBrewError('The field name must be file.')

        try:
            date = int(int(meta.pop('date')) / 1000)
        except (KeyError, ValueError):
            self.raiseBrewError('A timestamp is expected and its field name must be date.')

        name = file.name
        content = file.read()

        self.history.append('Received {}.'.format(name))

        for enzyme in enzymes:
            try:
                members = enzyme.convert(content)
            except EnzymeError as error:
                self.history.append('File is not a valid {} archive: {}'.format(enzyme.extension, error))
                continue
            self.history.append('File is a valid {} archive.'.format(enzyme.extension))

            inputs = {}
            sugars = []

            for date, name, content in members:
                self.history.append('Extracted {}.'.format(name))

                input = grower.grow(content, Yeasts)

                if input is None:
                    sugars.append((date, name, content))
                else:
                    inputs[name] = input

            if len(inputs) > 1:
                self.raiseBrewError('Multiple yeasts found: ' + ', '.join(inputs))

            if inputs:
                yeast, clean_meta, data = next(iter(inputs.values()))

                return yeast.ferment(clean_meta, data, sugars)
            else:
                return primer.prime(meta, sugars, Yeasts)

        input = grower.grow(content, Yeasts)

        if input is None:
            return primer.prime(meta, [(date, name, content)], Yeasts)
        else:
            yeast, clean_meta, data = input

            return yeast.ferment(clean_meta, data, [])
