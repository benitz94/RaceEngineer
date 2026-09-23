"""Text recovery demo: normalized recordings or UDP metadata."""

import argparse
import json
import sys
from .recording import encode
from .replay import ReplayController, validate_speed
from .rules import FUEL_LOW_THRESHOLD, RulesEngine
from .sources import paced, replay, synthetic, validate_rate
from .udp_probe import probe


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("synthetic", "file", "udp"), required=True)
    parser.add_argument("path", nargs="?")
    parser.add_argument("--rate", type=float, default=None, help="synthetic samples per second")
    parser.add_argument("--replay-speed", type=float, default=1.0,
                        help="recorded playback multiplier; does not rewrite source timestamps")
    parser.add_argument("--count", type=int, help="synthetic samples or UDP datagrams")
    parser.add_argument("--port", type=int, default=33740)
    parser.add_argument("--host", default="0.0.0.0", help="UDP bind address")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--alerts-only", action="store_true", help="suppress sample output")
    output.add_argument("--samples-only", action="store_true", help="print replayable sample recordings only")
    parser.add_argument("--fuel-low-threshold", type=float, default=FUEL_LOW_THRESHOLD)
    args = parser.parse_args(argv)
    if args.source == "file" and not args.path:
        parser.error("file source requires a path")
    if args.source != "file" and args.path:
        parser.error("path is only supported for file source")
    if args.source == "file" and args.count is not None:
        parser.error("--count is only supported for synthetic or udp")
    if args.source != "synthetic" and args.rate is not None:
        parser.error("--rate is only supported for synthetic source")
    if args.source != "file" and args.replay_speed != 1.0:
        parser.error("--replay-speed is only supported for file source")
    if args.count is not None and args.count < 0:
        parser.error("--count must be nonnegative")
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    if args.source == "udp" and (args.alerts_only or args.samples_only):
        parser.error("sample and alert output flags are not supported for UDP metadata")
    rate = 10.0 if args.rate is None else args.rate
    try:
        validate_rate(rate)
        validate_speed(args.replay_speed)
        if args.source == "udp":
            for info in probe(args.port, args.host, args.count):
                print(json.dumps(info.to_dict(), sort_keys=True), flush=True)
        else:
            engine = RulesEngine(args.fuel_low_threshold)
            if args.source == "synthetic":
                stream = paced(synthetic(20 if args.count is None else args.count, rate), rate)
            else:
                stream = ReplayController(replay(args.path), speed=args.replay_speed)
            for sample in stream:
                if not args.alerts_only:
                    print(encode(sample), flush=True)
                alert = engine.process(sample)
                if alert is not None and not args.samples_only:
                    print(alert.encode(), flush=True)
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
