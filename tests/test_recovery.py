import contextlib
import inspect
import io
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from raceengineer import demo
from raceengineer.demo import main
from raceengineer.model import Sample
from raceengineer.recording import encode, read_samples
from raceengineer.rules import RulesEngine
from raceengineer.sources import ReplaySession, paced, replay, synthetic
from raceengineer.udp_probe import receive_info


class FakeReplayTime:
    def __init__(self):
        self.now = 0.0
        self.waits = []
        self.on_wait = None

    def __call__(self):
        return self.now

    def wait(self, condition, timeout):
        condition.release()
        try:
            self.waits.append(timeout)
            interrupted = self.on_wait(timeout) if self.on_wait else False
            self.on_wait = None
            if timeout is not None and not interrupted:
                self.now += timeout
        finally:
            condition.acquire()


class RecoveryTests(unittest.TestCase):
    def test_repeatable_cli(self):
        outputs = []
        for _ in range(2):
            output = io.StringIO()
            with contextlib.redirect_stdout(output), patch("raceengineer.demo.paced", side_effect=lambda samples, rate: samples):
                self.assertEqual(main(["--source", "synthetic", "--samples-only"]), 0)
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

    def write_recording(self, directory, samples):
        path = Path(directory) / "replay.jsonl"
        path.write_text("\n".join(map(encode, samples)) + ("\n" if samples else ""), encoding="utf-8")
        return path

    def make_replay_session(self, path, fake_time, rate=1):
        return ReplaySession(path, rate, clock=fake_time, wait=fake_time.wait)

    def test_replay_session_without_pause_preserves_samples_and_rate(self):
        repeated = Sample(source_ts=3, fuel=8, valid=True)
        samples = [repeated, repeated, Sample(source_ts=1, fuel=7)]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = self.write_recording(directory, samples)
            fake_time = FakeReplayTime()
            session = self.make_replay_session(path, fake_time, rate=2)
            self.assertEqual(list(session), samples)
            self.assertEqual(list(replay(path)), samples)
            self.assertEqual(fake_time.waits, [0.5, 0.5])
            self.assertEqual(fake_time.now, 1.0)
            self.assertEqual(session.state, "exhausted")

    def test_replay_pause_before_first_sample_waits_for_resume(self):
        samples = [Sample(source_ts=4), Sample(source_ts=2)]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = self.write_recording(directory, samples)
            fake_time = FakeReplayTime()
            session = self.make_replay_session(path, fake_time)
            session.pause()
            session.pause()
            self.assertEqual(session.state, "paused")
            def resume_before_start(timeout):
                self.assertIsNone(timeout)
                session.resume()
                return True
            fake_time.on_wait = resume_before_start
            self.assertEqual(next(session), samples[0])
            self.assertEqual(session.state, "running")
            self.assertEqual(fake_time.now, 0)
            self.assertEqual(list(session), samples[1:])

    def test_replay_pause_between_samples_freezes_remaining_interval(self):
        samples = [Sample(source_ts=2), Sample(source_ts=1)]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = self.write_recording(directory, samples)
            fake_time = FakeReplayTime()
            session = self.make_replay_session(path, fake_time)
            self.assertEqual(next(session), samples[0])
            session.pause()
            def resume_after_long_pause(timeout):
                self.assertIsNone(timeout)
                fake_time.now += 1000
                session.resume()
                return True
            fake_time.on_wait = resume_after_long_pause
            self.assertEqual(next(session), samples[1])
            self.assertEqual(fake_time.waits, [None, 1])
            self.assertEqual(fake_time.now, 1001)
            self.assertEqual(list(session), [])

    def test_replay_pause_during_pending_interval_resumes_remaining_time(self):
        samples = [Sample(source_ts=2), Sample(source_ts=1)]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = self.write_recording(directory, samples)
            fake_time = FakeReplayTime()
            session = self.make_replay_session(path, fake_time)
            self.assertEqual(next(session), samples[0])
            def pause_during_wait(timeout):
                self.assertEqual(timeout, 1)
                fake_time.now += 0.25
                session.pause()
                fake_time.now += 100
                session.resume()
                return True
            fake_time.on_wait = pause_during_wait
            self.assertEqual(next(session), samples[1])
            self.assertEqual(fake_time.waits, [1, 0.75])
            self.assertEqual(fake_time.now, 101)
            self.assertEqual(list(session), [])

    def test_replay_long_pause_does_not_cause_catch_up(self):
        samples = [Sample(source_ts=index) for index in range(4)]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = self.write_recording(directory, samples)
            fake_time = FakeReplayTime()
            session = self.make_replay_session(path, fake_time)
            self.assertEqual(next(session), samples[0])
            session.pause()
            def long_pause(timeout):
                self.assertIsNone(timeout)
                fake_time.now += 10000
                session.resume()
                return True
            fake_time.on_wait = long_pause
            self.assertEqual(next(session), samples[1])
            self.assertEqual(fake_time.now, 10001)
            self.assertEqual(next(session), samples[2])
            self.assertEqual(fake_time.now, 10002)
            self.assertEqual(next(session), samples[3])
            self.assertEqual(fake_time.now, 10003)
            with self.assertRaises(StopIteration):
                next(session)

    def test_replay_multiple_pause_resume_cycles_and_no_op_calls(self):
        samples = [Sample(source_ts=index) for index in range(4)]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = self.write_recording(directory, samples)
            fake_time = FakeReplayTime()
            session = self.make_replay_session(path, fake_time)
            self.assertEqual(next(session), samples[0])
            session.resume()
            session.pause()
            session.pause()
            pauses = iter((5, 10))
            def resume_after_pause(timeout):
                self.assertIsNone(timeout)
                fake_time.now += next(pauses)
                session.resume()
                return True
            fake_time.on_wait = resume_after_pause
            self.assertEqual(next(session), samples[1])
            session.pause()
            session.pause()
            self.assertEqual(session.state, "paused")
            fake_time.on_wait = resume_after_pause
            self.assertEqual(next(session), samples[2])
            session.resume()
            self.assertEqual(list(session), samples[3:])
            self.assertEqual(fake_time.now, 18)

    def test_empty_single_sample_and_exhaustion_are_terminal(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            empty_path = self.write_recording(directory, [])
            empty_time = FakeReplayTime()
            empty = self.make_replay_session(empty_path, empty_time)
            with self.assertRaises(StopIteration):
                next(empty)
            self.assertEqual(empty.state, "exhausted")
            empty.pause()
            empty.resume()
            self.assertEqual(empty.state, "exhausted")

            sample = Sample(source_ts=8, fuel=9, valid=True)
            one_path = self.write_recording(directory, [sample])
            single = self.make_replay_session(one_path, FakeReplayTime())
            self.assertEqual(list(single), [sample])
            self.assertEqual(single.state, "exhausted")
            single.pause()
            single.resume()
            with self.assertRaises(StopIteration):
                next(single)
            self.assertEqual(single.state, "exhausted")

    def test_recorded_rules_are_equivalent_with_and_without_pauses(self):
        samples = [
            Sample(source_ts=5, fuel=11, valid=True),
            Sample(source_ts=3, fuel=9, valid=True),
            Sample(source_ts=4, fuel=8, valid=True),
            Sample(source_ts=1, fuel=13, valid=True),
            Sample(source_ts=0, fuel=9, valid=True),
        ]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = self.write_recording(directory, samples)
            expected_engine = RulesEngine()
            expected = [alert.encode() for sample in replay(path)
                        if (alert := expected_engine.process(sample)) is not None]

            fake_time = FakeReplayTime()
            session = self.make_replay_session(path, fake_time)
            paused_engine = RulesEngine()
            actual = []
            self.assertEqual(next(session), samples[0])
            session.pause()
            def resume_after_pause(timeout):
                self.assertIsNone(timeout)
                fake_time.now += 200
                session.resume()
                return True
            fake_time.on_wait = resume_after_pause
            remaining = [next(session)]
            remaining.extend(session)
            for sample in [samples[0], *remaining]:
                alert = paused_engine.process(sample)
                if alert is not None:
                    actual.append(alert.encode())
            self.assertEqual(actual, expected)

    def test_replay_stop_before_first_sample_yields_nothing(self):
        samples = [Sample(source_ts=4), Sample(source_ts=2)]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = self.write_recording(directory, samples)
            fake_time = FakeReplayTime()
            session = self.make_replay_session(path, fake_time)
            session.stop()
            session.stop()
            self.assertEqual(session.state, "stopped")
            with self.assertRaises(StopIteration):
                next(session)
            self.assertEqual(session.state, "stopped")
            self.assertEqual(list(session), [])
            self.assertEqual(fake_time.waits, [])
            session.pause()
            session.resume()
            self.assertEqual(session.state, "stopped")
            path.unlink()
            self.assertFalse(path.exists())

    def test_replay_stop_while_paused_before_first_sample_is_terminal(self):
        samples = [Sample(source_ts=4), Sample(source_ts=2)]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = self.write_recording(directory, samples)
            fake_time = FakeReplayTime()
            session = self.make_replay_session(path, fake_time)
            session.pause()
            self.assertEqual(session.state, "paused")
            def stop_before_first(timeout):
                self.assertIsNone(timeout)
                session.stop()
                return True
            fake_time.on_wait = stop_before_first
            with self.assertRaises(StopIteration):
                next(session)
            self.assertEqual(session.state, "stopped")
            session.pause()
            session.resume()
            self.assertEqual(session.state, "stopped")
            self.assertEqual(list(session), [])
            self.assertEqual(fake_time.now, 0)
            path.unlink()
            self.assertFalse(path.exists())

    def test_replay_stop_after_first_sample_drops_remaining(self):
        samples = [Sample(source_ts=index) for index in range(3)]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = self.write_recording(directory, samples)
            fake_time = FakeReplayTime()
            session = self.make_replay_session(path, fake_time)
            self.assertEqual(next(session), samples[0])
            session.stop()
            with self.assertRaises(StopIteration):
                next(session)
            self.assertEqual(session.state, "stopped")
            self.assertEqual(list(session), [])
            self.assertEqual(fake_time.now, 0)
            path.unlink()
            self.assertFalse(path.exists())

    def test_replay_stop_while_paused_without_waiter_is_terminal(self):
        samples = [Sample(source_ts=index) for index in range(3)]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = self.write_recording(directory, samples)
            fake_time = FakeReplayTime()
            session = self.make_replay_session(path, fake_time)
            self.assertEqual(next(session), samples[0])
            session.pause()
            self.assertEqual(session.state, "paused")
            session.stop()
            self.assertEqual(session.state, "stopped")
            with self.assertRaises(StopIteration):
                next(session)
            session.pause()
            session.resume()
            self.assertEqual(session.state, "stopped")
            self.assertEqual(list(session), [])
            self.assertEqual(fake_time.waits, [])
            path.unlink()
            self.assertFalse(path.exists())

    def test_replay_stop_during_pending_interval_does_not_yield_pending(self):
        samples = [Sample(source_ts=2), Sample(source_ts=1)]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = self.write_recording(directory, samples)
            fake_time = FakeReplayTime()
            session = self.make_replay_session(path, fake_time)
            self.assertEqual(next(session), samples[0])
            def stop_during_wait(timeout):
                self.assertEqual(timeout, 1)
                fake_time.now += 0.25
                session.stop()
                return True
            fake_time.on_wait = stop_during_wait
            with self.assertRaises(StopIteration):
                next(session)
            self.assertEqual(session.state, "stopped")
            self.assertEqual(fake_time.waits, [1])
            self.assertEqual(fake_time.now, 0.25)
            self.assertEqual(list(session), [])

    def test_replay_stop_while_paused_is_terminal(self):
        samples = [Sample(source_ts=index) for index in range(3)]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = self.write_recording(directory, samples)
            fake_time = FakeReplayTime()
            session = self.make_replay_session(path, fake_time)
            self.assertEqual(next(session), samples[0])
            session.pause()
            self.assertEqual(session.state, "paused")
            def stop_while_paused(timeout):
                self.assertIsNone(timeout)
                session.stop()
                return True
            fake_time.on_wait = stop_while_paused
            with self.assertRaises(StopIteration):
                next(session)
            self.assertEqual(session.state, "stopped")
            session.pause()
            session.resume()
            session.stop()
            self.assertEqual(session.state, "stopped")
            self.assertEqual(list(session), [])

    def test_replay_stop_after_exhaustion_is_no_op(self):
        samples = [Sample(source_ts=8, fuel=9, valid=True)]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = self.write_recording(directory, samples)
            session = self.make_replay_session(path, FakeReplayTime())
            self.assertEqual(list(session), samples)
            self.assertEqual(session.state, "exhausted")
            session.stop()
            self.assertEqual(session.state, "exhausted")
            with self.assertRaises(StopIteration):
                next(session)
            self.assertEqual(session.state, "exhausted")

    def test_recorded_rules_on_stopped_prefix_match_unpaused_prefix(self):
        samples = [
            Sample(source_ts=5, fuel=11, valid=True),
            Sample(source_ts=3, fuel=9, valid=True),
            Sample(source_ts=4, fuel=8, valid=True),
            Sample(source_ts=1, fuel=13, valid=True),
        ]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = self.write_recording(directory, samples)
            expected_engine = RulesEngine()
            expected = []
            for sample in samples[:2]:
                alert = expected_engine.process(sample)
                if alert is not None:
                    expected.append(alert.encode())

            fake_time = FakeReplayTime()
            session = self.make_replay_session(path, fake_time)
            paused_engine = RulesEngine()
            actual = []
            self.assertEqual(next(session), samples[0])
            session.pause()
            def stop_after_second(timeout):
                self.assertIsNone(timeout)
                fake_time.now += 50
                session.resume()
                return True
            fake_time.on_wait = stop_after_second
            self.assertEqual(next(session), samples[1])
            session.stop()
            with self.assertRaises(StopIteration):
                next(session)
            for sample in samples[:2]:
                alert = paused_engine.process(sample)
                if alert is not None:
                    actual.append(alert.encode())
            self.assertEqual(actual, expected)
            self.assertEqual(session.state, "stopped")

    def test_demo_has_no_pause_resume_or_stop_cli_flags(self):
        help_output = io.StringIO()
        with contextlib.redirect_stdout(help_output):
            with self.assertRaises(SystemExit) as raised:
                main(["--help"])
        self.assertEqual(raised.exception.code, 0)
        help_text = help_output.getvalue()
        for flag in ("--pause", "--resume", "--stop"):
            self.assertNotIn(flag, help_text)
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as rejected:
                    main(["--source", "synthetic", flag])
            self.assertNotEqual(rejected.exception.code, 0)
            self.assertRegex(stderr.getvalue(), rf"unrecognized arguments: {flag}")

    def test_replay_session_exposes_programmatic_pause_resume_and_stop(self):
        self.assertTrue(callable(getattr(ReplaySession, "pause")))
        self.assertTrue(callable(getattr(ReplaySession, "resume")))
        self.assertTrue(callable(getattr(ReplaySession, "stop")))

    def test_demo_file_replay_stays_on_paced_replay_not_session(self):
        source = inspect.getsource(demo)
        self.assertNotIn("ReplaySession", source)
        self.assertIn("from .sources import paced, replay, synthetic, validate_rate", source)
        self.assertIn("paced(samples, args.rate)", source)
        self.assertIn("replay(args.path)", source)

    def test_docs_state_replay_pause_resume_and_stop_are_programmatic_only(self):
        root = Path(__file__).resolve().parents[1]
        for relative in (
            "docs/DATA_RECOVERY.md",
            "ARCHITECTURE.md",
            "ROADMAP.md",
            "PROJECT_CONTEXT.md",
        ):
            collapsed = " ".join((root / relative).read_text(encoding="utf-8").split())
            self.assertIn("ReplaySession.pause", collapsed)
            self.assertIn("ReplaySession.resume", collapsed)
            self.assertIn("ReplaySession.stop", collapsed)
            self.assertIn("src/raceengineer/sources.py", collapsed)
            self.assertIn("no `--pause`, `--resume`, or `--stop`", collapsed)
            self.assertIn("Ctrl+C", collapsed)
            self.assertIn("process stop", collapsed)
        readme = (root / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("ReplaySession", readme)
        self.assertNotIn("--pause", readme)
        self.assertNotIn("--resume", readme)
        self.assertNotIn("--stop", readme)

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
