"""SnSBigData URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
import tbd.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', tbd.views.home_page, name='tbd_home'),
    url(r'^project$', tbd.views.project_page, name='tbd_project'),
    url(r'^build$', tbd.views.build_page, name='tbd_build'),
    url(r'^host$', tbd.views.host_page, name='tbd_host'),
    url(r'^testcase$', tbd.views.testcase_page, name='tbd_testcase'),
    url(r'^testaction$', tbd.views.testaction_page, name='tbd_testaction'),
    url(r'^testresult$', tbd.views.testresult_page, name='tbd_testresult'),
    url(r'^crash$', tbd.views.crash_page, name='tbd_crash'),
    url(r'^ajax/([^/]+)$', tbd.views.ajax, name='ajax'),
    url(r'^auto/([^/]+)$', tbd.views.auto, name='auto'),
]
