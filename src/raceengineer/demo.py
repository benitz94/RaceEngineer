"""Text recovery demo: normalized recordings or UDP metadata."""

import argparse
from dataclasses import asdict
import json
import sys
from .llm.briefing import LLM_DOWN_WARNING, speak
from .recording import encode
from .rules import FUEL_LOW_THRESHOLD, RulesEngine
from .sources import paced, replay, synthetic, validate_rate
from .udp_probe import probe


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
    parser.add_argument("--fuel-low-threshold", type=float, default=FUEL_LOW_THRESHOLD)
    parser.add_argument("--brief", action="store_true", help="optional spoken briefing after the session")
    parser.add_argument("--lang", choices=("en", "it"), default="en", help="briefing language")
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
    if args.source == "udp" and (args.alerts_only or args.samples_only):
        parser.error("sample and alert output flags are not supported for UDP metadata")
    if args.source == "udp" and args.brief:
        parser.error("--brief is not supported for UDP metadata")
    if args.brief and args.samples_only:
        parser.error("--brief cannot be combined with --samples-only")
    try:
        validate_rate(args.rate)
        if args.source == "udp":
            for info in probe(args.port, args.host, args.count):
                print(json.dumps(info.to_dict(), sort_keys=True), flush=True)
        else:
            engine = RulesEngine(args.fuel_low_threshold)
            samples = synthetic(20 if args.count is None else args.count, args.rate) if args.source == "synthetic" else replay(args.path)
            sample_dicts = []
            alert_dicts = []
            for sample in paced(samples, args.rate):
                if args.brief:
                    sample_dicts.append(sample.to_dict())
                if not args.alerts_only:
                    print(encode(sample), flush=True)
                alert = engine.process(sample)
                if alert is not None:
                    if args.brief:
                        alert_dicts.append(asdict(alert))
                    if not args.samples_only:
                        print(alert.encode(), flush=True)
            if args.brief:
                briefing = speak(sample_dicts, alert_dicts, lang=args.lang)
                if briefing:
                    print(briefing, flush=True)
                else:
                    print(LLM_DOWN_WARNING, file=sys.stderr)
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
