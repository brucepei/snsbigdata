from django.test import TestCase as TC
from django.core.urlresolvers import resolve
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils import timezone
from tbd.models import Project, Build, Host, TestCase, Crash
from tbd.views import home_page, project_page, build_page
from datetime import datetime
from .forms import AddProjectForm, AddBuildForm
import mock

# Create your tests here.
class TBDHomeTest(TC):
    def test_homepage_url_handler(self):
        handler_obj = resolve('/')
        self.assertEqual(handler_obj.func, home_page)
        
    def test_homepage_get_correct_html(self):
        request = HttpRequest()
        resp = home_page(request)
        
        self.assertIn(b'<html>', resp.content)
        self.assertTrue(resp.content.strip().endswith(b'</html>'))
        self.assertIn(b'<title>SnS Big Data</title>', resp.content)
        self.assertEqual(resp.content.decode('utf8'), render_to_string('tbd/home.html'))
        
class TBDProjectTest(TC):
    def test_project_url_handler(self):
        handler_obj = resolve('/project')
        self.assertEqual(handler_obj.func, project_page)
        
    def test_project_get_correct_html(self):
        request = HttpRequest()
        request.session = {}
        
        resp = project_page(request)
        
        self.assertIn(b'<html>', resp.content)
        self.assertTrue(resp.content.strip().endswith(b'</html>'))
        self.assertIn(b'<title>Project - SBD</title>', resp.content)
        saved_projects = Project.objects.all()
        form = AddProjectForm()
        
        self.assertEqual(saved_projects.count(), 0)
        self.assertEqual(resp.content.decode('utf8'), render_to_string('tbd/project.html', request=request, context={'form': form}))
        
    def test_project_post_add_project_with_invalid_input(self):
        #name [a-zA-Z]\w{0,39}, owner \w{1,20}
        for name, owner in (('', ''), ('a12', ''), ('a12', '!o'), ('', 'n1'), ('1ab', 'n1'), ('@n', 'n1')
            , ('a12', '123456789012345678901'), ('a1234567890123456789012345678901234567890', 'n1')):
            request = HttpRequest()
            request.session = {}
            request.method = 'POST'
            request.POST['project_name'] = name
            request.POST['project_owner'] = owner
    
            resp = project_page(request)
            saved_projects = Project.objects.all()
            
            self.assertEqual(saved_projects.count(), 0)
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp['location'], '/project')

    def test_project_post_add_project_with_valid_input(self):
        request = HttpRequest()
        request.session = {}
        request.method = 'POST'
        request.POST['project_name'] = 'unit_test_prj'
        request.POST['project_owner'] = 'tester'
        aware_create_time = timezone.now()

        resp = project_page(request)
        
        saved_projects = Project.objects.all()
        self.assertEqual(saved_projects.count(), 1)
        first_project = saved_projects[0]
        self.assertEqual(first_project.name, request.POST['project_name'])
        self.assertEqual(first_project.owner, request.POST['project_owner'])
        self.assertAlmostEqual((first_project.create - aware_create_time).seconds, 0)
        
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], '/project')
        
    def test_project_post_delete_project(self):
        request = HttpRequest()
        request.session = {}
        request.method = 'POST'
        request.POST['add'] = None
        request.POST['project_name'] = 'unit_test_prj'
        request.POST['project_owner'] = 'tester'

        resp = project_page(request)
        
        saved_projects = Project.objects.all()
        self.assertEqual(saved_projects.count(), 1)

        request = HttpRequest()
        request.session = {}
        request.GET['method'] = 'delete'
        request.GET['project_name'] = 'unit_test_prj'
        resp = project_page(request)
        
        saved_projects = Project.objects.all()
        form = AddProjectForm()
        flash_data = {'type': 'success', 'msg': "Delete Project {} successfully!".format('unit_test_prj')}
        self.assertEqual(saved_projects.count(), 0)
        self.assertEqual(resp.content.decode('utf8'), render_to_string('tbd/project.html', request=request, context={'flash': flash_data, 'form': form}))

class TBDTestBuild(TC):
    def test_build_url_handler(self):
        handler_obj = resolve('/build')
        self.assertEqual(handler_obj.func, build_page)
        
    def test_build_get_correct_html(self):
        request = HttpRequest()
        request.session = {}
        
        resp = build_page(request)
        
        self.assertIn(b'<html>', resp.content)
        self.assertTrue(resp.content.strip().endswith(b'</html>'))
        self.assertIn(b'<title>Build - SBD</title>', resp.content)
        saved_builds = Build.objects.all()
        form = AddBuildForm()
        
        self.assertEqual(saved_builds.count(), 0)
        self.assertEqual(resp.content.decode('utf8'), render_to_string('tbd/build.html', request=request, context={'form': form}))
        
    def test_build_post_add_project_with_invalid_input(self):
        prj = Project(name="unit_project", owner="tester")
        prj.save()
        #name [a-zA-Z]\w{0,39}, owner \w{1,20}
        for version, short_name, server_path, crash_path, local_path, use_server in (('', '', '', '', '', True), ('version1', '', '', '', '', True)
            , ('version1', 'v1', 'abc', 'def', 'agc', True), ('version1', 'v1', '\\\\a\\b', 'def', 'agc', True), ('version1', 'v1', '\\\\a\\b', '\\\\c\\d', 'agc', True)):
            request = HttpRequest()
            request.session = {}
            request.method = 'POST'
            request.POST['build_project_name'] = prj.name
            request.POST['build_version'] = version
            request.POST['build_name'] = short_name
            request.POST['build_server_path'] = server_path
            request.POST['build_crash_path'] = crash_path
            request.POST['build_local_path'] = local_path
            request.POST['build_use_server'] = use_server
    
            resp = build_page(request)
            saved_builds = Build.objects.all()
            
            self.assertEqual(saved_builds.count(), 0)
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp['location'], '/build?project_name='+prj.name)

    def test_project_post_add_project_with_valid_input(self):
        prj = Project(name="unit_project", owner="tester")
        prj.save()
        #name [a-zA-Z]\w{0,39}, owner \w{1,20}
        build_no = 0
        for version, short_name, server_path, crash_path, local_path, use_server in (('version1', 'v1', '\\\\s\\v1', '\\\\c\\v1', '\\\\l\\v1', True)
            , ('version2', 'v2', '\\\\s\\v2', '\\\\c\\v2', '', True), ('version3', 'v3', '\\\\s\\v3', '\\\\c\\v3', '', False), ('version4', 'v4', '\\\\s\\v4', '\\\\c\\v4', '\\\\l\\v4', False), ):
            build_no += 1
            request = HttpRequest()
            request.session = {}
            request.method = 'POST'
            request.POST['build_project_name'] = prj.name
            request.POST['build_version'] = version
            request.POST['build_name'] = short_name
            request.POST['build_server_path'] = server_path
            request.POST['build_crash_path'] = crash_path
            request.POST['build_local_path'] = local_path
            request.POST['build_use_server'] = use_server
            aware_create_time = timezone.now()

            resp = build_page(request)
            saved_builds = Build.objects.all()
            self.assertEqual(saved_builds.count(), build_no)
            target_build = Build.objects.filter(version=version)[0]
            self.assertEqual(target_build.project.name, prj.name)
            self.assertEqual(target_build.version, version)
            self.assertEqual(target_build.short_name, short_name)
            self.assertEqual(target_build.server_path, server_path)
            self.assertEqual(target_build.crash_path, crash_path)
            self.assertEqual(target_build.local_path, local_path)
            self.assertEqual(target_build.use_server, use_server)
            self.assertAlmostEqual((target_build.create - aware_create_time).seconds, 0)
            
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp['location'], '/build?project_name='+prj.name)
        
    def test_project_post_delete_project(self):
        request = HttpRequest()
        request.session = {}
        request.method = 'POST'
        prj = Project(name="unit_project", owner="tester")
        prj.save()
        version, short_name, server_path, crash_path, local_path, use_server = ('version1', 'v1', '\\\\s\\v1', '\\\\c\\v1', '\\\\l\\v1', True)
        request.POST['build_project_name'] = prj.name
        request.POST['build_version'] = version
        request.POST['build_name'] = short_name
        request.POST['build_server_path'] = server_path
        request.POST['build_crash_path'] = crash_path
        request.POST['build_local_path'] = local_path
        request.POST['build_use_server'] = use_server

        resp = build_page(request)
        
        saved_builds = Build.objects.all()
        self.assertEqual(saved_builds.count(), 1)

        request = HttpRequest()
        request.session = {}
        request.GET['method'] = 'delete'
        request.GET['project_name'] = prj.name
        request.GET['version'] = version
        resp = build_page(request)
        
        saved_builds = Build.objects.all()
        form = AddBuildForm(initial={'build_project_name': prj.name})
        page = {'list': []}
        flash_data = {'type': 'success', 'msg': "Delete Version {} in Project {} successfully!".format(version, prj.name)}
        self.assertEqual(saved_builds.count(), 0)
        self.assertEqual(resp.content.decode('utf8'), render_to_string('tbd/build.html', request=request, context={
            'page': page, 'project': prj, 'projects': Project.objects.all(), 'flash': flash_data, 'form': form}))
        
class TBDModelTest(TC):
    def test_saving_and_retrieve_project(self):
        prj1 = Project(name="unit_project1", owner="test1")
        prj1.save()
        prj2 = Project(name="unit_project2", owner="test1")
        prj2.save()
        
        saved_items = Project.objects.all()
        self.assertEqual(saved_items.count(), 2)
        
        first_prj = saved_items[0]
        second_prj = saved_items[1]
        self.assertEqual(first_prj.name, prj1.name)
        self.assertEqual(first_prj.owner, prj1.owner)
        self.assertEqual(second_prj.name, prj2.name)
        self.assertEqual(second_prj.owner, prj2.owner)
        
    def test_saving_and_retrieve_build(self):
        prj1 = Project(name="unit_project1", owner="tester1")
        prj1.save()
        prj2 = Project(name="unit_project2", owner="tester1")
        prj2.save()
        build1 = Build(version="unit_build1", project=prj1)
        build1.save()
        build2 = Build(version="unit_build2", project=prj2)
        build2.save()
        
        saved_items = Build.objects.all()
        self.assertEqual(saved_items.count(), 2)
        
        first_build = saved_items[0]
        second_build = saved_items[1]
        self.assertEqual(first_build.version, build1.version)
        self.assertEqual(first_build.project.name, build1.project.name)
        self.assertEqual(second_build.version, build2.version)
        self.assertEqual(second_build.project.name, build2.project.name)
        
    def test_saving_and_retrieve_host(self):
        host1 = Host(name="hostname1", ip="1.1.1.1")
        host1.save()
        host2 = Host(name="hostname2", ip="1.1.1.2")
        host2.save()
        
        saved_items = Host.objects.all()
        self.assertEqual(saved_items.count(), 2)
        
        first_host = saved_items[0]
        second_host = saved_items[1]
        self.assertEqual(first_host.name, host1.name)
        self.assertEqual(first_host.ip, host1.ip)
        self.assertEqual(second_host.name, host2.name)
        self.assertEqual(second_host.ip, host2.ip)
        
    def test_saving_and_retrieve_testcase(self):
        tc1 = TestCase(name="s3.xml", platform=TestCase.PHOENIX)
        tc1.save()
        tc2 = TestCase(name="s4.pl", platform=TestCase.WPA)
        tc2.save()
        
        saved_items = TestCase.objects.all()
        self.assertEqual(saved_items.count(), 2)
        
        first_item = saved_items[0]
        second_item = saved_items[1]
        
        self.assertEqual(first_item.name, tc1.name)
        self.assertEqual(first_item.platform, tc1.platform)
        self.assertEqual(second_item.name, tc2.name)
        self.assertEqual(second_item.platform, tc2.platform)

    def test_saving_and_retrieve_crash(self):
        prj1 = Project(name="unit_project1", owner="tester1")
        prj1.save()
        prj2 = Project(name="unit_project2", owner="tester1")
        prj2.save()
        build1 = Build(version="unit_project1", project=prj1)
        build1.save()
        build2 = Build(version="unit_project2", project=prj2)
        build2.save()
        host1 = Host(name="hostname1", ip="1.1.1.1")
        host1.save()
        host2 = Host(name="hostname2", ip="1.1.1.2")
        host2.save()
        tc1 = TestCase(name="s3.xml", platform=TestCase.PHOENIX)
        tc1.save()
        tc2 = TestCase(name="s4.xml", platform=TestCase.VEGA)
        tc2.save()
        crash1 = Crash(path='\\\\crash_server\\c1', testcase=tc1, host=host1, build=build1)
        crash1.save()
        crash2 = Crash(path='\\\\crash_server\\c2', testcase=tc2, host=host2, build=build2, category=Crash.NONCNSS)
        crash2.save()
        
        saved_items = Crash.objects.all()        
        
        self.assertEqual(crash1.is_cnss(), False)
        self.assertEqual(crash1.is_valid(), False)
        self.assertEqual(crash2.is_cnss(), False)
        self.assertEqual(crash2.is_valid(), True)
        self.assertEqual(saved_items.count(), 2)
        
        
        first_item = saved_items[0]
        second_item = saved_items[1]
        self.assertEqual(first_item.path, crash1.path)
        self.assertEqual(first_item.build.project.name, build1.project.name)
        self.assertEqual(first_item.build.version, build1.version)
        self.assertEqual(first_item.host.name, host1.name)
        self.assertEqual(first_item.testcase.name, tc1.name)
        self.assertEqual(first_item.is_cnss(), False)
        self.assertEqual(first_item.is_valid(), False)
        
        self.assertEqual(second_item.path, crash2.path)
        self.assertEqual(second_item.build.project.name, build2.project.name)
        self.assertEqual(second_item.build.version, build2.version)
        self.assertEqual(second_item.host.name, host2.name)
        self.assertEqual(second_item.testcase.name, tc2.name)
        self.assertEqual(second_item.is_cnss(), False)
        self.assertEqual(second_item.is_valid(), True)