"""Inspect a phone-test export locally without printing coordinates or timestamps.

Usage: python scripts/inspect_recording.py [JSON_FILE_OR_FOLDER]
With no argument, inspect the single JSON file in this project's data/ folder.
This checks exported timing and file consistency; it does not decode video or
prove GPS accuracy or frame-exact synchronization.
"""

import argparse
import json
import math
from pathlib import Path
import statistics


PROJECT_DIR = Path(__file__).resolve().parents[1]
GAP_REVIEW_MS = 5000  # An experiment review threshold, not a validated road standard.


def number(value, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number.")
    return value


def analyze(data: dict) -> dict:
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Expected a phone-test export with schema_version 1.")
    try:
        start = data["recording_start_requested"]
        stop = data["recording_stop_requested"]
        start_ms = number(start["epoch_ms"], "Start timestamp")
        stop_ms = number(stop["epoch_ms"], "Stop timestamp")
        elapsed = number(stop["monotonic_ms"], "Stop timer") - number(start["monotonic_ms"], "Start timer")
        declared_elapsed = number(data["elapsed_ms"], "Exported duration")
        locations = data["locations"]
    except (KeyError, TypeError) as error:
        raise ValueError("Required recording timing or locations are missing.") from error
    if elapsed < 0 or abs(elapsed - declared_elapsed) > 1:
        raise ValueError("Recording duration does not match its monotonic start/stop timers.")
    if not isinstance(locations, list):
        raise ValueError("Locations must be a list.")

    during = []
    timestamps = []
    for index, reading in enumerate(locations, start=1):
        try:
            captured = number(reading["timestamp_epoch_ms"], f"Reading {index} timestamp")
            offset = number(reading["offset_from_start_request_ms"], f"Reading {index} offset")
            accuracy = number(reading["accuracy_m"], f"Reading {index} accuracy")
            latitude = number(reading["latitude"], f"Reading {index} latitude")
            longitude = number(reading["longitude"], f"Reading {index} longitude")
        except (KeyError, TypeError) as error:
            raise ValueError(f"Reading {index} is missing required fields.") from error
        if abs(latitude) > 90 or abs(longitude) > 180 or accuracy < 0:
            raise ValueError(f"Reading {index} has invalid coordinates or accuracy.")
        if abs(offset - (captured - start_ms)) > 1:
            raise ValueError(f"Reading {index} has an inconsistent acquisition-time offset.")
        timestamps.append(captured)
        # Use acquisition timestamps, never callback receipt times. Pre-recording
        # samples remain valid in the export but do not count as recording coverage.
        if start_ms <= captured <= stop_ms:
            during.append((captured, accuracy))

    flags = []
    clock_change = (stop_ms - start_ms) - elapsed
    if abs(clock_change) > 1000:
        flags.append("Phone clock changed relative to the timer; review alignment before using this export.")
    if any(right <= left for left, right in zip(timestamps, timestamps[1:])):
        flags.append("Location timestamps repeat or are out of order.")
    if len(during) < 2:
        flags.append("Fewer than two readings during recording; repeat a short outdoor test.")
    if data.get("readings_during_recording") != len(during):
        flags.append("Exported reading count disagrees with the acquisition timestamps.")
    if data.get("stop_reason") not in ("user", "time_limit"):
        flags.append("Recording ended with an interruption; inspect its stop_reason in the JSON.")
    if data.get("warnings"):
        flags.append("The recorder included warnings; inspect them in your private JSON file.")

    ordered = sorted(captured for captured, _ in during)
    gaps = [right - left for left, right in zip(ordered, ordered[1:])]
    # Include the unobserved time before the first and after the last reading.
    # Suppress these metrics when the calendar clock disagrees with the timer.
    clock_stable = abs(clock_change) <= 1000 and stop_ms >= start_ms
    boundaries = [start_ms, *ordered, stop_ms]
    longest_unobserved = max((right - left for left, right in zip(boundaries, boundaries[1:])), default=0) if clock_stable else None
    if longest_unobserved is not None and longest_unobserved > GAP_REVIEW_MS:
        flags.append("A location gap exceeds the 5-second experiment review threshold (including start/end gaps).")
    accuracies = [accuracy for _, accuracy in during]
    return {
        "duration_s": elapsed / 1000,
        "total_readings": len(locations),
        "during_readings": len(during),
        "before_readings": sum(value < start_ms for value in timestamps),
        "after_readings": sum(value > stop_ms for value in timestamps),
        "largest_gap_s": max(gaps) / 1000 if gaps and clock_stable else None,
        "longest_unobserved_s": longest_unobserved / 1000 if longest_unobserved is not None else None,
        "accuracy_min_m": min(accuracies) if accuracies else None,
        "accuracy_median_m": statistics.median(accuracies) if accuracies else None,
        "accuracy_max_m": max(accuracies) if accuracies else None,
        "clock_change_ms": clock_change,
        "flags": flags,
    }


def check_video(data: dict, folder: Path) -> str:
    name = data.get("video_filename")
    if not isinstance(name, str) or not name or "/" in name or "\\" in name or Path(name).is_absolute():
        raise ValueError("Video filename must be a filename inside the export folder.")
    video = (folder / name).resolve()
    if video.parent != folder.resolve():
        raise ValueError("Video must remain inside the export folder.")
    if not video.is_file():
        return "Matching video is missing; copy the video beside the JSON with its original filename."
    size = video.stat().st_size
    if size == 0 or size != data.get("video_bytes"):
        return "Video size is empty or differs from the export; check that the download is complete."
    with video.open("rb") as handle:
        header = handle.read(12)
    mime = data.get("video_mime_type", "")
    if not isinstance(mime, str):
        raise ValueError("Video MIME type must be text.")
    if mime.startswith("video/mp4") and video.suffix.lower() == ".mp4" and header[4:8] == b"ftyp":
        return "MP4 header and byte count match the export; playback is not checked by this script."
    if mime.startswith("video/webm") and video.suffix.lower() == ".webm" and header[:4] == b"\x1aE\xdf\xa3":
        return "WebM header and byte count match the export; playback is not checked by this script."
    return "Video header, filename or format needs review. This script does not convert files."


def display(value, unit: str) -> str:
    return "not available" if value is None else f"{value:.2f} {unit}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=PROJECT_DIR / "data")
    args = parser.parse_args()
    try:
        source = args.path
        if source.is_dir():
            candidates = list(source.glob("*.json"))
            if len(candidates) != 1:
                raise ValueError("Put exactly one test JSON in data/, or pass the path to one JSON file explicitly.")
            source = candidates[0]
        if source.stat().st_size > 5 * 1024 * 1024:
            raise ValueError("This checker expects a short-test JSON smaller than 5 MiB.")
        data = json.loads(source.read_text(encoding="utf-8-sig"))
        result = analyze(data)
        video_result = check_video(data, source.parent)
    except (OSError, ValueError) as error:
        # JSON decoder messages/OS errors may quote file contents or paths. Keep
        # the CLI error concise without echoing location data from malformed input.
        if isinstance(error, json.JSONDecodeError):
            message = "The file is not valid JSON. Use Save timing & locations from the recording page."
        elif isinstance(error, OSError):
            message = "Cannot read the export. Copy the matching JSON and video into data/, then retry."
        else:
            message = str(error)
        parser.exit(1, f"Check failed: {message}\n")

    print("LOCAL RECORDING CHECK - coordinates and absolute timestamps are omitted")
    print(f"Requested recording duration: {result['duration_s']:.2f} s (not decoded video duration)")
    print(f"Location readings: {result['during_readings']} during recording; {result['before_readings']} before; {result['after_readings']} after")
    print(f"Largest gap between readings: {display(result['largest_gap_s'], 's')}")
    print(f"Longest gap including start/end: {display(result['longest_unobserved_s'], 's')}")
    print(f"Reported accuracy, best / median / worst: {display(result['accuracy_min_m'], 'm')} / {display(result['accuracy_median_m'], 'm')} / {display(result['accuracy_max_m'], 'm')}")
    print(f"Clock disagreement: {result['clock_change_ms']:.2f} ms")
    print(f"Video: {video_result}")
    print("Review flags: " + ("none from these limited checks" if not result['flags'] else ""))
    for flag in result["flags"]:
        print(f"- {flag}")
    print("Accuracy values are device estimates. First-frame alignment remains uncalibrated.")


if __name__ == "__main__":
    main()
