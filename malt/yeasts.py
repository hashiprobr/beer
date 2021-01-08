import datetime

from malt.models import Calendar, Course, CalendarCancelation
from malt.brewing import YAMLYeast


class CalendarYeast(YAMLYeast):
    Model = Calendar
    name = 'calendar'

    Models = {}

    @classmethod
    def get_read_kwargs(cls, meta):
        return {
            'user__username': meta['user'],
        }

    @classmethod
    def get_write_kwargs(cls, user, meta):
        return {
            'user': user,
        }

    @classmethod
    def get_cancelations(cls, object):
        return CalendarCancelation.objects.filter(calendar=object)

    @classmethod
    def get_context_data(cls, object):
        return {
            'cancelations': cls.get_cancelations(object),
        }

    @classmethod
    def get_child_filters(cls, object):
        return [
            cls.get_cancelations(object),
        ]

    def process(self, object, data):
        root = self.parse(data)
        title = self.get_or_exit(root, 'title', str, self.Model)
        begin_date = self.get_or_exit(root, 'begin_date', datetime.date, self.Model)
        end_date = self.get_or_exit(root, 'end_date', datetime.date, self.Model)
        if begin_date > end_date:
            self.exit('Begin date later than end date.')

        object.title = title
        object.begin_date = begin_date
        object.end_date = end_date

        objects = [object]

        dates = set()
        for cancelation in self.iterate(root, 'cancelations', dict):
            date = self.get_or_exit(cancelation, 'date', datetime.date, CalendarCancelation)
            if date in dates:
                self.exit('Date repeated.')
            if date < begin_date or date > end_date:
                self.exit('Date outside calendar interval.')
            title = self.get_or_exit(cancelation, 'title', str, CalendarCancelation)
            dates.add(date)

            cancelation = CalendarCancelation()
            cancelation.calendar = object
            cancelation.date = date
            cancelation.title = title

            objects.append(cancelation)

        return objects

    def post_process(self, sugars):
        pass


class CourseYeast(YAMLYeast):
    Model = Course
    name = 'course'
