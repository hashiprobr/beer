from django.urls import reverse

from malt.brewing import Yeast


class NodeYeast(Yeast):
    expected = [
        ('course_uid', str),
        ('uid', str),
    ]

    def ferment(self, sugars=[]):
        return reverse('index')

    def referment(self, sugars):
        return reverse('index')
