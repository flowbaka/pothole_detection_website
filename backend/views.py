"""Small JSON responses for the first Django backend lesson."""

from django.http import JsonResponse
from django.db import DatabaseError, connection


def home(request):
    return JsonResponse({"message": "Django backend is running"})


def health(request):
    return JsonResponse({"status": "ok"})


def database_health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            if cursor.fetchone() != (1,):
                raise DatabaseError("Unexpected result from the database.")
    except DatabaseError:
        # Driver errors can include connection details; send a fixed response.
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok", "database": "connected"})
