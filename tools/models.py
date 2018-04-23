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
    aging = models.DateTimeField(blank=True)
    type = models.CharField(choices=ENCRYPTION_TYPE, max_length=4)
    password = models.CharField(blank=True, max_length=20)

    class Meta:
        ordering = ("ssid", )

    def aging_time(self):
        result = None
        if self.aging is not None:
            tzinfo = self.aging.tzinfo
            now = datetime.now() if tzinfo is None else datetime.now(pytz.timezone(str(tzinfo)))
            seconds = now - self.aging
            result = "{:.2f}".format(seconds.total_seconds() / 60)
        return result


    def __unicode__(self):
        return "{}({}, {}, aging={})".format(self.ssid, self.password, self.type, self.aging)

