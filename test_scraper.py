import unittest
from scraper import WebScraper
import os
import json
import requests
from flask import Flask
from app import app
import threading
import time

class TestWebScraper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start Flask app in a separate thread
        cls.flask_thread = threading.Thread(target=lambda: app.run(debug=False, port=5001))
        cls.flask_thread.daemon = True
        cls.flask_thread.start()
        time.sleep(2)  # Wait for Flask to start

    def setUp(self):
        self.scraper = WebScraper(use_selenium=False, debug=True)
        self.test_url = "https://example.com"
        self.test_selectors = {
            'title': 'h1',
            'paragraphs': 'p',
            'links': 'a'
        }

    def tearDown(self):
        self.scraper.close()

    def test_basic_scraping(self):
        """Test basic scraping functionality"""
        soup = self.scraper.scrape(self.test_url)
        self.assertIsNotNone(soup)
        data = self.scraper.extract_data(soup, self.test_selectors)
        self.assertIsNotNone(data)
        self.assertIn('title', data)

    def test_selenium_scraping(self):
        """Test Selenium-based scraping"""
        selenium_scraper = WebScraper(use_selenium=True, debug=True)
        try:
            soup = selenium_scraper.scrape(self.test_url, wait_time=2)
            self.assertIsNotNone(soup)
            data = selenium_scraper.extract_data(soup, self.test_selectors)
            self.assertIsNotNone(data)
        finally:
            selenium_scraper.close()

    def test_basic_auth(self):
        """Test basic authentication"""
        credentials = {
            'username': 'test',
            'password': 'test'
        }
        result = self.scraper.authenticate(self.test_url, 'basic', credentials)
        self.assertIsInstance(result, bool)

    def test_form_auth(self):
        """Test form-based authentication"""
        credentials = {
            'username': 'test',
            'password': 'test',
            'username_field': 'username',
            'password_field': 'password',
            'submit_selector': 'button[type="submit"]'
        }
        result = self.scraper.authenticate(self.test_url, 'form', credentials)
        self.assertIsInstance(result, bool)

    def test_api_auth(self):
        """Test API authentication"""
        credentials = {
            'client_id': 'test',
            'client_secret': 'test'
        }
        result = self.scraper.authenticate(self.test_url, 'api', credentials)
        self.assertIsInstance(result, bool)

    def test_save_to_json(self):
        """Test saving data to JSON"""
        test_data = {'test': 'data'}
        filename = 'test_output.json'
        try:
            result = self.scraper.save_to_json(test_data, filename)
            self.assertTrue(result)
            self.assertTrue(os.path.exists(filename))
            with open(filename, 'r') as f:
                loaded_data = json.load(f)
            self.assertEqual(loaded_data, test_data)
        finally:
            if os.path.exists(filename):
                os.remove(filename)

class TestFlaskApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index_page(self):
        """Test the index page loads"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_scrape_endpoint(self):
        """Test the scrape endpoint"""
        test_data = {
            'url': 'https://example.com',
            'use_selenium': False,
            'selectors': {
                'title': 'h1',
                'paragraphs': 'p'
            }
        }
        response = self.app.post('/scrape', json=test_data)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])

    def test_invalid_url(self):
        """Test scraping with invalid URL"""
        test_data = {
            'url': 'invalid-url',
            'use_selenium': False,
            'selectors': {}
        }
        response = self.app.post('/scrape', json=test_data)
        self.assertEqual(response.status_code, 500)

    def test_missing_url(self):
        """Test scraping without URL"""
        test_data = {
            'use_selenium': False,
            'selectors': {}
        }
        response = self.app.post('/scrape', json=test_data)
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main(verbosity=2) 