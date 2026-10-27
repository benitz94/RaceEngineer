import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from raceengineer.demo import main
from raceengineer.speech import ESPEAK_NOTICE, PIPER_NOTICE, find_italian_model, find_piper, speak
import raceengineer.speech as speech


class SpeechTests(unittest.TestCase):
    def test_missing_piper_uses_sapi_once(self):
        speech._NOTICE_SENT = False
        error = io.StringIO()
        with patch("raceengineer.speech._on_windows", return_value=True), \
             patch("raceengineer.speech.find_piper", return_value=None), \
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

    def test_missing_piper_uses_espeak_on_linux(self):
        speech._NOTICE_SENT = False
        error = io.StringIO()
        with patch("raceengineer.speech._on_windows", return_value=False), \
             patch("raceengineer.speech.find_piper", return_value=None), \
             patch("raceengineer.speech.shutil.which", return_value="/usr/bin/espeak-ng"), \
             patch("raceengineer.speech.subprocess.run") as run, \
             patch("sys.stderr", error):
            run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=b"", stderr=b"")
            speak("Box, box. Questo giro.")
        self.assertEqual(error.getvalue().splitlines(), [ESPEAK_NOTICE])
        self.assertEqual(run.call_args.args[0], ["/usr/bin/espeak-ng", "-v", "it", "--stdin"])
        self.assertEqual(run.call_args.kwargs["input"], "Box, box. Questo giro.".encode("utf-8"))

    def test_missing_espeak_is_a_speech_error(self):
        speech._NOTICE_SENT = True
        with patch("raceengineer.speech._on_windows", return_value=False), \
             patch("raceengineer.speech.find_piper", return_value=None), \
             patch("raceengineer.speech.shutil.which", return_value=None), \
             patch("raceengineer.speech.subprocess.run") as run, \
             self.assertRaises(RuntimeError):
            speak("Box, box. Questo giro.")
        run.assert_not_called()

    def test_linux_playback_prefers_pipewire(self):
        installed = {"pw-play": "/usr/bin/pw-play", "aplay": "/usr/bin/aplay"}
        with patch("raceengineer.speech._on_windows", return_value=False), \
             patch("raceengineer.speech.shutil.which", side_effect=installed.get), \
             patch("raceengineer.speech.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=b"", stderr=b"")
            speech._play_wav(Path("radio.wav"))
        self.assertEqual(run.call_args.args[0], ["/usr/bin/pw-play", "radio.wav"])

    def test_linux_playback_falls_back_to_aplay(self):
        with patch("raceengineer.speech._on_windows", return_value=False), \
             patch("raceengineer.speech.shutil.which", side_effect={"aplay": "/usr/bin/aplay"}.get), \
             patch("raceengineer.speech.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=b"", stderr=b"")
            speech._play_wav(Path("radio.wav"))
        self.assertEqual(run.call_args.args[0], ["/usr/bin/aplay", "-q", "radio.wav"])

    def test_linux_playback_without_player_fails(self):
        with patch("raceengineer.speech._on_windows", return_value=False), \
             patch("raceengineer.speech.shutil.which", return_value=None), \
             patch("raceengineer.speech.subprocess.run") as run, \
             self.assertRaises(RuntimeError):
            speech._play_wav(Path("radio.wav"))
        run.assert_not_called()

    @unittest.skipIf(os.name == "nt", "POSIX executable bit")
    def test_finder_accepts_linux_piper_binary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "piper" / "piper"
            binary.parent.mkdir()
            binary.write_bytes(b"x")
            binary.chmod(0o755)
            with patch("raceengineer.speech._search_roots", return_value=[root]), \
                 patch("raceengineer.speech.shutil.which", return_value=None):
                found = find_piper()
        self.assertEqual(found, binary)

    def test_piper_writes_a_wav_and_does_not_use_sapi(self):
        played = []

        def fake_run(args, **kwargs):
            if args[0] == "powershell.exe":
                raise AssertionError(args[-1])
            output = Path(args[args.index("--output_file") + 1])
            output.write_bytes(b"RIFF")
            self.assertEqual(kwargs["input"], b"Box, box. Questo giro.")
            self.assertIn("it_IT-riccardo-x_low.onnx", " ".join(args))
            self.assertNotIn("http", " ".join(args))
            return subprocess.CompletedProcess(args, 0, b"", b"")

        with patch("raceengineer.speech.find_piper", return_value=Path("piper.exe")), \
             patch("raceengineer.speech.find_italian_model", return_value=Path("it_IT-riccardo-x_low.onnx")) as model, \
             patch("raceengineer.speech.subprocess.run", side_effect=fake_run), \
             patch("raceengineer.speech._play_wav", side_effect=played.append):
            speak("Box, box. Questo giro.", "riccardo")
        model.assert_called_once_with("riccardo")
        self.assertEqual(len(played), 1)
        self.assertTrue(str(played[0]).endswith(".wav"))
        self.assertFalse(played[0].exists())

    def test_finder_prefers_paola_and_skips_english(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in (
                "en_US-lessac-medium.onnx",
                "it_IT-riccardo-x_low.onnx",
                "it_IT-paola-medium.onnx",
                "it_IT-serena-medium.onnx",
                "it_IT-serena-high.onnx",
                "it_IT-dii-high.onnx",
            ):
                (root / name).write_bytes(b"x")
                (root / f"{name}.json").write_text("{}", encoding="utf-8")
            with patch("raceengineer.speech._search_roots", return_value=[root]), \
                 patch("raceengineer.speech.find_piper", return_value=None):
                chosen = find_italian_model()
                paola = find_italian_model("paola")
                riccardo = find_italian_model("riccardo")
                serena = find_italian_model("serena")
                dii = find_italian_model("dii")
        self.assertEqual(chosen.name, "it_IT-serena-high.onnx")
        self.assertEqual(paola.name, "it_IT-paola-medium.onnx")
        self.assertEqual(riccardo.name, "it_IT-riccardo-x_low.onnx")
        self.assertEqual(serena.name, "it_IT-serena-high.onnx")
        self.assertEqual(dii.name, "it_IT-dii-high.onnx")

    def test_unknown_voice_exits_without_speech(self):
        error = io.StringIO()
        with patch("raceengineer.demo.speak") as spoken, \
             patch("sys.stderr", error), \
             self.assertRaises(SystemExit) as raised:
            main(["--source", "synthetic", "--count", "0", "--speak", "--voice", "mario"])
        self.assertEqual(raised.exception.code, 2)
        spoken.assert_not_called()


if __name__ == "__main__":
    unittest.main()
