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
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers
import tbd.views
import tools.views


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', tools.views.UserViewSet)
router.register(r'groups', tools.views.GroupViewSet)
router.register(r'aps', tools.views.ApViewSet)

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
    url(r'^utility$', tbd.views.utility_page, name='tbd_utility'),
    url(r'^ajax/([^/]+)$', tbd.views.ajax, name='ajax'),
    url(r'^auto/([^/]+)$', tbd.views.auto, name='auto'),

    url(r'^tools$', tools.views.home_page, name='tools_home'),
    url(r'^tools/api/', include(router.urls)),
    url(r'^tools/ap_list', tools.views.ap_list),
    url(r'^tools/api/ap_types', tools.views.ApTypesView.as_view()),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
