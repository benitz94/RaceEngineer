import contextlib
import io
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from raceengineer.demo import main
from raceengineer.model import Sample
from raceengineer.recording import encode, read_samples
from raceengineer.sources import paced, synthetic
from raceengineer.udp_probe import receive_info


class RecoveryTests(unittest.TestCase):
    def test_repeatable_cli(self):
        outputs = []
        for _ in range(2):
            output = io.StringIO()
            with contextlib.redirect_stdout(output), patch("raceengineer.demo.paced", side_effect=lambda samples, rate: samples):
                self.assertEqual(main(["--source", "synthetic"]), 0)
            outputs.append(output.getvalue())
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(len(outputs[0].splitlines()), 20)
        samples = list(synthetic())
        self.assertIsNone(samples[6].speed)
        self.assertFalse(samples[10].valid)

    def test_replay_preserves_order_duplicates_and_missing_data(self):
        samples = [Sample(source_ts=2, valid=False), Sample(source_ts=1), Sample(source_ts=1)]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "recording.jsonl"
            path.write_text("\n".join(map(encode, samples)) + "\n", encoding="utf-8")
            self.assertEqual(list(read_samples(path)), samples)
            path.write_text("\n".join(map(encode, samples)) + "\n", encoding="utf-8-sig")
            self.assertEqual(list(read_samples(path)), samples)
            output = io.StringIO()
            with contextlib.redirect_stdout(output), patch("raceengineer.demo.paced", side_effect=lambda samples, rate: samples):
                self.assertEqual(main(["--source", "file", str(path)]), 0)
            self.assertEqual(output.getvalue(), path.read_text(encoding="utf-8-sig"))
            path.write_text('{"format":"raceengineer.sample","version":1,"sample":{}}\n', encoding="utf-8")
            self.assertEqual(list(read_samples(path)), [Sample()])

    def test_bad_recording_diagnostics(self):
        bad = ["{", '{"format":"raceengineer.sample","version":2,"sample":{}}',
               '{"format":"raceengineer.sample","version":true,"sample":{}}',
               '{"format":"raceengineer.sample","version":1,"sample":{"speed":NaN}}',
               '{"format":"raceengineer.sample","version":1,"sample":{"lap":true}}']
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "bad.jsonl"
            for line in bad:
                path.write_text(encode(Sample()) + "\n" + line, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "line 2"):
                    list(read_samples(path))

    def test_controlled_rate(self):
        now = [100.0]
        delays = []
        def sleep(delay):
            delays.append(delay)
            now[0] += delay
        samples = list(synthetic(3, 2))
        self.assertEqual(list(paced(samples, 2, clock=lambda: now[0], sleep=sleep)), samples)
        self.assertEqual(delays, [0.5, 0.5])
        for rate in (0, -1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                list(synthetic(rate=rate))

    def test_udp_metadata_only(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver, socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
            receiver.bind(("127.0.0.1", 0))
            receiver.settimeout(2)
            sender.sendto(b"opaque payload", receiver.getsockname())
            info = receive_info(receiver).to_dict()
        self.assertEqual(set(info), {"peer", "size", "recv_ts"})
        self.assertEqual(info["size"], 14)
        self.assertEqual(info["peer"][0], "127.0.0.1")
        self.assertGreater(info["recv_ts"], 0)


if __name__ == "__main__":
    unittest.main()
