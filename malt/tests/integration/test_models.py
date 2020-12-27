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
    def setUp(self):
        self.user = User.objects.create_user('u')
        self.other_user = User.objects.create_user('ou')

    def exists(self, user):
        return PowerUser.objects.filter(user=user).exists()

    def create(self, user):
        return PowerUser.objects.create(user=user)

    def retrieve(self, user):
        return PowerUser.objects.get(user=user)

    def update(self, power_user, user):
        power_user.user = user
        power_user.save()

    def delete(self, user):
        PowerUser.objects.filter(user=user).delete()

    def assertExists(self, user):
        self.assertTrue(self.exists(user))
        power_user = self.retrieve(user)
        self.assertEqual(user, power_user.user)

    def assertDoesNotExist(self, user):
        self.assertFalse(self.exists(user))
        with self.assertRaises(PowerUser.DoesNotExist):
            self.retrieve(user)

    def assertCreates(self, user):
        self.create(user)
        self.assertExists(user)

    def assertDoesNotCreate(self, user):
        with self.assertRaises(IntegrityError):
            self.create(user)

    def assertUpdates(self, power_user, user):
        self.update(power_user, user)
        self.assertExists(user)

    def assertDoesNotUpdate(self, power_user, user):
        with self.assertRaises(IntegrityError):
            self.update(power_user, user)

    def assertDeletes(self, user):
        self.delete(user)
        self.assertDoesNotExist(user)

    def testDoesNotExist(self):
        self.assertDoesNotExist(self.user)

    def testCreates(self):
        self.assertCreates(self.user)

    def testDoesNotCreateWithNoneUser(self):
        self.assertDoesNotCreate(None)

    def testDoesNotCreateWithSameUser(self):
        self.create(self.user)
        self.assertDoesNotCreate(self.user)

    def testUpdates(self):
        power_user = self.create(self.user)
        self.assertUpdates(power_user, self.other_user)

    def testDoesNotUpdateWithNoneUser(self):
        power_user = self.create(self.user)
        self.assertDoesNotUpdate(power_user, None)

    def testDoesNotUpdateWithSameUser(self):
        self.create(self.other_user)
        power_user = self.create(self.user)
        self.assertDoesNotUpdate(power_user, self.other_user)

    def testDeletes(self):
        self.create(self.user)
        self.assertDeletes(self.user)

    def testDeletesWhenDoesNotExist(self):
        self.assertDeletes(self.user)

    def testCascadeUser(self):
        self.create(self.user)
        self.user.delete()
        self.assertDoesNotExist(self.user)


class FolderAssetTests(IntegrationTestCase):
    name = 'f'
    other_name = 'of'

    def setUp(self):
        self.user = User.objects.create_user('u')
        self.other_user = User.objects.create_user('ou')

        self.grand_parent = FolderAsset.objects.create(user=self.user, parent=None, name='gp')
        self.parent = FolderAsset.objects.create(user=self.user, parent=self.grand_parent, name='p')
        self.other_parent = FolderAsset.objects.create(user=self.user, parent=self.grand_parent, name='op')

    def exists(self, user, parent, name):
        return FolderAsset.objects.filter(user=user, parent=parent, name=name).exists()

    def create(self, user, parent, name):
        return FolderAsset.objects.create(user=user, parent=parent, name=name)

    def retrieve(self, user, parent, name):
        return FolderAsset.objects.get(user=user, parent=parent, name=name)

    def update(self, folder_asset, user, parent, name):
        folder_asset.user = user
        folder_asset.parent = parent
        folder_asset.name = name
        folder_asset.save()

    def delete(self, user, parent, name):
        FolderAsset.objects.filter(user=user, parent=parent, name=name).delete()

    def assertExists(self, user, parent, name):
        self.assertTrue(self.exists(user, parent, name))
        folder_asset = self.retrieve(user, parent, name)
        self.assertEqual(user, folder_asset.user)
        self.assertEqual(parent, folder_asset.parent)
        self.assertEqual(name, folder_asset.name)

    def assertDoesNotExist(self, user, parent, name):
        self.assertFalse(self.exists(user, parent, name))
        with self.assertRaises(FolderAsset.DoesNotExist):
            self.retrieve(user, parent, name)

    def assertCreates(self, user, parent, name):
        self.create(user, parent, name)
        self.assertExists(user, parent, name)

    def assertDoesNotCreate(self, user, parent, name):
        with self.assertRaises(IntegrityError):
            self.create(user, parent, name)

    def assertUpdates(self, folder_asset, user, parent, name):
        self.update(folder_asset, user, parent, name)
        self.assertExists(user, parent, name)

    def assertDoesNotUpdate(self, folder_asset, user, parent, name):
        with self.assertRaises(IntegrityError):
            self.update(folder_asset, user, parent, name)

    def assertDeletes(self, user, parent, name):
        self.delete(user, parent, name)
        self.assertDoesNotExist(user, parent, name)

    def testDoesNotExist(self):
        self.assertDoesNotExist(self.user, self.parent, self.name)

    def testCreates(self):
        self.assertCreates(self.user, self.parent, self.name)

    def testDoesNotCreateWithNoneUser(self):
        self.assertDoesNotCreate(None, self.parent, self.name)

    def testCreatesWithSameUser(self):
        self.create(self.user, self.parent, self.name)
        self.assertCreates(self.user, self.other_parent, self.other_name)

    def testCreatesWithNoneParent(self):
        self.assertCreates(self.user, None, self.name)

    def testCreatesWithSameParent(self):
        self.create(self.user, self.parent, self.name)
        self.assertCreates(self.other_user, self.parent, self.other_name)

    def testCreatesWithGrandParent(self):
        self.assertCreates(self.user, self.grand_parent, self.name)

    def testDoesNotCreateWithNoneName(self):
        self.assertDoesNotCreate(self.user, self.parent, None)

    def testCreatesWithSameName(self):
        self.create(self.user, self.parent, self.name)
        self.assertCreates(self.other_user, self.other_parent, self.name)

    def testDoesNotCreateWithSameKey(self):
        self.create(self.user, self.parent, self.name)
        self.assertDoesNotCreate(self.user, self.parent, self.name)

    def testUpdates(self):
        folder_asset = self.create(self.user, self.parent, self.name)
        self.assertUpdates(folder_asset, self.other_user, self.other_parent, self.other_name)

    def testDoesNotUpdateWithNoneUser(self):
        folder_asset = self.create(self.user, self.parent, self.name)
        self.assertDoesNotUpdate(folder_asset, None, self.other_parent, self.other_name)

    def testUpdatesWithSameUser(self):
        self.create(self.other_user, self.parent, self.name)
        folder_asset = self.create(self.user, self.parent, self.name)
        self.assertUpdates(folder_asset, self.other_user, self.other_parent, self.other_name)

    def testUpdatesWithNoneParent(self):
        folder_asset = self.create(self.user, self.parent, self.name)
        self.assertUpdates(folder_asset, self.other_user, None, self.other_name)

    def testUpdatesWithSameParent(self):
        self.create(self.user, self.other_parent, self.name)
        folder_asset = self.create(self.user, self.parent, self.name)
        self.assertUpdates(folder_asset, self.other_user, self.other_parent, self.other_name)

    def testUpdatesWithGrandParent(self):
        folder_asset = self.create(self.user, self.parent, self.name)
        self.assertUpdates(folder_asset, self.other_user, self.grand_parent, self.other_name)

    def testDoesNotUpdateWithNoneName(self):
        folder_asset = self.create(self.user, self.parent, self.name)
        self.assertDoesNotUpdate(folder_asset, self.other_user, self.other_parent, None)

    def testUpdatesWithSameName(self):
        self.create(self.user, self.parent, self.other_name)
        folder_asset = self.create(self.user, self.parent, self.name)
        self.assertUpdates(folder_asset, self.other_user, self.other_parent, self.other_name)

    def testDoesNotUpdateWithSameKey(self):
        self.create(self.other_user, self.other_parent, self.other_name)
        folder_asset = self.create(self.user, self.parent, self.name)
        self.assertDoesNotUpdate(folder_asset, self.other_user, self.other_parent, self.other_name)

    def testDeletes(self):
        self.create(self.user, self.parent, self.name)
        self.assertDeletes(self.user, self.parent, self.name)

    def testDeletesWhenDoesNotExist(self):
        self.assertDeletes(self.user, self.parent, self.name)

    def testDeletesWithNoneParent(self):
        self.create(self.user, None, self.name)
        self.assertDeletes(self.user, None, self.name)

    def testDeletesWithGrandParent(self):
        self.create(self.user, self.grand_parent, self.name)
        self.assertDeletes(self.user, self.grand_parent, self.name)

    def testCascadeUser(self):
        self.create(self.user, self.parent, self.name)
        self.user.delete()
        self.assertDoesNotExist(self.user, self.parent, self.name)

    def testCascadeParent(self):
        self.create(self.user, self.parent, self.name)
        self.parent.delete()
        self.assertDoesNotExist(self.user, self.parent, self.name)


class FileAssetTests(IntegrationTestCase):
    name = 'f'
    other_name = 'of'

    def setUp(self):
        self.user = User.objects.create_user('u')
        self.other_user = User.objects.create_user('ou')

        self.grand_parent = FolderAsset.objects.create(user=self.user, parent=None, name='gp')
        self.parent = FolderAsset.objects.create(user=self.user, parent=self.grand_parent, name='p')
        self.other_parent = FolderAsset.objects.create(user=self.user, parent=self.grand_parent, name='op')

    def exists(self, user, parent, name):
        return FileAsset.objects.filter(user=user, parent=parent, name=name).exists()

    def create(self, user, parent, name):
        return FileAsset.objects.create(user=user, parent=parent, name=name)

    def retrieve(self, user, parent, name):
        return FileAsset.objects.get(user=user, parent=parent, name=name)

    def update(self, file_asset, user, parent, name):
        file_asset.user = user
        file_asset.parent = parent
        file_asset.name = name
        file_asset.save()

    def delete(self, user, parent, name):
        FileAsset.objects.filter(user=user, parent=parent, name=name).delete()

    def assertExists(self, user, parent, name):
        self.assertTrue(self.exists(user, parent, name))
        file_asset = self.retrieve(user, parent, name)
        self.assertEqual(user, file_asset.user)
        self.assertEqual(parent, file_asset.parent)
        self.assertEqual(name, file_asset.name)

    def assertDoesNotExist(self, user, parent, name):
        self.assertFalse(self.exists(user, parent, name))
        with self.assertRaises(FileAsset.DoesNotExist):
            self.retrieve(user, parent, name)

    def assertCreates(self, user, parent, name):
        self.create(user, parent, name)
        self.assertExists(user, parent, name)

    def assertDoesNotCreate(self, user, parent, name):
        with self.assertRaises(IntegrityError):
            self.create(user, parent, name)

    def assertUpdates(self, file_asset, user, parent, name):
        self.update(file_asset, user, parent, name)
        self.assertExists(user, parent, name)

    def assertDoesNotUpdate(self, file_asset, user, parent, name):
        with self.assertRaises(IntegrityError):
            self.update(file_asset, user, parent, name)

    def assertDeletes(self, user, parent, name):
        self.delete(user, parent, name)
        self.assertDoesNotExist(user, parent, name)

    def testDoesNotExist(self):
        self.assertDoesNotExist(self.user, self.parent, self.name)

    def testCreates(self):
        self.assertCreates(self.user, self.parent, self.name)

    def testDoesNotCreateWithNoneUser(self):
        self.assertDoesNotCreate(None, self.parent, self.name)

    def testCreatesWithSameUser(self):
        self.create(self.user, self.parent, self.name)
        self.assertCreates(self.user, self.other_parent, self.other_name)

    def testCreatesWithNoneParent(self):
        self.assertCreates(self.user, None, self.name)

    def testCreatesWithSameParent(self):
        self.create(self.user, self.parent, self.name)
        self.assertCreates(self.other_user, self.parent, self.other_name)

    def testCreatesWithGrandParent(self):
        self.assertCreates(self.user, self.grand_parent, self.name)

    def testDoesNotCreateWithNoneName(self):
        self.assertDoesNotCreate(self.user, self.parent, None)

    def testCreatesWithSameName(self):
        self.create(self.user, self.parent, self.name)
        self.assertCreates(self.other_user, self.other_parent, self.name)

    def testDoesNotCreateWithSameKey(self):
        self.create(self.user, self.parent, self.name)
        self.assertDoesNotCreate(self.user, self.parent, self.name)

    def testUpdates(self):
        file_asset = self.create(self.user, self.parent, self.name)
        self.assertUpdates(file_asset, self.other_user, self.other_parent, self.other_name)

    def testDoesNotUpdateWithNoneUser(self):
        file_asset = self.create(self.user, self.parent, self.name)
        self.assertDoesNotUpdate(file_asset, None, self.other_parent, self.other_name)

    def testUpdatesWithSameUser(self):
        self.create(self.other_user, self.parent, self.name)
        file_asset = self.create(self.user, self.parent, self.name)
        self.assertUpdates(file_asset, self.other_user, self.other_parent, self.other_name)

    def testUpdatesWithNoneParent(self):
        file_asset = self.create(self.user, self.parent, self.name)
        self.assertUpdates(file_asset, self.other_user, None, self.other_name)

    def testUpdatesWithSameParent(self):
        self.create(self.user, self.other_parent, self.name)
        file_asset = self.create(self.user, self.parent, self.name)
        self.assertUpdates(file_asset, self.other_user, self.other_parent, self.other_name)

    def testUpdatesWithGrandParent(self):
        file_asset = self.create(self.user, self.parent, self.name)
        self.assertUpdates(file_asset, self.other_user, self.grand_parent, self.other_name)

    def testDoesNotUpdateWithNoneName(self):
        file_asset = self.create(self.user, self.parent, self.name)
        self.assertDoesNotUpdate(file_asset, self.other_user, self.other_parent, None)

    def testUpdatesWithSameName(self):
        self.create(self.user, self.parent, self.other_name)
        file_asset = self.create(self.user, self.parent, self.name)
        self.assertUpdates(file_asset, self.other_user, self.other_parent, self.other_name)

    def testDoesNotUpdateWithSameKey(self):
        self.create(self.other_user, self.other_parent, self.other_name)
        file_asset = self.create(self.user, self.parent, self.name)
        self.assertDoesNotUpdate(file_asset, self.other_user, self.other_parent, self.other_name)

    def testDeletes(self):
        self.create(self.user, self.parent, self.name)
        self.assertDeletes(self.user, self.parent, self.name)

    def testDeletesWhenDoesNotExist(self):
        self.assertDeletes(self.user, self.parent, self.name)

    def testDeletesWithNoneParent(self):
        self.create(self.user, None, self.name)
        self.assertDeletes(self.user, None, self.name)

    def testDeletesWithGrandParent(self):
        self.create(self.user, self.grand_parent, self.name)
        self.assertDeletes(self.user, self.grand_parent, self.name)

    def testCascadeUser(self):
        self.create(self.user, self.parent, self.name)
        self.user.delete()
        self.assertDoesNotExist(self.user, self.parent, self.name)

    def testCascadeParent(self):
        self.create(self.user, self.parent, self.name)
        self.parent.delete()
        self.assertDoesNotExist(self.user, self.parent, self.name)


class CalendarTests(IntegrationTestCase):
    username = 'u'
    other_username = 'ou'

    def createValues(self):
        user = User.objects.create_user(self.username)
        slug = 's'
        begin_date = timezone.now()
        end_date = timezone.now()
        return user, slug, begin_date, end_date

    def create(self, user, slug, begin_date, end_date):
        Calendar.objects.create(user=user, slug=slug, begin_date=begin_date, end_date=end_date)

    def retrieve(self, user, slug, begin_date, end_date):
        return Calendar.objects.filter(user=user, slug=slug, begin_date=begin_date, end_date=end_date).exists()

    def delete(self, user, slug, begin_date, end_date):
        Calendar.objects.filter(user=user, slug=slug, begin_date=begin_date, end_date=end_date).delete()

    def assertDoesNotCreate(self, user, slug, begin_date, end_date):
        with self.assertRaises(IntegrityError):
            self.create(user, slug, begin_date, end_date)

    def assertRetrieves(self, user, slug, begin_date, end_date):
        self.assertTrue(self.retrieve(user, slug, begin_date, end_date))

    def assertDoesNotRetrieve(self, user, slug, begin_date, end_date):
        self.assertFalse(self.retrieve(user, slug, begin_date, end_date))

    def testDoesNotCreateWithNoneUser(self):
        _, slug, begin_date, end_date = self.createValues()
        self.assertDoesNotCreate(None, slug, begin_date, end_date)

    def testDoesNotCreateWithNoneSlug(self):
        user, _, begin_date, end_date = self.createValues()
        self.assertDoesNotCreate(user, None, begin_date, end_date)

    def testDoesNotCreateWithNoneBeginDate(self):
        user, slug, _, end_date = self.createValues()
        self.assertDoesNotCreate(user, slug, None, end_date)

    def testDoesNotCreateWithNoneEndDate(self):
        user, slug, begin_date, _ = self.createValues()
        self.assertDoesNotCreate(user, slug, begin_date, None)

    def testDoesNotCreateWithSameKey(self):
        user, slug, begin_date, end_date = self.createValues()
        self.create(user, slug, begin_date, end_date)
        other_user = User.objects.create_user(self.other_username)
        self.assertDoesNotCreate(other_user, slug, begin_date, end_date)

    def testRetrievesAfterCreate(self):
        user, slug, begin_date, end_date = self.createValues()
        self.create(user, slug, begin_date, end_date)
        self.assertRetrieves(user, slug, begin_date, end_date)

    def testDoesNotRetrieveAfterCreateAndDelete(self):
        user, slug, begin_date, end_date = self.createValues()
        self.create(user, slug, begin_date, end_date)
        self.delete(user, slug, begin_date, end_date)
        self.assertDoesNotRetrieve(user, slug, begin_date, end_date)

    def testDoesNotRetrieveAfterCreateAndDeleteUser(self):
        user, slug, begin_date, end_date = self.createValues()
        self.create(user, slug, begin_date, end_date)
        user.delete()
        self.assertDoesNotRetrieve(user, slug, begin_date, end_date)


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
        title = 't'
        return course, title

    def create(self, course, title):
        Schedule.objects.create(course=course, title=title)

    def retrieve(self, course, title):
        return Schedule.objects.filter(course=course, title=title).exists()

    def delete(self, course, title):
        Schedule.objects.filter(course=course, title=title).delete()

    def assertDoesNotCreate(self, course, title):
        with self.assertRaises(IntegrityError):
            self.create(course, title)

    def assertRetrieves(self, course, title):
        self.assertTrue(self.retrieve(course, title))

    def assertDoesNotRetrieve(self, course, title):
        self.assertFalse(self.retrieve(course, title))

    def testDoesNotCreateWithNoneCourse(self):
        _, title = self.createValues()
        self.assertDoesNotCreate(None, title)

    def testDoesNotCreateWithNoneTitle(self):
        course, _ = self.createValues()
        self.assertDoesNotCreate(course, None)

    def testRetrievesAfterCreate(self):
        course, title = self.createValues()
        self.create(course, title)
        self.assertRetrieves(course, title)

    def testDoesNotRetrieveAfterCreateAndDelete(self):
        course, title = self.createValues()
        self.create(course, title)
        self.delete(course, title)
        self.assertDoesNotRetrieve(course, title)

    def testDoesNotRetrieveAfterCreateAndDeleteCourse(self):
        course, title = self.createValues()
        self.create(course, title)
        course.delete()
        self.assertDoesNotRetrieve(course, title)


class SingleEventTests(IntegrationTestCase):
    def createValues(self):
        user = User.objects.create_user('u')
        course = Course.objects.create(user=user, slug='s')
        schedule = Schedule.objects.create(course=course, title='t')
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
        schedule = Schedule.objects.create(course=course, title='t')
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
        calendar = Calendar.objects.create(user=user, slug='s', begin_date=timezone.now(), end_date=timezone.now())
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
        schedule = Schedule.objects.create(course=course, title='t')
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
