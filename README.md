# Pothole Reporting System — Backend and recording experiment

Computer vision final-year project for Biratnagar International College, Nepal.

## What works now

A minimal FastAPI backend with `GET /`, `GET /health`, automatic API documentation at `/docs`, and a phone recording experiment at `/capture`.

The recording page captures a short video and timestamped browser location readings, then offers two local downloads. The user confirmed iPhone camera/location access and MP4 playback both on the page and after downloading to Files. The recorder prefers H.264/MP4 when supported. A local Python checker can summarize the saved JSON and check its matching video file without printing coordinates. Actual location quality/timing and Android compatibility remain to be verified. Detection, uploads, database storage and the map are still future milestones.

## Run on Windows (PowerShell)

The existing virtual environment in this workspace is named `.pothholevenv` (with an extra `h`), and was created with Python 3.13. The commands below use that exact name. A virtual environment keeps this project's Python packages separate from other projects. Both `.pothholevenv/` and `.potholevenv/` are excluded from Git.

Open PowerShell in the project folder. Use the existing environment directly; activation is optional and you do not need to recreate it:

```powershell
Set-Location 'C:\Users\kshit\Documents\pothole_project'
.\.pothholevenv\Scripts\python.exe -m pip install -r requirements.txt
.\.pothholevenv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```

Alternatively, activate the environment and use the shorter command:

```powershell
.\.pothholevenv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8001
```

If PowerShell blocks activation, use the direct commands above; no execution-policy change is needed. You only need to install requirements on first setup or when they change.

Open http://127.0.0.1:8001 to see:

```json
{"message":"Pothole Reporting API is running"}
```

Open http://127.0.0.1:8001/docs and try `GET /health`. It should return HTTP 200 and `{"status":"ok"}`. Stop the server with Ctrl+C.

Open http://127.0.0.1:8001/capture on the laptop to inspect the recording page. For phone access, use the prepared [local HTTPS setup](docs/phone-https.md). Android also has a USB localhost-forwarding option. See [the phone experiment guide](docs/phone-test.md). The web application has not been deployed.

## Understand the files

| File | Purpose |
|---|---|
| `app/main.py` | Creates the API, serves `/capture`, and exposes its static assets. |
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

`app.main:app` means load the `app` object from `app/main.py`. Uvicorn runs the server. `--reload` restarts it when code changes during development. Port 8001 avoids the common 8000 port used by other local APIs.

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

1. Backend foundation — this starter.
2. Phone feasibility experiment: iPhone camera, location and both MP4 playback checks confirmed by the user. Next: inspect the real export with the local checker, then test Android and interruptions.
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
