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
    last_update = models.DateTimeField(unique=False, auto_now=True)
    is_stop = models.BooleanField(default=False)
    _attr = models.TextField(unique=False, default='')
    
    @AttrLookup
    def attr(self,  name,  value=None):
        attr_list = self._attr.split(';')
        is_updated = False
        is_found = False
        if value is not None:
            value = str(value)
        print("Ready to call attr({}, {}) in project {}!".format(name, value, self.name))
        for i,  k_v in enumerate(attr_list):
            if k_v.startswith(name+'='):
                if value is None:
                    get_val = k_v[len(name)+1:]
                    if get_val:
                        print("!!!!!!!!!!! attr get {}={} in project {} attr={}!".format(name, get_val, self.name, self._attr))
                        return get_val
                    else:
                        attr_list[i] = ''
                        is_updated = True
                else:
                    orig_val = k_v[len(name)+1:]
                    is_found = True
                    if orig_val != value:
                        attr_list[i] = "{}={}".format(name,  value)
                        is_updated = True
                break
        if (value is not None) and (not is_found):
            if len(value):
                is_updated = True
                attr_list.append('{}={}'.format(name,  value))
        if is_updated:
            self._attr = ';'.join([i for i in attr_list if i])
            print("!!!!!!!!!!! attr set {}={}, new _attr={} in project {}!".format(name, value, self._attr, self.name))
            if value is None:
                self.save()
                return ''
            return True
        return ''

    class Meta:
        ordering = ('-create',)
        
    def __unicode__(self):
        return "Project {}({})".format(self.name, self.owner)

class Build(models.Model):
    version = models.CharField(default='', max_length=80)
    short_name = models.CharField(default='', max_length=80)
    server_path = models.CharField(default='', max_length=255)
    local_path = models.CharField(blank=True, default='', max_length=255)
    crash_path = models.CharField(default='', max_length=255)
    use_server = models.BooleanField(default=False)
    test_hours = models.PositiveIntegerField(default=0)
    is_stop = models.BooleanField(default=False)
    create = models.DateTimeField(auto_now_add=True)
    
    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        verbose_name="the related project",
    )
    
    class Meta:
        unique_together = ('project', 'version')
        ordering = ('project', '-create')
        
    def __unicode__(self):
        return "Build {}({})".format(self.short_name, self.version)
        
class Host(models.Model):
    name = models.CharField(default='', max_length=50)
    ip = models.CharField(default='', max_length=15)
    mac = models.CharField(default='', max_length=17)
    is_default = models.BooleanField(default=False)
    
    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        verbose_name="the related project",
        null=True
    )
    
    class Meta:
        unique_together = ("project", "name")
        ordering = ('project', 'name')
        
    def __unicode__(self):
        return "{}".format(self.name)

class TestAction(models.Model):
    name = models.CharField(default='', max_length=80)
    is_default = models.BooleanField(default=False)

    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        verbose_name="the related project",
        null=True
    )
    
    class Meta:
        unique_together = ("project", "name")
        ordering = ('project', 'name',)
        
    def __unicode__(self):
        return "{}".format(self.name)
    
class TestCase(models.Model):
    PHOENIX = 'PHO'
    VEGA    = 'VEG'
    WPA     = 'WPA'
    GARNET  = 'GAR'
    PAT     = 'PAT'
    PLATFORM_CHOICE = (
        ('', 'N/A'),
        (PHOENIX, 'Phoenix XML'),
        (VEGA, 'Vega XML'),
        (GARNET, 'Garnet XML'),
        (WPA, 'WPA Perl'),
        (PAT, 'PAT Python'),
    )
    name = models.CharField(default='', max_length=80)
    platform = models.CharField(default='', choices=PLATFORM_CHOICE, max_length=3)
    is_default = models.BooleanField(default=False)
    testactions = models.ManyToManyField(TestAction)
    
    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        verbose_name="the related project",
        null=True
    )
    
    class Meta:
        unique_together = ("project", "name")
        ordering = ('project', 'name',)
        
    def __unicode__(self):
        return "{}".format(self.name)

class TestResult(models.Model):
    pass_count = models.PositiveIntegerField(default=0)
    fail_count = models.PositiveIntegerField(default=0)
    last_update = models.DateTimeField(unique=False, auto_now=True)
    
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
    testaction = models.ForeignKey(
        TestAction,
        on_delete=models.PROTECT,
        verbose_name="the related testaction",
    )
    
    class Meta:
        unique_together = ("build", "host", "testaction")
        ordering = ('build', 'host', 'testaction')
        
    def __unicode__(self):
        return "{}-()-{}({}/{})".format(self.build.version, self.host.name, self.testaction.name, self.pass_count, self.fail_count)

class JIRA(models.Model):
    NONE = ''
    OPEN = 'OP'
    INVALID     = 'IN'
    WITHDRAW  = 'WD'
    CNSS    = 'CN'
    NONCNSS = 'NC'
    CATEGORY_CHOICE = (
        (NONE, ''),
        (OPEN, 'Open'),
        (INVALID, 'Invalid'),
        (WITHDRAW, 'Withdraw'),
        (CNSS, 'CNSS'),
        (NONCNSS, 'Non-CNSS'),
    )
    jira_id = models.CharField(unique=True, default='', max_length=20)
    category = models.CharField(default=OPEN, choices=CATEGORY_CHOICE, max_length=2)
    cr_id = models.CharField(default='', blank=True, max_length=20)
    is_default = models.BooleanField(default=False)
    
    def is_valid(self):
        return self.category in (self.OPEN, self.CNSS, self.NONCNSS)
        
    def is_cnss(self):
        return self.category == self.CNSS
    
    def __unicode__(self):
        return "{}".format(self.jira_id)
        
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
    )
    
    class Meta:
        ordering = ('build', '-create')
        
    def __unicode__(self):
        return "Crash {}({})".format(self.host.name, self.path)
        
            
class TestTime(models.Model):
    testbuild = models.ForeignKey(Build)
    testdut = models.ForeignKey(Host)
    testdate = models.DateField(auto_now_add=True)
    testcount = models.IntegerField(default=0)
    timesection = models.IntegerField(default=0)
    actionpass = models.IntegerField(default=0)
    actionfail = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('testbuild','testdut','testdate','timesection')