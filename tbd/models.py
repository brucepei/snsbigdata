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
    PHOENIX = 'PH'
    VEGA    = 'VE'
    WPA     = 'WP'
    GARNET  = 'GA'
    PLATFORM_CHOICE = (
        (PHOENIX, 'Phoenix XML'),
        (VEGA, 'Vega XML'),
        (GARNET, 'Garnet XML'),
        (WPA, 'WPA Perl'),
    )
    name = models.CharField(default='', max_length=80)
    platform = models.CharField(default='', choices=PLATFORM_CHOICE, max_length=2)
    
    class Meta:
        unique_together = ("name", "platform")
        
    def __unicode__(self):
        return "TestCase {}({})".format(self.name, self.platform)
        
class Crash(models.Model):
    UNDETERMINED = 'UN'
    INVALID     = 'IN'
    WITHDRAW  = 'WD'
    CNSS    = 'CN'
    NONCNSS = 'NC'
    CATEGORY_CHOICE = (
        (UNDETERMINED, 'Undetermined Issue'),
        (INVALID, 'Invalid Issue'),
        (WITHDRAW, 'Withdraw Issue'),
        (CNSS, 'CNSS Issue'),
        (NONCNSS, 'Non-CNSS Issue'),
    )
    path = models.CharField(unique=True, default='', max_length=255)
    category = models.CharField(default=UNDETERMINED, choices=CATEGORY_CHOICE, max_length=2)
    create = models.DateTimeField(auto_now_add=True)
    
    build = models.ForeignKey(
        Build,
        on_delete=models.PROTECT,
        verbose_name="the related build",
    )
    host = models.ForeignKey(
        Host,
        on_delete=models.PROTECT,
        verbose_name="the related host",
    )
    testcase = models.ForeignKey(
        TestCase,
        on_delete=models.PROTECT,
        verbose_name="the related testcase",
    )
    
    def is_valid(self):
        return self.category in (self.CNSS, self.NONCNSS)
        
    def is_cnss(self):
        return self.category == self.CNSS
        
            