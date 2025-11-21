"""Subprocess entry-point that streams noise as WAV PCM data."""

from __future__ import annotations

import argparse
import json
import logging
import signal
import sys
from typing import Any

from .const import PROFILE_TYPES, SAMPLE_RATE, STREAM_CHUNK_DURATION
from .noise import create_generator, build_wav_header

_STOP_REQUESTED = False
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
_LOGGER = logging.getLogger(__name__)


def _handle_signal(_: int, __) -> None:
    global _STOP_REQUESTED
    _STOP_REQUESTED = True


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Noise generator streaming process")
    parser.add_argument("--mode", required=True, choices=PROFILE_TYPES)
    parser.add_argument("--subtype", required=True)
    parser.add_argument("--volume", type=float, default=0.5)
    parser.add_argument("--seed", default=None)
    parser.add_argument("--sample-rate", type=int, default=SAMPLE_RATE)
    parser.add_argument("--chunk-duration", type=float, default=STREAM_CHUNK_DURATION)
    parser.add_argument("--parameters", default="{}")
    return parser.parse_args(argv)


def _coerce_seed(seed: Any | None) -> Any | None:
    if seed in (None, "", "None"):
        return None
    try:
        return int(seed)
    except (TypeError, ValueError):
        return seed


def run(argv: list[str]) -> int:
    args = _parse_args(argv)

    chunk_samples = max(1, int(args.sample_rate * max(args.chunk_duration, 0.05)))
    try:
        parameters = json.loads(args.parameters)
    except json.JSONDecodeError:
        parameters = {}
    _LOGGER.info(
        "Starting noise_process mode=%s subtype=%s volume=%s params=%s",
        args.mode,
        args.subtype,
        args.volume,
        parameters,
    )
    generator = create_generator(
        args.mode,
        args.subtype,
        args.volume,
        _coerce_seed(args.seed),
        parameters,
    )

    buffer = sys.stdout.buffer
    try:
        buffer.write(build_wav_header(args.sample_rate))
        buffer.flush()

        while not _STOP_REQUESTED:
            buffer.write(generator.next_chunk(chunk_samples))
            buffer.flush()
    except BrokenPipeError:
        return 0

    _LOGGER.info("Exiting noise_process mode=%s subtype=%s", args.mode, args.subtype)
    return 0


def main() -> None:
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)
    sys.exit(run(sys.argv[1:]))


if __name__ == "__main__":  # pragma: no cover - executed as a module
    main()
