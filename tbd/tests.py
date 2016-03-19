from django.test import TestCase
from django.core.urlresolvers import resolve
from django.http import HttpRequest
from django.template.loader import render_to_string
from tbd.views import home_page


# Create your tests here.
class Homepage(TestCase):
    def test_homepage_url_handler(self):
        handler_obj = resolve('/')
        self.assertEqual(handler_obj.func, home_page)
        
    def test_homepage_return_correct_html(self):
        request = HttpRequest()
        resp = home_page(request)
        
        self.assertIn(b'<html>', resp.content)
        self.assertTrue(resp.content.strip().endswith(b'</html>'))
        self.assertIn(b'<title>SnS Big Data</title>', resp.content)
        self.assertTrue(resp.content.decode('utf8') == render_to_string('tbd/home.html'))