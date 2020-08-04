from django.core.cache import cache

from .models import PowerUser


class PowerCache:
    def key(self, user):
        return 'power:' + user.get_username()

    def miss(self, user):
        return PowerUser.objects.filter(user=user).exists()

    def get(self, user):
        return cache.get_or_set(self.key(user), lambda: self.miss(user))

    def set(self, user, value):
        cache.set(self.key(user), value)


class MemberCache:
    pass


power_cache = PowerCache()
member_cache = MemberCache()
