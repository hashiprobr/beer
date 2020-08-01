from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class UserAddForm(forms.Form):
    file = forms.FileField(label='List')
    domain = forms.CharField(label='Domain', required=False)
    promote = forms.BooleanField(label='Promote all users in the list.', required=False)

    def raiseValidationErrorFile(self, i, message):
        raise ValidationError({'file': 'Line {}: {}.'.format(i, message)})

    def clean(self):
        data = super().clean()

        if 'file' not in data:
            for errorlist in self.errors.values():
                errorlist.clear()
            raise ValidationError({'file': 'This field is required and the file cannot have more than 25MB.'})

        content = data['file'].read()
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            raise ValidationError({'file': 'The file cannot be binary.'})

        self.users = {}

        for i, line in enumerate(text.split('\n'), 1):
            words = line.strip().split()
            if words:
                username = words[0]

                if username in self.users:
                    self.raiseValidationErrorFile(i, 'username already seen in line {}'.format(self.users[username]['line']))
                if User.objects.filter(username=username).exists():
                    self.raiseValidationErrorFile(i, 'username already exists')

                kwargs = {
                    'line': i,
                }

                if data['domain']:
                    if len(words) < 2:
                        self.raiseValidationErrorFile(i, 'must have at least an username and a first name')
                    if '@' in words[1]:
                        self.raiseValidationErrorFile(i, 'the second word looks like an email, but should be a first name because you specified a domain')

                    kwargs['email'] = '{}@{}'.format(username, data['domain'])
                    kwargs['first_name'] = words[1]
                    kwargs['last_name'] = ' '.join(words[2:])
                else:
                    if len(words) < 3:
                        self.raiseValidationErrorFile(i, 'must have at least an username, an email, and a first name')
                    if '@' not in words[1]:
                        self.raiseValidationErrorFile(i, 'the second word does not look like an email, but should be one because you did not specify a domain')

                    kwargs['email'] = words[1]
                    kwargs['first_name'] = words[2]
                    kwargs['last_name'] = ' '.join(words[3:])

                self.users[username] = kwargs

        for kwargs in self.users.values():
            del kwargs['line']

        self.promote = data['promote']

        return data
