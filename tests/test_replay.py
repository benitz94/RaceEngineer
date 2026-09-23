import tempfile
import unittest
from pathlib import Path

from raceengineer.clock import VirtualClock
from raceengineer.model import Sample
from raceengineer.recording import encode, read_samples
from raceengineer.replay import ReplayController, ReplayState, validate_speed
from raceengineer.rules import RulesEngine


def recording(*timestamps, fuel=None):
    samples = []
    for index, ts in enumerate(timestamps):
        value = 15.0 if fuel is None else fuel[index]
        samples.append(Sample(source_ts=ts, recv_ts=ts, fuel=value, valid=True, source_id="rec"))
    return samples


class ReplayControllerTests(unittest.TestCase):
    def test_reaches_eof_preserves_order_and_source_timestamps(self):
        samples = recording(0.0, 2.0, 2.0, 5.0)
        clock = VirtualClock()
        controller = ReplayController(samples, clock=clock)
        emitted = list(controller)
        self.assertEqual(emitted, samples)
        self.assertEqual([s.source_ts for s in emitted], [0.0, 2.0, 2.0, 5.0])
        self.assertEqual(controller.state, ReplayState.FINISHED)
        self.assertIsNone(controller.step())

    def test_speed_scales_wait_not_timestamps(self):
        samples = recording(0.0, 2.0, 4.0)
        for speed, expected_elapsed in ((1.0, 4.0), (2.0, 2.0), (10.0, 0.4)):
            clock = VirtualClock()
            controller = ReplayController(samples, speed=speed, clock=clock)
            emitted = list(controller)
            self.assertEqual([s.source_ts for s in emitted], [0.0, 2.0, 4.0])
            self.assertAlmostEqual(clock.now(), expected_elapsed)

    def test_speed_change_during_replay(self):
        samples = recording(0.0, 2.0, 4.0)
        clock = VirtualClock()
        controller = ReplayController(samples, speed=1.0, clock=clock)
        controller.start()
        self.assertEqual(controller.step().source_ts, 0.0)
        self.assertEqual(controller.step().source_ts, 2.0)
        self.assertAlmostEqual(clock.now(), 2.0)
        controller.set_speed(2.0)
        self.assertEqual(controller.step().source_ts, 4.0)
        self.assertAlmostEqual(clock.now(), 3.0)

    def test_invalid_speed_rejected(self):
        for speed in (0, -1, float("nan"), float("inf"), -float("inf")):
            with self.assertRaises(ValueError):
                validate_speed(speed)
            with self.assertRaises(ValueError):
                ReplayController([], speed=speed)

    def test_pause_resume_does_not_skip_or_duplicate(self):
        samples = recording(0.0, 1.0, 2.0)
        clock = VirtualClock()
        controller = ReplayController(samples, clock=clock)
        controller.start()
        self.assertEqual(controller.step().source_ts, 0.0)
        controller.pause()
        self.assertEqual(controller.state, ReplayState.PAUSED)
        self.assertIsNone(controller.step())
        self.assertAlmostEqual(clock.now(), 0.0)
        controller.resume()
        self.assertEqual(controller.state, ReplayState.RUNNING)
        self.assertEqual(controller.step().source_ts, 1.0)
        self.assertEqual(controller.step().source_ts, 2.0)
        self.assertEqual([s.source_ts for s in samples], [0.0, 1.0, 2.0])

    def test_stop_is_idempotent_and_emits_nothing_after(self):
        samples = recording(0.0, 1.0, 2.0)
        controller = ReplayController(samples, clock=VirtualClock())
        controller.start()
        self.assertEqual(controller.step().source_ts, 0.0)
        controller.stop()
        self.assertEqual(controller.state, ReplayState.STOPPED)
        self.assertIsNone(controller.step())
        controller.stop()
        self.assertEqual(controller.state, ReplayState.STOPPED)
        self.assertIsNone(controller.step())

    def test_illegal_transitions_are_noops(self):
        controller = ReplayController(recording(0.0, 1.0), clock=VirtualClock())
        controller.pause()
        self.assertEqual(controller.state, ReplayState.STOPPED)
        controller.resume()
        self.assertEqual(controller.state, ReplayState.STOPPED)
        controller.start()
        controller.pause()
        controller.start()
        self.assertEqual(controller.state, ReplayState.PAUSED)
        controller.stop()
        controller.start()
        list(iter(lambda: controller.step(), None))
        self.assertEqual(controller.state, ReplayState.FINISHED)
        controller.resume()
        self.assertEqual(controller.state, ReplayState.FINISHED)
        controller.pause()
        self.assertEqual(controller.state, ReplayState.FINISHED)

    def test_empty_recording_finishes(self):
        controller = ReplayController([], clock=VirtualClock())
        controller.start()
        self.assertEqual(controller.state, ReplayState.FINISHED)
        self.assertIsNone(controller.step())

    def test_missing_timestamps_emit_immediately(self):
        samples = [Sample(fuel=11, valid=True), Sample(source_ts=3.0, fuel=10, valid=True)]
        clock = VirtualClock()
        controller = ReplayController(samples, clock=clock)
        self.assertEqual(list(controller), samples)
        self.assertEqual(clock.now(), 0.0)

    def test_backward_or_duplicate_timestamps_do_not_sleep(self):
        samples = recording(5.0, 3.0, 3.0)
        clock = VirtualClock()
        self.assertEqual(list(ReplayController(samples, clock=clock)), samples)
        self.assertEqual(clock.now(), 0.0)

    def test_event_sequence_identical_across_speeds(self):
        fuels = [15.0, 10.0, 9.0, 13.5, 9.0]
        samples = recording(0.0, 1.0, 2.0, 3.0, 4.0, fuel=fuels)
        sequences = []
        for speed in (1.0, 2.0, 10.0):
            engine = RulesEngine()
            controller = ReplayController(samples, speed=speed, clock=VirtualClock())
            events = []
            for sample in controller:
                alert = engine.process(sample)
                if alert is not None:
                    events.append((alert.type, alert.timestamp, alert.fuel))
            sequences.append(events)
        self.assertEqual(sequences[0], sequences[1])
        self.assertEqual(sequences[0], sequences[2])
        self.assertEqual(sequences[0], [("fuel_low", 1.0, 10.0), ("fuel_low", 4.0, 9.0)])

    def test_imperfect_recording_uses_existing_reader(self):
        samples = [
            Sample(source_ts=2, valid=False),
            Sample(source_ts=1),
            Sample(source_ts=1),
        ]
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "recording.jsonl"
            path.write_text("\n".join(map(encode, samples)) + "\n", encoding="utf-8")
            loaded = list(read_samples(path))
        self.assertEqual(loaded, samples)
        controller = ReplayController(loaded, clock=VirtualClock())
        self.assertEqual(list(controller), samples)


if __name__ == "__main__":
    unittest.main()
