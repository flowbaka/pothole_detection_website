"""Match an incoming path to the Python function that handles it."""

from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("health/database/", views.database_health, name="database_health"),
]
