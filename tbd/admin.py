from django.contrib import admin
from .models import Project, Build
# Register your models here.

admin.site.register(Project)
admin.site.register(Build)