"""Text recovery demo: normalized recordings or UDP metadata."""

import argparse
import json
import os
import subprocess
import sys
from .briefing import BriefRejected, BriefingUnavailable, brief_alert
from .recording import encode
from .rules import FUEL_LOW_THRESHOLD, Radio, RulesEngine, rule_radio
from .sources import paced, replay, synthetic, validate_rate
from .udp_probe import probe

_SPEAK_SCRIPT = r"""
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


def speak(text: str) -> None:
    """Speak one radio line with Windows SAPI. Raises RuntimeError on failure."""
    env = os.environ.copy()
    env["RACEENGINEER_RADIO_TEXT"] = text
    try:
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", _SPEAK_SCRIPT],
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("synthetic", "file", "udp"), required=True)
    parser.add_argument("path", nargs="?")
    parser.add_argument("--rate", type=float, default=10.0, help="samples per second")
    parser.add_argument("--count", type=int, help="synthetic samples or UDP datagrams")
    parser.add_argument("--port", type=int, default=33740)
    parser.add_argument("--host", default="0.0.0.0", help="UDP bind address")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--alerts-only", action="store_true", help="suppress sample output")
    output.add_argument("--samples-only", action="store_true", help="print replayable sample recordings only")
    output.add_argument("--radio-only", action="store_true", help="print radio lines only")
    parser.add_argument("--speak", action="store_true", help="speak radio lines with local Windows speech")
    parser.add_argument("--brief", action="store_true", help="ask local Ollama for a briefing after a rule radio line")
    parser.add_argument("--fuel-low-threshold", type=float, default=FUEL_LOW_THRESHOLD)
    args = parser.parse_args(argv)
    if args.source == "file" and not args.path:
        parser.error("file source requires a path")
    if args.source != "file" and args.path:
        parser.error("path is only supported for file source")
    if args.source == "file" and args.count is not None:
        parser.error("--count is only supported for synthetic or udp")
    if args.count is not None and args.count < 0:
        parser.error("--count must be nonnegative")
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    if args.source == "udp" and (args.alerts_only or args.samples_only or args.radio_only):
        parser.error("sample, alert, and radio output flags are not supported for UDP metadata")
    try:
        validate_rate(args.rate)
        if args.source == "udp":
            for info in probe(args.port, args.host, args.count):
                print(json.dumps(info.to_dict(), sort_keys=True), flush=True)
        else:
            engine = RulesEngine(args.fuel_low_threshold)
            samples = synthetic(20 if args.count is None else args.count, args.rate) if args.source == "synthetic" else replay(args.path)
            speech_failed = False
            for sample in paced(samples, args.rate):
                if not args.alerts_only and not args.radio_only:
                    print(encode(sample), flush=True)
                alert = engine.process(sample)
                if alert is None or args.samples_only:
                    continue
                if not args.radio_only:
                    print(alert.encode(), flush=True)
                if args.alerts_only:
                    continue
                radio = rule_radio(alert)
                print(radio.encode(), flush=True)
                if args.speak:
                    try:
                        speak(radio.text)
                    except RuntimeError as error:
                        speech_failed = True
                        print(f"error: speech failed: {error}", file=sys.stderr)
                if args.brief and alert.type == "fuel_low":
                    try:
                        sentence = brief_alert(alert)
                    except BriefRejected:
                        print("error: brief rejected", file=sys.stderr)
                    except BriefingUnavailable as error:
                        print(f"error: briefing unavailable: {error}", file=sys.stderr)
                    else:
                        print(Radio("llm", radio.type, sentence, radio.timestamp).encode(), flush=True)
            if speech_failed:
                return 1
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
