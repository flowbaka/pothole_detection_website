"""Synthetic credentials only. Successful checks use a simulated driver."""

import io
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from dotenv import set_key
import psycopg

from app.database import DatabaseConfigError, check_database, database_settings
from app.main import app
from scripts import configure_database


class DatabaseTests(unittest.TestCase):
    def test_config_missing_and_invalid_port(self):
        with patch.dict(os.environ, {}, clear=True), patch('app.database.dotenv_values', return_value={}):
            with self.assertRaises(DatabaseConfigError):
                database_settings()
            with patch.dict(os.environ, {'DB_PORT': 'invalid'}):
                with self.assertRaises(DatabaseConfigError):
                    database_settings(password='synthetic')

    def test_literal_password_and_environment_override(self):
        secret = "synthetic'@:${HOME}\\path# spaces"
        with tempfile.TemporaryDirectory(prefix='pothole-db-test-') as directory:
            env_file = Path(directory) / '.env'
            set_key(env_file, 'DB_PASSWORD', secret)
            with patch('app.database.ENV_FILE', env_file), patch.dict(os.environ, {}, clear=True):
                self.assertEqual(database_settings()['password'], secret)
                with patch.dict(os.environ, {'DB_PASSWORD': 'override'}):
                    self.assertEqual(database_settings()['password'], 'override')

    def test_query_and_cleanup_on_failure(self):
        with patch('app.database.psycopg.connect') as connect:
            cursor = connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
            cursor.fetchone.return_value = (1,)
            check_database({'password': 'synthetic'})
            cursor.execute.assert_called_once_with('SELECT 1')
            cursor.execute.side_effect = psycopg.OperationalError('synthetic failure')
            with self.assertRaises(psycopg.OperationalError):
                check_database({'password': 'synthetic'})
            self.assertEqual(connect.return_value.__exit__.call_count, 2)

    def test_real_driver_refuses_unavailable_port(self):
        # Reserve a local port without listening; no database or credentials used.
        with socket.socket() as reserved:
            reserved.bind(('127.0.0.1', 0))
            with self.assertRaises(psycopg.OperationalError):
                check_database({'host': '127.0.0.1', 'port': reserved.getsockname()[1],
                                'user': 'synthetic', 'password': 'synthetic',
                                'dbname': 'synthetic', 'connect_timeout': 2})

    def test_setup_failure_does_not_save_or_print_password(self):
        output = io.StringIO()
        with patch('scripts.configure_database.getpass', return_value='synthetic-secret'), \
             patch('scripts.configure_database.database_settings', return_value={}), \
             patch('scripts.configure_database.check_database', side_effect=psycopg.OperationalError('synthetic-secret')), \
             patch('scripts.configure_database.set_key') as save, redirect_stdout(output):
            self.assertEqual(configure_database.main(), 1)
            save.assert_not_called()
        self.assertNotIn('synthetic-secret', output.getvalue())

    def test_setup_success_preserves_password_and_other_settings(self):
        secret = "synthetic'@:${HOME}\\\\folder\\n# spaced"
        with tempfile.TemporaryDirectory(prefix='pothole-db-test-') as directory:
            env_file = Path(directory) / '.env'
            env_file.write_text('UNRELATED=value\n', encoding='utf-8')
            with patch.dict(os.environ, {}, clear=True), \
                 patch('app.database.ENV_FILE', env_file), \
                 patch('scripts.configure_database.ENV_FILE', env_file), \
                 patch('scripts.configure_database.getpass', return_value=secret), \
                 patch('scripts.configure_database.check_database') as check, \
                 redirect_stdout(io.StringIO()) as output:
                self.assertEqual(configure_database.main(), 0)
                self.assertEqual(check.call_args.args[0]['password'], secret)
                self.assertEqual(database_settings()['password'], secret)
                self.assertIn('UNRELATED=value', env_file.read_text(encoding='utf-8'))
                self.assertNotIn(secret, output.getvalue())


class EndpointTests(unittest.IsolatedAsyncioTestCase):
    async def request(self, path):
        messages = []

        async def receive():
            return {'type': 'http.request', 'body': b'', 'more_body': False}

        async def send(message):
            messages.append(message)

        await app({'type': 'http', 'asgi': {'version': '3.0'}, 'http_version': '1.1',
                   'method': 'GET', 'scheme': 'http', 'path': path, 'root_path': '',
                   'query_string': b'', 'headers': [], 'server': ('test', 80),
                   'client': ('127.0.0.1', 12345)}, receive, send)
        status = next(message['status'] for message in messages if message['type'] == 'http.response.start')
        body = b''.join(message.get('body', b'') for message in messages if message['type'] == 'http.response.body')
        return status, json.loads(body)

    async def test_success_and_sanitized_failures(self):
        with patch('app.main.check_database'):
            self.assertEqual(await self.request('/health/database'), (200, {'status': 'ok', 'database': 'connected'}))
        for failure in (DatabaseConfigError('synthetic-secret'), psycopg.OperationalError('synthetic-secret')):
            with self.subTest(failure=type(failure).__name__), patch('app.main.check_database', side_effect=failure):
                status, body = await self.request('/health/database')
                self.assertEqual(status, 503)
                self.assertNotIn('synthetic-secret', str(body))
                self.assertEqual(await self.request('/health'), (200, {'status': 'ok'}))


if __name__ == '__main__':
    unittest.main()
