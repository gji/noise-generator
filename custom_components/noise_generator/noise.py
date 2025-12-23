"""Utilities for generating synthetic noise audio."""

from __future__ import annotations

import random
import struct
import math
from typing import Any

from .const import (
    COLOR_NOISE_SUBTYPES,
    CONF_CUSTOM_HIGH_CUTOFF,
    CONF_CUSTOM_LOW_CUTOFF,
    CONF_CUSTOM_SLOPE,
    CONF_PROFILE_PARAMETERS,
    CONF_PROFILE_SUBTYPE,
    CONF_PROFILE_TYPE,
    CONF_SEED,
    CONF_TONAL_ATTACK,
    CONF_TONAL_BASE_FREQUENCY,
    CONF_TONAL_DECAY,
    CONF_TONAL_PAUSE_DURATION,
    CONF_TONAL_PULSE_DURATION,
    CONF_TONAL_SECONDARY_RATIO,
    CONF_TONAL_WAVEFORM,
    CONF_VOLUME,
    CUSTOM_HIGH_CUTOFF_MAX,
    CUSTOM_LOW_CUTOFF_MIN,
    CUSTOM_SLOPE_MAX,
    CUSTOM_SLOPE_MIN,
    DEFAULT_CUSTOM_HIGH_CUTOFF,
    DEFAULT_CUSTOM_LOW_CUTOFF,
    DEFAULT_CUSTOM_SLOPE,
    DEFAULT_PROFILE_SUBTYPE,
    DEFAULT_PROFILE_TYPE,
    DEFAULT_TONAL_SUBTYPE,
    DEFAULT_VOLUME,
    PROFILE_TYPES,
    SAMPLE_RATE,
    TONAL_CUSTOM,
    TONAL_PRESET_PARAMETERS,
    TONAL_SUBTYPES,
    TONAL_WAVEFORMS,
    normalize_subtype,
)

class UnknownNoiseTypeError(ValueError):
    """Error raised when an unsupported noise type is requested."""


def _clamp(value: float, minimum: float, maximum: float) -> float:
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def _normalise(value: float) -> int:
    return int(_clamp(value, -1.0, 1.0) * 32767)


def _alpha_lowpass(cutoff_hz: float) -> float:
    if cutoff_hz <= 0:
        return 1.0
    rc = 1.0 / (2 * math.pi * cutoff_hz)
    dt = 1.0 / SAMPLE_RATE
    return dt / (rc + dt)


def _alpha_highpass(cutoff_hz: float) -> float:
    if cutoff_hz <= 0:
        return 0.0
    rc = 1.0 / (2 * math.pi * cutoff_hz)
    dt = 1.0 / SAMPLE_RATE
    return rc / (rc + dt)


class NoiseGenerator:
    """Generate PCM frames for a specific colored noise profile."""

    def __init__(
        self,
        noise_subtype: str,
        volume: float,
        seed: Any | None = None,
        *,
        custom_params: dict[str, Any] | None = None,
    ) -> None:
        if noise_subtype not in COLOR_NOISE_SUBTYPES:
            raise UnknownNoiseTypeError(noise_subtype)

        self.noise_type = noise_subtype
        self.volume = _clamp(float(volume), 0.0, 1.0)
        self._rng = random.Random(seed)
        self._brown_value = 0.0
        self._pink_state = [0.0] * 7
        self._custom_state: dict[str, float] | None = None
        if self.noise_type == "custom":
            params = custom_params or {}
            slope = _clamp(
                float(params.get(CONF_CUSTOM_SLOPE, DEFAULT_CUSTOM_SLOPE)),
                CUSTOM_SLOPE_MIN,
                CUSTOM_SLOPE_MAX,
            )
            low = _clamp(
                float(params.get(CONF_CUSTOM_LOW_CUTOFF, DEFAULT_CUSTOM_LOW_CUTOFF)),
                CUSTOM_LOW_CUTOFF_MIN,
                CUSTOM_HIGH_CUTOFF_MAX,
            )
            high = _clamp(
                float(params.get(CONF_CUSTOM_HIGH_CUTOFF, DEFAULT_CUSTOM_HIGH_CUTOFF)),
                low + 1.0,
                CUSTOM_HIGH_CUTOFF_MAX,
            )
            print(f"slope={slope}, low={low}, high={high}")
            if high <= low:
                high = min(max(low + 50.0, CUSTOM_LOW_CUTOFF_MIN + 1.0), CUSTOM_HIGH_CUTOFF_MAX)

            order = int(params.get("filter_order", 4))
            order = max(1, min(order, 8))  # practical cap

            self._custom_state = {
                "tilt": slope / max(abs(CUSTOM_SLOPE_MIN), CUSTOM_SLOPE_MAX),
                "order": order,

                "hp_alpha": _alpha_highpass(low),
                "lp_alpha": _alpha_lowpass(high),

                # HP state (arrays)
                "hp_prev": [0.0] * order,
                "hp_prev_input": [0.0] * order,

                # LP state (arrays)
                "lp_prev": [0.0] * order,

                # noise shaping
                "prev_white": 0.0,
                "brown": 0.0,
            }

            print(self._custom_state)

    def _next_sample(self) -> float:
        if self.noise_type == "white":
            return self._rng.uniform(-1.0, 1.0)
        if self.noise_type == "brown":
            self._brown_value += self._rng.uniform(-1.0, 1.0) * 0.02
            self._brown_value = _clamp(self._brown_value, -1.0, 1.0)
            # Apply slight damping so it does not drift indefinitely
            self._brown_value *= 0.98
            return self._brown_value
        if self.noise_type == "pink":
            white = self._rng.uniform(-1.0, 1.0)
            self._pink_state[0] = 0.99886 * self._pink_state[0] + white * 0.0555179
            self._pink_state[1] = 0.99332 * self._pink_state[1] + white * 0.0750759
            self._pink_state[2] = 0.96900 * self._pink_state[2] + white * 0.1538520
            self._pink_state[3] = 0.86650 * self._pink_state[3] + white * 0.3104856
            self._pink_state[4] = 0.55000 * self._pink_state[4] + white * 0.5329522
            self._pink_state[5] = -0.7616 * self._pink_state[5] - white * 0.0168980
            pink = (
                self._pink_state[0]
                + self._pink_state[1]
                + self._pink_state[2]
                + self._pink_state[3]
                + self._pink_state[4]
                + self._pink_state[5]
                + self._pink_state[6]
                + white * 0.5362
            )
            self._pink_state[6] = white * 0.115926
            return _clamp(pink * 0.11, -1.0, 1.0)

        if self.noise_type == "custom":
            return self._next_custom_sample()

        raise UnknownNoiseTypeError(self.noise_type)

    def _next_custom_sample(self) -> float:
        assert self._custom_state is not None
        s = self._custom_state

        # ---- base noise ----
        white = self._rng.uniform(-1.0, 1.0)

        brown = s["brown"] + white * 0.02
        brown = _clamp(brown, -1.0, 1.0)
        s["brown"] = brown * 0.98

        blue = _clamp(white - s["prev_white"], -1.0, 1.0)
        s["prev_white"] = white

        tilt = s["tilt"]
        if tilt >= 0:
            shaped = (1.0 - tilt) * white + tilt * blue
        else:
            shaped = (1.0 + tilt) * white - tilt * brown

        # ---- N-pole high-pass ----
        x = shaped
        a = s["hp_alpha"]

        for i in range(s["order"]):
            y = a * (s["hp_prev"][i] + x - s["hp_prev_input"][i])
            s["hp_prev"][i] = y
            s["hp_prev_input"][i] = x
            x = y

        hp = _clamp(x, -1.5, 1.5)

        # ---- N-pole low-pass ----
        x = hp
        a = s["lp_alpha"]

        for i in range(s["order"]):
            y = s["lp_prev"][i] + a * (x - s["lp_prev"][i])
            s["lp_prev"][i] = y
            x = y

        return _clamp(x, -1.0, 1.0)

    def next_chunk(self, sample_count: int) -> bytes:
        """Return the next PCM chunk for the configured noise profile."""

        frames = bytearray()
        for _ in range(sample_count):
            sample = self._next_sample() * self.volume
            frames.extend(struct.pack("<h", _normalise(sample)))
        return bytes(frames)

    def next_chunk_raw(self, sample_count: int) -> list[int]:
        out = []
        for _ in range(sample_count):
            out.append(_normalise(self._next_sample() * self.volume))
        return out



def build_wav_header(sample_rate: int = SAMPLE_RATE) -> bytes:
    """Return a WAV header suitable for indefinite streaming."""

    channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    return struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        0xFFFFFFFF,
        b"WAVE",
        b"fmt ",
        16,
        1,
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        0xFFFFFFFF,
    )


def coerce_profile(raw_profile: dict[str, Any]) -> dict[str, Any]:
    """Return a serialisable copy of a profile definition."""

    profile_type = raw_profile.get(CONF_PROFILE_TYPE)
    profile_subtype = raw_profile.get(CONF_PROFILE_SUBTYPE)

    if isinstance(profile_subtype, str):
        profile_subtype = normalize_subtype(profile_subtype)

    # Legacy values stored subtype directly in CONF_PROFILE_TYPE.
    if profile_type not in PROFILE_TYPES:
        if profile_type in COLOR_NOISE_SUBTYPES:
            profile_subtype = profile_type
            profile_type = "color_noise"
        else:
            profile_type = DEFAULT_PROFILE_TYPE

    if profile_type == "color_noise":
        if profile_subtype not in COLOR_NOISE_SUBTYPES:
            profile_subtype = DEFAULT_PROFILE_SUBTYPE
    else:
        if profile_subtype not in TONAL_SUBTYPES:
            profile_subtype = DEFAULT_TONAL_SUBTYPE

    parameters = dict(raw_profile.get(CONF_PROFILE_PARAMETERS, {}))

    volume = float(parameters.get(CONF_VOLUME, DEFAULT_VOLUME))
    volume = _clamp(volume, 0.0, 1.0)
    parameters[CONF_VOLUME] = volume

    seed = parameters.get(CONF_SEED)
    if seed in ("", None):
        parameters.pop(CONF_SEED, None)
    else:
        parameters[CONF_SEED] = seed

    if profile_type == "color_noise":
        if profile_subtype == "custom":
            slope = float(parameters.get(CONF_CUSTOM_SLOPE, DEFAULT_CUSTOM_SLOPE))
            slope = _clamp(slope, CUSTOM_SLOPE_MIN, CUSTOM_SLOPE_MAX)
            low = float(parameters.get(CONF_CUSTOM_LOW_CUTOFF, DEFAULT_CUSTOM_LOW_CUTOFF))
            low = _clamp(low, CUSTOM_LOW_CUTOFF_MIN, CUSTOM_HIGH_CUTOFF_MAX)
            high = float(parameters.get(CONF_CUSTOM_HIGH_CUTOFF, DEFAULT_CUSTOM_HIGH_CUTOFF))
            high = _clamp(high, low + 1.0, CUSTOM_HIGH_CUTOFF_MAX)
            if high <= low:
                high = min(max(low + 50.0, CUSTOM_LOW_CUTOFF_MIN + 1.0), CUSTOM_HIGH_CUTOFF_MAX)
            parameters[CONF_CUSTOM_SLOPE] = slope
            parameters[CONF_CUSTOM_LOW_CUTOFF] = low
            parameters[CONF_CUSTOM_HIGH_CUTOFF] = high
        else:
            parameters.pop(CONF_CUSTOM_SLOPE, None)
            parameters.pop(CONF_CUSTOM_LOW_CUTOFF, None)
            parameters.pop(CONF_CUSTOM_HIGH_CUTOFF, None)
    else:
        fallback = TONAL_PRESET_PARAMETERS.get(profile_subtype, {})
        for key in (
            CONF_TONAL_WAVEFORM,
            CONF_TONAL_BASE_FREQUENCY,
            CONF_TONAL_SECONDARY_RATIO,
            CONF_TONAL_PULSE_DURATION,
            CONF_TONAL_PAUSE_DURATION,
            CONF_TONAL_ATTACK,
            CONF_TONAL_DECAY,
        ):
            if key in parameters:
                continue
            if fallback:
                parameters[key] = fallback.get(key)

    return {
        CONF_PROFILE_TYPE: profile_type,
        CONF_PROFILE_SUBTYPE: profile_subtype,
        CONF_PROFILE_PARAMETERS: parameters,
    }


class TonalGenerator:
    """Generate deterministic tonal alarm-like audio."""

    def __init__(
        self,
        subtype: str,
        volume: float,
        seed: Any | None = None,
        *,
        params: dict[str, Any] | None = None,
    ) -> None:
        if subtype not in TONAL_SUBTYPES:
            raise UnknownNoiseTypeError(subtype)

        self.subtype = subtype
        self.volume = _clamp(float(volume), 0.0, 1.0)
        self._rng = random.Random(seed)
        merged = dict(TONAL_PRESET_PARAMETERS.get(subtype, {}))
        if params:
            merged.update(params)

        waveform = merged.get(CONF_TONAL_WAVEFORM, TONAL_WAVEFORMS[0])
        if waveform not in TONAL_WAVEFORMS:
            waveform = TONAL_WAVEFORMS[0]
        self.waveform = waveform
        self.base_freq = max(20.0, float(merged.get(CONF_TONAL_BASE_FREQUENCY, 880.0)))
        self.secondary_ratio = max(0.0, float(merged.get(CONF_TONAL_SECONDARY_RATIO, 0.0)))
        self.pulse_samples = max(
            1, int(float(merged.get(CONF_TONAL_PULSE_DURATION, 400.0)) / 1000 * SAMPLE_RATE)
        )
        self.pause_samples = max(
            0, int(float(merged.get(CONF_TONAL_PAUSE_DURATION, 300.0)) / 1000 * SAMPLE_RATE)
        )
        self.attack_samples = max(
            1, int(float(merged.get(CONF_TONAL_ATTACK, 10.0)) / 1000 * SAMPLE_RATE)
        )
        self.decay_samples = max(
            1, int(float(merged.get(CONF_TONAL_DECAY, 150.0)) / 1000 * SAMPLE_RATE)
        )
        self._cycle_samples = self.pulse_samples + self.pause_samples
        if self._cycle_samples <= 0:
            self._cycle_samples = self.pulse_samples
        self._position = 0
        self._phase = 0.0
        self._secondary_phase = 0.0

    def _osc(self, phase: float, freq: float) -> float:
        t = phase % 1.0
        if self.waveform == "sine":
            return math.sin(2 * math.pi * t)
        if self.waveform == "square":
            return 1.0 if t < 0.5 else -1.0
        if self.waveform == "triangle":
            return 4.0 * abs(t - 0.5) - 1.0
        if self.waveform == "saw":
            return 2.0 * (t - 0.5)
        return math.sin(2 * math.pi * t)

    def _next_sample(self) -> float:
        if self._cycle_samples <= 0:
            self._cycle_samples = 1

        cycle_pos = self._position % self._cycle_samples
        self._position = (self._position + 1) % self._cycle_samples

        if cycle_pos >= self.pulse_samples:
            return 0.0

        freq = self.base_freq
        self._phase += freq / SAMPLE_RATE
        sample = self._osc(self._phase, freq)

        if self.secondary_ratio > 0:
            sec_freq = freq * self.secondary_ratio
            self._secondary_phase += sec_freq / SAMPLE_RATE
            sample = 0.6 * sample + 0.4 * self._osc(self._secondary_phase, sec_freq)

        if cycle_pos < self.attack_samples:
            sample *= cycle_pos / max(self.attack_samples, 1)
        elif cycle_pos > self.pulse_samples - self.decay_samples:
            tail = self.pulse_samples - cycle_pos
            sample *= tail / max(self.decay_samples, 1)

        return sample

    def next_chunk(self, sample_count: int) -> bytes:
        frames = bytearray()
        for _ in range(sample_count):
            frames.extend(struct.pack("<h", _normalise(self._next_sample() * self.volume)))
        return bytes(frames)

def create_generator(
    profile_type: str,
    subtype: str,
    volume: float,
    seed: Any | None,
    params: dict[str, Any],
) -> Any:
    if profile_type == "color_noise":
        custom_params = params if subtype == "custom" else None
        return NoiseGenerator(subtype, volume, seed, custom_params=custom_params)
    if profile_type == "tonal_noise":
        if subtype != TONAL_CUSTOM:
            params = TONAL_PRESET_PARAMETERS.get(subtype, {})
        return TonalGenerator(subtype, volume, seed, params=params)
    raise UnknownNoiseTypeError(profile_type)
