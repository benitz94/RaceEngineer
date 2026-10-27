"""Text recovery demo: normalized recordings or UDP metadata, with an optional engineer radio."""

import argparse
import json
import sys
from .briefing import MODEL, OLLAMA_URL, BriefRejected, BriefingUnavailable, _accept_radio_text, brief_alert, chat_url
from .decision import URGENCY_SECONDS, answer
from .recording import encode
from .rules import FUEL_LOW_THRESHOLD, Radio, RulesEngine
from .sources import paced, replay, synthetic, validate_rate
from .speech import speak
from .udp_probe import probe


def _speak_printed(text: str, voice: str) -> bool:
    """Speak one printed radio line. Return True when speech fails."""
    try:
        speak(text, voice)
    except RuntimeError as error:
        print(f"error: speech failed: {error}", file=sys.stderr)
        return True
    return False


def _engineer_line(alert, args) -> str | None:
    """The engineer's own words for an alert, or None when the radio stays silent.

    There is no canned fallback. A silent engineer is a defect to fix, so the
    reason goes to stderr and the run exits nonzero.
    """
    urgency = answer("urgency", {"priority": alert.priority})
    try:
        candidate = brief_alert(
            alert, timeout=URGENCY_SECONDS[urgency], base_url=args.ollama_url, model=args.engineer_model,
        )
        if answer("grounded_or_reject", {"text": candidate, "fuel": alert.fuel}) == "reject":
            raise BriefRejected()
        return _accept_radio_text(candidate)
    except BriefRejected:
        print("error: engineer silent: line rejected", file=sys.stderr)
    except BriefingUnavailable as error:
        print(f"error: engineer silent: {error}", file=sys.stderr)
    return None


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
    parser.add_argument("--speak", action="store_true", help="speak radio lines with local Piper Italian, or Windows SAPI / Linux espeak-ng")
    parser.add_argument("--voice", choices=("paola", "riccardo", "serena", "dii"), default="serena", help="Piper Italian voice")
    parser.add_argument("--engineer", action="store_true", help="let the local language model speak each alert on the radio")
    parser.add_argument("--ollama-url", default=OLLAMA_URL, help="Ollama base URL for --engineer")
    parser.add_argument("--engineer-model", default=MODEL, help="Ollama model for --engineer")
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
    try:
        chat_url(args.ollama_url)
    except ValueError as error:
        parser.error(str(error))
    if not args.engineer_model.strip():
        parser.error("--engineer-model must not be empty")
    if (args.radio_only or args.speak) and not args.engineer:
        parser.error("--radio-only and --speak need --engineer: every radio line comes from the engineer")
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
            failed = False
            for sample in paced(samples, args.rate):
                if not args.alerts_only and not args.radio_only:
                    print(encode(sample), flush=True)
                alert = engine.process(sample)
                if alert is None or args.samples_only:
                    continue
                if not args.radio_only:
                    print(alert.encode(), flush=True)
                if args.alerts_only or not args.engineer:
                    continue
                text = _engineer_line(alert, args)
                if text is None:
                    failed = True
                    continue
                radio = Radio("llm", alert.type, text, alert.timestamp)
                print(radio.encode(), flush=True)
                if args.speak and _speak_printed(radio.text, args.voice):
                    failed = True
            if failed:
                return 1
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
