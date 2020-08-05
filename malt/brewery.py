import yaml

from yaml import YAMLError

from .brewing import YeastError, Brewer
from .enzymes import EnzymeError, ZipEnzyme, TarEnzyme


ENZYMES = [
    ZipEnzyme(),
    TarEnzyme(),
]

YEASTS = {
}


class Brewery(Brewer):
    def grow(self, content, yeasts=YEASTS):
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
                    yeast = yeasts[type]
                except KeyError:
                    self.history.append('Preamble type {} does not exist.'.format(type))
                    return None
                self.history.append('Preamble type {} exists.'.format(type))

                try:
                    clean_meta = yeast.clean(meta)
                except YeastError as error:
                    self.history.append('Preamble does not describe a valid {}: {}'.format(type, error))
                    return None
                self.history.append('Preamble describes a valid {}.'.format(type))

                return yeast, clean_meta, '\n'.join(lines[(i + 1):])

        self.history.append('Separator not found.')
        return None

    def prime(self, meta, sugars, yeasts=YEASTS):
        try:
            type = meta.pop('view_name')
        except KeyError:
            self.raiseBrewError('Page not found.')

        try:
            yeast = yeasts[type]
        except KeyError:
            self.raiseBrewError('File does not have an yeast and page is not editable.')

        try:
            clean_meta = yeast.clean(meta)
        except YeastError as error:
            self.raiseBrewError('Page not valid.')

        return yeast.referment(clean_meta, sugars)

    def brew(self, files, meta, enzymes=ENZYMES, yeasts=YEASTS):
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
            else:
                self.history.append('File is a valid {} archive.'.format(enzyme.extension))

                inputs = {}
                sugars = []

                for date, name, content in members:
                    self.history.append('Extracted {}.'.format(name))

                    input = self.grow(content, yeasts)

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
                    return self.prime(meta, sugars, yeasts)

        input = self.grow(content, yeasts)

        if input is None:
            return self.prime(meta, [(date, name, content)], yeasts)
        else:
            yeast, clean_meta, data = input

            return yeast.ferment(clean_meta, data, [])
