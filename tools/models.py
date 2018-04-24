from __future__ import unicode_literals
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import models
from datetime import datetime
import pytz

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
    ping_aging = models.DateTimeField(null=True, blank=True)
    type = models.CharField(choices=ENCRYPTION_TYPE, max_length=4)
    password = models.CharField(blank=True, max_length=20)
    ip = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        ordering = ("ssid", )

    @classmethod
    def aging_time(cls, aging):
        result = None
        if aging is not None:
            now = datetime.now(pytz.timezone('UTC'))
            seconds = now - aging
            result = "{:.2f}".format(seconds.total_seconds() / 60)
        return result

    def update_aging(self, aging_type):
        if aging_type == 'ping':
            self.ping_aging = datetime.now(pytz.timezone('UTC'))

    def __unicode__(self):
        return "{}({}, {}, ip={})".format(self.ssid, self.password, self.type, self.ip)

