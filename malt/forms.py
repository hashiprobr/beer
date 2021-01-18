from django import forms
from django.core.exceptions import ValidationError

from .models import FolderAsset
from .brewing import YeastError


class UserForm(forms.Form):
    file = forms.FileField(label='List')
    domain = forms.CharField(label='Domain', required=False)
    promote = forms.BooleanField(label='Promote all users in the list.', required=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def raiseValidationErrorFile(self, i, message):
        raise ValidationError({'file': 'Line {}: {}.'.format(i, message)})

    def clean(self):
        data = super().clean()

        if self.request.skip:
            for errorlist in self.errors.values():
                errorlist.clear()
            raise ValidationError({'file': 'The file cannot have more than 25MB.'})

        if 'file' in data:
            content = data['file'].read()
            try:
                text = content.decode()
            except UnicodeDecodeError:
                raise ValidationError({'file': 'The file cannot be binary.'})

            self.users = {}

            for i, line in enumerate(text.split('\n'), 1):
                words = line.strip().split()
                if words:
                    username = words[0]

                    if username in self.users:
                        self.raiseValidationErrorFile(i, 'username already seen in line {}'.format(self.users[username]['line']))

                    defaults = {
                        'line': i,
                    }

                    if data['domain']:
                        if len(words) > 1:
                            if '@' in words[1]:
                                self.raiseValidationErrorFile(i, 'the second word looks like an email, but should be a first name because you specified a domain')
                        else:
                            words.append('')

                        defaults['email'] = '{}@{}'.format(username, data['domain'])
                        defaults['first_name'] = words[1]
                        defaults['last_name'] = ' '.join(words[2:])
                    else:
                        if len(words) > 1:
                            if '@' not in words[1]:
                                self.raiseValidationErrorFile(i, 'the second word does not look like an email, but should be one because you did not specify a domain')
                        else:
                            self.raiseValidationErrorFile(i, 'must have at least an username and an email')

                        defaults['email'] = words[1]
                        defaults['first_name'] = words[2] if len(words) > 2 else ''
                        defaults['last_name'] = ' '.join(words[3:])

                    self.users[username] = defaults

            if not self.users:
                raise ValidationError({'file': 'The file cannot be empty.'})

            for defaults in self.users.values():
                del defaults['line']

        return data


class AssetForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.Asset = kwargs.pop('Asset')
        self.user = kwargs.pop('user')
        self.names = kwargs.pop('names')
        super().__init__(*args, **kwargs)


class AssetAddForm(AssetForm):
    def __init__(self, *args, **kwargs):
        self.parent = kwargs.pop('parent')
        super().__init__(*args, **kwargs)
        self.fields['name'] = forms.CharField(validators=self.Asset.name.field.validators)

    def clean(self):
        data = super().clean()
        if 'name' in data:
            self.name = data['name']
            if self.Asset.objects.filter(user=self.user, parent=self.parent, name=self.name, trashed=False).exists():
                raise ValidationError('An asset with that path already exists.')
        return data


class AssetMoveForm(AssetForm):
    def __init__(self, *args, **kwargs):
        self.asset = kwargs.pop('asset')
        super().__init__(*args, **kwargs)
        self.fields['path'] = forms.CharField()

    def clean(self):
        data = super().clean()

        if 'path' in data:
            self.path = data['path']
            if self.path.startswith('/') or self.path.endswith('/'):
                raise ValidationError({'path': 'This value cannot start or end with slashes.'})

            names = self.path.split('/')

            self.parent = None
            for name in names[:-1]:
                try:
                    self.parent = FolderAsset.objects.get(user=self.user, parent=self.parent, name=name, trashed=False)
                except FolderAsset.DoesNotExist:
                    raise ValidationError('The parent does not exist.')
                if self.parent == self.asset:
                    raise ValidationError('The asset cannot be moved inside itself.')

            self.name = names[-1]
            for validator in self.Asset.name.field.validators:
                try:
                    validator(self.name)
                except ValidationError as error:
                    raise ValidationError(error.messages[0])

        return data


class YeastForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.Yeast = kwargs.pop('Yeast')
        self.user = kwargs.pop('user')
        self.active = kwargs.pop('active')
        self.old_meta = kwargs['initial']
        super().__init__(*args, **kwargs)
        for key, Model in self.Yeast.get_models().items():
            self.fields[key] = forms.SlugField(validators=Model.slug.field.validators)

    def get_fields(self):
        for key in self.fields:
            yield self[key]

    def clean(self):
        data = super().clean()

        if len(data) == len(self.old_meta) - 1:
            self.meta = data.copy()
            self.meta['user'] = self.old_meta['user']

            if self.meta != self.old_meta:
                kwargs = self.Yeast.get_all_read_kwargs(self.meta, self.active)
                if self.Yeast.Model.objects.filter(**kwargs).exists():
                    raise ValidationError('An yeast with that path already exists.')

            try:
                self.kwargs = self.Yeast.get_all_write_kwargs(self.user, self.meta, self.active)
            except YeastError as error:
                raise ValidationError(error)

        return data
