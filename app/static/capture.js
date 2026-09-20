"use strict";

const ui = Object.fromEntries([
  "preview", "status", "elapsed", "count", "accuracy", "age", "location-status",
  "prepare", "start", "stop", "cancel", "downloads", "summary", "video-download",
  "json-download", "reset", "camera-status", "show-preview", "location",
  "recorded-video", "playback-status",
].map((id) => [id, document.getElementById(id)]));
const MAX_SECONDS = 60;
const MAX_BYTES = 32 * 1024 * 1024;
const FRESH_LOCATION_MS = 15000;
let state = "idle";
let stream = null;
let recorder = null;
let watchId = null;
let timer = null;
let samples = [];
let chunks = [];
let bytes = 0;
let session = null;
let urls = [];
let setupAttempt = 0;
let locationAttempt = 0;
let locationNeedsRetry = false;
let cameraReady = false;
let previewTimer = null;
let previewAttempt = 0;

// Save both clocks: Unix milliseconds match GPS timestamps; performance time
// measures elapsed time without jumping when the phone's clock is adjusted.
function stamp() {
  return { epoch_ms: Date.now(), monotonic_ms: performance.now() };
}

function freshLocation() {
  const latest = samples.at(-1);
  if (!latest) return false;
  const age = Date.now() - latest.timestamp_epoch_ms;
  return age >= 0 && age <= FRESH_LOCATION_MS;
}

function liveCamera() {
  const track = stream?.getVideoTracks()[0];
  return cameraReady && track?.readyState === "live" && !track.muted && !document.hidden;
}

function update() {
  ui.prepare.disabled = state !== "idle";
  ui.location.disabled = state !== "ready" || !liveCamera() || (watchId !== null && !locationNeedsRetry);
  ui.start.disabled = state !== "ready" || !liveCamera() || !freshLocation();
  ui.stop.disabled = state !== "recording";
  ui.cancel.disabled = !["preparing", "ready"].includes(state);
  ui.count.textContent = String(samples.length);
  if (state === "ready") {
    if (!liveCamera()) ui.status.textContent = "Waiting for the camera preview. Use Show camera preview if needed.";
    else if (!samples.length && watchId === null) ui.status.textContent = "Camera ready. Next, enable location.";
    else if (!freshLocation()) ui.status.textContent = "Start is waiting for a recent location reading. Check the location message below.";
    else ui.status.textContent = "Camera and location ready. You can start recording.";
  }
  const latest = samples.at(-1);
  if (latest) {
    ui.accuracy.textContent = `${Math.round(latest.accuracy_m)} m`;
    ui.age.textContent = `${Math.round((Date.now() - latest.timestamp_epoch_ms) / 1000)} s`;
  }
  if (state === "recording") {
    const seconds = (performance.now() - session.recording_start_requested.monotonic_ms) / 1000;
    ui.elapsed.textContent = `${Math.floor(seconds)} s`;
    if (seconds >= MAX_SECONDS) stopRecording("time_limit");
  }
}

function releaseDevices() {
  locationAttempt += 1;
  locationNeedsRetry = false;
  previewAttempt += 1;
  cameraReady = false;
  clearTimeout(previewTimer);
  ui["show-preview"].hidden = true;
  if (watchId !== null) navigator.geolocation.clearWatch(watchId);
  watchId = null;
  if (stream) stream.getTracks().forEach((track) => track.stop());
  stream = null;
  ui.preview.srcObject = null;
  ui["camera-status"].textContent = "Camera is off.";
  clearInterval(timer);
  timer = null;
}

function cancelSetup(message = "Setup cancelled. You can try again.") {
  setupAttempt += 1; // Ignore late permission responses from a cancelled attempt.
  state = "idle";
  releaseDevices();
  ui.status.textContent = message;
  update();
}

function onPosition(position) {
  if (!["ready", "recording"].includes(state)) return;
  const { latitude, longitude, accuracy } = position.coords;
  const timestamp = position.timestamp;
  if (![latitude, longitude, accuracy, timestamp].every(Number.isFinite)
      || Math.abs(latitude) > 90 || Math.abs(longitude) > 180 || accuracy < 0) return;
  // Use the sensor reading's timestamp, NOT the time its callback arrives.
  if (samples.length && timestamp <= samples.at(-1).timestamp_epoch_ms) return;
  samples.push({
    timestamp_epoch_ms: timestamp,
    received: stamp(),
    latitude,
    longitude,
    accuracy_m: accuracy,
  });
  // Only retain a small pre-recording buffer while waiting for the user.
  if (state === "ready") samples = samples.slice(-10);
  locationNeedsRetry = false;
  ui.location.textContent = "2. Enable location";
  ui["location-status"].textContent = "Location received. Accuracy is an estimate; updates may be irregular.";
  update();
}

function onLocationError(error) {
  if (!["ready", "recording"].includes(state)) return;
  const message = error.code === 1
    ? "Location permission denied. Allow location in browser/site settings, then retry."
    : "Location unavailable or timed out. Move outdoors and wait for another reading.";
  ui["location-status"].textContent = message;
  if (state === "recording") {
    session.events.push({ type: "location_error", code: error.code, ...stamp() });
    if (error.code === 1) stopRecording("location_permission_revoked");
  } else {
    // A GPS problem must not tear down a working camera preview.
    // Timeouts/unavailable readings can recover on the same watch. Only a
    // permission denial requires stopping it; also offer an explicit retry.
    if (error.code === 1) {
      if (watchId !== null) navigator.geolocation.clearWatch(watchId);
      watchId = null;
      locationAttempt += 1;
    }
    locationNeedsRetry = true;
    samples = [];
    ui.accuracy.textContent = ui.age.textContent = "Waiting";
    ui.location.textContent = "2. Retry location";
    update();
  }
}

function requestLocation() {
  if (state !== "ready" || !liveCamera() || (watchId !== null && !locationNeedsRetry)) return;
  if (watchId !== null) navigator.geolocation.clearWatch(watchId);
  locationNeedsRetry = false;
  const attempt = ++locationAttempt;
  ui.location.textContent = "2. Enable location";
  ui["location-status"].textContent = "Allow location access. A first reading may take time outdoors.";
  watchId = navigator.geolocation.watchPosition(
    (position) => { if (attempt === locationAttempt) onPosition(position); },
    (error) => { if (attempt === locationAttempt) onLocationError(error); },
    { enableHighAccuracy: true, maximumAge: 0, timeout: 15000 },
  );
  update();
}

function previewReady() {
  if (state !== "ready" || !stream || !ui.preview.videoWidth || ui.preview.readyState < 2 || ui.preview.paused) return;
  const track = stream.getVideoTracks()[0];
  if (track.readyState !== "live" || track.muted || document.hidden) return;
  cameraReady = true;
  clearTimeout(previewTimer);
  ui["show-preview"].hidden = true;
  ui["camera-status"].textContent = "Camera preview is ready. Check that it shows the intended camera.";
  update();
}

function showPreview() {
  if (state !== "ready" || !stream || document.hidden) return;
  const attempt = ++previewAttempt;
  // Set DOM properties as well as HTML attributes before playing on iOS.
  ui.preview.muted = true;
  ui.preview.defaultMuted = true;
  ui.preview.playsInline = true;
  ui.preview.scrollIntoView({ block: "center", behavior: "instant" });
  ui["show-preview"].hidden = true;
  clearTimeout(previewTimer);
  previewTimer = setTimeout(() => {
    if (attempt !== previewAttempt || state !== "ready" || cameraReady) return;
    ui["show-preview"].hidden = false;
    ui["camera-status"].textContent = "Camera access was granted, but no preview has appeared. Tap Show camera preview. If it stays blank, cancel setup and report this message.";
  }, 5000);
  // Do not await playback in camera setup: browsers may reject or delay it.
  // This button also allows a new play() call directly from a user gesture.
  ui.preview.play().then(() => {
    if (attempt === previewAttempt) previewReady();
  }).catch((error) => {
    if (attempt !== previewAttempt || state !== "ready") return;
    clearTimeout(previewTimer);
    ui["show-preview"].hidden = false;
    ui["camera-status"].textContent = `Camera access was granted, but preview playback did not start (${error.name}). Tap Show camera preview.`;
  });
}

async function prepare() {
  if (state !== "idle") return;
  if (!window.isSecureContext) {
    ui.status.textContent = "Camera/location need trusted HTTPS or localhost. An ordinary phone-to-laptop HTTP address will not work.";
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia || !navigator.geolocation || !window.MediaRecorder) {
    ui.status.textContent = "This browser cannot run the experiment. Try a current Chrome or Safari browser.";
    return;
  }
  const attempt = ++setupAttempt;
  state = "preparing";
  cameraReady = false;
  samples = [];
  ui.count.textContent = "0";
  ui.accuracy.textContent = ui.age.textContent = "Waiting";
  ui.status.textContent = "Allow camera access when asked.";
  ui["camera-status"].textContent = "Waiting for camera permission. Respond to Safari's camera prompt.";
  ui["location-status"].textContent = "Location will be requested separately after the camera works.";
  ui.location.textContent = "2. Enable location";
  update();
  try {
    const camera = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 }, frameRate: { ideal: 30 } },
    });
    if (attempt !== setupAttempt) {
      camera.getTracks().forEach((track) => track.stop());
      return;
    }
    stream = camera;
    ui.preview.muted = true;
    ui.preview.defaultMuted = true;
    ui.preview.playsInline = true;
    ui.preview.srcObject = stream;
    const track = stream.getVideoTracks()[0];
    track.addEventListener("ended", () => {
      if (attempt !== setupAttempt) return;
      if (state === "recording") stopRecording("camera_ended");
      else if (state === "ready") cancelSetup("Camera stopped. Please retry.");
    });
    track.addEventListener("mute", () => {
      if (attempt !== setupAttempt || state !== "ready") return;
      cameraReady = false;
      ui["camera-status"].textContent = "Camera is temporarily interrupted. Return to this page and try Show camera preview.";
      ui["show-preview"].hidden = false;
      update();
    });
    track.addEventListener("unmute", () => {
      if (attempt === setupAttempt && state === "ready") showPreview();
    });
    state = "ready";
    ui["camera-status"].textContent = "Camera access granted. Starting the preview.";
    timer = setInterval(update, 250);
    showPreview();
    update();
  } catch (error) {
    if (attempt !== setupAttempt) return;
    const message = error.name === "NotAllowedError"
      ? "Camera access was blocked (NotAllowedError). Allow Camera for this website in Safari, then retry."
      : `Camera could not open (${error.name}). Close other camera apps, then retry.`;
    cancelSetup(message);
    ui["camera-status"].textContent = message;
  }
}

function startRecording() {
  if (state !== "ready" || !liveCamera() || !freshLocation()) return;
  try {
    // Prefer H.264 in MP4 for downloaded-file playback on phones. Safari can
    // also record WebM, but its Files preview may not open that container.
    const mimeType = ["video/mp4;codecs=avc1", "video/mp4", "video/webm;codecs=vp8", "video/webm"]
      .find((type) => MediaRecorder.isTypeSupported(type));
    recorder = new MediaRecorder(stream, { ...(mimeType ? { mimeType } : {}), videoBitsPerSecond: 2000000 });
    chunks = [];
    bytes = 0;
    const settings = stream.getVideoTracks()[0].getSettings();
    session = {
      schema_version: 1,
      test_id: `phone-test-${crypto.randomUUID()}`,
      video_requested_mime_type: mimeType || "browser-default",
      timing_note: "Start-request time is an approximate video origin. First-frame offset is uncalibrated. Do not assume frame-exact alignment.",
      location_note: "Browser geolocation may use GPS, Wi-Fi or other sources. Coordinates locate the phone, not a pothole.",
      camera: { width: settings.width, height: settings.height, frame_rate: settings.frameRate, facing_mode: settings.facingMode },
      recording_start_requested: stamp(),
      recording_start_event: null,
      recording_stop_requested: null,
      events: [],
    };
    recorder.onstart = () => { session.recording_start_event = stamp(); };
    recorder.ondataavailable = (event) => {
      if (event.data.size) {
        chunks.push(event.data);
        bytes += event.data.size;
      }
      // Chunk delivery is irregular. It must never be used as a clock.
      if (bytes >= MAX_BYTES) stopRecording("size_limit");
    };
    recorder.onerror = (event) => {
      session.events.push({ type: "recorder_error", name: event.error?.name || "UnknownError", ...stamp() });
      stopRecording("recorder_error");
    };
    recorder.onstop = finishRecording;
    // Timestamp immediately before start(), after recorder setup is complete.
    session.recording_start_requested = stamp();
    recorder.start(1000);
    state = "recording";
    ui.status.textContent = "Recording. Keep this page visible and the screen unlocked.";
    update();
  } catch (error) {
    session = null;
    cancelSetup(`Recording could not start (${error.name}). Enable the camera again to retry.`);
  }
}

function stopRecording(reason) {
  if (state !== "recording") return;
  state = "stopping";
  session.stop_reason = reason;
  session.recording_stop_requested = stamp();
  // Stop accepting GPS callbacks at the requested end of recording.
  if (watchId !== null) navigator.geolocation.clearWatch(watchId);
  watchId = null;
  ui.status.textContent = "Finishing the video. Keep this page open.";
  if (recorder.state !== "inactive") recorder.stop();
  update();
}

function downloadLink(id, blob, filename) {
  const url = URL.createObjectURL(blob);
  urls.push(url);
  ui[id].href = url;
  ui[id].download = filename;
  return url;
}

function finishRecording() {
  // MediaRecorder may stop itself after a device or encoding failure.
  if (!session.recording_stop_requested) {
    session.stop_reason = "recorder_ended";
    session.recording_stop_requested = stamp();
  }
  session.recording_stop_event = stamp();
  state = "complete";
  releaseDevices();
  const mime = recorder.mimeType || chunks.find((chunk) => chunk.type)?.type || "application/octet-stream";
  const video = new Blob(chunks, { type: mime });
  const extension = mime.includes("mp4") ? "mp4" : mime.includes("webm") ? "webm" : "bin";
  session.video_filename = `${session.test_id}.${extension}`;
  session.video_mime_type = mime;
  session.video_bytes = video.size;
  session.elapsed_ms = session.recording_stop_requested.monotonic_ms - session.recording_start_requested.monotonic_ms;
  session.clock_change_ms = (session.recording_stop_requested.epoch_ms - session.recording_start_requested.epoch_ms) - session.elapsed_ms;
  // Negative offsets are genuine readings from just before recording started.
  session.locations = samples.map((sample) => ({
    ...sample,
    offset_from_start_request_ms: sample.timestamp_epoch_ms - session.recording_start_requested.epoch_ms,
  }));
  const inRecording = session.locations.filter((sample) => sample.offset_from_start_request_ms >= 0
    && sample.timestamp_epoch_ms <= session.recording_stop_requested.epoch_ms);
  session.readings_during_recording = inRecording.length;
  session.warnings = [];
  if (inRecording.length < 2) session.warnings.push("Fewer than two location readings during recording; repeat outdoors to assess continuity.");
  if (Math.abs(session.clock_change_ms) > 1000) session.warnings.push("Phone clock changed; timestamp alignment requires review.");
  if (session.stop_reason !== "user" && session.stop_reason !== "time_limit") session.warnings.push(`Recording interrupted: ${session.stop_reason}.`);
  if (!video.size) session.warnings.push("No video data captured; repeat the test.");
  if (extension === "webm") session.warnings.push("WebM recording: if your file viewer cannot open it, try the player on this page.");
  if (video.size) {
    ui["recorded-video"].src = downloadLink("video-download", video, session.video_filename);
    ui["recorded-video"].load();
  }
  ui["recorded-video"].hidden = !video.size;
  ui["playback-status"].textContent = video.size ? "Tap Play to check the recording before saving both files." : "No video to play.";
  ui["video-download"].textContent = `Save video (.${extension})`;
  ui["video-download"].hidden = !video.size;
  downloadLink("json-download", new Blob([JSON.stringify(session, null, 2)], { type: "application/json" }), `${session.test_id}.json`);
  ui.downloads.hidden = false;
  ui.elapsed.textContent = `${(session.elapsed_ms / 1000).toFixed(1)} s`;
  ui.summary.textContent = `${extension.toUpperCase()} video, ${(video.size / 1024 / 1024).toFixed(1)} MB; ${inRecording.length} location readings during recording. ${session.warnings.join(" ")}`;
  ui.status.textContent = "Test ended. Save both files below, then check video playback.";
  chunks = [];
  update();
}

ui.prepare.addEventListener("click", prepare);
ui.location.addEventListener("click", requestLocation);
ui["show-preview"].addEventListener("click", showPreview);
ui.preview.addEventListener("playing", previewReady);
ui.preview.addEventListener("loadeddata", previewReady);
ui.start.addEventListener("click", startRecording);
ui.stop.addEventListener("click", () => stopRecording("user"));
ui.cancel.addEventListener("click", () => cancelSetup());
ui["recorded-video"].addEventListener("playing", () => {
  if (state === "complete") ui["playback-status"].textContent = "The recording is playing in this browser. Also check the downloaded file.";
});
ui["recorded-video"].addEventListener("error", () => {
  if (state === "complete") ui["playback-status"].textContent = "This browser could not play the recording. Save both files so we can investigate.";
});
ui.reset.addEventListener("click", () => {
  if (!window.confirm("Have you saved both files? Starting another test discards this page's copies.")) return;
  ui["recorded-video"].pause();
  ui["recorded-video"].removeAttribute("src");
  ui["recorded-video"].load();
  urls.forEach((url) => URL.revokeObjectURL(url));
  urls = [];
  session = null;
  samples = [];
  recorder = null;
  state = "idle";
  ui.downloads.hidden = true;
  ui.elapsed.textContent = "0 s";
  ui.accuracy.textContent = ui.age.textContent = "Waiting";
  ui["location-status"].textContent = "Location has not been requested.";
  ui["camera-status"].textContent = "Camera has not been requested.";
  ui.location.textContent = "2. Enable location";
  ui.status.textContent = "Ready for another test.";
  update();
});
document.addEventListener("visibilitychange", () => {
  // Keep permission/preview setup intact across temporary visibility changes.
  // A real recording still stops immediately when the page is hidden.
  if (document.hidden && state === "recording") stopRecording("page_hidden");
  else if (!document.hidden && state === "ready") showPreview();
  update();
});
window.addEventListener("pagehide", () => {
  if (state === "recording") stopRecording("page_hidden");
  else if (["preparing", "ready"].includes(state)) cancelSetup();
});
window.addEventListener("beforeunload", (event) => {
  if (["recording", "stopping", "complete"].includes(state)) {
    event.preventDefault();
    event.returnValue = "";
  }
});
