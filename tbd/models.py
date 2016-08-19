from __future__ import unicode_literals
from django.utils import timezone
from django.db import models

class AttrLookup(object):
    def __init__(self, func, instance=None):
        self._func = func
        self._instance = instance

    def __get__(self, instance, owner):
        return AttrLookup(self._func, instance)

    def __getitem__(self, argument):
        return self._func(self._instance, argument)

    def __call__(self, *args):
        if len(args) == 0:
            return self
        else:
            return self._func(self._instance, *args)

# Create your models here.
class Project(models.Model):
    name = models.CharField(unique=True, default='', max_length=30)
    owner = models.CharField(unique=False, default='', max_length=30)
    create = models.DateTimeField(unique=False, auto_now_add=True)
    _attr = models.TextField(unique=False, default='')
    
    @AttrLookup
    def attr(self,  name,  value=None):
        attr_list = self._attr.split(';')
        is_updated = False
        if value is not None:
            value = str(value)
        for i,  k_v in enumerate(attr_list):
            if k_v.startswith(name+'='):
                if value is None:
                    get_val = k_v[len(name)+1:]
                    if get_val:
                        print "!!!!!!!!!!! attr get {}={}".format(name, get_val)
                        return get_val
                    else:
                        attr_list[i] = ''
                        is_updated = True
                else:
                    attr_list[i] = "{}={}".format(name,  value)
                    is_updated = True
        if (value is not None) and (not is_updated):
            if len(value):
                is_updated = True
                attr_list.append('{}={}'.format(name,  value))
        if is_updated:
            self._attr = ';'.join([i for i in attr_list if i])
            print "!!!!!!!!!!! attr set {}={}, new _attr={}!".format(name, value, self._attr)
            return value
        return ''

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
    name = models.CharField(default='', max_length=50)
    ip = models.GenericIPAddressField(protocol='IPv4', default='')
    mac = models.CharField(default='', max_length=12)
    
    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        verbose_name="the related project",
        null=True
    )
    
    class Meta:
        unique_together = ("project", "name")
        
    def __unicode__(self):
        return "Host {}(IPv4{})".format(self.name, self.ip)
        
class TestCase(models.Model):
    PHOENIX = 'PH'
    VEGA    = 'VE'
    WPA     = 'WP'
    GARNET  = 'GA'
    PLATFORM_CHOICE = (
        ('', '--select testcase--'),
        (PHOENIX, 'Phoenix XML'),
        (VEGA, 'Vega XML'),
        (GARNET, 'Garnet XML'),
        (WPA, 'WPA Perl'),
    )
    name = models.CharField(default='', max_length=80)
    platform = models.CharField(default='', choices=PLATFORM_CHOICE, max_length=2)
    
    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        verbose_name="the related project",
        null=True
    )
    
    class Meta:
        unique_together = ("project", "name", "platform")
        
    def __unicode__(self):
        return "TestCase {}({})".format(self.name, self.platform)

class JIRA(models.Model):
    OPEN = 'OP'
    INVALID     = 'IN'
    WITHDRAW  = 'WD'
    CNSS    = 'CN'
    NONCNSS = 'NC'
    CATEGORY_CHOICE = (
        (OPEN, 'Open Issue'),
        (INVALID, 'Invalid Issue'),
        (WITHDRAW, 'Withdraw Issue'),
        (CNSS, 'CNSS Issue'),
        (NONCNSS, 'Non-CNSS Issue'),
    )
    jira_id = models.CharField(unique=True, default='', max_length=20)
    category = models.CharField(default=OPEN, choices=CATEGORY_CHOICE, max_length=2)
    
    def is_valid(self):
        return self.category in (self.CNSS, self.NONCNSS)
        
    def is_cnss(self):
        return self.category == self.CNSS
    
    def __unicode__(self):
        return "JIRA {}".format(self.jira_id)
        
class Crash(models.Model):
    path = models.CharField(unique=True, default='', max_length=255)
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
    
    jira = models.ForeignKey(
        JIRA,
        on_delete=models.PROTECT,
        verbose_name="the related JIRA",
        null = True
    )
    
    def __unicode__(self):
        return "Crash {}({})".format(self.host.name, self.path)
        
            
