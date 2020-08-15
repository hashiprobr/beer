from malt.models import Calendar
from malt.brewing import YAMLYeast


class CalendarYeast(YAMLYeast):
    Model = Calendar
    name = 'calendar'

    expected = [
        'slug',
    ]

    def process(self, data):
        pass

    def post_process(self, sugars):
        pass


class CourseYeast(YAMLYeast):
    name = 'course'
