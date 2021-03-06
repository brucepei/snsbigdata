from django.test import TestCase as TC
from django.core.urlresolvers import resolve
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils import timezone
from tbd.models import Project, Build, Host, TestCase, Crash
from tbd.views import home_page, project_page, build_page, testdata_page, ajax, ajax_get_builds
from datetime import datetime
from .forms import AddProjectForm, AddBuildForm, AddCrashForm, AddHostForm, AddTestCaseForm
import mock
import json
import time

# Create your tests here.
class TBDAjaxTest(TC):
    def test_ajax_get_builds_url_handler(self):
        handler_obj = resolve('/ajax/get_builds')
        self.assertEqual(handler_obj.func, ajax)
        
    def test_ajax_get_builds_get_correct_list(self):
        prj1 = Project(name="unit_project1", owner="tester1")
        prj1.save()
        build1 = Build(version="unit_build1", project=prj1)
        build1.save()
        time.sleep(0.1) #need to guarentee build2's create-time late than build1's
        build2 = Build(version="unit_build2", project=prj1)
        build2.save()

        request = HttpRequest()
        request.method = 'POST'
        request.POST['project_name'] = "unit_project1"
        
        resp = ajax_get_builds(request)
        
        self.assertEqual(resp.content.decode('utf8'), '{"code": 0, "result": [[{"version": "unit_build2", "short_name": ""}, "unit_build2", false], [{"version": "unit_build1", "short_name": ""}, "unit_build1", false]]}')

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
        request.method = 'POST'
        request.session = {}
        request.POST['method'] = 'delete'
        request.POST['project_name'] = 'unit_test_prj'
        resp = project_page(request)
        
        saved_projects = Project.objects.all()
        form = AddProjectForm()
        flash_data = {'type': 'success', 'msg': "Delete Project {} successfully!".format('unit_test_prj')}
        self.assertEqual(saved_projects.count(), 0)
        
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], '/project')
        
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
        
    def test_build_post_add_build_with_invalid_input(self):
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

    def test_build_post_add_build_with_valid_input(self):
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
        
    def test_build_post_delete_build(self):
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
        request.method = 'POST'
        request.session = {}
        request.POST['method'] = 'delete'
        request.POST['project_name'] = prj.name
        request.POST['version'] = version
        resp = build_page(request)
        
        saved_builds = Build.objects.all()
        form = AddBuildForm(initial={'build_project_name': prj.name})
        page = None
        flash_data = {'type': 'success', 'msg': "Delete Version {} in Project {} successfully!".format(version, prj.name)}
        self.assertEqual(saved_builds.count(), 0)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], '/build?project_name=unit_project')

class TBDTestTestData(TC):
    def test_testdata_url_handler(self):
        handler_obj = resolve('/testdata')
        self.assertEqual(handler_obj.func, testdata_page)
        
    def test_testdata_get_correct_html(self):
        prj1 = Project(name="unit_project1", owner="tester1")
        prj1.save()
        build1 = Build(version="unit_project1", project=prj1)
        build1.save()
        host1 = Host(name="hostname1", ip="1.1.1.1", project=prj1)
        host1.save()
        tc1 = TestCase(name="s3.xml", platform=TestCase.PHOENIX, project=prj1)
        tc1.save()
        crash1 = Crash(path='\\\\crash_server\\c1', testcase=tc1, host=host1, build=build1)
        crash1.save()
        request = HttpRequest()
        request.session = {}
        request.GET['project_name'] = prj1.name
        request.GET['version'] = build1.version
        resp = testdata_page(request)
        
        self.assertIn(b'<html>', resp.content)
        self.assertTrue(resp.content.strip().endswith(b'</html>'))
        self.assertIn(b'<title>TestData - SBD</title>', resp.content)

        crash_form = AddCrashForm(initial={'crash_project_name': prj1.name, 'crash_build_version': build1.version})
        host_form = AddHostForm(initial={'host_project_name': prj1.name})
        testcase_form = AddTestCaseForm(initial={'testcase_project_name': prj1.name})
        form = {'crash':crash_form, 'host': host_form, 'testcase': testcase_form}
        host1.no = 1
        host1.total_dump = 1
        host1.valid_crash = 0
        host1.open_crash = 0
        page = {'list': [1], 'previous': 1, 'next': 1, 'cur': 1, 'items': [host1]}
        json_vars = {
            'builds': json.dumps([({'version': build1.version, 'short_name': build1.short_name}, build1.version, True)]),
            'projects': json.dumps([({'name': prj1.name, 'owner': prj1.owner}, prj1.name, True)]),
            'testcases': json.dumps([({'testcase_name': tc1.name, 'testcase_platform': tc1.platform}, "{}({})".format(tc1.name, tc1.platform), False)]),
            'hosts': json.dumps([({'host_name': host1.name, 'host_ip': host1.ip, 'host_mac': host1.mac}, "{}({})".format(host1.name, host1.ip), False)]),
        }
        self.assertEqual(resp.content.decode('utf8'), render_to_string('tbd/testdata.html', request=request, context={
            'project': prj1, 'build': build1, 'sort_by': 'Host', 'page': page, 'form': form, 'json_vars': json_vars}
        ))
        
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
        crash2 = Crash(path='\\\\crash_server\\c2', testcase=tc2, host=host2, build=build2)
        crash2.save()
        
        saved_items = Crash.objects.all()        
        self.assertEqual(saved_items.count(), 2)
        
        
        first_item = saved_items[0]
        second_item = saved_items[1]
        self.assertEqual(first_item.path, crash1.path)
        self.assertEqual(first_item.build.project.name, build1.project.name)
        self.assertEqual(first_item.build.version, build1.version)
        self.assertEqual(first_item.host.name, host1.name)
        self.assertEqual(first_item.testcase.name, tc1.name)
        
        self.assertEqual(second_item.path, crash2.path)
        self.assertEqual(second_item.build.project.name, build2.project.name)
        self.assertEqual(second_item.build.version, build2.version)
        self.assertEqual(second_item.host.name, host2.name)
        self.assertEqual(second_item.testcase.name, tc2.name)