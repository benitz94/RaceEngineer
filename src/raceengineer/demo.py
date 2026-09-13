"""Text recovery demo: normalized recordings or UDP metadata."""

import argparse
import json
import sys
from .recording import encode
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
        validate_rate(args.rate)
        if args.source == "udp":
            for info in probe(args.port, args.host, args.count):
                print(json.dumps(info.to_dict(), sort_keys=True), flush=True)
        else:
            samples = synthetic(20 if args.count is None else args.count, args.rate) if args.source == "synthetic" else replay(args.path)
            for sample in paced(samples, args.rate):
                print(encode(sample), flush=True)
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
