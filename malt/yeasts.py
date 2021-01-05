import datetime

from malt.models import Calendar, Course, CalendarCancelation
from malt.brewing import YAMLYeast


class CalendarYeast(YAMLYeast):
    Model = Calendar
    name = 'calendar'

    @classmethod
    def get_cancelations(cls, object):
        return CalendarCancelation.objects.filter(calendar=object)

    @classmethod
    def get_queries(cls, object):
        return [
            cls.get_cancelations(object),
        ]

    @classmethod
    def update_kwargs(cls, kwargs):
        kwargs['user__username'] = kwargs.pop('user')

    @classmethod
    def update_context_data(self, context, object):
        context['cancelations'] = self.get_cancelations(object)

    def process(self, meta, data):
        model_kwargs = {
            'user': self.user,
        }

        view_kwargs = {
            'user': self.user.get_username(),
        }

        root = self.parse(data)
        title = self.get_or_exit(root, 'title', str, self.Model)
        begin_date = self.get_or_exit(root, 'begin_date', datetime.date, self.Model)
        end_date = self.get_or_exit(root, 'end_date', datetime.date, self.Model)
        if begin_date > end_date:
            self.exit('Begin date later than end date.')

        defaults = {
            'title': title,
            'begin_date': begin_date,
            'end_date': end_date,
        }
        objects = self.pre_process(model_kwargs, defaults)

        dates = set()
        for cancelation in self.iterate(root, 'cancelations', dict):
            date = self.get_or_exit(cancelation, 'date', datetime.date, CalendarCancelation)
            if date in dates:
                self.exit('Date repeated.')
            if date < begin_date or date > end_date:
                self.exit('Date outside calendar interval.')
            title = self.get_or_exit(cancelation, 'title', str, CalendarCancelation)
            dates.add(date)

            kwargs = {
                'calendar': objects[0],
                'date': date,
                'title': title,
            }
            objects.append(CalendarCancelation(**kwargs))

        return model_kwargs, view_kwargs, objects


class CourseYeast(YAMLYeast):
    Model = Course
    name = 'course'
