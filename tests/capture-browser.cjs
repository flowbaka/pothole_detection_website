// Integration checks with Chrome's simulated camera/location. These do not
// establish real phone compatibility or real GPS accuracy. No npm packages needed.
const assert = require("node:assert/strict");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "pothole-capture-test-"));
const python = path.join(root, ".pothholevenv", "Scripts", "python.exe");
const chromePath = process.env.CHROME_PATH || "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
let server, chrome, socket, send, readDebug;

async function until(check, description) {
  for (let i = 0; i < 80; i++) {
    const result = await check();
    if (result) return result;
    await delay(100);
  }
  throw new Error(`Timed out: ${description}`);
}

async function main() {
  let serverLog = "";
  server = spawn(python, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "0"], { cwd: root, windowsHide: true });
  server.on("error", (error) => { serverLog += error.message; });
  server.stderr.on("data", (data) => { serverLog += data; });
  const origin = await until(() => {
    if (server.exitCode !== null) throw new Error(serverLog);
    return serverLog.match(/http:\/\/127\.0\.0\.1:\d+/)?.[0];
  }, "temporary API server");
  assert.deepEqual(await (await fetch(`${origin}/health`)).json(), { status: "ok" });
  assert.deepEqual(await (await fetch(`${origin}/`)).json(), { message: "Pothole Reporting API is running" });
  for (const endpoint of ["/docs", "/openapi.json", "/capture", "/static/capture.js", "/static/capture.css"]) {
    assert.equal((await fetch(origin + endpoint)).status, 200, endpoint);
  }
  const capturePage = await fetch(`${origin}/capture`);
  assert.equal(capturePage.headers.get("cache-control"), "no-store");
  assert.match(await capturePage.text(), /capture\.js\?v=3/);
  assert.equal((await fetch(`${origin}/static/requirements.txt`)).status, 404);
  console.log("PASS API routes, capture assets, and static directory boundary");

  chrome = spawn(chromePath, ["--headless=new", "--no-first-run", "--no-default-browser-check",
    "--remote-debugging-port=0", `--user-data-dir=${profile}`, "--use-fake-device-for-media-stream",
    "--use-fake-ui-for-media-stream", "--window-size=390,844", "about:blank"], { windowsHide: true, stdio: "ignore" });
  let chromeError;
  chrome.on("error", (error) => { chromeError = error; });
  const port = await until(() => {
    if (chromeError) throw chromeError;
    const portFile = path.join(profile, "DevToolsActivePort");
    return fs.existsSync(portFile) && fs.readFileSync(portFile, "utf8").split(/\r?\n/)[0];
  }, "isolated headless Chrome");
  const tabs = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  socket = new WebSocket(tabs.find((tab) => tab.type === "page").webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
  let id = 0;
  const pending = new Map();
  const errors = [];
  socket.onmessage = ({ data }) => {
    const message = JSON.parse(data);
    if (message.method === "Runtime.exceptionThrown") errors.push(message.params.exceptionDetails.text);
    const waiter = pending.get(message.id);
    if (waiter) {
      pending.delete(message.id);
      clearTimeout(waiter.timeout);
      if (message.error) waiter.reject(new Error(JSON.stringify(message.error)));
      else waiter.resolve(message.result);
    }
  };
  send = (method, params = {}) => new Promise((resolve, reject) => {
    const requestId = ++id;
    const timeout = setTimeout(() => { pending.delete(requestId); reject(new Error(`CDP timeout: ${method}`)); }, 8000);
    pending.set(requestId, { resolve, reject, timeout });
    socket.send(JSON.stringify({ id: requestId, method, params }));
  });
  const evaluate = async (expression) => {
    const result = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true, userGesture: true });
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  readDebug = () => evaluate(`({state, cameraReady, cameraLive: liveCamera(), hidden: document.hidden,
    trackState: stream?.getVideoTracks()[0]?.readyState, trackMuted: stream?.getVideoTracks()[0]?.muted,
    watchId, sampleCount: samples.length, latestAge: Date.now() - samples.at(-1)?.timestamp_epoch_ms,
    status: ui.status.textContent, cameraStatus: ui['camera-status'].textContent,
    locationStatus: ui['location-status'].textContent})`);
  await send("Runtime.enable");
  await send("Page.enable");
  await send("Browser.grantPermissions", { origin, permissions: ["geolocation"] });
  await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await send("Emulation.setGeolocationOverride", { latitude: 26.45, longitude: 87.27, accuracy: 12 });
  await send("Page.navigate", { url: `${origin}/capture` });
  await until(() => evaluate("typeof prepare === 'function'"), "capture page loaded");
  assert.equal(await evaluate("document.documentElement.scrollWidth <= window.innerWidth"), true, "mobile width");
  await evaluate("prepare()");
  await until(() => evaluate("liveCamera()"), "camera preview ready");
  assert.equal(await evaluate("watchId === null && ui.start.disabled && !ui.location.disabled"), true, "camera and location are separate steps");
  await evaluate("requestLocation()");
  await until(() => evaluate("!ui.start.disabled"), "camera and simulated GPS ready");
  const supportsMp4 = await evaluate("MediaRecorder.isTypeSupported('video/mp4;codecs=avc1') || MediaRecorder.isTypeSupported('video/mp4')");
  assert.ok(supportsMp4, "this integration run needs Chrome with MP4 recording support");
  await evaluate("startRecording()");
  for (let i = 1; i <= 3; i++) {
    await delay(1100);
    await send("Emulation.setGeolocationOverride", { latitude: 26.45 + i * 0.0001, longitude: 87.27, accuracy: 12 });
  }
  await evaluate("stopRecording('user')");
  await until(() => evaluate("state === 'complete'"), "recording finalized");
  const metadata = await evaluate("fetch(ui['json-download'].href).then(r => r.json())");
  assert.ok(metadata.video_bytes > 1000, "real encoded video from simulated camera");
  assert.ok(metadata.readings_during_recording >= 2);
  assert.ok(metadata.elapsed_ms >= 3000 && metadata.elapsed_ms < 8000);
  assert.equal(metadata.stop_reason, "user");
  assert.match(metadata.video_requested_mime_type, /^video\/mp4/);
  assert.match(metadata.video_mime_type, /^video\/mp4/);
  assert.match(metadata.video_filename, /\.mp4$/);
  assert.equal(await evaluate("ui['video-download'].download === session.video_filename"), true);
  // Inspect actual bytes as well as the extension: MP4 starts with an ftyp box.
  assert.equal(await evaluate("fetch(ui['video-download'].href).then(r => r.arrayBuffer()).then(b => new TextDecoder().decode(b.slice(4, 8)))"), "ftyp");
  for (const sample of metadata.locations) {
    assert.equal(sample.offset_from_start_request_ms, sample.timestamp_epoch_ms - metadata.recording_start_requested.epoch_ms);
    assert.equal(sample.accuracy_m, 12);
  }
  assert.equal(await evaluate("stream === null && watchId === null"), true, "devices released");
  await evaluate("ui['recorded-video'].play()");
  await until(() => evaluate("ui['recorded-video'].videoWidth > 0 && ui['recorded-video'].currentTime > 0.2"), "MP4 playback advances");
  assert.match(await evaluate("ui['playback-status'].textContent"), /playing in this browser/);
  await evaluate("ui['recorded-video'].pause()");
  console.log("PASS real MP4 bytes, advancing playback, paired JSON, acquisition-time offsets, and cleanup (simulated inputs)");

  await evaluate("window.confirm = () => true; ui.reset.click();");
  assert.equal(await evaluate("ui['recorded-video'].getAttribute('src')"), null, "reset detaches recorded video");
  // Model a browser with WebM recording only; still encode a real WebM file.
  await evaluate("window.originalTypeSupport = MediaRecorder.isTypeSupported.bind(MediaRecorder); MediaRecorder.isTypeSupported = type => type.startsWith('video/webm') && originalTypeSupport(type);");
  await evaluate("prepare()");
  await until(() => evaluate("liveCamera()"), "second camera preview");
  await evaluate("requestLocation()");
  await until(() => evaluate("!ui.start.disabled"), "second test ready");
  await evaluate("samples[samples.length - 1].timestamp_epoch_ms = Date.now() - 16000; update(); startRecording();");
  assert.equal(await evaluate("ui.start.disabled && state === 'ready'"), true, "stale GPS cannot start recording");
  await send("Emulation.setGeolocationOverride", { latitude: 26.451, longitude: 87.27, accuracy: 12 });
  await until(() => evaluate("!ui.start.disabled"), "fresh position");
  await evaluate("startRecording()");
  await delay(1100);
  await evaluate("Object.defineProperty(document, 'hidden', { configurable: true, value: true }); document.dispatchEvent(new Event('visibilitychange'));");
  await until(() => evaluate("state === 'complete'"), "hidden-page recording finalized");
  assert.equal(await evaluate("session.stop_reason"), "page_hidden");
  assert.ok(await evaluate("session.warnings.some(w => w.includes('page_hidden'))"));
  assert.match(await evaluate("session.video_filename"), /\.webm$/);
  assert.ok(await evaluate("session.warnings.some(w => w.includes('WebM recording'))"));
  assert.equal(await evaluate("fetch(ui['video-download'].href).then(r => r.arrayBuffer()).then(b => Array.from(new Uint8Array(b.slice(0, 4))).map(n => n.toString(16).padStart(2, '0')).join(''))"), "1a45dfa3");
  await evaluate("Object.defineProperty(document, 'hidden', { configurable: true, value: false }); ui['recorded-video'].play();");
  await until(() => evaluate("ui['recorded-video'].videoWidth > 0 && ui['recorded-video'].currentTime > 0.2"), "WebM fallback plays");
  await evaluate("MediaRecorder.isTypeSupported = originalTypeSupport;");
  console.log("PASS WebM fallback has matching bytes, filename, warning and playable output");
  await evaluate("Object.defineProperty(document, 'hidden', { configurable: true, value: false }); ui.reset.click();");
  await send("Browser.setPermission", { origin, permission: { name: "geolocation" }, setting: "denied" });
  await evaluate("prepare()");
  await until(() => evaluate("liveCamera()"), "camera before location denial");
  await evaluate("requestLocation()");
  await until(() => evaluate("ui['location-status'].textContent.includes('denied')"), "location denial handled");
  assert.equal(await evaluate("liveCamera() && watchId === null && ui.start.disabled && !ui.location.disabled"), true, "location denial leaves camera working and allows retry");
  await send("Browser.setPermission", { origin, permission: { name: "geolocation" }, setting: "granted" });
  await evaluate("requestLocation()");
  await until(() => evaluate("!ui.start.disabled"), "location retry succeeds");
  await evaluate("cancelSetup()");
  console.log("PASS stale location, recording interruption, separate permissions, GPS denial/retry, and mobile layout");

  // Reproduce a delayed permission response with an intervening hidden page.
  // This models the lifecycle race; it does not claim to emulate Safari itself.
  await evaluate(`
    window.originalGetUserMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
    navigator.mediaDevices.getUserMedia = async (options) => {
      window.heldCamera = await originalGetUserMedia(options);
      await new Promise(resolve => { window.resolveCamera = resolve; });
      return heldCamera;
    };
    void prepare();
  `);
  await until(() => evaluate("typeof window.resolveCamera === 'function'"), "pending camera permission");
  await evaluate("Object.defineProperty(document, 'hidden', { configurable: true, value: true }); document.dispatchEvent(new Event('visibilitychange'));");
  assert.equal(await evaluate("state"), "preparing", "temporary hidden state must not cancel permission setup");
  await evaluate("resolveCamera()");
  await until(() => evaluate("state === 'ready'"), "camera permission completes while hidden");
  assert.equal(await evaluate("stream.getVideoTracks()[0].readyState"), "live");
  await evaluate("Object.defineProperty(document, 'hidden', { configurable: true, value: false }); document.dispatchEvent(new Event('visibilitychange'));");
  await until(() => evaluate("liveCamera()"), "preview resumes when visible");
  await evaluate("cancelSetup(); navigator.mediaDevices.getUserMedia = originalGetUserMedia;");
  assert.equal(await evaluate("heldCamera.getTracks().every(track => track.readyState === 'ended')"), true);
  console.log("PASS delayed permission survives visibility changes and preview resumes");

  // Reject preview playback while still granting a real simulated camera stream.
  await evaluate(`
    ui.preview.autoplay = false;
    window.originalPlay = ui.preview.play.bind(ui.preview);
    ui.preview.play = () => Promise.reject(new DOMException('Playback needs a tap', 'NotAllowedError'));
    prepare();
  `);
  await until(() => evaluate("!ui['show-preview'].hidden"), "manual preview recovery offered");
  assert.equal(await evaluate("state === 'ready' && stream.getVideoTracks()[0].readyState === 'live' && ui.start.disabled"), true);
  assert.match(await evaluate("ui['camera-status'].textContent"), /access was granted.*NotAllowedError/);
  await evaluate("ui.preview.play = originalPlay; ui['show-preview'].click();");
  await until(() => evaluate("liveCamera()"), "tap resumes playback");
  await evaluate("cancelSetup()");

  // A play() promise that never settles must not leave setup stuck forever.
  await evaluate("ui.preview.play = () => new Promise(() => {}); prepare();");
  await until(() => evaluate("!ui['show-preview'].hidden"), "delayed playback exposes retry");
  assert.equal(await evaluate("state === 'ready' && !ui.cancel.disabled"), true);
  await evaluate("ui.preview.play = originalPlay; ui['show-preview'].click();");
  await until(() => evaluate("liveCamera()"), "delayed playback recovers");
  await evaluate("cancelSetup(); ui.preview.autoplay = true;");
  console.log("PASS rejected and delayed playback recover through the preview button");

  await evaluate("navigator.mediaDevices.getUserMedia = () => Promise.reject(new DOMException('Denied', 'NotAllowedError')); prepare();");
  await until(() => evaluate("ui['camera-status'].textContent.includes('Camera access was blocked')"), "camera permission denial message");
  assert.equal(await evaluate("state === 'idle' && stream === null && !ui.prepare.disabled"), true);
  await evaluate("navigator.mediaDevices.getUserMedia = originalGetUserMedia;");
  await evaluate("prepare()");
  await until(() => evaluate("liveCamera()"), "camera before recorder failure");
  await evaluate("requestLocation()");
  await until(() => evaluate("!ui.start.disabled"), "GPS before recorder failure");
  await evaluate(`
    window.originalRecorderStart = MediaRecorder.prototype.start;
    MediaRecorder.prototype.start = () => { throw new DOMException('Unsupported encoder', 'NotSupportedError'); };
    startRecording();
    update();
    MediaRecorder.prototype.start = originalRecorderStart;
  `);
  assert.equal(await evaluate("state === 'idle' && stream === null && session === null"), true);
  assert.match(await evaluate("ui.status.textContent"), /Recording could not start \(NotSupportedError\)/);
  assert.deepEqual(errors, []);
  console.log("PASS camera permission and recorder errors remain visible and clean up devices");
}

main().catch(async (error) => {
  console.error(error);
  if (readDebug && socket?.readyState === WebSocket.OPEN) console.error(await readDebug().catch(() => "Browser diagnostics unavailable"));
  process.exitCode = 1;
}).finally(async () => {
  if (send && socket?.readyState === WebSocket.OPEN) {
    await send("Browser.close").catch(() => {});
    socket.close();
  }
  if (chrome && chrome.exitCode === null) chrome.kill();
  if (server && server.exitCode === null) server.kill();
  await delay(500);
  // Delete only this test's newly created Chrome profile inside the OS temp folder.
  const resolvedProfile = path.resolve(profile);
  if (path.dirname(resolvedProfile) === path.resolve(os.tmpdir())
      && path.basename(resolvedProfile).startsWith("pothole-capture-test-")) {
    fs.rmSync(resolvedProfile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
  }
});
