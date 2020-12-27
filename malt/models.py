from django.contrib.auth import get_user_model
from django.db import models, transaction, IntegrityError
from shortuuid import uuid

from beer import public_storage

User = get_user_model()


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
    @transaction.atomic
    def create(self, **kwargs):
        if 'uid' in kwargs:
            raise IntegrityError('uid not allowed in kwargs')
        user = kwargs.pop('user', None)
        while True:
            uid = uuid()
            if not self.filter(user=user, uid=uid).exists():
                return super().create(user=user, uid=uid, **kwargs)


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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=22)
    active = models.BooleanField(default=False)


class Calendar(YeastModel):
    class Meta:
        unique_together = [
            ('slug', 'active'),
        ]

    title = models.CharField(max_length=44)
    begin_date = models.DateField()
    end_date = models.DateField()


class Course(YeastModel):
    class Meta:
        unique_together = [
            ('slug', 'active'),
        ]

    title = models.CharField(max_length=44)
    calendar = models.ForeignKey(Calendar, null=True, on_delete=models.SET_NULL)


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


class SingleEvent(Event):
    date = models.DateField()


class WeeklyEvent(Event):
    class Weekday(models.IntegerChoices):
        MONDAY = 0
        TUESDAY = 1
        WEDNESDAY = 2
        THURSDAY = 3
        FRIDAY = 4
        SATURDAY = 5
        SUNDAY = 6

    weekday = models.IntegerField(choices=Weekday.choices)


class Cancelation(models.Model):
    class Meta:
        abstract = True

    title = models.CharField(max_length=44, null=True)
    date = models.DateField()


class CalendarCancelation(Cancelation):
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE)


class ScheduleCancelation(Cancelation):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
