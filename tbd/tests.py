from django.test import TestCase
from django.core.urlresolvers import resolve
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils import timezone
from tbd.models import Project
from tbd.views import home_page, project_page


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
        resp = project_page(request)
        
        self.assertIn(b'<html>', resp.content)
        self.assertTrue(resp.content.strip().endswith(b'</html>'))
        self.assertIn(b'<title>Project - SBD</title>', resp.content)
        saved_projects = Project.objects.all()
        self.assertEqual(saved_projects.count(), 0)
        self.assertEqual(resp.content.decode('utf8'), render_to_string('tbd/project.html', request=request))
        
    def test_project_post_add_project(self):
        request = HttpRequest()
        request.method = 'POST'
        request.POST['add'] = None
        request.POST['name'] = 'unit_test_prj'
        request.POST['owner'] = 'tester'
        #request.POST['create'] = timezone.now()
        
        resp = project_page(request)
        
        saved_projects = Project.objects.all()
        self.assertEqual(saved_projects.count(), 1)
        first_project = saved_projects[0]
        self.assertEqual(first_project.name, request.POST['name'])
        self.assertEqual(first_project.owner, request.POST['owner'])
        #self.assertEqual(first_project.create, request.POST['create'])
        
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], '/project')

class ProjectModelTest(TestCase):
    def test_saving_and_retrieve_project(self):
        prj1 = Project(name="unit_project1")
        prj1.save()
        prj2 = Project(name="unit_project2")
        prj2.save()
        
        saved_items = Project.objects.all()
        self.assertEqual(saved_items.count(), 2)
        
        first_prj = saved_items[0]
        second_prj = saved_items[1]
        self.assertEqual(first_prj.name, prj1.name)
        self.assertEqual(second_prj.name, prj2.name)