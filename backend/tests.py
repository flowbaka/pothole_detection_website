"""Check that Django sends each URL to the expected view."""

from django.test import SimpleTestCase
from django.db import DatabaseError
from unittest.mock import patch


class FirstRoutesTests(SimpleTestCase):
    def test_home(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Django backend is running"})

    def test_health(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("backend.views.connection")
    def test_database_health(self, database):
        cursor = database.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (1,)
        response = self.client.get("/health/database/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "database": "connected"})
        cursor.execute.assert_called_once_with("SELECT 1")

    @patch("backend.views.connection")
    def test_database_error_keeps_details_private(self, database):
        database.cursor.side_effect = DatabaseError("synthetic-secret")
        response = self.client.get("/health/database/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
        self.assertNotIn("synthetic-secret", response.content.decode())
        self.assertEqual(self.client.get("/health/").status_code, 200)
