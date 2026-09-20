# Step 2: phone recording experiment

## Current checkpoint

The user has confirmed iPhone camera/location access and successful MP4 playback both on the recording page and after downloading to Files. Two actual iPhone exports have now been inspected locally: the first 9.32-second test and a 25.66-second outdoor follow-up. Both transferred MP4s pass filename, byte-count and container-header checks after restoring their expected filenames. The outdoor export contains 21 location readings during recording, with median device-reported accuracy of 14.47 metres and an initial 4.45-second measurement gap. The user has no Android phone available and asked to continue with iPhone; the next small checkpoint is switching away from Safari during a short recording. Android compatibility, video decoding on the laptop, frame alignment, broader location quality and interruption testing remain pending.

First open the page on the laptop. Run in PowerShell:

```powershell
Set-Location 'C:\Users\kshit\Documents\pothole_project'
.\.pothholevenv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```

Open http://127.0.0.1:8001/capture. This address refers to the laptop only. A desktop location reading may come from Wi-Fi or other sources and does not establish phone GPS performance.

## Phone connection status

Camera and geolocation require permission and a secure browser context. A page at `http://192.168.x.x:8001` is not a secure context. Ignoring a certificate warning is not our setup method.

For both phones, use trusted HTTPS over the same private Wi-Fi network. The project now includes a [local HTTPS helper and phone setup instructions](phone-https.md). It uses the OpenSSL already included with Git for Windows to generate a certificate for the laptop's LAN address. Its public root certificate must be installed and trusted on each test phone. On iPhone, a manually installed certificate also needs full trust enabled under Settings > General > About > Certificate Trust Settings; see [Apple's instructions](https://support.apple.com/en-us/102390). Exact Android settings vary by device.

Project-local certificates have been generated and HTTPS verified from the laptop. The user installed the test certificate on the iPhone and confirmed page access and MP4 recording/playback. Android access remains untested. The helper does not change device trust or firewall settings automatically. The local HTTPS option needs no paid hosting or tunnel service. The laptop must stay running and reachable; a changed LAN address requires a new server certificate. A test certificate authority changes device trust: keep its private key private, install only your own public certificate, and remove its trust after the experiment. Clients will not need to install development certificates for a future publicly hosted HTTPS site.

Android/Chrome also supports [USB port forwarding](https://developer.chrome.com/docs/devtools/remote-debugging/local-server). It maps phone `localhost:8001` to laptop `localhost:8001` for a tethered test. That is an Android development option; it does not solve iPhone access.

## Short test after connection is ready

1. Begin outdoors while stationary. Open `/capture` in the phone's browser.
2. Tap **Enable camera**, grant permission, and check the preview shows the intended camera. If playback does not start, tap **Show camera preview**. The page requests the rear camera when available; check the actual result.
3. Once the preview works, tap **Enable location**, grant permission, and wait for a recent reading. Start stays disabled until the camera is ready and a reading is at most 15 seconds old. The page states which requirement is missing. This freshness rule does not guarantee positional accuracy.
4. Tap **Start recording**, keep the screen unlocked and page visible, and record for 20–30 seconds. Do not operate the phone while driving.
5. Tap **Stop**, then tap Play in the recorded-video player. Check the format shown in the summary and save the video and JSON separately. Safari may show a preview or save dialog; verify both files actually exist in Files/Downloads before refreshing.
6. Play the saved video. Check it is readable and shows the full test. Copy both files to a private location such as this project's ignored `data/` directory if you want to inspect them on the laptop.
7. Repeat on the other phone. Next, try a separate short test that switches away from the page: it should request a stop and report `page_hidden` if the browser delivers the event. A browser can suspend or terminate a page before it saves; this is one reason real-device testing is necessary.

Keep a separate result for each device:

| Check | Android / Chrome | iPhone / Safari |
|---|---|---|
| Phone model, OS and browser version | Pending | Pending |
| HTTPS recording page opens after certificate installation | Pending | Confirmed by user |
| Camera preview works | Pending | Confirmed by user after startup fix |
| Location readings arrive | Pending | Confirmed by user after enabling Safari Websites location permission |
| MP4 plays on the page | Pending | Confirmed by user |
| Downloaded MP4 plays in Files | Pending | Confirmed by user |
| Intended camera selection and road image quality | Pending | Pending |
| Video and matching JSON both saved | Pending | Two MP4/JSON exports pass filename, byte-count and header checks; JSON inspected |
| Reading count, accuracy range and largest time gap | Pending | 9.32 s and 25.66 s exports inspected; see comparison below |
| Switching away stops or interrupts recording as expected | Pending | Pending |

The first test evaluates capture feasibility. It does not evaluate pothole detection, road accuracy, long journeys or background recording.

## Downloaded video playback checkpoint

The original format order selected WebM before MP4. Newer Safari versions can record WebM, but a browser's recording capability does not guarantee that the phone's file viewer can preview that format. The reported screenshot is consistent with a viewer compatibility issue; it does not establish whether the original media data is valid. See [WebKit's recording format notes](https://webkit.org/blog/16574/webkit-features-in-safari-18-4/) and [Apple's guidance on H.264 MP4 video](https://developer.apple.com/documentation/webkit/delivering-video-content-for-safari).

The new order requests H.264 in MP4, then generic MP4, then WebM if MP4 is unavailable. The saved extension follows the actual recorded MIME type, and `video_requested_mime_type` preserves the requested format in the JSON. The page includes a playback control and identifies the download format. A WebM fallback includes a viewer-compatibility notice.

The user has confirmed that the new MP4 plays both on the page and after download. Existing WebM files are not converted by this change; changing an extension does not convert a video. Desktop Chrome tests also verified MP4 container bytes, advancing playback and matching metadata, plus a playable WebM fallback. These observations do not establish support across all iPhone models or Android browsers.

## Next checkpoint: inspect one saved test locally

### First local export observations

The user supplied a real JSON and a video transferred through WhatsApp. Local inspection found:

- Requested duration: 9.32 seconds. Camera settings recorded in the JSON: 720 by 1280 pixels, 30 fps (portrait).
- Four location measurements during recording, five before it, and none after it. The largest interval between measurements during recording was 1.95 seconds.
- The first measurement during recording was 4.83 seconds after Start; the last was 0.54 seconds before Stop. The earlier measurements do not establish fresh coverage of that initial gap.
- Device-reported accuracy ranged from 15.94 to 19.29 metres, with a median of 18.81 metres. These estimates do not establish the exact position of a pothole.
- Exported epoch and monotonic durations agreed (0.00 ms discrepancy). This does not establish first-frame alignment.
- The JSON expects a 2,245,513-byte MP4. The transferred video is 1,552,161 bytes and has a WhatsApp filename. Its header identifies an MP4 container, but its original-file pairing and playback were not verified locally. The size difference is consistent with processing during transfer; its cause is not proven.

The user then retransferred the original through WhatsApp's Document option. The new file arrived as `IMG_7479.MP4`, with the expected 2,245,513-byte size and an MP4 header. Its filename was restored to the name recorded in the JSON, and the existing checker was rerun successfully. These checks establish file consistency, not cryptographic identity or decoded playback; no original-file checksum is available. The JSON was left unchanged. WhatsApp notes that shared media can be compressed and documents can be selected separately in its [iPhone attachment instructions](https://faq.whatsapp.com/453914586839706/?cms_platform=iphone).

The checker printed no timing review flags because the 4.83-second gap is below its five-second heuristic. Location coverage still needs evaluation despite passing the limited file checks. Private footage, coordinates and absolute timestamps remain outside Git.

### Outdoor follow-up observations

The user completed the requested outdoor follow-up and supplied one MP4 and its JSON in `data/iphone-outdoor/`. The recorded request-to-stop duration was 25.66 seconds, rather than the suggested 30 seconds; this is sufficient to inspect a longer sample. The file arrived as `IMG_7480.MP4`. After checking its 5,880,873-byte size against the JSON and recognizing its MP4 header, its expected filename was restored. The JSON was left unchanged. Running `scripts/inspect_recording.py data/iphone-outdoor` passed the limited file checks and reported no timing review flags.

| Measurement | First test | Outdoor follow-up |
|---|---|---|
| Requested recording duration | 9.32 s | 25.66 s |
| Location readings during recording | 4 | 21 |
| Location readings before / after recording | 5 / 0 | 5 / 0 |
| Largest gap between readings during recording | 1.95 s | 3.88 s |
| First reading after Start | 4.83 s | 4.45 s |
| Last reading to Stop | 0.54 s | 0.32 s |
| Reported accuracy, best / median / worst | 15.94 / 18.81 / 19.29 m | 11.35 / 14.47 / 20.56 m |
| Epoch versus monotonic duration discrepancy | 0.00 ms | -1.00 ms |

The outdoor JSON records portrait camera settings of 720 by 1280 pixels at 30 fps and a user-requested stop. Its median reported accuracy is better, but its worst reported accuracy and largest interval between measurements are worse. The initial gap remains, so this is evidence that readings were saved over a longer test, not proof of continuous coverage or exact road/pothole positions. The one-millisecond clock discrepancy does not indicate a large clock change. No decoded-video or first-frame synchronization check was performed.

The user confirmed that no Android phone is available and asked to continue with iPhone. Android compatibility remains pending. Next, start one short iPhone recording, switch to the Home Screen after about five seconds without pressing Stop, wait about two seconds, and return to Safari without refreshing. Check whether recording stopped and whether an interruption warning appears. The expected stop reason is `page_hidden`; actual device behavior has not yet been observed. Report the visible result before requesting another export transfer.

### Running the checker

Copy the matching `.mp4` and `.json` files from the successful iPhone test into `C:\Users\kshit\Documents\pothole_project\data`. Preserve their original names. This folder is ignored by Git; phone exports must not be committed.

From PowerShell:

```powershell
Set-Location 'C:\Users\kshit\Documents\pothole_project'
.\.pothholevenv\Scripts\python.exe scripts\inspect_recording.py
```

With exactly one JSON in `data/`, the checker selects it automatically. For multiple tests, supply the exact path to one JSON as an argument. The script uses Python's standard library; no package installation is needed.

The summary omits coordinates and absolute timestamps. It reports the requested recording duration, reading counts before/during/after recording, largest gap between readings, longest gap including the recording edges, and the best/median/worst reported accuracy. A gap is time with no location measurement. The median is the middle accuracy estimate after sorting, so one unusually poor reading does not dominate it. Smaller reported metre values indicate a tighter device estimate; they do not prove actual positional accuracy.

The five-second gap threshold is a prompt to review this experiment, not a validated road-mapping standard. A warm-up reading before recording is valid but cannot stand in for coverage throughout recording. A detected clock change suppresses gap metrics that would be misleading. The video check verifies the exported byte count and a recognizable container header; it does not decode the video, measure its actual duration or calibrate the first frame against GPS.

Share only the printed summary for the next discussion. We will decide what to test next from the real measurements. Automated checker tests use synthetic timestamps and tiny header fixtures, not private footage:

```powershell
.\.pothholevenv\Scripts\python.exe -m unittest discover -s tests -p test_inspect_recording.py -v
```

## Camera preview troubleshooting checkpoint

The original combined setup cancelled on any hidden-page event and awaited preview playback before proceeding to location. These were code weaknesses; the exact cause of the reported iPhone failure has not been established from device diagnostics. The revised flow requests camera and location separately, preserves setup through temporary visibility changes, explicitly configures muted inline playback, and offers a direct-tap playback retry. Actual recording still stops when hidden, and navigating away releases setup devices. A location denial keeps the camera available, while temporary location errors can recover or be retried.

The user has now confirmed that the camera preview works after the revised startup flow. Browser playback may reject or delay `play()`; see the [playback API documentation](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/play) and [WebKit's inline video policies](https://webkit.org/blog/6784/new-video-policies-for-ios/). This confirms preview startup on the user's phone, not recording, location capture or compatibility with every Safari version.

## Resolved location permission issue

The user confirmed that location was disabled for Safari Websites and that enabling it resolved the issue. No location collection code change was needed. This confirms access to readings, but does not yet establish their accuracy or continuity during recording.

On the iPhone, open **Settings > Privacy & Security > Location Services**, ensure Location Services is enabled, and find **Safari Websites**. Allow access while using the app; enable Precise Location if that option is available for the road-location experiment. This requests better location information but does not guarantee accuracy. [Apple's Location Services instructions](https://support.apple.com/en-us/102647)

Return to the HTTPS page, enable the camera if necessary, tap **Enable location** or **Retry location**, and allow the site's request if shown. Keep Safari visible outdoors while waiting for a reading. Report the exact location status, whether the browser displayed a permission prompt, and whether the reading counter changes. Keep Start disabled until a real recent location reading is available; do not substitute demonstration coordinates.

## What the JSON means

A **timestamp** records when something happened. Unix timestamps here count milliseconds since 1 January 1970 UTC, independent of a displayed time zone. For example, a difference of 5,000 milliseconds means five seconds.

- `test_id` pairs the video and JSON filenames.
- `recording_start_requested.epoch_ms` is saved immediately before asking the browser to start recording. It is our provisional time origin.
- `recording_start_event` saves when the browser reports recording has started. That callback can arrive later than the first captured frame.
- Each location's `timestamp_epoch_ms` comes from the browser's position measurement. `received` records when our code got the reading; callback delay is not measurement time.
- `offset_from_start_request_ms` is the measurement timestamp minus the recording start-request timestamp. Negative values are readings from just before recording. A positive value of 5,000 is roughly five seconds into recording.
- `latitude`, `longitude` and `accuracy_m` preserve the approximate phone position and reported accuracy. Browser geolocation can use GPS, Wi-Fi or other sources.
- `elapsed_ms` uses a monotonic clock: it measures duration without jumping if the phone's calendar clock changes. `clock_change_ms` helps flag disagreement between the clocks.
- `stop_reason`, `events` and `warnings` preserve interruptions and failures instead of disguising them as successful capture.

The first encoded video frame is not guaranteed to coincide exactly with the start request. Before processing journeys we must inspect media timestamps/duration and assess alignment uncertainty. Do not use upload time or count video chunks to align GPS. Browser chunk delivery and location updates can be irregular; inspect gaps instead of assuming one reading per second.

## Limits and privacy

This experiment requests video only, with no microphone. It targets 720p at 30 frames per second and 2 Mbps, but the actual camera settings and encoding depend on the device. Format selection prefers H.264/MP4 where supported and falls back to WebM; recording failures are shown rather than fabricating data.

The page requests a stop at 60 seconds or once received video chunks reach 32 MiB. These are best-effort bounds, not exact limits, because the browser may delay timers or chunk delivery. Keep tests short and foreground-only. Unsaved data lives in memory and can be lost on refresh, browser termination or a locked screen. Save both downloads before starting again.

The application sends no captured video or location data to the backend. The browser/OS location service itself may use a network provider. Full location traces remain private test material; generated `phone-test-*` files, videos and `data/` are ignored by Git. GPS describes the phone, not the exact location of a pothole ahead of it.

## Repeat the automated checks

From the project folder, with the existing Node.js and Chrome installations:

```powershell
node tests\capture-browser.cjs
```

The script runs a temporary API server on a free port and isolated headless Chrome with a simulated camera and location. It checks endpoint responses, mobile page width, actual MP4/WebM container bytes, advancing playback, matching filenames/metadata, acquisition-time offsets, stale-reading prevention, permission denial/retry, interruption handling and device cleanup. It also exercises a delayed camera permission across visibility changes, rejected and unresolved playback promises with manual recovery, and visible recorder errors. The integration run requires a Chrome version with MP4 recording support. It then stops its own processes and removes its temporary browser profile. These checks are not evidence of Safari compatibility or real GPS quality.

Suggested commit message: `Add browser video and timestamped location experiment`.

## API references

- [Camera access and secure contexts](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)
- [Position acquisition timestamps](https://developer.mozilla.org/en-US/docs/Web/API/GeolocationPosition/timestamp)
- [MediaRecorder start](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/start)
- [Irregular video chunk delivery](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/dataavailable_event)
