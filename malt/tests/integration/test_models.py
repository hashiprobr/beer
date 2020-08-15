from io import BytesIO

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone

from beer import public_storage
from beer.tests import IntegrationTestCase

from ...models import (
    PowerUser,
    FolderAsset, FileAsset,
    Calendar, Course, Schedule, SingleEvent, WeeklyEvent, CalendarCancelation, ScheduleCancelation,
)

User = get_user_model()


class PowerUserTests(IntegrationTestCase):
    def createValues(self):
        return User.objects.create_user('u')

    def create(self, user):
        PowerUser.objects.create(user=user)

    def retrieve(self, user):
        return PowerUser.objects.filter(user=user).exists()

    def delete(self, user):
        PowerUser.objects.filter(user=user).delete()

    def assertDoesNotCreate(self, user):
        with self.assertRaises(IntegrityError):
            self.create(user)

    def assertRetrieves(self, user):
        self.assertTrue(self.retrieve(user))

    def assertDoesNotRetrieve(self, user):
        self.assertFalse(self.retrieve(user))

    def testDoesNotCreateWithNoneUser(self):
        _ = self.createValues()
        self.assertDoesNotCreate(None)

    def testDoesNotCreateWithSameUser(self):
        user = self.createValues()
        self.create(user)
        self.assertDoesNotCreate(user)

    def testRetrievesAfterCreate(self):
        user = self.createValues()
        self.create(user)
        self.assertRetrieves(user)

    def testDoesNotRetrieveAfterCreateAndDelete(self):
        user = self.createValues()
        self.create(user)
        self.delete(user)
        self.assertDoesNotRetrieve(user)

    def testDoesNotRetrieveAfterCreateAndDeleteUser(self):
        user = self.createValues()
        self.create(user)
        user.delete()
        self.assertDoesNotRetrieve(user)


class FolderAssetTests(IntegrationTestCase):
    def createValues(self):
        user = User.objects.create_user('u')
        parent = FolderAsset.objects.create(user=user, parent=None, name='p')
        name = 'f'
        return user, parent, name

    def create(self, user, parent, name):
        FolderAsset.objects.create(user=user, parent=parent, name=name)

    def retrieve(self, user, parent, name):
        return FolderAsset.objects.filter(user=user, parent=parent, name=name).exists()

    def delete(self, user, parent, name):
        FolderAsset.objects.filter(user=user, parent=parent, name=name).delete()

    def assertDoesNotCreate(self, user, parent, name):
        with self.assertRaises(IntegrityError):
            self.create(user, parent, name)

    def assertRetrieves(self, user, parent, name):
        self.assertTrue(self.retrieve(user, parent, name))

    def assertDoesNotRetrieve(self, user, parent, name):
        self.assertFalse(self.retrieve(user, parent, name))

    def testDoesNotCreateWithNoneUser(self):
        _, parent, name = self.createValues()
        self.assertDoesNotCreate(None, parent, name)

    def testDoesNotCreateWithNoneName(self):
        user, parent, _ = self.createValues()
        self.assertDoesNotCreate(user, parent, None)

    def testDoesNotCreateWithSameKey(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        self.assertDoesNotCreate(user, parent, name)

    def testRetrievesAfterCreate(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        self.assertRetrieves(user, parent, name)

    def testRetrievesAfterCreateWithNoneParent(self):
        user, _, name = self.createValues()
        self.create(user, None, name)
        self.assertRetrieves(user, None, name)

    def testDoesNotRetrieveAfterCreateAndDelete(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        self.delete(user, parent, name)
        self.assertDoesNotRetrieve(user, parent, name)

    def testDoesNotRetrieveAfterCreateAndDeleteUser(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        user.delete()
        self.assertDoesNotRetrieve(user, parent, name)

    def testDoesNotRetrieveAfterCreateAndDeleteParent(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        parent.delete()
        self.assertDoesNotRetrieve(user, parent, name)


class FileAssetTests(IntegrationTestCase):
    def createValues(self):
        user = User.objects.create_user('u')
        parent = FolderAsset.objects.create(user=user, parent=None, name='p')
        name = 'f'
        return user, parent, name

    def create(self, user, parent, name):
        return FileAsset.create(user=user, parent=parent, name=name)

    def retrieve(self, user, parent, name):
        return FileAsset.objects.filter(user=user, parent=parent, name=name).exists()

    def delete(self, user, parent, name):
        FileAsset.objects.filter(user=user, parent=parent, name=name).delete()

    def assertDoesNotCreate(self, user, parent, name):
        with self.assertRaises(IntegrityError):
            self.create(user, parent, name)

    def assertRetrieves(self, user, parent, name):
        self.assertTrue(self.retrieve(user, parent, name))

    def assertDoesNotRetrieve(self, user, parent, name):
        self.assertFalse(self.retrieve(user, parent, name))

    def assertDataDoesNotExist(self, key):
        self.assertFalse(public_storage.exists(key))

    def testDoesNotCreateWithNoneUser(self):
        _, parent, name = self.createValues()
        self.assertDoesNotCreate(None, parent, name)

    def testDoesNotCreateWithNoneName(self):
        user, parent, _ = self.createValues()
        self.assertDoesNotCreate(user, parent, None)

    def testDoesNotCreateWithSameKey(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        self.assertDoesNotCreate(user, parent, name)

    def testRetrievesAfterCreate(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        self.assertRetrieves(user, parent, name)

    def testRetrievesAfterCreateWithNoneParent(self):
        user, _, name = self.createValues()
        self.create(user, None, name)
        self.assertRetrieves(user, None, name)

    def testDoesNotRetrieveAfterCreateAndDelete(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        self.delete(user, parent, name)
        self.assertDoesNotRetrieve(user, parent, name)

    def testDoesNotRetrieveAfterCreateAndDeleteUser(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        user.delete()
        self.assertDoesNotRetrieve(user, parent, name)

    def testDoesNotRetrieveAfterCreateAndDeleteParent(self):
        user, parent, name = self.createValues()
        self.create(user, parent, name)
        parent.delete()
        self.assertDoesNotRetrieve(user, parent, name)

    def testDataDoesNotExistAfterDelete(self):
        user, parent, name = self.createValues()
        file = self.create(user, parent, name)
        key = file.key()
        public_storage.save(key, BytesIO(b'c'))
        file.delete()
        self.assertDataDoesNotExist(key)

    def testIdempotence(self):
        user, parent, name = self.createValues()
        expected = FileAsset.get_or_create(user=user, parent=parent, name=name)
        actual = FileAsset.get_or_create(user=user, parent=parent, name=name)
        self.assertEqual(expected.uid, actual.uid)


class CalendarTests(IntegrationTestCase):
    username = 'u'
    other_username = 'ou'

    def createValues(self):
        user = User.objects.create_user(self.username)
        slug = 's'
        return user, slug

    def create(self, user, slug):
        Calendar.objects.create(user=user, slug=slug)

    def retrieve(self, user, slug):
        return Calendar.objects.filter(user=user, slug=slug).exists()

    def delete(self, user, slug):
        Calendar.objects.filter(user=user, slug=slug).delete()

    def assertDoesNotCreate(self, user, slug):
        with self.assertRaises(IntegrityError):
            self.create(user, slug)

    def assertRetrieves(self, user, slug):
        self.assertTrue(self.retrieve(user, slug))

    def assertDoesNotRetrieve(self, user, slug):
        self.assertFalse(self.retrieve(user, slug))

    def testDoesNotCreateWithNoneUser(self):
        _, slug = self.createValues()
        self.assertDoesNotCreate(None, slug)

    def testDoesNotCreateWithNoneSlug(self):
        user, _ = self.createValues()
        self.assertDoesNotCreate(user, None)

    def testDoesNotCreateWithSameKey(self):
        user, slug = self.createValues()
        self.create(user, slug)
        other_user = User.objects.create_user(self.other_username)
        self.assertDoesNotCreate(other_user, slug)

    def testRetrievesAfterCreate(self):
        user, slug = self.createValues()
        self.create(user, slug)
        self.assertRetrieves(user, slug)

    def testDoesNotRetrieveAfterCreateAndDelete(self):
        user, slug = self.createValues()
        self.create(user, slug)
        self.delete(user, slug)
        self.assertDoesNotRetrieve(user, slug)

    def testDoesNotRetrieveAfterCreateAndDeleteUser(self):
        user, slug = self.createValues()
        self.create(user, slug)
        user.delete()
        self.assertDoesNotRetrieve(user, slug)


class CourseTests(IntegrationTestCase):
    username = 'u'
    other_username = 'ou'

    def createValues(self):
        user = User.objects.create_user(self.username)
        slug = 's'
        return user, slug

    def create(self, user, slug):
        Course.objects.create(user=user, slug=slug)

    def retrieve(self, user, slug):
        return Course.objects.filter(user=user, slug=slug).exists()

    def delete(self, user, slug):
        Course.objects.filter(user=user, slug=slug).delete()

    def assertDoesNotCreate(self, user, slug):
        with self.assertRaises(IntegrityError):
            self.create(user, slug)

    def assertRetrieves(self, user, slug):
        self.assertTrue(self.retrieve(user, slug))

    def assertDoesNotRetrieve(self, user, slug):
        self.assertFalse(self.retrieve(user, slug))

    def testDoesNotCreateWithNoneUser(self):
        _, slug = self.createValues()
        self.assertDoesNotCreate(None, slug)

    def testDoesNotCreateWithNoneSlug(self):
        user, _ = self.createValues()
        self.assertDoesNotCreate(user, None)

    def testDoesNotCreateWithSameKey(self):
        user, slug = self.createValues()
        self.create(user, slug)
        other_user = User.objects.create_user(self.other_username)
        self.assertDoesNotCreate(other_user, slug)

    def testRetrievesAfterCreate(self):
        user, slug = self.createValues()
        self.create(user, slug)
        self.assertRetrieves(user, slug)

    def testDoesNotRetrieveAfterCreateAndDelete(self):
        user, slug = self.createValues()
        self.create(user, slug)
        self.delete(user, slug)
        self.assertDoesNotRetrieve(user, slug)

    def testDoesNotRetrieveAfterCreateAndDeleteUser(self):
        user, slug = self.createValues()
        self.create(user, slug)
        user.delete()
        self.assertDoesNotRetrieve(user, slug)


class ScheduleTests(IntegrationTestCase):
    def createValues(self):
        user = User.objects.create_user('u')
        course = Course.objects.create(user=user, slug='s')
        key = 'k'
        title = 't'
        return course, key, title

    def create(self, course, key, title):
        Schedule.objects.create(course=course, key=key, title=title)

    def retrieve(self, course, key, title):
        return Schedule.objects.filter(course=course, key=key, title=title).exists()

    def delete(self, course, key, title):
        Schedule.objects.filter(course=course, key=key, title=title).delete()

    def assertDoesNotCreate(self, course, key, title):
        with self.assertRaises(IntegrityError):
            self.create(course, key, title)

    def assertRetrieves(self, course, key, title):
        self.assertTrue(self.retrieve(course, key, title))

    def assertDoesNotRetrieve(self, course, key, title):
        self.assertFalse(self.retrieve(course, key, title))

    def testDoesNotCreateWithNoneCourse(self):
        _, key, title = self.createValues()
        self.assertDoesNotCreate(None, key, title)

    def testDoesNotCreateWithNoneKey(self):
        course, _, title = self.createValues()
        self.assertDoesNotCreate(course, None, title)

    def testDoesNotCreateWithNoneTitle(self):
        course, key, _ = self.createValues()
        self.assertDoesNotCreate(course, key, None)

    def testRetrievesAfterCreate(self):
        course, key, title = self.createValues()
        self.create(course, key, title)
        self.assertRetrieves(course, key, title)

    def testDoesNotRetrieveAfterCreateAndDelete(self):
        course, key, title = self.createValues()
        self.create(course, key, title)
        self.delete(course, key, title)
        self.assertDoesNotRetrieve(course, key, title)

    def testDoesNotRetrieveAfterCreateAndDeleteCourse(self):
        course, key, title = self.createValues()
        self.create(course, key, title)
        course.delete()
        self.assertDoesNotRetrieve(course, key, title)


class SingleEventTests(IntegrationTestCase):
    def createValues(self):
        user = User.objects.create_user('u')
        course = Course.objects.create(user=user, slug='s')
        schedule = Schedule.objects.create(course=course, key='k', title='t')
        date = timezone.now()
        return schedule, date

    def create(self, schedule, date):
        SingleEvent.objects.create(schedule=schedule, date=date)

    def retrieve(self, schedule, date):
        return SingleEvent.objects.filter(schedule=schedule, date=date).exists()

    def delete(self, schedule, date):
        SingleEvent.objects.filter(schedule=schedule, date=date).delete()

    def assertDoesNotCreate(self, schedule, date):
        with self.assertRaises(IntegrityError):
            self.create(schedule, date)

    def assertRetrieves(self, schedule, date):
        self.assertTrue(self.retrieve(schedule, date))

    def assertDoesNotRetrieve(self, schedule, date):
        self.assertFalse(self.retrieve(schedule, date))

    def testDoesNotCreateWithNoneSchedule(self):
        _, date = self.createValues()
        self.assertDoesNotCreate(None, date)

    def testDoesNotCreateWithNoneDate(self):
        schedule, _ = self.createValues()
        self.assertDoesNotCreate(schedule, None)

    def testRetrievesAfterCreate(self):
        schedule, date = self.createValues()
        self.create(schedule, date)
        self.assertRetrieves(schedule, date)

    def testDoesNotRetrieveAfterCreateAndDelete(self):
        schedule, date = self.createValues()
        self.create(schedule, date)
        self.delete(schedule, date)
        self.assertDoesNotRetrieve(schedule, date)

    def testDoesNotRetrieveAfterCreateAndDeleteSchedule(self):
        schedule, date = self.createValues()
        self.create(schedule, date)
        schedule.delete()
        self.assertDoesNotRetrieve(schedule, date)


class WeeklyEventTests(IntegrationTestCase):
    def createValues(self):
        user = User.objects.create_user('u')
        course = Course.objects.create(user=user, slug='s')
        schedule = Schedule.objects.create(course=course, key='k', title='t')
        weekday = WeeklyEvent.Weekday.MONDAY
        return schedule, weekday

    def create(self, schedule, weekday):
        WeeklyEvent.objects.create(schedule=schedule, weekday=weekday)

    def retrieve(self, schedule, weekday):
        return WeeklyEvent.objects.filter(schedule=schedule, weekday=weekday).exists()

    def delete(self, schedule, weekday):
        WeeklyEvent.objects.filter(schedule=schedule, weekday=weekday).delete()

    def assertDoesNotCreate(self, schedule, weekday):
        with self.assertRaises(IntegrityError):
            self.create(schedule, weekday)

    def assertRetrieves(self, schedule, weekday):
        self.assertTrue(self.retrieve(schedule, weekday))

    def assertDoesNotRetrieve(self, schedule, weekday):
        self.assertFalse(self.retrieve(schedule, weekday))

    def testDoesNotCreateWithNoneSchedule(self):
        _, weekday = self.createValues()
        self.assertDoesNotCreate(None, weekday)

    def testDoesNotCreateWithNoneWeekday(self):
        schedule, _ = self.createValues()
        self.assertDoesNotCreate(schedule, None)

    def testRetrievesAfterCreate(self):
        schedule, weekday = self.createValues()
        self.create(schedule, weekday)
        self.assertRetrieves(schedule, weekday)

    def testDoesNotRetrieveAfterCreateAndDelete(self):
        schedule, weekday = self.createValues()
        self.create(schedule, weekday)
        self.delete(schedule, weekday)
        self.assertDoesNotRetrieve(schedule, weekday)

    def testDoesNotRetrieveAfterCreateAndDeleteSchedule(self):
        schedule, weekday = self.createValues()
        self.create(schedule, weekday)
        schedule.delete()
        self.assertDoesNotRetrieve(schedule, weekday)


class CalendarCancelationTests(IntegrationTestCase):
    def createValues(self):
        user = User.objects.create_user('u')
        calendar = Calendar.objects.create(user=user, slug='s')
        date = timezone.now()
        return calendar, date

    def create(self, calendar, date):
        CalendarCancelation.objects.create(calendar=calendar, date=date)

    def retrieve(self, calendar, date):
        return CalendarCancelation.objects.filter(calendar=calendar, date=date).exists()

    def delete(self, calendar, date):
        CalendarCancelation.objects.filter(calendar=calendar, date=date).delete()

    def assertDoesNotCreate(self, calendar, date):
        with self.assertRaises(IntegrityError):
            self.create(calendar, date)

    def assertRetrieves(self, calendar, date):
        self.assertTrue(self.retrieve(calendar, date))

    def assertDoesNotRetrieve(self, calendar, date):
        self.assertFalse(self.retrieve(calendar, date))

    def testDoesNotCreateWithNoneCalendar(self):
        _, date = self.createValues()
        self.assertDoesNotCreate(None, date)

    def testDoesNotCreateWithNoneDate(self):
        calendar, _ = self.createValues()
        self.assertDoesNotCreate(calendar, None)

    def testRetrievesAfterCreate(self):
        calendar, date = self.createValues()
        self.create(calendar, date)
        self.assertRetrieves(calendar, date)

    def testDoesNotRetrieveAfterCreateAndDelete(self):
        calendar, date = self.createValues()
        self.create(calendar, date)
        self.delete(calendar, date)
        self.assertDoesNotRetrieve(calendar, date)

    def testDoesNotRetrieveAfterCreateAndDeleteCalendar(self):
        calendar, date = self.createValues()
        self.create(calendar, date)
        calendar.delete()
        self.assertDoesNotRetrieve(calendar, date)


class ScheduleCancelationTests(IntegrationTestCase):
    def createValues(self):
        user = User.objects.create_user('u')
        course = Course.objects.create(user=user, slug='s')
        schedule = Schedule.objects.create(course=course, key='k', title='t')
        date = timezone.now()
        return schedule, date

    def create(self, schedule, date):
        ScheduleCancelation.objects.create(schedule=schedule, date=date)

    def retrieve(self, schedule, date):
        return ScheduleCancelation.objects.filter(schedule=schedule, date=date).exists()

    def delete(self, schedule, date):
        ScheduleCancelation.objects.filter(schedule=schedule, date=date).delete()

    def assertDoesNotCreate(self, schedule, date):
        with self.assertRaises(IntegrityError):
            self.create(schedule, date)

    def assertRetrieves(self, schedule, date):
        self.assertTrue(self.retrieve(schedule, date))

    def assertDoesNotRetrieve(self, schedule, date):
        self.assertFalse(self.retrieve(schedule, date))

    def testDoesNotCreateWithNoneSchedule(self):
        _, date = self.createValues()
        self.assertDoesNotCreate(None, date)

    def testDoesNotCreateWithNoneDate(self):
        schedule, _ = self.createValues()
        self.assertDoesNotCreate(schedule, None)

    def testRetrievesAfterCreate(self):
        schedule, date = self.createValues()
        self.create(schedule, date)
        self.assertRetrieves(schedule, date)

    def testDoesNotRetrieveAfterCreateAndDelete(self):
        schedule, date = self.createValues()
        self.create(schedule, date)
        self.delete(schedule, date)
        self.assertDoesNotRetrieve(schedule, date)

    def testDoesNotRetrieveAfterCreateAndDeleteSchedule(self):
        schedule, date = self.createValues()
        self.create(schedule, date)
        schedule.delete()
        self.assertDoesNotRetrieve(schedule, date)
