import yaml

from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse
from yaml import YAMLError

from beer.utils import collapse


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

    @classmethod
    def update_kwargs(cls, kwargs):
        pass

    @classmethod
    def update_context_data(self, context, object):
        pass

    def collapse(self, value):
        value = collapse(value)
        if not value:
            raise ValueError()
        return value

    def clean(self, meta):
        clean_meta = {}
        for key in ['slug', 'title'] + self.expected:
            try:
                value = meta[key]
            except KeyError:
                raise YeastError('expected ' + key)
            if not isinstance(value, str):
                raise YeastError(key + ' must be of type str')
            try:
                clean_meta[key] = self.collapse(value)
            except ValueError:
                raise YeastError(key + ' cannot be blank')
        return clean_meta

    def validate(self, Model, key, value):
        self.print('{}: {}'.format(key, value))
        for validator in getattr(Model, key).field.validators:
            try:
                validator(value)
            except ValidationError as error:
                self.exit(error.messages[0])

    def pre_process(self, kwargs, defaults):
        return [self.Model(**kwargs, **defaults)]

    def process(self, meta, data):
        self.exit('Processing not implemented.')

    def post_process(self, sugars):
        pass

    def ferment(self, meta, data, sugars):
        self.print('File has an yeast!')

        self.print('type: ' + self.name)

        slug = meta.pop('slug')
        self.validate(self.Model, 'slug', slug)

        active = False

        title = meta.pop('title')
        self.validate(self.Model, 'title', title)

        model_kwargs, objects, view_kwargs = self.process(meta, data)
        model_kwargs['slug'] = slug
        model_kwargs['active'] = active
        setattr(objects[0], 'slug', slug)
        setattr(objects[0], 'active', active)
        setattr(objects[0], 'title', title)
        view_kwargs['slug'] = slug

        with transaction.atomic():
            self.Model.objects.filter(**model_kwargs).delete()
            for object in objects:
                object.save()

        self.post_process(sugars)

        return reverse(self.name + '_draft', kwargs=view_kwargs)

    def referment(self, meta, sugars, active):
        self.print('File does not have an yeast but page is editable.')

        self.post_process(sugars)

        self.exit('mock')


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
        if type is str:
            try:
                value = self.collapse(value)
            except ValueError:
                self.exit('The value cannot be blank.')
        return value

    def get(self, data, key, type):
        self.print('Trying to get value of {}.'.format(key))
        value = data.get(key)
        if value is None:
            self.print('Value not found, but not required.')
        else:
            value = self.check(value, type)
        return value

    def get_or_exit(self, data, key, type):
        self.print('Getting value of {}.'.format(key))
        try:
            value = data[key]
        except KeyError:
            self.exit('Value not found.')
        return self.check(value, type)

    def iterate(self, value, type):
        for i, element in enumerate(value):
            self.print('Processing element at {}.'.format(i))
            yield self.check(element, type)
