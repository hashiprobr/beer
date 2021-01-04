from datetime import date

from django.contrib.auth import get_user_model
from django.db import DatabaseError

from beer.tests import IntegrationTestCase

from ...models import (
    Weekday,
    PowerUser,
    FolderAsset, FileAsset,
    Calendar,
    Course,
    Schedule,
    SingleEvent, WeeklyEvent,
    CalendarCancelation, ScheduleCancelation,
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

    def create_retrieve(self, user):
        return PowerUser.objects.get_or_create(user=user)

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
        with self.assertRaises(DatabaseError):
            self.create(user)

    def assertCreatesToRetrieve(self, user):
        _, created = self.create_retrieve(user)
        self.assertExists(user)
        self.assertTrue(created)

    def assertDoesNotCreateToRetrieve(self, user):
        self.create(user)
        _, created = self.create_retrieve(user)
        self.assertFalse(created)

    def assertUpdates(self, power_user, user):
        self.update(power_user, user)
        self.assertExists(user)

    def assertDoesNotUpdate(self, power_user, user):
        with self.assertRaises(DatabaseError):
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

    def testCreatesToRetrieve(self):
        self.assertCreatesToRetrieve(self.user)

    def testDoesNotCreateToRetrieve(self):
        self.assertDoesNotCreateToRetrieve(self.user)

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
    name = 'n'
    other_name = 'on'

    def setUp(self):
        self.upper_name = (FolderAsset.name.field.max_length + 1) * 'n'

        self.user = User.objects.create_user('u')
        self.other_user = User.objects.create_user('ou')

        self.grand_parent = FolderAsset.objects.create(user=self.user, parent=None, name='gpn')
        self.parent = FolderAsset.objects.create(user=self.user, parent=self.grand_parent, name='pn')
        self.other_parent = FolderAsset.objects.create(user=self.user, parent=self.grand_parent, name='opn')

    def exists(self, user, parent, name):
        return FolderAsset.objects.filter(user=user, parent=parent, name=name).exists()

    def create(self, user, parent, name):
        return FolderAsset.objects.create(user=user, parent=parent, name=name)

    def retrieve(self, user, parent, name):
        return FolderAsset.objects.get(user=user, parent=parent, name=name)

    def create_retrieve(self, user, parent, name):
        return FolderAsset.objects.get_or_create(user=user, parent=parent, name=name)

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
        with self.assertRaises(DatabaseError):
            self.create(user, parent, name)

    def assertCreatesToRetrieve(self, user, parent, name):
        _, created = self.create_retrieve(user, parent, name)
        self.assertExists(user, parent, name)
        self.assertTrue(created)

    def assertDoesNotCreateToRetrieve(self, user, parent, name):
        self.create(user, parent, name)
        _, created = self.create_retrieve(user, parent, name)
        self.assertFalse(created)

    def assertUpdates(self, folder_asset, user, parent, name):
        self.update(folder_asset, user, parent, name)
        self.assertExists(user, parent, name)

    def assertDoesNotUpdate(self, folder_asset, user, parent, name):
        with self.assertRaises(DatabaseError):
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

    def testDoesNotCreateWithUpperName(self):
        self.assertDoesNotCreate(self.user, self.parent, self.upper_name)

    def testDoesNotCreateWithSameKey(self):
        self.create(self.user, self.parent, self.name)
        self.assertDoesNotCreate(self.user, self.parent, self.name)

    def testCreatesToRetrieve(self):
        self.assertCreatesToRetrieve(self.user, self.parent, self.name)

    def testDoesNotCreateToRetrieve(self):
        self.assertDoesNotCreateToRetrieve(self.user, self.parent, self.name)

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

    def testDoesNotUpdateWithUpperName(self):
        folder_asset = self.create(self.user, self.parent, self.name)
        self.assertDoesNotUpdate(folder_asset, self.other_user, self.other_parent, self.upper_name)

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
    name = 'n'
    other_name = 'on'

    uid = 'u'

    def setUp(self):
        self.upper_name = (FileAsset.name.field.max_length + 1) * 'n'

        self.user = User.objects.create_user('u')
        self.other_user = User.objects.create_user('ou')

        self.grand_parent = FolderAsset.objects.create(user=self.user, parent=None, name='gpn')
        self.parent = FolderAsset.objects.create(user=self.user, parent=self.grand_parent, name='pn')
        self.other_parent = FolderAsset.objects.create(user=self.user, parent=self.grand_parent, name='opn')

    def exists(self, user, parent, name):
        return FileAsset.objects.filter(user=user, parent=parent, name=name).exists()

    def create(self, user, parent, name, **kwargs):
        return FileAsset.objects.create(user=user, parent=parent, name=name, **kwargs)

    def retrieve(self, user, parent, name):
        return FileAsset.objects.get(user=user, parent=parent, name=name)

    def create_retrieve(self, user, parent, name, **kwargs):
        return FileAsset.objects.get_or_create(user=user, parent=parent, name=name, **kwargs)

    def update(self, file_asset, user, parent, name):
        file_asset.user = user
        file_asset.parent = parent
        file_asset.name = name
        file_asset.uid = ''
        file_asset.active = True
        file_asset.save()

    def delete(self, user, parent, name):
        FileAsset.objects.filter(user=user, parent=parent, name=name).delete()

    def assertExists(self, user, parent, name):
        self.assertTrue(self.exists(user, parent, name))
        file_asset = self.retrieve(user, parent, name)
        self.assertEqual(user, file_asset.user)
        self.assertEqual(parent, file_asset.parent)
        self.assertEqual(name, file_asset.name)
        return file_asset

    def assertDoesNotExist(self, user, parent, name):
        self.assertFalse(self.exists(user, parent, name))
        with self.assertRaises(FileAsset.DoesNotExist):
            self.retrieve(user, parent, name)

    def assertCreates(self, user, parent, name):
        self.create(user, parent, name)
        file_asset = self.assertExists(user, parent, name)
        self.assertTrue(file_asset.uid)
        self.assertFalse(file_asset.active)

    def assertDoesNotCreate(self, user, parent, name, **kwargs):
        with self.assertRaises(DatabaseError):
            self.create(user, parent, name, **kwargs)

    def assertCreatesToRetrieve(self, user, parent, name):
        _, created = self.create_retrieve(user, parent, name)
        self.assertExists(user, parent, name)
        self.assertTrue(created)

    def assertDoesNotCreateToRetrieve(self, user, parent, name):
        self.create(user, parent, name)
        _, created = self.create_retrieve(user, parent, name)
        self.assertFalse(created)

    def assertDoesNotCreateOrRetrieve(self, user, parent, name, **kwargs):
        with self.assertRaises(DatabaseError):
            self.create_retrieve(user, parent, name, **kwargs)

    def assertUpdates(self, file_asset, user, parent, name):
        self.update(file_asset, user, parent, name)
        file_asset = self.assertExists(user, parent, name)
        self.assertFalse(file_asset.uid)
        self.assertTrue(file_asset.active)

    def assertDoesNotUpdate(self, file_asset, user, parent, name):
        with self.assertRaises(DatabaseError):
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

    def testDoesNotCreateWithUpperName(self):
        self.assertDoesNotCreate(self.user, self.parent, self.upper_name)

    def testDoesNotCreateWithSameKey(self):
        self.create(self.user, self.parent, self.name)
        self.assertDoesNotCreate(self.user, self.parent, self.name)

    def testDoesNotCreateWithUID(self):
        self.assertDoesNotCreate(self.user, self.parent, self.name, uid=self.uid)

    def testDoesNotCreateWithFalseActive(self):
        self.assertDoesNotCreate(self.user, self.parent, self.name, active=False)

    def testDoesNotCreateWithTrueActive(self):
        self.assertDoesNotCreate(self.user, self.parent, self.name, active=True)

    def testCreatesToRetrieve(self):
        self.assertCreatesToRetrieve(self.user, self.parent, self.name)

    def testDoesNotCreateToRetrieve(self):
        self.assertDoesNotCreateToRetrieve(self.user, self.parent, self.name)

    def testDoesNotCreateOrRetrieveWithUID(self):
        self.assertDoesNotCreateOrRetrieve(self.user, self.parent, self.name, uid=self.uid)

    def testDoesNotCreateOrRetrieveWithFalseActive(self):
        self.assertDoesNotCreateOrRetrieve(self.user, self.parent, self.name, active=False)

    def testDoesNotCreateOrRetrieveWithTrueActive(self):
        self.assertDoesNotCreateOrRetrieve(self.user, self.parent, self.name, active=True)

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

    def testDoesNotUpdateWithUpperName(self):
        file_asset = self.create(self.user, self.parent, self.name)
        self.assertDoesNotUpdate(file_asset, self.other_user, self.other_parent, self.upper_name)

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


class BaseCalendarTests:
    slug = 's'
    other_slug = 'os'

    title = 't'
    other_title = 'ot'

    def setUp(self):
        self.upper_slug = (Calendar.slug.field.max_length + 1) * 's'

        self.upper_title = (Calendar.title.field.max_length + 1) * 't'

        self.user = User.objects.create_user('u')
        self.other_user = User.objects.create_user('ou')

        self.begin_date = date(1983, 4, 25)
        self.other_begin_date = date(1983, 4, 26)

        self.end_date = date(1983, 5, 25)
        self.other_end_date = date(1983, 5, 26)

    def exists(self, user, slug, title, begin_date, end_date):
        return Calendar.objects.filter(user=user, slug=slug, active=self.active, title=title, begin_date=begin_date, end_date=end_date).exists()

    def create(self, user, slug, title, begin_date, end_date):
        return Calendar.objects.create(user=user, slug=slug, active=self.active, title=title, begin_date=begin_date, end_date=end_date)

    def retrieve(self, user, slug, title, begin_date, end_date):
        return Calendar.objects.get(user=user, slug=slug, active=self.active, title=title, begin_date=begin_date, end_date=end_date)

    def create_retrieve(self, user, slug, title, begin_date, end_date):
        return Calendar.objects.get_or_create(user=user, slug=slug, active=self.active, title=title, begin_date=begin_date, end_date=end_date)

    def update(self, calendar, user, slug, title, begin_date, end_date):
        calendar.user = user
        calendar.slug = slug
        calendar.active = self.active
        calendar.title = title
        calendar.begin_date = begin_date
        calendar.end_date = end_date
        calendar.save()

    def delete(self, user, slug, title, begin_date, end_date):
        Calendar.objects.filter(user=user, slug=slug, active=self.active, title=title, begin_date=begin_date, end_date=end_date).delete()

    def assertExists(self, user, slug, title, begin_date, end_date):
        self.assertTrue(self.exists(user, slug, title, begin_date, end_date))
        calendar = self.retrieve(user, slug, title, begin_date, end_date)
        self.assertEqual(user, calendar.user)
        self.assertEqual(slug, calendar.slug)
        self.assertEqual(self.active, calendar.active)
        self.assertEqual(title, calendar.title)
        self.assertEqual(begin_date, calendar.begin_date)
        self.assertEqual(end_date, calendar.end_date)

    def assertDoesNotExist(self, user, slug, title, begin_date, end_date):
        self.assertFalse(self.exists(user, slug, title, begin_date, end_date))
        with self.assertRaises(Calendar.DoesNotExist):
            self.retrieve(user, slug, title, begin_date, end_date)

    def assertCreates(self, user, slug, title, begin_date, end_date):
        self.create(user, slug, title, begin_date, end_date)
        self.assertExists(user, slug, title, begin_date, end_date)

    def assertDoesNotCreate(self, user, slug, title, begin_date, end_date):
        with self.assertRaises(DatabaseError):
            self.create(user, slug, title, begin_date, end_date)

    def assertCreatesToRetrieve(self, user, slug, title, begin_date, end_date):
        _, created = self.create_retrieve(user, slug, title, begin_date, end_date)
        self.assertExists(user, slug, title, begin_date, end_date)
        self.assertTrue(created)

    def assertDoesNotCreateToRetrieve(self, user, slug, title, begin_date, end_date):
        self.create(user, slug, title, begin_date, end_date)
        _, created = self.create_retrieve(user, slug, title, begin_date, end_date)
        self.assertFalse(created)

    def assertUpdates(self, calendar, user, slug, title, begin_date, end_date):
        self.update(calendar, user, slug, title, begin_date, end_date)
        self.assertExists(user, slug, title, begin_date, end_date)

    def assertDoesNotUpdate(self, calendar, user, slug, title, begin_date, end_date):
        with self.assertRaises(DatabaseError):
            self.update(calendar, user, slug, title, begin_date, end_date)

    def assertDeletes(self, user, slug, title, begin_date, end_date):
        self.delete(user, slug, title, begin_date, end_date)
        self.assertDoesNotExist(user, slug, title, begin_date, end_date)

    def testDoesNotExist(self):
        self.assertDoesNotExist(self.user, self.slug, self.title, self.begin_date, self.end_date)

    def testCreates(self):
        self.assertCreates(self.user, self.slug, self.title, self.begin_date, self.end_date)

    def testDoesNotCreateWithNoneUser(self):
        self.assertDoesNotCreate(None, self.slug, self.title, self.begin_date, self.end_date)

    def testCreatesWithSameUser(self):
        self.create(self.user, self.slug, self.title, self.begin_date, self.end_date)
        self.assertCreates(self.user, self.other_slug, self.other_title, self.other_begin_date, self.other_end_date)

    def testDoesNotCreateWithNoneSlug(self):
        self.assertDoesNotCreate(self.user, None, self.title, self.begin_date, self.end_date)

    def testCreatesWithSameSlug(self):
        self.create(self.user, self.slug, self.title, self.begin_date, self.end_date)
        self.assertCreates(self.other_user, self.slug, self.other_title, self.other_begin_date, self.other_end_date)

    def testDoesNotCreateWithUpperSlug(self):
        self.assertDoesNotCreate(self.user, self.upper_slug, self.title, self.begin_date, self.end_date)

    def testDoesNotCreateWithNoneTitle(self):
        self.assertDoesNotCreate(self.user, self.slug, None, self.begin_date, self.end_date)

    def testDoesNotCreateWithUpperTitle(self):
        self.assertDoesNotCreate(self.user, self.slug, self.upper_title, self.begin_date, self.end_date)

    def testDoesNotCreateWithNoneBeginDate(self):
        self.assertDoesNotCreate(self.user, self.slug, self.title, None, self.end_date)

    def testDoesNotCreateWithNoneEndDate(self):
        self.assertDoesNotCreate(self.user, self.slug, self.title, self.begin_date, None)

    def testDoesNotCreateWithUnorderedDates(self):
        self.assertDoesNotCreate(self.user, self.slug, self.title, self.end_date, self.begin_date)

    def testDoesNotCreateWithSameKey(self):
        self.create(self.user, self.slug, self.title, self.begin_date, self.end_date)
        self.assertDoesNotCreate(self.user, self.slug, self.other_title, self.other_begin_date, self.other_end_date)

    def testCreatesToRetrieve(self):
        self.assertCreatesToRetrieve(self.user, self.slug, self.title, self.begin_date, self.end_date)

    def testDoesNotCreateToRetrieve(self):
        self.assertDoesNotCreateToRetrieve(self.user, self.slug, self.title, self.begin_date, self.end_date)

    def testUpdates(self):
        calendar = self.create(self.user, self.slug, self.title, self.begin_date, self.end_date)
        self.assertUpdates(calendar, self.other_user, self.other_slug, self.other_title, self.other_begin_date, self.other_end_date)

    def testDoesNotUpdateWithNoneUser(self):
        calendar = self.create(self.user, self.slug, self.title, self.begin_date, self.end_date)
        self.assertDoesNotUpdate(calendar, None, self.other_slug, self.other_title, self.other_begin_date, self.other_end_date)

    def testUpdatesWithSameUser(self):
        self.create(self.other_user, self.slug, self.title, self.begin_date, self.end_date)
        calendar = self.create(self.user, self.slug, self.title, self.begin_date, self.end_date)
        self.assertUpdates(calendar, self.other_user, self.other_slug, self.other_title, self.other_begin_date, self.other_end_date)

    def testDoesNotUpdateWithNoneSlug(self):
        calendar = self.create(self.user, self.slug, self.title, self.begin_date, self.end_date)
        self.assertDoesNotUpdate(calendar, self.other_user, None, self.other_title, self.other_begin_date, self.other_end_date)

    def testUpdatesWithSameSlug(self):
        self.create(self.user, self.other_slug, self.title, self.begin_date, self.end_date)
        calendar = self.create(self.user, self.slug, self.title, self.begin_date, self.end_date)
        self.assertUpdates(calendar, self.other_user, self.other_slug, self.other_title, self.other_begin_date, self.other_end_date)

    def testDoesNotUpdateWithUpperSlug(self):
        calendar = self.create(self.user, self.slug, self.title, self.begin_date, self.end_date)
        self.assertDoesNotUpdate(calendar, self.other_user, self.upper_slug, self.other_title, self.other_begin_date, self.other_end_date)

    def testDoesNotUpdateWithNoneTitle(self):
        calendar = self.create(self.user, self.slug, self.title, self.begin_date, self.end_date)
        self.assertDoesNotUpdate(calendar, self.other_user, self.other_slug, None, self.other_begin_date, self.other_end_date)

    def testDoesNotUpdateWithUpperTitle(self):
        calendar = self.create(self.user, self.slug, self.title, self.begin_date, self.end_date)
        self.assertDoesNotUpdate(calendar, self.other_user, self.other_slug, self.upper_title, self.other_begin_date, self.other_end_date)

    def testDoesNotUpdateWithNoneBeginDate(self):
        calendar = self.create(self.user, self.slug, self.title, self.begin_date, self.end_date)
        self.assertDoesNotUpdate(calendar, self.other_user, self.other_slug, self.other_title, None, self.other_end_date)

    def testDoesNotUpdateWithNoneEndDate(self):
        calendar = self.create(self.user, self.slug, self.title, self.begin_date, self.end_date)
        self.assertDoesNotUpdate(calendar, self.other_user, self.other_slug, self.other_title, self.other_begin_date, None)

    def testDoesNotUpdateWithUnorderedDates(self):
        calendar = self.create(self.user, self.slug, self.title, self.begin_date, self.end_date)
        self.assertDoesNotUpdate(calendar, self.other_user, self.other_slug, self.other_title, self.other_end_date, self.other_begin_date)

    def testDoesNotUpdateWithSameKey(self):
        self.create(self.other_user, self.other_slug, self.other_title, self.other_begin_date, self.other_end_date)
        calendar = self.create(self.user, self.slug, self.title, self.begin_date, self.end_date)
        self.assertDoesNotUpdate(calendar, self.other_user, self.other_slug, self.other_title, self.other_begin_date, self.other_end_date)

    def testDeletes(self):
        self.create(self.user, self.slug, self.title, self.begin_date, self.end_date)
        self.assertDeletes(self.user, self.slug, self.title, self.begin_date, self.end_date)

    def testDeletesWhenDoesNotExist(self):
        self.assertDeletes(self.user, self.slug, self.title, self.begin_date, self.end_date)

    def testCascadeUser(self):
        self.create(self.user, self.slug, self.title, self.begin_date, self.end_date)
        self.user.delete()
        self.assertDoesNotExist(self.user, self.slug, self.title, self.begin_date, self.end_date)


class DraftCalendarTests(BaseCalendarTests, IntegrationTestCase):
    active = False


class CalendarTests(BaseCalendarTests, IntegrationTestCase):
    active = True


class BaseCourseTests:
    slug = 's'
    other_slug = 'os'

    title = 't'
    other_title = 'ot'

    def setUp(self):
        self.upper_slug = (Course.slug.field.max_length + 1) * 's'

        self.upper_title = (Course.title.field.max_length + 1) * 't'

        user = User.objects.create_user('u')
        begin_date = date(1983, 4, 25)
        end_date = date(1983, 5, 25)
        self.calendar = Calendar.objects.create(user=user, slug='cs', active=True, title='ct', begin_date=begin_date, end_date=end_date)
        other_begin_date = date(1983, 4, 26)
        other_end_date = date(1983, 5, 26)
        self.other_calendar = Calendar.objects.create(user=user, slug='ocs', active=True, title='oct', begin_date=other_begin_date, end_date=other_end_date)

    def exists(self, calendar, slug, title):
        return Course.objects.filter(calendar=calendar, slug=slug, active=self.active, title=title).exists()

    def create(self, calendar, slug, title):
        return Course.objects.create(calendar=calendar, slug=slug, active=self.active, title=title)

    def retrieve(self, calendar, slug, title):
        return Course.objects.get(calendar=calendar, slug=slug, active=self.active, title=title)

    def create_retrieve(self, calendar, slug, title):
        return Course.objects.get_or_create(calendar=calendar, slug=slug, active=self.active, title=title)

    def update(self, course, calendar, slug, title):
        course.calendar = calendar
        course.slug = slug
        course.active = self.active
        course.title = title
        course.save()

    def delete(self, calendar, slug, title):
        Course.objects.filter(calendar=calendar, slug=slug, active=self.active, title=title).delete()

    def assertExists(self, calendar, slug, title):
        self.assertTrue(self.exists(calendar, slug, title))
        course = self.retrieve(calendar, slug, title)
        self.assertEqual(calendar, course.calendar)
        self.assertEqual(slug, course.slug)
        self.assertEqual(self.active, course.active)
        self.assertEqual(title, course.title)

    def assertDoesNotExist(self, calendar, slug, title):
        self.assertFalse(self.exists(calendar, slug, title))
        with self.assertRaises(Course.DoesNotExist):
            self.retrieve(calendar, slug, title)

    def assertCreates(self, calendar, slug, title):
        self.create(calendar, slug, title)
        self.assertExists(calendar, slug, title)

    def assertDoesNotCreate(self, calendar, slug, title):
        with self.assertRaises(DatabaseError):
            self.create(calendar, slug, title)

    def assertCreatesToRetrieve(self, calendar, slug, title):
        _, created = self.create_retrieve(calendar, slug, title)
        self.assertExists(calendar, slug, title)
        self.assertTrue(created)

    def assertDoesNotCreateToRetrieve(self, calendar, slug, title):
        self.create(calendar, slug, title)
        _, created = self.create_retrieve(calendar, slug, title)
        self.assertFalse(created)

    def assertUpdates(self, course, calendar, slug, title):
        self.update(course, calendar, slug, title)
        self.assertExists(calendar, slug, title)

    def assertDoesNotUpdate(self, course, calendar, slug, title):
        with self.assertRaises(DatabaseError):
            self.update(course, calendar, slug, title)

    def assertDeletes(self, calendar, slug, title):
        self.delete(calendar, slug, title)
        self.assertDoesNotExist(calendar, slug, title)

    def testDoesNotExist(self):
        self.assertDoesNotExist(self.calendar, self.slug, self.title)

    def testCreates(self):
        self.assertCreates(self.calendar, self.slug, self.title)

    def testDoesNotCreateWithNoneCalendar(self):
        self.assertDoesNotCreate(None, self.slug, self.title)

    def testCreatesWithSameCalendar(self):
        self.create(self.calendar, self.slug, self.title)
        self.assertCreates(self.calendar, self.other_slug, self.other_title)

    def testDoesNotCreateWithNoneSlug(self):
        self.assertDoesNotCreate(self.calendar, None, self.title)

    def testCreatesWithSameSlug(self):
        self.create(self.calendar, self.slug, self.title)
        self.assertCreates(self.other_calendar, self.slug, self.other_title)

    def testDoesNotCreateWithUpperSlug(self):
        self.assertDoesNotCreate(self.calendar, self.upper_slug, self.title)

    def testDoesNotCreateWithNoneTitle(self):
        self.assertDoesNotCreate(self.calendar, self.slug, None)

    def testDoesNotCreateWithUpperTitle(self):
        self.assertDoesNotCreate(self.calendar, self.slug, self.upper_title)

    def testDoesNotCreateWithSameKey(self):
        self.create(self.calendar, self.slug, self.title)
        self.assertDoesNotCreate(self.calendar, self.slug, self.other_title)

    def testCreatesToRetrieve(self):
        self.assertCreatesToRetrieve(self.calendar, self.slug, self.title)

    def testDoesNotCreateToRetrieve(self):
        self.assertDoesNotCreateToRetrieve(self.calendar, self.slug, self.title)

    def testUpdates(self):
        course = self.create(self.calendar, self.slug, self.title)
        self.assertUpdates(course, self.other_calendar, self.other_slug, self.other_title)

    def testDoesNotUpdateWithNoneCalendar(self):
        course = self.create(self.calendar, self.slug, self.title)
        self.assertDoesNotUpdate(course, None, self.other_slug, self.other_title)

    def testUpdatesWithSameCalendar(self):
        self.create(self.other_calendar, self.slug, self.title)
        course = self.create(self.calendar, self.slug, self.title)
        self.assertUpdates(course, self.other_calendar, self.other_slug, self.other_title)

    def testDoesNotUpdateWithNoneSlug(self):
        course = self.create(self.calendar, self.slug, self.title)
        self.assertDoesNotUpdate(course, self.other_calendar, None, self.other_title)

    def testUpdatesWithSameSlug(self):
        self.create(self.calendar, self.other_slug, self.title)
        course = self.create(self.calendar, self.slug, self.title)
        self.assertUpdates(course, self.other_calendar, self.other_slug, self.other_title)

    def testDoesNotUpdateWithUpperSlug(self):
        course = self.create(self.calendar, self.slug, self.title)
        self.assertDoesNotUpdate(course, self.other_calendar, self.upper_slug, self.other_title)

    def testDoesNotUpdateWithNoneTitle(self):
        course = self.create(self.calendar, self.slug, self.title)
        self.assertDoesNotUpdate(course, self.other_calendar, self.other_slug, None)

    def testDoesNotUpdateWithUpperTitle(self):
        course = self.create(self.calendar, self.slug, self.title)
        self.assertDoesNotUpdate(course, self.other_calendar, self.other_slug, self.upper_title)

    def testDoesNotUpdateWithSameKey(self):
        self.create(self.other_calendar, self.other_slug, self.other_title)
        course = self.create(self.calendar, self.slug, self.title)
        self.assertDoesNotUpdate(course, self.other_calendar, self.other_slug, self.other_title)

    def testDeletes(self):
        self.create(self.calendar, self.slug, self.title)
        self.assertDeletes(self.calendar, self.slug, self.title)

    def testDeletesWhenDoesNotExist(self):
        self.assertDeletes(self.calendar, self.slug, self.title)

    def testCascadeCalendar(self):
        self.create(self.calendar, self.slug, self.title)
        self.calendar.delete()
        self.assertDoesNotExist(self.calendar, self.slug, self.title)


class DraftCourseTests(BaseCourseTests, IntegrationTestCase):
    active = False


class CourseTests(BaseCourseTests, IntegrationTestCase):
    active = True


class ScheduleTests(IntegrationTestCase):
    title = 't'
    other_title = 'ot'

    def setUp(self):
        self.upper_title = (Schedule.title.field.max_length + 1) * 't'

        user = User.objects.create_user('u')
        begin_date = date(1983, 4, 25)
        end_date = date(1983, 5, 25)
        calendar = Calendar.objects.create(user=user, slug='cas', active=True, title='cat', begin_date=begin_date, end_date=end_date)
        self.course = Course.objects.create(calendar=calendar, slug='cos', active=True, title='cot')
        self.other_course = Course.objects.create(calendar=calendar, slug='ocos', active=True, title='ocot')

    def exists(self, course, title):
        return Schedule.objects.filter(course=course, title=title).exists()

    def create(self, course, title):
        return Schedule.objects.create(course=course, title=title)

    def retrieve(self, course, title):
        return Schedule.objects.get(course=course, title=title)

    def create_retrieve(self, course, title):
        return Schedule.objects.get_or_create(course=course, title=title)

    def update(self, schedule, course, title):
        schedule.course = course
        schedule.title = title
        schedule.save()

    def delete(self, course, title):
        Schedule.objects.filter(course=course, title=title).delete()

    def assertExists(self, course, title):
        self.assertTrue(self.exists(course, title))
        schedule = self.retrieve(course, title)
        self.assertEqual(course, schedule.course)
        self.assertEqual(title, schedule.title)

    def assertDoesNotExist(self, course, title):
        self.assertFalse(self.exists(course, title))
        with self.assertRaises(Schedule.DoesNotExist):
            self.retrieve(course, title)

    def assertCreates(self, course, title):
        self.create(course, title)
        self.assertExists(course, title)

    def assertDoesNotCreate(self, course, title):
        with self.assertRaises(DatabaseError):
            self.create(course, title)

    def assertCreatesToRetrieve(self, course, title):
        _, created = self.create_retrieve(course, title)
        self.assertExists(course, title)
        self.assertTrue(created)

    def assertDoesNotCreateToRetrieve(self, course, title):
        self.create(course, title)
        _, created = self.create_retrieve(course, title)
        self.assertFalse(created)

    def assertUpdates(self, schedule, course, title):
        self.update(schedule, course, title)
        self.assertExists(course, title)

    def assertDoesNotUpdate(self, schedule, course, title):
        with self.assertRaises(DatabaseError):
            self.update(schedule, course, title)

    def assertDeletes(self, course, title):
        self.delete(course, title)
        self.assertDoesNotExist(course, title)

    def testDoesNotExist(self):
        self.assertDoesNotExist(self.course, self.title)

    def testCreates(self):
        self.assertCreates(self.course, self.title)

    def testDoesNotCreateWithNoneCourse(self):
        self.assertDoesNotCreate(None, self.title)

    def testDoesNotCreateWithNoneTitle(self):
        self.assertDoesNotCreate(self.course, None)

    def testDoesNotCreateWithUpperTitle(self):
        self.assertDoesNotCreate(self.course, self.upper_title)

    def testCreatesToRetrieve(self):
        self.assertCreatesToRetrieve(self.course, self.title)

    def testDoesNotCreateToRetrieve(self):
        self.assertDoesNotCreateToRetrieve(self.course, self.title)

    def testUpdates(self):
        schedule = self.create(self.course, self.title)
        self.assertUpdates(schedule, self.other_course, self.other_title)

    def testDoesNotUpdateWithNoneCourse(self):
        schedule = self.create(self.course, self.title)
        self.assertDoesNotUpdate(schedule, None, self.other_title)

    def testDoesNotUpdateWithNoneTitle(self):
        schedule = self.create(self.course, self.title)
        self.assertDoesNotUpdate(schedule, self.other_course, None)

    def testDoesNotUpdateWithUpperTitle(self):
        schedule = self.create(self.course, self.title)
        self.assertDoesNotUpdate(schedule, self.other_course, self.upper_title)

    def testDeletes(self):
        self.create(self.course, self.title)
        self.assertDeletes(self.course, self.title)

    def testDeletesWhenDoesNotExist(self):
        self.assertDeletes(self.course, self.title)

    def testCascadeCourse(self):
        self.create(self.course, self.title)
        self.course.delete()
        self.assertDoesNotExist(self.course, self.title)


class SingleEventTests(IntegrationTestCase):
    place = 'p'
    other_place = 'pt'

    def setUp(self):
        self.upper_place = (SingleEvent.place.field.max_length + 1) * 'p'

        self.date = date(1983, 4, 25)
        self.other_date = date(1983, 4, 26)

        self.begin_time = SingleEvent.time(6, 15)
        self.other_begin_time = SingleEvent.time(6, 16)

        self.end_time = SingleEvent.time(12, 30)
        self.other_end_time = SingleEvent.time(12, 31)

        user = User.objects.create_user('u')
        begin_date = date(1983, 4, 26)
        end_date = date(1983, 5, 26)
        calendar = Calendar.objects.create(user=user, slug='cas', active=True, title='cat', begin_date=begin_date, end_date=end_date)
        course = Course.objects.create(calendar=calendar, slug='cos', active=True, title='cot')
        self.schedule = Schedule.objects.create(course=course, title='st')
        self.other_schedule = Schedule.objects.create(course=course, title='ost')

    def exists(self, schedule, date, begin_time, end_time, place):
        return SingleEvent.objects.filter(schedule=schedule, date=date, begin_time=begin_time, end_time=end_time, place=place).exists()

    def create(self, schedule, date, begin_time, end_time, place):
        return SingleEvent.objects.create(schedule=schedule, date=date, begin_time=begin_time, end_time=end_time, place=place)

    def retrieve(self, schedule, date, begin_time, end_time, place):
        return SingleEvent.objects.get(schedule=schedule, date=date, begin_time=begin_time, end_time=end_time, place=place)

    def create_retrieve(self, schedule, date, begin_time, end_time, place):
        return SingleEvent.objects.get_or_create(schedule=schedule, date=date, begin_time=begin_time, end_time=end_time, place=place)

    def update(self, single_event, schedule, date, begin_time, end_time, place):
        single_event.schedule = schedule
        single_event.date = date
        single_event.begin_time = begin_time
        single_event.end_time = end_time
        single_event.place = place
        single_event.save()

    def delete(self, schedule, date, begin_time, end_time, place):
        SingleEvent.objects.filter(schedule=schedule, date=date, begin_time=begin_time, end_time=end_time, place=place).delete()

    def assertExists(self, schedule, date, begin_time, end_time, place):
        self.assertTrue(self.exists(schedule, date, begin_time, end_time, place))
        single_event = self.retrieve(schedule, date, begin_time, end_time, place)
        self.assertEqual(schedule, single_event.schedule)
        self.assertEqual(date, single_event.date)
        self.assertEqual(begin_time, single_event.begin_time)
        self.assertEqual(end_time, single_event.end_time)
        self.assertEqual(place, single_event.place)

    def assertDoesNotExist(self, schedule, date, begin_time, end_time, place):
        self.assertFalse(self.exists(schedule, date, begin_time, end_time, place))
        with self.assertRaises(SingleEvent.DoesNotExist):
            self.retrieve(schedule, date, begin_time, end_time, place)

    def assertCreates(self, schedule, date, begin_time, end_time, place):
        self.create(schedule, date, begin_time, end_time, place)
        self.assertExists(schedule, date, begin_time, end_time, place)

    def assertDoesNotCreate(self, schedule, date, begin_time, end_time, place):
        with self.assertRaises(DatabaseError):
            self.create(schedule, date, begin_time, end_time, place)

    def assertCreatesToRetrieve(self, schedule, date, begin_time, end_time, place):
        _, created = self.create_retrieve(schedule, date, begin_time, end_time, place)
        self.assertExists(schedule, date, begin_time, end_time, place)
        self.assertTrue(created)

    def assertDoesNotCreateToRetrieve(self, schedule, date, begin_time, end_time, place):
        self.create(schedule, date, begin_time, end_time, place)
        _, created = self.create_retrieve(schedule, date, begin_time, end_time, place)
        self.assertFalse(created)

    def assertUpdates(self, single_event, schedule, date, begin_time, end_time, place):
        self.update(single_event, schedule, date, begin_time, end_time, place)
        self.assertExists(schedule, date, begin_time, end_time, place)

    def assertDoesNotUpdate(self, single_event, schedule, date, begin_time, end_time, place):
        with self.assertRaises(DatabaseError):
            self.update(single_event, schedule, date, begin_time, end_time, place)

    def assertDeletes(self, schedule, date, begin_time, end_time, place):
        self.delete(schedule, date, begin_time, end_time, place)
        self.assertDoesNotExist(schedule, date, begin_time, end_time, place)

    def testDoesNotExist(self):
        self.assertDoesNotExist(self.schedule, self.date, self.begin_time, self.end_time, self.place)

    def testCreates(self):
        self.assertCreates(self.schedule, self.date, self.begin_time, self.end_time, self.place)

    def testDoesNotCreateWithNoneSchedule(self):
        self.assertDoesNotCreate(None, self.date, self.begin_time, self.end_time, self.place)

    def testDoesNotCreateWithNoneDate(self):
        self.assertDoesNotCreate(self.schedule, None, self.begin_time, self.end_time, self.place)

    def testDoesNotCreateWithNoneBeginTime(self):
        self.assertDoesNotCreate(self.schedule, self.date, None, self.end_time, self.place)

    def testDoesNotCreateWithNoneEndTime(self):
        self.assertDoesNotCreate(self.schedule, self.date, self.begin_time, None, self.place)

    def testCreatesWithNoneTimes(self):
        self.assertCreates(self.schedule, self.date, None, None, self.place)

    def testDoesNotCreateWithUnorderedTimes(self):
        self.assertDoesNotCreate(self.schedule, self.date, self.end_time, self.begin_time, self.place)

    def testCreatesWithNonePlace(self):
        self.assertCreates(self.schedule, self.date, self.begin_time, self.end_time, None)

    def testDoesNotCreateWithUpperPlace(self):
        self.assertDoesNotCreate(self.schedule, self.date, self.begin_time, self.end_time, self.upper_place)

    def testCreatesToRetrieve(self):
        self.assertCreatesToRetrieve(self.schedule, self.date, self.begin_time, self.end_time, self.place)

    def testDoesNotCreateToRetrieve(self):
        self.assertDoesNotCreateToRetrieve(self.schedule, self.date, self.begin_time, self.end_time, self.place)

    def testUpdates(self):
        single_event = self.create(self.schedule, self.date, self.begin_time, self.end_time, self.place)
        self.assertUpdates(single_event, self.other_schedule, self.other_date, self.other_begin_time, self.other_end_time, self.other_place)

    def testDoesNotUpdateWithNoneSchedule(self):
        single_event = self.create(self.schedule, self.date, self.begin_time, self.end_time, self.place)
        self.assertDoesNotUpdate(single_event, None, self.other_date, self.other_begin_time, self.other_end_time, self.other_place)

    def testDoesNotUpdateWithNoneDate(self):
        single_event = self.create(self.schedule, self.date, self.begin_time, self.end_time, self.place)
        self.assertDoesNotUpdate(single_event, self.other_schedule, None, self.other_begin_time, self.other_end_time, self.other_place)

    def testDoesNotUpdateWithNoneBeginTime(self):
        single_event = self.create(self.schedule, self.date, self.begin_time, self.end_time, self.place)
        self.assertDoesNotUpdate(single_event, self.other_schedule, self.other_date, None, self.other_end_time, self.other_place)

    def testDoesNotUpdateWithNoneEndTime(self):
        single_event = self.create(self.schedule, self.date, self.begin_time, self.end_time, self.place)
        self.assertDoesNotUpdate(single_event, self.other_schedule, self.other_date, self.other_begin_time, None, self.other_place)

    def testUpdatesWithNoneTimes(self):
        single_event = self.create(self.schedule, self.date, self.begin_time, self.end_time, self.place)
        self.assertUpdates(single_event, self.other_schedule, self.other_date, None, None, self.other_place)

    def testDoesNotUpdateWithUnorderedTimes(self):
        single_event = self.create(self.schedule, self.date, self.begin_time, self.end_time, self.place)
        self.assertDoesNotUpdate(single_event, self.other_schedule, self.other_date, self.other_end_time, self.other_begin_time, self.other_place)

    def testUpdatesWithNonePlace(self):
        single_event = self.create(self.schedule, self.date, self.begin_time, self.end_time, self.place)
        self.assertUpdates(single_event, self.other_schedule, self.other_date, self.other_begin_time, self.other_end_time, None)

    def testDoesNotUpdateWithUpperPlace(self):
        single_event = self.create(self.schedule, self.date, self.begin_time, self.end_time, self.place)
        self.assertDoesNotUpdate(single_event, self.other_schedule, self.other_date, self.other_begin_time, self.other_end_time, self.upper_place)

    def testDeletes(self):
        self.create(self.schedule, self.date, self.begin_time, self.end_time, self.place)
        self.assertDeletes(self.schedule, self.date, self.begin_time, self.end_time, self.place)

    def testDeletesWhenDoesNotExist(self):
        self.assertDeletes(self.schedule, self.date, self.begin_time, self.end_time, self.place)

    def testDeletesWithNoneTimes(self):
        self.create(self.schedule, self.date, self.begin_time, self.end_time, self.place)
        self.assertDeletes(self.schedule, self.date, None, None, self.place)

    def testDeletesWithNonePlace(self):
        self.create(self.schedule, self.date, self.begin_time, self.end_time, self.place)
        self.assertDeletes(self.schedule, self.date, self.begin_time, self.end_time, None)

    def testCascadeSchedule(self):
        self.create(self.schedule, self.date, self.begin_time, self.end_time, self.place)
        self.schedule.delete()
        self.assertDoesNotExist(self.schedule, self.date, self.begin_time, self.end_time, self.place)


class WeeklyEventTests(IntegrationTestCase):
    place = 'p'
    other_place = 'pt'

    def setUp(self):
        self.upper_place = (WeeklyEvent.place.field.max_length + 1) * 'p'

        self.weekday = Weekday.MONDAY
        self.other_weekday = Weekday.SUNDAY

        self.begin_time = WeeklyEvent.time(6, 15)
        self.other_begin_time = WeeklyEvent.time(6, 16)

        self.end_time = WeeklyEvent.time(12, 30)
        self.other_end_time = WeeklyEvent.time(12, 31)

        user = User.objects.create_user('u')
        begin_date = date(1983, 4, 26)
        end_date = date(1983, 5, 26)
        calendar = Calendar.objects.create(user=user, slug='cas', active=True, title='cat', begin_date=begin_date, end_date=end_date)
        course = Course.objects.create(calendar=calendar, slug='cos', active=True, title='cot')
        self.schedule = Schedule.objects.create(course=course, title='st')
        self.other_schedule = Schedule.objects.create(course=course, title='ost')

    def exists(self, schedule, weekday, begin_time, end_time, place):
        return WeeklyEvent.objects.filter(schedule=schedule, weekday=weekday, begin_time=begin_time, end_time=end_time, place=place).exists()

    def create(self, schedule, weekday, begin_time, end_time, place):
        return WeeklyEvent.objects.create(schedule=schedule, weekday=weekday, begin_time=begin_time, end_time=end_time, place=place)

    def retrieve(self, schedule, weekday, begin_time, end_time, place):
        return WeeklyEvent.objects.get(schedule=schedule, weekday=weekday, begin_time=begin_time, end_time=end_time, place=place)

    def create_retrieve(self, schedule, weekday, begin_time, end_time, place):
        return WeeklyEvent.objects.get_or_create(schedule=schedule, weekday=weekday, begin_time=begin_time, end_time=end_time, place=place)

    def update(self, weekly_event, schedule, weekday, begin_time, end_time, place):
        weekly_event.schedule = schedule
        weekly_event.weekday = weekday
        weekly_event.begin_time = begin_time
        weekly_event.end_time = end_time
        weekly_event.place = place
        weekly_event.save()

    def delete(self, schedule, weekday, begin_time, end_time, place):
        WeeklyEvent.objects.filter(schedule=schedule, weekday=weekday, begin_time=begin_time, end_time=end_time, place=place).delete()

    def assertExists(self, schedule, weekday, begin_time, end_time, place):
        self.assertTrue(self.exists(schedule, weekday, begin_time, end_time, place))
        weekly_event = self.retrieve(schedule, weekday, begin_time, end_time, place)
        self.assertEqual(schedule, weekly_event.schedule)
        self.assertEqual(weekday, weekly_event.weekday)
        self.assertEqual(begin_time, weekly_event.begin_time)
        self.assertEqual(end_time, weekly_event.end_time)
        self.assertEqual(place, weekly_event.place)

    def assertDoesNotExist(self, schedule, weekday, begin_time, end_time, place):
        self.assertFalse(self.exists(schedule, weekday, begin_time, end_time, place))
        with self.assertRaises(WeeklyEvent.DoesNotExist):
            self.retrieve(schedule, weekday, begin_time, end_time, place)

    def assertCreates(self, schedule, weekday, begin_time, end_time, place):
        self.create(schedule, weekday, begin_time, end_time, place)
        self.assertExists(schedule, weekday, begin_time, end_time, place)

    def assertDoesNotCreate(self, schedule, weekday, begin_time, end_time, place):
        with self.assertRaises(DatabaseError):
            self.create(schedule, weekday, begin_time, end_time, place)

    def assertCreatesToRetrieve(self, schedule, weekday, begin_time, end_time, place):
        _, created = self.create_retrieve(schedule, weekday, begin_time, end_time, place)
        self.assertExists(schedule, weekday, begin_time, end_time, place)
        self.assertTrue(created)

    def assertDoesNotCreateToRetrieve(self, schedule, weekday, begin_time, end_time, place):
        self.create(schedule, weekday, begin_time, end_time, place)
        _, created = self.create_retrieve(schedule, weekday, begin_time, end_time, place)
        self.assertFalse(created)

    def assertUpdates(self, single_event, schedule, weekday, begin_time, end_time, place):
        self.update(single_event, schedule, weekday, begin_time, end_time, place)
        self.assertExists(schedule, weekday, begin_time, end_time, place)

    def assertDoesNotUpdate(self, single_event, schedule, weekday, begin_time, end_time, place):
        with self.assertRaises(DatabaseError):
            self.update(single_event, schedule, weekday, begin_time, end_time, place)

    def assertDeletes(self, schedule, weekday, begin_time, end_time, place):
        self.delete(schedule, weekday, begin_time, end_time, place)
        self.assertDoesNotExist(schedule, weekday, begin_time, end_time, place)

    def testDoesNotExist(self):
        self.assertDoesNotExist(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)

    def testCreates(self):
        self.assertCreates(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)

    def testDoesNotCreateWithNoneSchedule(self):
        self.assertDoesNotCreate(None, self.weekday, self.begin_time, self.end_time, self.place)

    def testDoesNotCreateWithNoneWeekday(self):
        self.assertDoesNotCreate(self.schedule, None, self.begin_time, self.end_time, self.place)

    def testDoesNotCreateWithNoneBeginTime(self):
        self.assertDoesNotCreate(self.schedule, self.weekday, None, self.end_time, self.place)

    def testDoesNotCreateWithNoneEndTime(self):
        self.assertDoesNotCreate(self.schedule, self.weekday, self.begin_time, None, self.place)

    def testCreatesWithNoneTimes(self):
        self.assertCreates(self.schedule, self.weekday, None, None, self.place)

    def testDoesNotCreateWithUnorderedTimes(self):
        self.assertDoesNotCreate(self.schedule, self.weekday, self.end_time, self.begin_time, self.place)

    def testCreatesWithNonePlace(self):
        self.assertCreates(self.schedule, self.weekday, self.begin_time, self.end_time, None)

    def testDoesNotCreateWithUpperPlace(self):
        self.assertDoesNotCreate(self.schedule, self.weekday, self.begin_time, self.end_time, self.upper_place)

    def testCreatesToRetrieve(self):
        self.assertCreatesToRetrieve(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)

    def testDoesNotCreateToRetrieve(self):
        self.assertDoesNotCreateToRetrieve(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)

    def testUpdates(self):
        weekly_event = self.create(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)
        self.assertUpdates(weekly_event, self.other_schedule, self.other_weekday, self.other_begin_time, self.other_end_time, self.other_place)

    def testDoesNotUpdateWithNoneSchedule(self):
        weekly_event = self.create(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)
        self.assertDoesNotUpdate(weekly_event, None, self.other_weekday, self.other_begin_time, self.other_end_time, self.other_place)

    def testDoesNotUpdateWithNoneWeekday(self):
        weekly_event = self.create(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)
        self.assertDoesNotUpdate(weekly_event, self.other_schedule, None, self.other_begin_time, self.other_end_time, self.other_place)

    def testDoesNotUpdateWithNoneBeginTime(self):
        weekly_event = self.create(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)
        self.assertDoesNotUpdate(weekly_event, self.other_schedule, self.other_weekday, None, self.other_end_time, self.other_place)

    def testDoesNotUpdateWithNoneEndTime(self):
        weekly_event = self.create(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)
        self.assertDoesNotUpdate(weekly_event, self.other_schedule, self.other_weekday, self.other_begin_time, None, self.other_place)

    def testUpdatesWithNoneTimes(self):
        weekly_event = self.create(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)
        self.assertUpdates(weekly_event, self.other_schedule, self.other_weekday, None, None, self.other_place)

    def testDoesNotUpdateWithUnorderedTimes(self):
        weekly_event = self.create(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)
        self.assertDoesNotUpdate(weekly_event, self.other_schedule, self.other_weekday, self.other_end_time, self.other_begin_time, self.other_place)

    def testUpdatesWithNonePlace(self):
        weekly_event = self.create(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)
        self.assertUpdates(weekly_event, self.other_schedule, self.other_weekday, self.other_begin_time, self.other_end_time, None)

    def testDoesNotUpdateWithUpperPlace(self):
        weekly_event = self.create(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)
        self.assertDoesNotUpdate(weekly_event, self.other_schedule, self.other_weekday, self.other_begin_time, self.other_end_time, self.upper_place)

    def testDeletes(self):
        self.create(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)
        self.assertDeletes(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)

    def testDeletesWhenDoesNotExist(self):
        self.assertDeletes(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)

    def testDeletesWithNoneTimes(self):
        self.create(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)
        self.assertDeletes(self.schedule, self.weekday, None, None, self.place)

    def testDeletesWithNonePlace(self):
        self.create(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)
        self.assertDeletes(self.schedule, self.weekday, self.begin_time, self.end_time, None)

    def testCascadeSchedule(self):
        self.create(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)
        self.schedule.delete()
        self.assertDoesNotExist(self.schedule, self.weekday, self.begin_time, self.end_time, self.place)


class CalendarCancelationTests(IntegrationTestCase):
    title = 't'
    other_title = 'ot'

    def setUp(self):
        self.upper_title = (CalendarCancelation.title.field.max_length + 1) * 't'

        self.date = date(1983, 4, 25)
        self.other_date = date(1983, 4, 26)

        user = User.objects.create_user('u')
        begin_date = date(1983, 4, 25)
        end_date = date(1983, 5, 25)
        self.calendar = Calendar.objects.create(user=user, slug='cs', active=True, title='ct', begin_date=begin_date, end_date=end_date)
        other_begin_date = date(1983, 4, 26)
        other_end_date = date(1983, 5, 26)
        self.other_calendar = Calendar.objects.create(user=user, slug='ocs', active=True, title='oct', begin_date=other_begin_date, end_date=other_end_date)

    def exists(self, calendar, date, title):
        return CalendarCancelation.objects.filter(calendar=calendar, date=date, title=title).exists()

    def create(self, calendar, date, title):
        return CalendarCancelation.objects.create(calendar=calendar, date=date, title=title)

    def retrieve(self, calendar, date, title):
        return CalendarCancelation.objects.get(calendar=calendar, date=date, title=title)

    def create_retrieve(self, calendar, date, title):
        return CalendarCancelation.objects.get_or_create(calendar=calendar, date=date, title=title)

    def update(self, cancelation, calendar, date, title):
        cancelation.calendar = calendar
        cancelation.date = date
        cancelation.title = title
        cancelation.save()

    def delete(self, calendar, date, title):
        CalendarCancelation.objects.filter(calendar=calendar, date=date, title=title).delete()

    def assertExists(self, calendar, date, title):
        self.assertTrue(self.exists(calendar, date, title))
        cancelation = self.retrieve(calendar, date, title)
        self.assertEqual(calendar, cancelation.calendar)
        self.assertEqual(date, cancelation.date)
        self.assertEqual(title, cancelation.title)

    def assertDoesNotExist(self, calendar, date, title):
        self.assertFalse(self.exists(calendar, date, title))
        with self.assertRaises(CalendarCancelation.DoesNotExist):
            self.retrieve(calendar, date, title)

    def assertCreates(self, calendar, date, title):
        self.create(calendar, date, title)
        self.assertExists(calendar, date, title)

    def assertDoesNotCreate(self, calendar, date, title):
        with self.assertRaises(DatabaseError):
            self.create(calendar, date, title)

    def assertCreatesToRetrieve(self, calendar, date, title):
        _, created = self.create_retrieve(calendar, date, title)
        self.assertExists(calendar, date, title)
        self.assertTrue(created)

    def assertDoesNotCreateToRetrieve(self, calendar, date, title):
        self.create(calendar, date, title)
        _, created = self.create_retrieve(calendar, date, title)
        self.assertFalse(created)

    def assertUpdates(self, cancelation, calendar, date, title):
        self.update(cancelation, calendar, date, title)
        self.assertExists(calendar, date, title)

    def assertDoesNotUpdate(self, cancelation, calendar, date, title):
        with self.assertRaises(DatabaseError):
            self.update(cancelation, calendar, date, title)

    def assertDeletes(self, calendar, date, title):
        self.delete(calendar, date, title)
        self.assertDoesNotExist(calendar, date, title)

    def testDoesNotExist(self):
        self.assertDoesNotExist(self.calendar, self.date, self.title)

    def testCreates(self):
        self.assertCreates(self.calendar, self.date, self.title)

    def testDoesNotCreateWithNoneCalendar(self):
        self.assertDoesNotCreate(None, self.date, self.title)

    def testCreatesWithSameCalendar(self):
        self.create(self.calendar, self.date, self.title)
        self.assertCreates(self.calendar, self.other_date, self.other_title)

    def testDoesNotCreateWithNoneDate(self):
        self.assertDoesNotCreate(self.calendar, None, self.title)

    def testCreatesWithSameDate(self):
        self.create(self.calendar, self.date, self.title)
        self.assertCreates(self.other_calendar, self.date, self.other_title)

    def testDoesNotCreateWithNoneTitle(self):
        self.assertDoesNotCreate(self.calendar, self.date, None)

    def testDoesNotCreateWithUpperTitle(self):
        self.assertDoesNotCreate(self.calendar, self.date, self.upper_title)

    def testDoesNotCreateWithSameKey(self):
        self.create(self.calendar, self.date, self.title)
        self.assertDoesNotCreate(self.calendar, self.date, self.other_title)

    def testCreatesToRetrieve(self):
        self.assertCreatesToRetrieve(self.calendar, self.date, self.title)

    def testDoesNotCreateToRetrieve(self):
        self.assertDoesNotCreateToRetrieve(self.calendar, self.date, self.title)

    def testUpdates(self):
        cancelation = self.create(self.calendar, self.date, self.title)
        self.assertUpdates(cancelation, self.other_calendar, self.other_date, self.other_title)

    def testDoesNotUpdateWithNoneCalendar(self):
        cancelation = self.create(self.calendar, self.date, self.title)
        self.assertDoesNotUpdate(cancelation, None, self.other_date, self.other_title)

    def testUpdatesWithSameCalendar(self):
        self.create(self.other_calendar, self.date, self.title)
        cancelation = self.create(self.calendar, self.date, self.title)
        self.assertUpdates(cancelation, self.other_calendar, self.other_date, self.other_title)

    def testDoesNotUpdateWithNoneDate(self):
        cancelation = self.create(self.calendar, self.date, self.title)
        self.assertDoesNotUpdate(cancelation, self.other_calendar, None, self.other_title)

    def testUpdatesWithSameDate(self):
        self.create(self.calendar, self.other_date, self.title)
        cancelation = self.create(self.calendar, self.date, self.title)
        self.assertUpdates(cancelation, self.other_calendar, self.other_date, self.other_title)

    def testDoesNotUpdateWithNoneTitle(self):
        cancelation = self.create(self.calendar, self.date, self.title)
        self.assertDoesNotUpdate(cancelation, self.other_calendar, self.other_date, None)

    def testDoesNotUpdateWithUpperTitle(self):
        cancelation = self.create(self.calendar, self.date, self.title)
        self.assertDoesNotUpdate(cancelation, self.other_calendar, self.other_date, self.upper_title)

    def testDoesNotUpdateWithSameKey(self):
        self.create(self.other_calendar, self.other_date, self.other_title)
        cancelation = self.create(self.calendar, self.date, self.title)
        self.assertDoesNotUpdate(cancelation, self.other_calendar, self.other_date, self.other_title)

    def testDeletes(self):
        self.create(self.calendar, self.date, self.title)
        self.assertDeletes(self.calendar, self.date, self.title)

    def testDeletesWhenDoesNotExist(self):
        self.assertDeletes(self.calendar, self.date, self.title)

    def testCascadeCalendar(self):
        self.create(self.calendar, self.date, self.title)
        self.calendar.delete()
        self.assertDoesNotExist(self.calendar, self.date, self.title)


class ScheduleCancelationTests(IntegrationTestCase):
    title = 't'
    other_title = 'ot'

    def setUp(self):
        self.upper_title = (ScheduleCancelation.title.field.max_length + 1) * 't'

        self.date = date(1983, 4, 25)
        self.other_date = date(1983, 4, 26)

        user = User.objects.create_user('u')
        begin_date = date(1983, 4, 26)
        end_date = date(1983, 5, 26)
        calendar = Calendar.objects.create(user=user, slug='cas', active=True, title='cat', begin_date=begin_date, end_date=end_date)
        course = Course.objects.create(calendar=calendar, slug='cos', active=True, title='cot')
        self.schedule = Schedule.objects.create(course=course, title='st')
        self.other_schedule = Schedule.objects.create(course=course, title='ost')

    def exists(self, schedule, date, title):
        return ScheduleCancelation.objects.filter(schedule=schedule, date=date, title=title).exists()

    def create(self, schedule, date, title):
        return ScheduleCancelation.objects.create(schedule=schedule, date=date, title=title)

    def retrieve(self, schedule, date, title):
        return ScheduleCancelation.objects.get(schedule=schedule, date=date, title=title)

    def create_retrieve(self, schedule, date, title):
        return ScheduleCancelation.objects.get_or_create(schedule=schedule, date=date, title=title)

    def update(self, cancelation, schedule, date, title):
        cancelation.schedule = schedule
        cancelation.date = date
        cancelation.title = title
        cancelation.save()

    def delete(self, schedule, date, title):
        ScheduleCancelation.objects.filter(schedule=schedule, date=date, title=title).delete()

    def assertExists(self, schedule, date, title):
        self.assertTrue(self.exists(schedule, date, title))
        cancelation = self.retrieve(schedule, date, title)
        self.assertEqual(schedule, cancelation.schedule)
        self.assertEqual(date, cancelation.date)
        self.assertEqual(title, cancelation.title)

    def assertDoesNotExist(self, schedule, date, title):
        self.assertFalse(self.exists(schedule, date, title))
        with self.assertRaises(ScheduleCancelation.DoesNotExist):
            self.retrieve(schedule, date, title)

    def assertCreates(self, schedule, date, title):
        self.create(schedule, date, title)
        self.assertExists(schedule, date, title)

    def assertDoesNotCreate(self, schedule, date, title):
        with self.assertRaises(DatabaseError):
            self.create(schedule, date, title)

    def assertCreatesToRetrieve(self, schedule, date, title):
        _, created = self.create_retrieve(schedule, date, title)
        self.assertExists(schedule, date, title)
        self.assertTrue(created)

    def assertDoesNotCreateToRetrieve(self, schedule, date, title):
        self.create(schedule, date, title)
        _, created = self.create_retrieve(schedule, date, title)
        self.assertFalse(created)

    def assertUpdates(self, cancelation, schedule, date, title):
        self.update(cancelation, schedule, date, title)
        self.assertExists(schedule, date, title)

    def assertDoesNotUpdate(self, cancelation, schedule, date, title):
        with self.assertRaises(DatabaseError):
            self.update(cancelation, schedule, date, title)

    def assertDeletes(self, schedule, date, title):
        self.delete(schedule, date, title)
        self.assertDoesNotExist(schedule, date, title)

    def testDoesNotExist(self):
        self.assertDoesNotExist(self.schedule, self.date, self.title)

    def testCreates(self):
        self.assertCreates(self.schedule, self.date, self.title)

    def testDoesNotCreateWithNoneCalendar(self):
        self.assertDoesNotCreate(None, self.date, self.title)

    def testCreatesWithSameCalendar(self):
        self.create(self.schedule, self.date, self.title)
        self.assertCreates(self.schedule, self.other_date, self.other_title)

    def testDoesNotCreateWithNoneDate(self):
        self.assertDoesNotCreate(self.schedule, None, self.title)

    def testCreatesWithSameDate(self):
        self.create(self.schedule, self.date, self.title)
        self.assertCreates(self.other_schedule, self.date, self.other_title)

    def testDoesNotCreateWithNoneTitle(self):
        self.assertDoesNotCreate(self.schedule, self.date, None)

    def testDoesNotCreateWithUpperTitle(self):
        self.assertDoesNotCreate(self.schedule, self.date, self.upper_title)

    def testDoesNotCreateWithSameKey(self):
        self.create(self.schedule, self.date, self.title)
        self.assertDoesNotCreate(self.schedule, self.date, self.other_title)

    def testCreatesToRetrieve(self):
        self.assertCreatesToRetrieve(self.schedule, self.date, self.title)

    def testDoesNotCreateToRetrieve(self):
        self.assertDoesNotCreateToRetrieve(self.schedule, self.date, self.title)

    def testUpdates(self):
        cancelation = self.create(self.schedule, self.date, self.title)
        self.assertUpdates(cancelation, self.other_schedule, self.other_date, self.other_title)

    def testDoesNotUpdateWithNoneCalendar(self):
        cancelation = self.create(self.schedule, self.date, self.title)
        self.assertDoesNotUpdate(cancelation, None, self.other_date, self.other_title)

    def testUpdatesWithSameCalendar(self):
        self.create(self.other_schedule, self.date, self.title)
        cancelation = self.create(self.schedule, self.date, self.title)
        self.assertUpdates(cancelation, self.other_schedule, self.other_date, self.other_title)

    def testDoesNotUpdateWithNoneDate(self):
        cancelation = self.create(self.schedule, self.date, self.title)
        self.assertDoesNotUpdate(cancelation, self.other_schedule, None, self.other_title)

    def testUpdatesWithSameDate(self):
        self.create(self.schedule, self.other_date, self.title)
        cancelation = self.create(self.schedule, self.date, self.title)
        self.assertUpdates(cancelation, self.other_schedule, self.other_date, self.other_title)

    def testDoesNotUpdateWithNoneTitle(self):
        cancelation = self.create(self.schedule, self.date, self.title)
        self.assertDoesNotUpdate(cancelation, self.other_schedule, self.other_date, None)

    def testDoesNotUpdateWithUpperTitle(self):
        cancelation = self.create(self.schedule, self.date, self.title)
        self.assertDoesNotUpdate(cancelation, self.other_schedule, self.other_date, self.upper_title)

    def testDoesNotUpdateWithSameKey(self):
        self.create(self.other_schedule, self.other_date, self.other_title)
        cancelation = self.create(self.schedule, self.date, self.title)
        self.assertDoesNotUpdate(cancelation, self.other_schedule, self.other_date, self.other_title)

    def testDeletes(self):
        self.create(self.schedule, self.date, self.title)
        self.assertDeletes(self.schedule, self.date, self.title)

    def testDeletesWhenDoesNotExist(self):
        self.assertDeletes(self.schedule, self.date, self.title)

    def testCascadeCalendar(self):
        self.create(self.schedule, self.date, self.title)
        self.schedule.delete()
        self.assertDoesNotExist(self.schedule, self.date, self.title)
