"""Version 1 JSONL sample persistence, independent of source timing."""

import json
from .model import Sample

FORMAT = "raceengineer.sample"
VERSION = 1


def encode(sample: Sample) -> str:
    return json.dumps(
        {"format": FORMAT, "version": VERSION, "sample": sample.to_dict()},
        sort_keys=True, separators=(",", ":"), allow_nan=False,
    )


def read_samples(path):
    with open(path, encoding="utf-8-sig") as recording:
        for number, line in enumerate(recording, 1):
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("record must be an object")
                if record.get("format") != FORMAT or type(record.get("version")) is not int or record["version"] != VERSION:
                    raise ValueError("unsupported recording format or version")
                if not isinstance(record.get("sample"), dict):
                    raise ValueError("sample must be an object")
                yield Sample(**record["sample"])
            except (ValueError, TypeError) as error:
                raise ValueError(f"{path}: line {number}: {error}") from error
