from selenium import webdriver
import unittest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.common.keys import Keys

class TBDTest(StaticLiveServerTestCase):
    
    def setUp(self):
        self.browser = webdriver.Chrome()
        self.browser.implicitly_wait(1)
    
    def tearDown(self):
        self.browser.quit()
        
    def test_homepage_title(self):
        self.browser.get(self.live_server_url)
        self.assertIn('SnS Big Data', self.browser.title)
    
    def test_homepage_links(self):
        self.browser.get(self.live_server_url)
        links = self.browser.find_elements_by_tag_name('a')
        links_text = [link.text for link in links]
        self.assertIn('Home', links_text)
        self.assertIn('Project', links_text)
    
    def test_static_bootstap(self):
        self.browser.get(self.live_server_url + '/static/css/bootstrap.min.css')
        self.assertNotIn('Page not found', self.browser.title)
        self.browser.get(self.live_server_url + '/static/js/jquery-1.11.3.min.js')
        self.assertNotIn('Page not found', self.browser.title)
        self.browser.get(self.live_server_url + '/static/js/bootstrap.min.js')
        self.assertNotIn('Page not found', self.browser.title)
    
    def test_project_form(self):
        self.browser.get(self.live_server_url + '/project')
        target_project = self.browser.find_element_by_id('id_target_project')
        target_project.send_keys("test_func")
        target_project.send_keys(Keys.ENTER)
        project_table = self.browser.find_element_by_id('id_project_table')
        rows = project_table.find_elements_by_tag_name('tr')
        self.assertIn('test_func', [row.text for row in rows])
