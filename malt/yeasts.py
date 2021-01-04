import datetime

from malt.models import Calendar, Course, CalendarCancelation
from malt.brewing import YAMLYeast


class CalendarYeast(YAMLYeast):
    Model = Calendar
    name = 'calendar'

    @classmethod
    def update_kwargs(cls, kwargs):
        kwargs['user__username'] = kwargs.pop('username')

    @classmethod
    def update_context_data(self, context, object):
        context['cancelations'] = CalendarCancelation.objects.filter(calendar=object)

    def process(self, meta, data):
        root = self.parse_dict(data)

        begin_date = self.get_or_exit(root, 'begin_date', datetime.date)
        self.validate(self.Model, 'begin_date', begin_date)

        end_date = self.get_or_exit(root, 'end_date', datetime.date)
        self.validate(self.Model, 'end_date', end_date)

        if begin_date > end_date:
            self.exit('Begin date later than end date.')

        model_kwargs = {'user': self.user}
        defaults = {'begin_date': begin_date, 'end_date': end_date}
        objects = self.pre_process(model_kwargs, defaults)
        view_kwargs = {'username': self.user.get_username()}

        cancelations = self.get(root, 'cancelations', list)
        if cancelations is not None:
            dates = set()
            for cancelation in self.iterate(cancelations, dict):
                date = self.get_or_exit(cancelation, 'date', datetime.date)
                self.validate(CalendarCancelation, 'date', date)
                if date in dates:
                    self.exit('Date repeated.')
                if date < begin_date or date > end_date:
                    self.exit('Date outside calendar interval.')
                dates.add(date)

                title = self.get_or_exit(cancelation, 'title', str)
                self.validate(CalendarCancelation, 'title', title)

                objects.append(CalendarCancelation(calendar=objects[0], date=date, title=title))

        return model_kwargs, objects, view_kwargs


class CourseYeast(YAMLYeast):
    Model = Course
    name = 'course'
