from __future__ import unicode_literals
from django.utils import timezone
from django.db import models

# Create your models here.
class Project(models.Model):
    name = models.CharField(unique=True, default='', max_length=30)
    owner = models.CharField(unique=False, default='', max_length=30)
    create = models.DateTimeField(unique=False, auto_now_add=True)
    
    def __unicode__(self):
        return "Project {}({})".format(self.name, self.owner)

class Build(models.Model):
    version = models.CharField(default='', max_length=80)
    short_name = models.CharField(default='', max_length=20)
    server_path = models.CharField(default='', max_length=255)
    local_path = models.CharField(blank=True, default='', max_length=255)
    crash_path = models.CharField(default='', max_length=255)
    use_server = models.BooleanField(default=False)
    create = models.DateTimeField(auto_now_add=True)
    
    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        verbose_name="the related project",
    )
    
    class Meta:
        unique_together = ("version", "project")
        
    def __unicode__(self):
        return "Build {}({})".format(self.short_name, self.version)
        
class Host(models.Model):
    name = models.CharField(unique=True, default='', max_length=50)
    ip = models.GenericIPAddressField(protocol='IPv4', default='')
    mac = models.CharField(default='', max_length=12)
    
    def __unicode__(self):
        return "Host {}(IPv4{})".format(self.name, self.ip)
        
class TestCase(models.Model):
    name = models.CharField(unique=True, default='', max_length=80)
    platform = models.CharField(default='', max_length=30)
    
    def __unicode__(self):
        return "TestCase {}({})".format(self.name, self.platform)
        
        