
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class PowerUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
