from __future__ import unicode_literals
from django.utils import timezone
from django.db import models

# Create your models here.
class Project(models.Model):
    name = models.CharField(unique=True, default='', max_length=30)
    owner = models.CharField(unique=False, default='', max_length=30)
    create = models.DateTimeField(unique=False, default=timezone.now())