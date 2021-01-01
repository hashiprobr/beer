from datetime import time

from django.contrib.auth import get_user_model
from django.db import models, transaction, IntegrityError
from django.db.models import F, Q
from shortuuid import uuid

from beer import public_storage

User = get_user_model()


class Weekday(models.IntegerChoices):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class PowerUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class Asset(models.Model):
    class Meta:
        abstract = True
        unique_together = [
            ('user', 'parent', 'name'),
        ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=22)

    def names(self):
        if self.parent is None:
            return []
        else:
            return [*self.parent.names(), self.parent.name]


class FolderAsset(Asset):
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True)


class FileAssetManager(models.Manager):
    def pop(self, kwargs):
        if 'uid' in kwargs:
            raise IntegrityError('uid not allowed in kwargs')
        if 'active' in kwargs:
            raise IntegrityError('active not allowed in kwargs')
        user = kwargs.pop('user', None)
        while True:
            uid = uuid()
            if not self.filter(user=user, uid=uid).exists():
                return user, uid

    @transaction.atomic
    def create(self, **kwargs):
        user, uid = self.pop(kwargs)
        return super().create(user=user, **kwargs, uid=uid)

    @transaction.atomic
    def get_or_create(self, **kwargs):
        user, uid = self.pop(kwargs)
        return super().get_or_create(user=user, **kwargs, defaults={'uid': uid})


class FileAsset(Asset):
    parent = models.ForeignKey(FolderAsset, on_delete=models.CASCADE, null=True)
    uid = models.CharField(max_length=22)
    active = models.BooleanField(default=False)
    objects = FileAssetManager()

    def key(self):
        return '{}/assets/{}'.format(self.user.get_username(), self.uid)

    def url(self):
        return public_storage.url(self.key())


class YeastModel(models.Model):
    class Meta:
        abstract = True

    slug = models.SlugField(max_length=22)
    title = models.CharField(max_length=44)


class BaseCalendar(YeastModel):
    class Meta:
        abstract = True
        unique_together = [
            ('user', 'slug'),
        ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    begin_date = models.DateField()
    end_date = models.DateField()


class Calendar(BaseCalendar):
    class Meta(BaseCalendar.Meta):
        constraints = [
            models.CheckConstraint(name='calendar_dates_order', check=Q(begin_date__lte=F('end_date'))),
        ]


class DraftCalendar(BaseCalendar):
    class Meta(BaseCalendar.Meta):
        constraints = [
            models.CheckConstraint(name='draft_calendar_dates_order', check=Q(begin_date__lte=F('end_date'))),
        ]


class BaseCourse(YeastModel):
    class Meta:
        abstract = True
        unique_together = [
            ('calendar', 'slug'),
        ]

    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE)


class Course(BaseCourse):
    pass


class DraftCourse(BaseCourse):
    pass


class Schedule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=44)


class Event(models.Model):
    class Meta:
        abstract = True

    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    begin_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)
    place = models.CharField(max_length=44, null=True)

    @classmethod
    def time(cls, hour, minute):
        return time(hour, minute, 0, 0, None)


class SingleEvent(Event):
    class Meta:
        constraints = [
            models.CheckConstraint(name='singleevent_times_order', check=Q(begin_time__isnull=True, end_time__isnull=True)|Q(begin_time__isnull=False, end_time__isnull=False, begin_time__lt=F('end_time'))),
        ]

    date = models.DateField()


class WeeklyEvent(Event):
    class Meta:
        constraints = [
            models.CheckConstraint(name='weeklyevent_times_order', check=Q(begin_time__isnull=True, end_time__isnull=True)|Q(begin_time__isnull=False, end_time__isnull=False, begin_time__lt=F('end_time'))),
        ]

    weekday = models.IntegerField(choices=Weekday.choices)


class Cancelation(models.Model):
    class Meta:
        abstract = True

    title = models.CharField(max_length=44)
    date = models.DateField()


class CalendarCancelation(Cancelation):
    class Meta:
        unique_together = [
            ('calendar', 'date'),
        ]

    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE)


class ScheduleCancelation(Cancelation):
    class Meta:
        unique_together = [
            ('schedule', 'date'),
        ]

    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
