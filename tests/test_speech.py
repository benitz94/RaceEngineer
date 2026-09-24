import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from raceengineer.speech import PIPER_NOTICE, find_italian_model, speak
import raceengineer.speech as speech


class SpeechTests(unittest.TestCase):
    def test_missing_piper_uses_sapi_once(self):
        speech._NOTICE_SENT = False
        error = io.StringIO()
        with patch("raceengineer.speech.find_piper", return_value=None), \
             patch("raceengineer.speech.subprocess.run") as run, \
             patch("sys.stderr", error):
            run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
            speak("Box, box. Questo giro.")
            speak("Box, box. Questo giro.")
        self.assertEqual(error.getvalue().splitlines(), [PIPER_NOTICE])
        self.assertEqual(run.call_count, 2)
        for call in run.call_args_list:
            self.assertEqual(call.args[0][0], "powershell.exe")
            self.assertIn("System.Speech", call.args[0][-1])

    def test_piper_writes_a_wav_and_does_not_use_sapi(self):
        played = []

        def fake_run(args, **kwargs):
            if args[0] == "powershell.exe":
                raise AssertionError(args[-1])
            output = Path(args[args.index("--output_file") + 1])
            output.write_bytes(b"RIFF")
            self.assertEqual(kwargs["input"], b"Box, box. Questo giro.")
            self.assertIn("it_IT-paola-medium.onnx", " ".join(args))
            self.assertNotIn("http", " ".join(args))
            return subprocess.CompletedProcess(args, 0, b"", b"")

        with patch("raceengineer.speech.find_piper", return_value=Path("piper.exe")), \
             patch("raceengineer.speech.find_italian_model", return_value=Path("it_IT-paola-medium.onnx")), \
             patch("raceengineer.speech.subprocess.run", side_effect=fake_run), \
             patch("raceengineer.speech._play_wav", side_effect=played.append):
            speak("Box, box. Questo giro.")
        self.assertEqual(len(played), 1)
        self.assertTrue(str(played[0]).endswith(".wav"))
        self.assertFalse(played[0].exists())

    def test_finder_prefers_paola_and_skips_english(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("en_US-lessac-medium.onnx", "it_IT-riccardo-x_low.onnx", "it_IT-paola-medium.onnx"):
                (root / name).write_bytes(b"x")
                (root / f"{name}.json").write_text("{}", encoding="utf-8")
            with patch("raceengineer.speech._search_roots", return_value=[root]), \
                 patch("raceengineer.speech.find_piper", return_value=None):
                chosen = find_italian_model()
        self.assertEqual(chosen.name, "it_IT-paola-medium.onnx")


if __name__ == "__main__":
    unittest.main()
