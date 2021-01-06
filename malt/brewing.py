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
    @classmethod
    def get_models(cls):
        Models = cls.Models.copy()
        Models['slug'] = cls.Model
        return Models

    @classmethod
    def get_all_read_kwargs(cls, meta, active):
        kwargs = cls.get_read_kwargs(meta)
        kwargs['slug'] = meta['slug']
        kwargs['active'] = active
        return kwargs

    @classmethod
    def get_all_write_kwargs(cls, user, meta, active):
        kwargs = cls.get_write_kwargs(user, meta)
        kwargs['slug'] = meta['slug']
        kwargs['active'] = active
        return kwargs

    def collapse(self, value):
        value = collapse(value)
        if not value:
            raise ValueError()
        return value

    def clean(self, meta):
        clean_meta = {}
        for key in self.get_models():
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

    def ferment(self, meta, data, sugars):
        self.print('File has an yeast.')
        self.print('type: ' + self.name)

        for key, Model in self.get_models().items():
            self.validate(Model, 'slug', meta[key])

        read_kwargs = self.get_all_read_kwargs(meta, False)

        object = self.Model()

        objects = self.process(object, data)

        with transaction.atomic():
            try:
                write_kwargs = self.get_all_write_kwargs(self.user, meta, False)
            except YeastError as error:
                self.exit(error)

            for name, value in write_kwargs.items():
                setattr(object, name, value)

            self.Model.objects.filter(**read_kwargs).delete()

            for object in objects:
                object.save()

        self.post_process(sugars)

        return reverse(self.name + '_draft', kwargs=meta)

    def referment(self, meta, sugars, active):
        self.print('Page is editable.')
        self.print('type: ' + self.name)

        self.post_process(sugars)

        self.exit('Referment not implemented.')


class YAMLYeast(Yeast):
    def parse(self, data):
        try:
            parsed_data = yaml.load(data, Loader=yaml.Loader)
        except YAMLError as error:
            self.exit('Content is not valid YAML: {}.'.format(error))
        self.print('Content is valid YAML.')
        if not isinstance(parsed_data, dict):
            self.exit('Content is not a dictionary.')
        self.print('Content is a dictionary.')
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

    def get(self, data, key, type, Model):
        self.print('Trying to get value of {}.'.format(key))
        value = data.get(key)
        if value is None:
            self.print('Value not found, but not required.')
        else:
            value = self.check(value, type)
            self.validate(Model, key, value)
        return value

    def get_or_exit(self, data, key, type, Model):
        self.print('Getting value of {}.'.format(key))
        try:
            value = data[key]
        except KeyError:
            self.exit('Value not found.')
        value = self.check(value, type)
        self.validate(Model, key, value)
        return value

    def iterate(self, data, key, type):
        self.print('Trying to iterate over {}.'.format(key))
        try:
            value = data[key]
        except KeyError:
            return
        value = self.check(value, list)
        for i, element in enumerate(value):
            self.print('Processing index {}.'.format(i))
            yield self.check(element, type)
