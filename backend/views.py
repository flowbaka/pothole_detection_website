"""Small JSON responses for the first Django backend lesson."""

from django.http import JsonResponse


def home(request):
    return JsonResponse({"message": "Django backend is running"})


def health(request):
    return JsonResponse({"status": "ok"})
