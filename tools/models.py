from __future__ import unicode_literals
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import models


# Create your models here.
class Ap(models.Model):
    ENCRYPTION_TYPE = (
        ('WPA2', 'WPA2_PSK'),
        ('OPEN', 'OPEN'),
        ('WPA', 'WPA_PSK'),
        ('WEP', 'WEP')
    )
    brand = models.CharField(default="", max_length=30)
    owner = models.CharField(default="", max_length=30)
    ssid = models.CharField(unique=True, max_length=50)
    type = models.CharField(choices=ENCRYPTION_TYPE, max_length=4)
    password = models.CharField(blank=True, max_length=20)

    class Meta:
        ordering = ("ssid", )

    def __unicode__(self):
        return "{}({}, {})".format(self.ssid, self.password, self.type)

