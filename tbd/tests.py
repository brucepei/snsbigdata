from django.test import TestCase
from django.core.urlresolvers import resolve
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils import timezone
from tbd.models import Project, Build
from tbd.views import home_page, project_page, build_page
from datetime import datetime
from .forms import AddProjectForm
import mock

# Create your tests here.
class TBDTest(TestCase):
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
        
        self.assertEqual(saved_projects.count(), 0)
        self.assertEqual(resp.content.decode('utf8'), render_to_string('tbd/project.html', request=request, context={'form': form}))

class TBDModelTest(TestCase):
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
        prj1 = Project(name="unit_project1", owner="test1")
        prj1.save()
        prj2 = Project(name="unit_project2", owner="test1")
        prj2.save()
        build1 = Build(version="unit_project1", project=prj1)
        build1.save()
        build2 = Build(version="unit_project2", project=prj2)
        build2.save()
        
        saved_items = Build.objects.all()
        self.assertEqual(saved_items.count(), 2)
        
        first_build = saved_items[0]
        second_build = saved_items[1]
        self.assertEqual(first_build.version, build1.version)
        self.assertEqual(first_build.project.name, build1.project.name)
        self.assertEqual(second_build.version, build2.version)
        self.assertEqual(second_build.project.name, build2.project.name)