from selenium import webdriver
import unittest


class TBDTest(unittest.TestCase):
    def setUp(self):
        self.browser = webdriver.Chrome()
        self.browser.implicitly_wait(3)
    
    def tearDown(self):
        self.browser.quit()
        
    def test_homepage_title(self):
        self.browser.get('http://127.0.0.1:8000')
        self.assertIn('SnS Big Data', self.browser.title)
    
    def test_homepage_links(self):
        self.browser.get('http://127.0.0.1:8000')
        links = self.browser.find_elements_by_tag_name('a')
        links_text = [link.text for link in links]
        self.assertIn('Home', links_text)
        self.assertIn('Project', links_text)
            
        
if __name__ == '__main__':
    unittest.main()