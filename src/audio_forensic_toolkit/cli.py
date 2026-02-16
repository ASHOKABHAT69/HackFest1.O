from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from audio_forensic_toolkit.analyzer import analyze_hybrid


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Hybrid audio forensic analysis for digital integrity and biological signature checks."
    )
    parser.add_argument("audio_file", help="Path to 16-bit PCM WAV file")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )

    args = parser.parse_args()
    report = analyze_hybrid(args.audio_file)
    payload = asdict(report)

    if args.pretty:
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(payload))


if __name__ == "__main__":
    main()
