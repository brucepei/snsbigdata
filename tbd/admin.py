from django.contrib import admin
from .models import Project, Build, Host, TestCase, Crash, JIRA
# Register your models here.

admin.site.register(Project)
admin.site.register(Build)
admin.site.register(Host)
admin.site.register(TestCase)
admin.site.register(Crash)
admin.site.register(JIRA)