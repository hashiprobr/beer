from django import forms
from django.core.exceptions import ValidationError

from .models import Asset


class UserForm(forms.Form):
    file = forms.FileField(label='List')
    domain = forms.CharField(label='Domain', required=False)
    promote = forms.BooleanField(label='Promote all users in the list.', required=False)

    def raiseValidationErrorFile(self, i, message):
        raise ValidationError({'file': 'Line {}: {}.'.format(i, message)})

    def clean(self):
        data = super().clean()

        try:
            file = data['file']
        except KeyError:
            for errorlist in self.errors.values():
                errorlist.clear()
            raise ValidationError({'file': 'This field is required and the file cannot have more than 25MB.'})

        content = file.read()
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


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name']

    def __init__(self, *args, **kwargs):
        self.Asset = kwargs.pop('Asset')
        self.user = kwargs.pop('user')
        self.parent = kwargs.pop('parent')
        self.child = kwargs.pop('child')
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        if 'name' in data:
            name = data['name']
            if self.child is None or self.child.name != name:
                if self.Asset.objects.filter(user=self.user, parent=self.parent, name=name).exists():
                    raise ValidationError({'name': 'An asset with that name already exists.'})
        return data
