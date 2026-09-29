# Pothole Reporting System — Django backend and recording experiment

Computer vision final-year project for Biratnagar International College, Nepal.

## What works now

The backend is moving from FastAPI to Django in small lessons. [Django lesson 1](docs/django-step-1.md) adds `GET /` and `GET /health/` on local port 8003. [Django lesson 2](docs/django-step-2.md) connects it to PostgreSQL through `GET /health/database/`; a real HTTP request confirmed access to `pothole_db` with the existing local settings. The previously tested FastAPI server remains available on port 8001 for the phone recording experiment while that route is migrated. No report tables have been created yet. See [database setup](docs/database-setup.md).

The recording page captures a short video and timestamped browser location readings, then offers two local downloads. The user confirmed iPhone camera/location access, MP4 playback both on the page and after downloading to Files, and recording stopping with an interruption message when leaving Safari. Two real iPhone exports passed the local checker's timing-consistency and video filename, size and header checks. The outdoor test still had a 4.45-second initial location gap; exact video/location alignment and road-position accuracy remain unverified. Android testing is pending because no phone is available. The recorder prefers H.264/MP4 when supported. Detection, uploads, database storage and the map are still future milestones.

## Run on Windows (PowerShell)

The existing virtual environment in this workspace is named `.pothholevenv` (with an extra `h`), and was created with Python 3.13. The commands below use that exact name. A virtual environment keeps this project's Python packages separate from other projects. Both `.pothholevenv/` and `.potholevenv/` are excluded from Git.

Open PowerShell in the project folder. Use the existing environment directly; activation is optional and you do not need to recreate it:

```powershell
Set-Location 'C:\Users\kshit\Documents\pothole_project'
.\.pothholevenv\Scripts\python.exe -m pip install -r requirements.txt
.\.pothholevenv\Scripts\python.exe manage.py runserver 127.0.0.1:8003
```

Alternatively, activate the environment and use the shorter command:

```powershell
.\.pothholevenv\Scripts\Activate.ps1
python manage.py runserver 127.0.0.1:8003
```

If PowerShell blocks activation, use the direct commands above; no execution-policy change is needed. You only need to install requirements on first setup or when they change.

Open http://127.0.0.1:8003 to see:

```json
{"message":"Django backend is running"}
```

Open http://127.0.0.1:8003/health/ to see `{"status":"ok"}` and http://127.0.0.1:8003/health/database/ to see `{"status":"ok","database":"connected"}`. Stop the server with Ctrl+C.

The existing phone recording page still runs through the earlier FastAPI server at http://127.0.0.1:8001/capture. Start it separately with `.\.pothholevenv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001` if needed. Its [local HTTPS setup](docs/phone-https.md) is unchanged. See the [phone experiment guide](docs/phone-test.md). The web application has not been deployed.

## Understand the files

| File | Purpose |
|---|---|
| `manage.py` | Runs Django commands such as `runserver`, `check` and `test`. |
| `backend/settings.py` | Django configuration, including the local PostgreSQL connection. |
| `backend/urls.py` | Connects URL paths to Django views. |
| `backend/views.py` | Returns JSON responses for the first two routes. |
| `backend/tests.py` | Checks the Django URL-to-view behavior. |
| `app/main.py` | Earlier FastAPI server, kept during the phone-page transition. |
| `app/database.py` | Reads local connection settings and checks PostgreSQL with `SELECT 1`. |
| `scripts/configure_database.py` | Prompts for the application password locally, checks it, and saves the ignored `.env`. |
| `.env.example` | Password-free reference for database settings. |
| `tests/test_database.py` | Checks configuration, password preservation, connection failures and endpoint responses. |
| `app/__init__.py` | Marks `app` as a Python package. |
| `app/static/capture.html` | Recording controls, camera preview, status and download links. |
| `app/static/capture.js` | Requests permissions, records video, timestamps locations and prepares downloads. |
| `app/static/capture.css` | Simple layout for laptop and phone screens. |
| `tests/capture-browser.cjs` | Browser checks with simulated devices; requires existing Node and Chrome. |
| `scripts/phone_https.py` | Prepares local certificates and starts the HTTPS phone test server. |
| `scripts/inspect_recording.py` | Summarizes recording timestamps, location gaps and accuracy estimates without printing coordinates. |
| `tests/test_inspect_recording.py` | Checks timing, malformed exports, file pairing and private output using synthetic fixtures. |
| `requirements.txt` | Lists the Python packages to install. |
| `.gitignore` | Keeps virtual environments, secrets, footage and model weights out of Git. |

`manage.py` loads the `backend.settings` Django configuration. `runserver` starts Django for local development. Port 8003 keeps it separate from the earlier FastAPI phone test on port 8001.

## GitHub checkpoints

Source repository: [flowbaka/pothole_detection_website](https://github.com/flowbaka/pothole_detection_website).

Git is initialized on `main`. Completed small milestones are committed and pushed to `origin` at the user's request. Review the changes and staged file list for each checkpoint. Record automated checks and actual phone results separately; a source push is not website deployment.

Virtual environments, certificates/private keys, private recordings/location exports, secrets and large model weights are excluded. Keep collected footage and journey files in the ignored `data/` folder.

From the project folder, inspect progress with:

```powershell
git status
git log --oneline -5
```

## Development order

1. Django backend foundation — request handling and PostgreSQL connection verified. The first report model and migration are next.
2. Phone feasibility experiment: iPhone camera, location, both MP4 playback checks and visible interruption behavior confirmed by the user; two local exports inspected. Android, exact media alignment and road-quality checks remain pending. Current iPhone checkpoint complete; proceed one small backend milestone at a time.
3. PostgreSQL reports and photo uploads; validate files and coordinates.
4. Leaflet/OpenStreetMap page with clickable report markers and photos, initially using manually confirmed locations.
5. Pothole detection baseline and evaluation on held-out local Nepal footage.
6. Video tracking, duplicate reduction, evidence-frame selection and video/GPS timestamp matching.
7. Public submission, verification and authorised repair-status updates.
8. Experimental visual severity, comparisons, testing and dissertation.

Learn and collect data throughout the 7–8 months. Split model evaluation by road/journey rather than neighbouring frames. First process journeys after recording; live updates are a later extension.

## Scope and accuracy

Store each GPS reading's capture timestamp and accuracy, together with the recording start time. Upload-time location cannot locate an earlier journey. GPS initially locates the phone; a pothole ahead of the vehicle will have an additional offset. Reports must communicate approximate positioning and allow correction. An ordinary image alone does not establish pothole depth or physical severity.

Keep full journey traces private by default, and publish only needed report information. Before public deployment add authentication, authorisation, secure uploads, HTTPS and appropriate privacy controls. These are future work, not protections implemented by this starter.

## References

- FastAPI: https://fastapi.tiangolo.com/tutorial/first-steps/
- Browser location: https://developer.mozilla.org/en-US/docs/Web/API/Geolocation/watchPosition
- Maps and popups: https://leafletjs.com/
- Map tile usage: https://operations.osmfoundation.org/policies/tiles/
