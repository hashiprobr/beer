import yaml

from yaml import YAMLError

from .brewing import YeastError, Brewer
from .enzymes import EnzymeError, ZipEnzyme, TarEnzyme
from .yeasts import CalendarYeast, CourseYeast

from lager.yeasts import SheetYeast

from ale.yeasts import NodeYeast


ENZYMES = [
    ZipEnzyme(),
    TarEnzyme(),
]

YEASTS = {Yeast.name: Yeast for Yeast in [
    CalendarYeast,
    CourseYeast,
    SheetYeast,
    NodeYeast,
]}


class Grower(Brewer):
    def grow(self, content, Yeasts):
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            self.print('File seems to be binary.')
            return None
        self.print('File does not seem to be binary.')

        lines = text.split('\n')

        for i, line in enumerate(lines):
            if line.strip() == '...':
                self.print('Separator found in line {}.'.format(i + 1))

                try:
                    meta = yaml.load('\n'.join(lines[:i]), Loader=yaml.Loader)
                except YAMLError as error:
                    self.print('Preamble is not valid YAML: {}'.format(error))
                    return None
                self.print('Preamble is valid YAML.')

                if not isinstance(meta, dict):
                    self.print('Preamble is not a dictionary.')
                    return None
                self.print('Preamble is a dictionary.')

                try:
                    type = meta.pop('type')
                except KeyError:
                    self.print('Preamble does not have a type.')
                    return None
                self.print('Preamble has a type.')

                try:
                    Yeast = Yeasts[type]
                except KeyError:
                    self.print('Preamble type {} does not exist.'.format(type))
                    return None
                self.print('Preamble type {} exists.'.format(type))

                yeast = Yeast(self.user, [])

                try:
                    clean_meta = yeast.clean(meta)
                except YeastError as error:
                    self.print('Preamble does not describe a valid {}: {}'.format(type, error))
                    return None
                self.print('Preamble describes a valid {}.'.format(type))

                return yeast, clean_meta, '\n'.join(lines[(i + 1):])

        self.print('Separator not found.')
        return None


class Primer(Brewer):
    def prime(self, meta, sugars, Yeasts):
        try:
            type = meta.pop('view_name')
        except KeyError:
            self.exit('Page not found.')

        if type.endswith('_draft'):
            type = type[:-6]
            active = False
        else:
            active = True

        try:
            Yeast = Yeasts[type]
        except KeyError:
            self.exit('File does not have an yeast and page is not editable.')

        yeast = Yeast(self.user, [])

        try:
            clean_meta = yeast.clean(meta)
        except YeastError as error:
            self.exit('Page not valid.')

        clean_meta['active'] = active

        return yeast.referment(clean_meta, sugars)


class Brewery(Brewer):
    def brew(self, files, meta, enzymes=ENZYMES, Yeasts=YEASTS, Grower=Grower, Primer=Primer):
        grower = Grower(self.user, self.history)
        primer = Primer(self.user, self.history)

        if len(files) != 1:
            self.exit('One file is expected and this file cannot have more than 25MB.')

        try:
            file = files['file']
        except KeyError:
            self.exit('The field name must be file.')

        try:
            date = int(int(meta.pop('date')) / 1000)
        except (KeyError, ValueError):
            self.exit('A timestamp is expected and its field name must be date.')

        name = file.name
        content = file.read()

        self.print('Received {}.'.format(name))

        for enzyme in enzymes:
            try:
                members = enzyme.convert(content)
            except EnzymeError as error:
                self.print('File is not a valid {} archive: {}'.format(enzyme.extension, error))
                continue
            self.print('File is a valid {} archive.'.format(enzyme.extension))

            inputs = {}
            sugars = []

            for date, name, content in members:
                self.print('Extracted {}.'.format(name))

                input = grower.grow(content, Yeasts)

                if input is None:
                    sugars.append((date, name, content))
                else:
                    inputs[name] = input

            if len(inputs) > 1:
                self.exit('Multiple yeasts found: ' + ', '.join(inputs))

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
