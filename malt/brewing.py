import yaml

from django.db import transaction
from django.urls import reverse
from yaml import YAMLError


class BrewError(Exception):
    def __init__(self, history, message):
        self.history = history
        self.message = message


class YeastError(Exception):
    pass


class Brewer:
    def __init__(self, user, history):
        self.user = user
        self.history = history

    def print(self, message):
        self.history.append(message)

    def exit(self, message):
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

    def describe(self, meta):
        self.print('type: ' + self.name)
        for key, value in meta.items():
            self.print('{}: {}'.format(key, value))

    def authenticate(self):
        if self.object.user != self.user:
            self.exit('You do not have permission to edit.')

    def get_kwargs(self, meta):
        return {}

    def new_kwargs(self, meta):
        return {}

    def url_kwargs(self):
        return {
            'slug': self.object.slug,
        }

    def get_url(self):
        if self.object.active:
            view_name = self.name
        else:
            view_name = self.name + '_draft'
        return reverse(view_name, kwargs=self.url_kwargs())

    def get_object(self, active, meta):
        kwargs = {
            'slug': meta['slug'],
            'active': active,
        }
        kwargs.update(self.get_kwargs(meta))
        return self.Model.objects.get(**kwargs)

    def pre_process(self, meta_data):
        self.exit('Pre-processing not implemented.')

    def process(self, data):
        self.exit('Processing not implemented.')

    def post_process(self, sugars):
        self.exit('Post-processing not implemented.')

    def ferment(self, meta, data, sugars):
        self.print('File has an yeast!')
        self.describe(meta)

        with transaction.atomic():
            try:
                self.object = self.get_object(False, meta)
            except self.Model.DoesNotExist:
                kwargs = {
                    'user': self.user,
                    'slug': meta['slug'],
                    'active': False,
                }
                kwargs.update(self.get_kwargs(meta))
                self.object = self.Model.objects.create(**kwargs)

        self.authenticate()

        if self.also_expected or self.optional:
            lines = data.split('\n')
            found = False

            for i, line in enumerate(lines):
                if line.strip() == '...':
                    self.print('Separator found in line {}.'.format(i + 1))
                    found = True

                    try:
                        meta_data = yaml.load('\n'.join(lines[:i]), Loader=yaml.Loader)
                    except YAMLError as error:
                        self.exit('Preamble is not valid YAML: {}'.format(error))
                    self.print('Preamble is valid YAML.')

                    if not isinstance(meta_data, dict):
                        self.exit('Preamble is not a dictionary.')
                    self.print('Preamble is a dictionary.')

                    if self.also_expected:
                        clean_meta_data = {}
                        for key, type in self.also_expected.items():
                            try:
                                value = meta_data.pop(key)
                            except KeyError:
                                self.exit('This yeast requires a value for {}.'.format(key))
                            if not isinstance(value, type):
                                self.exit('The value of {} must be of type {}.'.format(key, type.__name__))
                            clean_meta_data[key] = value

                        self.pre_process(clean_meta_data)

                    for key, value in meta_data.items():
                        try:
                            type = self.optional[key]
                        except KeyError:
                            self.exit('Unrecognized argument {}.'.format(key))
                        if not isinstance(value, type):
                            self.exit('The value of {} must be of type {}.'.format(key, type.__name__))
                        try:
                            method = getattr(self, 'process_' + key)
                        except AttributeError:
                            self.exit('Processing of {} not implemented.'.format(key))
                        method(value)

                    data = '\n'.join(lines[(i + 1):])
                    break

            if not found:
                self.print('Separator not found.')
                if self.also_expected:
                    self.exit('Separator expected because this yeast requires: {}.'.format(', '.join(self.also_expected)))

        self.process(data)
        self.object.save()
        self.post_process(sugars)
        return self.get_url()

    def referment(self, meta, sugars):
        self.print('File does not have an yeast but page is editable.')
        self.describe(meta)
        self.object = self.get_object(meta['active'], meta)
        self.authenticate()
        self.post_process(sugars)
        return self.get_url()


class YAMLYeast(Yeast):
    def parse(self, data):
        try:
            parsed_data = yaml.load(data, Loader=yaml.Loader)
        except YAMLError as error:
            self.exit('Content is not valid YAML: {}'.format(error))
        self.print('Content is valid YAML.')
        return parsed_data

    def parse_dict(self, data):
        parsed_data = self.parse(data)
        if not isinstance(parsed_data, dict):
            self.exit('Content is not a dictionary.')
        self.print('Content is a dictionary.')
        return parsed_data

    def parse_list(self, data):
        parsed_data = self.parse(data)
        if not isinstance(parsed_data, list):
            self.exit('Content is not a list.')
        self.print('Content is a list.')
        return parsed_data

    def check(self, value, type):
        if not isinstance(value, type):
            self.exit('The value must be of type {}.'.format(type.__name__))

    def get(self, data, key, type):
        self.print('Getting value of {}.'.format(key))
        value = data.get(key)
        if value is None:
            self.print('Value not found, but not required.')
        else:
            self.check(value, type)
        return value

    def get_or_exit(self, data, key, type):
        self.print('Getting value of {}.'.format(key))
        try:
            value = data[key]
        except KeyError:
            self.exit('Value not found.')
        self.check(value, type)
        return value

    def iterate(self, value, type):
        for i, element in enumerate(value):
            self.print('Processing element at {}.'.format(i))
            self.check(element, type)
            yield element
