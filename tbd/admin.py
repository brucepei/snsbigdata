from django.contrib import admin
from .models import Project, TestAction, Build, Host, TestCase, Crash, JIRA, TestResult
# Register your models here.

admin.site.register(Project)
admin.site.register(TestAction)
admin.site.register(Build)
admin.site.register(Host)
admin.site.register(TestCase)
admin.site.register(TestResult)
admin.site.register(Crash)
admin.site.register(JIRA)