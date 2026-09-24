"""Local Italian speech: Piper when a voice is installed, otherwise Windows SAPI."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

PIPER_NOTICE = "piper unavailable, using SAPI"
_NOTICE_SENT = False

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


def find_italian_model(voice: str = "paola") -> Path | None:
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


def _run_powershell(script: str, env: dict) -> None:
    try:
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("timed out") from None
    except OSError as error:
        raise RuntimeError(f"could not run powershell.exe: {error}") from error
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "Windows speech failed").strip()
        raise RuntimeError(detail)


def _speak_sapi(text: str) -> None:
    env = os.environ.copy()
    env["RACEENGINEER_RADIO_TEXT"] = text
    _run_powershell(_SAPI_SCRIPT, env)


def _play_wav(path: Path) -> None:
    env = os.environ.copy()
    env["RACEENGINEER_WAV"] = str(path)
    _run_powershell(_PLAY_SCRIPT, env)


def _try_piper(text: str, voice: str) -> bool:
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
        _play_wav(wav)
    finally:
        try:
            wav.unlink()
        except OSError:
            pass
    return True


def speak(text: str, voice: str = "paola") -> None:
    """Speak one radio line with the selected Piper voice, or Windows SAPI when it is missing."""
    global _NOTICE_SENT
    if _try_piper(text, voice):
        return
    if not _NOTICE_SENT:
        print(PIPER_NOTICE, file=sys.stderr)
        _NOTICE_SENT = True
    _speak_sapi(text)
