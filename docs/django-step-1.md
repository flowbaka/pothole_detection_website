# Django lesson 1: request, URL, view, response

This is the first small step in moving the project's backend from FastAPI to Django. Django runs independently on port 8003 for now. The earlier FastAPI code remains available on port 8001 so the tested phone recording page keeps working during the transition. No project table or frontend page is added in this lesson.

## Run it

From the project folder in PowerShell:

```powershell
.\.pothholevenv\Scripts\python.exe -m pip install -r requirements.txt
.\.pothholevenv\Scripts\python.exe manage.py runserver 127.0.0.1:8003
```

Open `http://127.0.0.1:8003/` for `{"message":"Django backend is running"}` and `http://127.0.0.1:8003/health/` for `{"status":"ok"}`. Press Ctrl+C in the server terminal to stop it. These are JSON responses from the backend; there is no frontend lesson here.

## Trace one request

1. The browser requests `/health/` from the Django server.
2. `manage.py` points Django at `backend.settings` through `DJANGO_SETTINGS_MODULE`.
3. `backend/settings.py` sets `ROOT_URLCONF = "backend.urls"`, telling Django where the URL rules live.
4. In `backend/urls.py`, `path("health/", views.health, name="health")` matches the rest of the request path. The final `/` is part of this URL.
5. Django calls `health(request)` in `backend/views.py`. Django provides the `request` object, even though this first view does not need to read it.
6. `JsonResponse({"status": "ok"})` becomes an HTTP response with JSON for the browser.

The `""` path matches `/` and calls `home(request)` in the same way. `name="health"` gives that URL a reusable name for later code.

## What each file contains

- `manage.py` is the command entry point. `os.environ.setdefault(...)` chooses the Django settings module unless one is already selected. `execute_from_command_line(sys.argv)` runs commands such as `runserver`, `check` and `test`.
- `backend/__init__.py` marks `backend` as a Python package. It contains no logic.
- `backend/settings.py` holds configuration: a development-only secret key, debug mode, allowed localhost hosts, URL module, empty app and middleware lists, and an empty database setting. This lesson does not use authentication, sessions or the database. The development secret must be replaced with a private value before adding account features or deploying.
- `backend/urls.py` is the route table. `path()` maps a URL pattern to a view function; importing `views` makes those functions available.
- `backend/views.py` contains the two view functions. Each accepts a `request` and returns a `JsonResponse`.
- `backend/tests.py` checks that the route table really calls the intended views and returns HTTP 200 with the expected JSON. `SimpleTestCase` runs without creating a database.

The short route flow is: **browser URL → Django URL rule → Python view → JSON response**.

## Check it

```powershell
.\.pothholevenv\Scripts\python.exe manage.py check
.\.pothholevenv\Scripts\python.exe manage.py test backend.tests
```

Both tests and the system check passed locally. The next lesson will configure Django to use the existing `pothole_db` with the `pothole_app` account. Until then, `/health/` means that Django responds; it does not check PostgreSQL.

Django 5.2 is a [long-term support release compatible with Python 3.13](https://docs.djangoproject.com/en/5.2/releases/5.2/). The [official first-app tutorial](https://docs.djangoproject.com/en/5.2/intro/tutorial01/) also introduces project structure, URL rules and views.
