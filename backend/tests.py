"""Check that Django sends each URL to the expected view."""

from django.test import SimpleTestCase


class FirstRoutesTests(SimpleTestCase):
    def test_home(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Django backend is running"})

    def test_health(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
