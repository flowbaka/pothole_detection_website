"""Synthetic fixtures only: these tests do not represent a real journey."""

import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.inspect_recording import analyze, check_video, main


def example():
    start = 1_700_000_000_000
    # One warm-up reading and two during recording. Callback receipt is delayed
    # on purpose; the inspector must use measurement time for alignment.
    locations = [{
        "timestamp_epoch_ms": start + offset,
        "offset_from_start_request_ms": offset,
        "received": {"epoch_ms": start + offset + 7000},
        "latitude": 26.45,
        "longitude": 87.27,
        "accuracy_m": accuracy,
    } for offset, accuracy in [(-1000, 100), (2000, 6), (8000, 10)]]
    return {
        "schema_version": 1,
        "recording_start_requested": {"epoch_ms": start, "monotonic_ms": 100},
        "recording_stop_requested": {"epoch_ms": start + 10000, "monotonic_ms": 10100},
        "elapsed_ms": 10000,
        "locations": locations,
        "readings_during_recording": 2,
        "stop_reason": "user",
        "warnings": [],
    }


class RecordingInspectionTests(unittest.TestCase):
    def test_cli_reports_stats_without_coordinates_or_absolute_times(self):
        with tempfile.TemporaryDirectory(prefix="pothole-inspector-") as directory:
            folder = Path(directory)
            data = example()
            header = b"\x00\x00\x00\x18ftypisom"
            data.update(video_filename="test.mp4", video_bytes=len(header), video_mime_type="video/mp4")
            (folder / "test.mp4").write_bytes(header)
            (folder / "test.json").write_text(json.dumps(data), encoding="utf-8")
            output = io.StringIO()
            with patch("sys.argv", ["inspect_recording.py", str(folder)]), redirect_stdout(output):
                main()
            report = output.getvalue()
            self.assertIn("duration: 10.00 s", report)
            self.assertIn("2 during recording; 1 before", report)
            self.assertIn("6.00 s", report)
            self.assertIn("8.00 m", report)
            for private_value in ("26.45", "87.27", "1700000000000"):
                self.assertNotIn(private_value, report)

    def test_acquisition_times_and_pre_recording_reading(self):
        result = analyze(example())
        self.assertEqual(result["duration_s"], 10)
        self.assertEqual(result["before_readings"], 1)
        self.assertEqual(result["during_readings"], 2)
        self.assertEqual(result["largest_gap_s"], 6)
        self.assertEqual(result["accuracy_median_m"], 8)
        self.assertTrue(any("5-second" in flag for flag in result["flags"]))
        self.assertNotIn("latitude", str(result))
        self.assertNotIn("26.45", str(result))

    def test_no_readings_does_not_invent_coverage(self):
        data = example()
        data["locations"] = []
        data["readings_during_recording"] = 0
        result = analyze(data)
        self.assertIsNone(result["accuracy_min_m"])
        self.assertIsNone(result["largest_gap_s"])
        self.assertEqual(result["longest_unobserved_s"], 10)
        self.assertTrue(any("Fewer than two" in flag for flag in result["flags"]))

    def test_clock_change_suppresses_gap_metrics(self):
        data = example()
        data["recording_stop_requested"]["epoch_ms"] += 5000
        result = analyze(data)
        self.assertEqual(result["clock_change_ms"], 5000)
        self.assertIsNone(result["largest_gap_s"])
        self.assertIsNone(result["longest_unobserved_s"])

    def test_invalid_offset_and_non_numeric_readings(self):
        for field, value in [("offset_from_start_request_ms", 999), ("latitude", float("nan")), ("accuracy_m", True)]:
            data = copy.deepcopy(example())
            data["locations"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                analyze(data)

    def test_gaps_include_unobserved_recording_edges(self):
        data = example()
        data["locations"] = data["locations"][:2]
        data["readings_during_recording"] = 1
        result = analyze(data)
        self.assertIsNone(result["largest_gap_s"])
        self.assertEqual(result["longest_unobserved_s"], 8)

    def test_pair_checks_header_and_size_without_claiming_playback(self):
        # A synthetic MP4 header, deliberately not a decodable video.
        header = b"\x00\x00\x00\x18ftypisom"
        with tempfile.TemporaryDirectory(prefix="pothole-inspector-") as directory:
            folder = Path(directory)
            data = {"video_filename": "test.mp4", "video_bytes": len(header), "video_mime_type": "video/mp4"}
            self.assertIn("missing", check_video(data, folder))
            (folder / "test.mp4").write_bytes(header)
            self.assertIn("playback is not checked", check_video(data, folder))
            (folder / "test.mp4").write_bytes(header[:-1])
            self.assertIn("differs", check_video(data, folder))
            data["video_filename"] = "../outside.mp4"
            with self.assertRaises(ValueError):
                check_video(data, folder)


if __name__ == "__main__":
    unittest.main()
