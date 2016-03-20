from django.test import TestCase
from django.core.urlresolvers import resolve
from django.http import HttpRequest
from django.template.loader import render_to_string
from tbd.views import home_page, project_page


# Create your tests here.
class Homepage(TestCase):
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
        self.assertEqual(resp.content.decode('utf8'), render_to_string('tbd/project.html', request=request))
        
    def test_project_post_add_project(self):
        request = HttpRequest()
        request.method = 'POST'
        request.POST['add'] = None
        request.POST['name'] = 'unit_test_prj'
        
        resp = project_page(request)
        
        self.assertEqual(resp.content.decode('utf8'), render_to_string('tbd/project.html', request=request))
        self.assertIn("unit_test_prj", resp.content.decode('utf8'))
        
       