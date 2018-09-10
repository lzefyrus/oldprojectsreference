# encode: utf-8

from django.conf import settings
from django.db import models


# Create your models here.


def operator_upload(instance, filename):
    import os
    _, filename_ext = os.path.splitext(filename)
    return 'operators/{0}{1}'.format(instance.pk, filename_ext)


class Operator(models.Model):
    avatar = models.ImageField(upload_to=operator_upload, null=True, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True, on_delete=models.CASCADE)

    def __str__(self):
        return "%s" % self.user.username
