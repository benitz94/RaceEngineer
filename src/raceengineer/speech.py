"""Local Italian speech: Piper when a voice is installed, otherwise the OS fallback.

Windows falls back to SAPI and plays WAV files through PowerShell. Linux falls
back to espeak-ng and plays WAV files through pw-play, paplay, or aplay.
Each line opens with a short radio beep, so the driver is never caught by
surprise.
"""

import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import wave

PIPER_NOTICE = "piper unavailable, using SAPI"
ESPEAK_NOTICE = "piper unavailable, using espeak-ng"
_NOTICE_SENT = False
# Original radio-open jingle: (frequency Hz, seconds, level); 0 Hz is a gap.
# Four short pure tones, C6 A5 D6 B5, soft first note. It ends on an
# unresolved note with no tail, so the driver waits for the engineer's voice.
_BEEP_TONES = (
    (0, 0.03, 0.0),
    (1046.50, 0.092, 0.30), (0, 0.012, 0.0),
    (880.00, 0.080, 1.00), (0, 0.016, 0.0),
    (1174.66, 0.082, 0.80), (0, 0.016, 0.0),
    (987.77, 0.082, 0.75),
    (0, 0.04, 0.0),
)
_BEEP_RATE = 44100

_SAPI_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$italian = @($synth.GetInstalledVoices() | Where-Object {
    $_.Enabled -and $_.VoiceInfo.Culture.TwoLetterISOLanguageName -eq 'it'
})
if ($italian.Count -gt 0) {
    $synth.SelectVoice($italian[0].VoiceInfo.Name)
}
$synth.Speak($env:RACEENGINEER_RADIO_TEXT)
"""

_PLAY_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$player = New-Object System.Media.SoundPlayer $env:RACEENGINEER_WAV
$player.PlaySync()
"""

# First installed player wins: PipeWire, then PulseAudio, then ALSA.
_POSIX_PLAYERS = (("pw-play",), ("paplay",), ("aplay", "-q"))


def _on_windows() -> bool:
    return os.name == "nt"


def cache_dir() -> Path:
    root = os.environ.get("LOCALAPPDATA")
    if root:
        return Path(root) / "RaceEngineer" / "piper"
    return Path.home() / ".cache" / "piper"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _search_roots() -> list[Path]:
    return [
        _repo_root() / "tools" / "piper",
        cache_dir(),
        _repo_root() / ".cache" / "piper",
    ]


def find_piper() -> Path | None:
    """piper on PATH, or a copy under tools/piper or the local cache.

    When several copies exist, the newest wins. High voices need a current
    Piper; the 2023 binary cannot phonemize them.
    """
    found = []
    for name in ("piper", "piper.exe"):
        located = shutil.which(name)
        if located:
            found.append(Path(located))
    for root in _search_roots():
        if root.is_dir():
            found.extend(root.rglob("piper.exe"))
            found.extend(path for path in root.rglob("piper") if os.access(path, os.X_OK))
    unique = []
    seen = set()
    for path in found:
        if not path.is_file():
            continue
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    if not unique:
        return None
    unique.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return unique[0]


def _config_for(model: Path) -> Path:
    return Path(str(model) + ".json")


def _voice_rank(model: Path, voice: str) -> int | None:
    name = model.name.lower()
    if "it_it" not in name or voice not in name:
        return None
    if not _config_for(model).is_file():
        return None
    if "high" in name:
        return 0
    if "medium" in name:
        return 1
    return 2


def find_italian_model(voice: str = "serena") -> Path | None:
    """Return the installed it_IT Piper model for the named voice. High ranks above medium."""
    found = []
    seen = set()
    roots = list(_search_roots())
    binary = find_piper()
    if binary is not None:
        roots.append(binary.resolve().parent)
    for root in roots:
        if not root.is_dir():
            continue
        for model in root.rglob("*.onnx"):
            key = str(model.resolve())
            if key in seen:
                continue
            seen.add(key)
            rank = _voice_rank(model, voice)
            if rank is not None:
                found.append((rank, model))
    if not found:
        return None
    found.sort(key=lambda item: (item[0], item[1].name))
    return found[0][1]


def _run(command: list[str], failure: str, **kwargs) -> None:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            timeout=30,
            **kwargs,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("timed out") from None
    except OSError as error:
        raise RuntimeError(f"could not run {Path(command[0]).name}: {error}") from error
    if completed.returncode != 0:
        detail = completed.stderr or completed.stdout or failure
        if isinstance(detail, bytes):
            detail = detail.decode("utf-8", errors="replace")
        raise RuntimeError(detail.strip() or failure)


def _run_powershell(script: str, env: dict) -> None:
    _run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        "Windows speech failed",
        env=env,
        text=True,
    )


def _speak_sapi(text: str) -> None:
    env = os.environ.copy()
    env["RACEENGINEER_RADIO_TEXT"] = text
    _run_powershell(_SAPI_SCRIPT, env)


def _speak_espeak(text: str) -> None:
    binary = shutil.which("espeak-ng")
    if binary is None:
        raise RuntimeError("espeak-ng not found")
    _run([binary, "-v", "it", "--stdin"], "espeak-ng failed", input=text.encode("utf-8"))


def _play_wav(path: Path) -> None:
    if _on_windows():
        env = os.environ.copy()
        env["RACEENGINEER_WAV"] = str(path)
        _run_powershell(_PLAY_SCRIPT, env)
        return
    for player in _POSIX_PLAYERS:
        binary = shutil.which(player[0])
        if binary is not None:
            _run([binary, *player[1:], str(path)], f"{player[0]} failed")
            return
    raise RuntimeError("no WAV player found (pw-play, paplay, or aplay)")


def write_beep(path: Path) -> None:
    """Write the radio-open jingle as a mono 16-bit WAV file."""
    attack = int(_BEEP_RATE * 0.004)
    release = int(_BEEP_RATE * 0.012)
    frames = bytearray()
    for frequency, seconds, level in _BEEP_TONES:
        count = int(_BEEP_RATE * seconds)
        for index in range(count):
            envelope = min(1.0, index / attack, (count - index) / release)
            phase = 2 * math.pi * frequency * index / _BEEP_RATE
            sample = 0.6 * level * envelope * (math.sin(phase) + 0.04 * math.sin(3 * phase)) / 1.04
            frames += struct.pack("<h", int(sample * 32767))
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(_BEEP_RATE)
        output.writeframes(bytes(frames))


def radio_beep() -> None:
    """Play the radio-open chirp before a line."""
    handle = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    handle.close()
    path = Path(handle.name)
    try:
        write_beep(path)
        _play_wav(path)
    finally:
        try:
            path.unlink()
        except OSError:
            pass


def _try_piper(text: str, voice: str, beep: bool = True) -> bool:
    """Synthesize with the selected Italian model. False when Piper or that model is missing."""
    binary = find_piper()
    model = find_italian_model(voice)
    if binary is None or model is None:
        return False
    handle = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    handle.close()
    wav = Path(handle.name)
    command = [str(binary), "--model", str(model), "--output_file", str(wav)]
    espeak = binary.resolve().parent / "espeak-ng-data"
    if espeak.is_dir():
        command.extend(["--espeak_data", str(espeak)])
    try:
        try:
            completed = subprocess.run(
                command,
                input=text.encode("utf-8"),
                capture_output=True,
                check=False,
                timeout=30,
                cwd=str(binary.resolve().parent),
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("timed out") from None
        except OSError as error:
            raise RuntimeError(f"could not run piper: {error}") from error
        if completed.returncode != 0 or not wav.is_file() or wav.stat().st_size == 0:
            detail = completed.stderr.decode("utf-8", errors="replace").strip() or "piper failed"
            raise RuntimeError(detail)
        if beep:
            radio_beep()
        _play_wav(wav)
    finally:
        try:
            wav.unlink()
        except OSError:
            pass
    return True


def speak(text: str, voice: str = "serena", beep: bool = True) -> None:
    """Speak one radio line with the selected Piper voice, or the OS fallback when it is missing.

    The radio beep plays right before the voice, after Piper has synthesized it.
    """
    global _NOTICE_SENT
    if _try_piper(text, voice, beep):
        return
    windows = _on_windows()
    if not _NOTICE_SENT:
        print(PIPER_NOTICE if windows else ESPEAK_NOTICE, file=sys.stderr)
        _NOTICE_SENT = True
    if beep:
        radio_beep()
    if windows:
        _speak_sapi(text)
    else:
        _speak_espeak(text)
