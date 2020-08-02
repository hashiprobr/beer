import yaml

from io import BytesIO

from yaml import YAMLError

from .brewing import YeastError, Brewer
from .enzymes import EnzymeError, ZipEnzyme, TarEnzyme

from ale.yeasts import NodeYeast


ENZYMES = [
    ZipEnzyme(),
    TarEnzyme(),
]

YEASTS = {
    'node': NodeYeast,
}


class Brewery(Brewer):
    def grow(self, name, content):
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            self.history.append('File seems to be binary.')
            return None
        self.history.append('File does not seem to be binary.')

        lines = text.split('\n')

        for i, line in enumerate(lines, 1):
            if line.strip() == '...':
                self.history.append('Separator found in line {}.'.format(i))

                try:
                    meta = yaml.load('\n'.join(lines[:i]))
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
                    Yeast = YEASTS[type]
                except KeyError:
                    self.history.append('Preamble type {} does not exist.'.format(type))
                    return None
                self.history.append('Preamble type {} exists.'.format(type))

                try:
                    clean_meta = Yeast.clean(meta)
                except YeastError as error:
                    self.history.append('Preamble does not describe a valid {}: {}'.format(type, error))
                    return None
                self.history.append('Preamble describes a valid {}.'.format(type))

                return Yeast(clean_meta, '\n'.join(lines[(i + 1):]), name)

        self.history.append('Separator not found.')
        return None

    def prime(self, meta, sugars):
        try:
            type = meta.pop('view_name')
        except KeyError:
            self.raiseBrewError('Page not found.')

        try:
            Yeast = YEASTS[type]
        except KeyError:
            self.raiseBrewError('File is not an yeast and page is not editable.')

        try:
            clean_meta = Yeast.clean(meta)
        except YeastError as error:
            self.raiseBrewError('Page not valid.')

        yeast = Yeast(clean_meta)

        return yeast.referment(sugars)

    def brew(self, files, meta):
        if len(files) != 1:
            self.raiseBrewError('One file is expected and this file cannot have more than 25MB.')

        try:
            file = files['file']
        except KeyError:
            self.raiseBrewError('The field name must be file.')

        name = file.name
        content = file.read()

        self.history.append('Received {}.'.format(name))

        for enzyme in ENZYMES:
            file = BytesIO(content)

            try:
                members = enzyme.convert(file)
            except EnzymeError as error:
                self.history.append('File is not a valid {} archive: {}'.format(enzyme.extension, error))
            else:
                self.history.append('File is a valid {} archive.'.format(enzyme.extension))

                yeasts = []
                sugars = []

                for name, content in members:
                    self.history.append('Extracted {}.'.format(name))

                    yeast = self.grow(name, content)

                    if yeast is None:
                        sugars.append((name, BytesIO(content)))
                    else:
                        yeasts.append(yeast)

                if len(yeasts) > 1:
                    self.raiseBrewError('Multiple yeasts found: ' + ', '.join(yeast.name for yeast in yeasts))

                if yeasts:
                    return yeasts[0].ferment(sugars)
                else:
                    return self.prime(meta, sugars)

        yeast = self.grow(name, content)

        if yeast is None:
            return self.prime(meta, [(name, BytesIO(content))])
        else:
            return yeast.ferment()
