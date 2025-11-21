"""Constants for the Noise Generator integration."""

from __future__ import annotations

DOMAIN = "noise_generator"

CONF_PROFILES = "profiles"
CONF_PROFILE_NAME = "name"
CONF_PROFILE_TYPE = "type"
CONF_PROFILE_SUBTYPE = "subtype"
CONF_PROFILE_PARAMETERS = "parameters"

CONF_VOLUME = "volume"
CONF_SEED = "seed"
CONF_CUSTOM_SLOPE = "Custom slope"
CONF_CUSTOM_LOW_CUTOFF = "Custom low cutoff"
CONF_CUSTOM_HIGH_CUTOFF = "Custom high cutoff"

CONF_TONAL_WAVEFORM = "tonal_waveform"
CONF_TONAL_BASE_FREQUENCY = "tonal_base_frequency"
CONF_TONAL_SECONDARY_RATIO = "tonal_secondary_ratio"
CONF_TONAL_PULSE_DURATION = "tonal_pulse_duration"
CONF_TONAL_PAUSE_DURATION = "tonal_pause_duration"
CONF_TONAL_ATTACK = "tonal_attack"
CONF_TONAL_DECAY = "tonal_decay"

CONF_ACTION = "action"

DEFAULT_PROFILE_NAME = "White noise"
DEFAULT_PROFILE_TYPE = "color_noise"
DEFAULT_PROFILE_SUBTYPE = "white"
DEFAULT_VOLUME = 0.5
DEFAULT_CUSTOM_SLOPE = 0.0
DEFAULT_CUSTOM_LOW_CUTOFF = 20.0
DEFAULT_CUSTOM_HIGH_CUTOFF = 16000.0
CUSTOM_SLOPE_MIN = -12.0
CUSTOM_SLOPE_MAX = 12.0
CUSTOM_LOW_CUTOFF_MIN = 1.0
TONAL_WAVEFORMS = ["sine", "triangle", "square", "saw"]

PROFILE_TYPES = [
    "color_noise",
    "tonal_noise",
]

COLOR_NOISE_SUBTYPES = [
    "white",
    "pink",
    "brown",
    "custom",
]

TONAL_CUSTOM = "custom_tonal"

TONAL_PRESET_PARAMETERS = {
    "gentle_beep": {
        CONF_TONAL_WAVEFORM: "sine",
        CONF_TONAL_BASE_FREQUENCY: 880.0,
        CONF_TONAL_SECONDARY_RATIO: 1.5,
        CONF_TONAL_PULSE_DURATION: 350.0,
        CONF_TONAL_PAUSE_DURATION: 250.0,
        CONF_TONAL_ATTACK: 10.0,
        CONF_TONAL_DECAY: 120.0,
    },
    "classic_digital": {
        CONF_TONAL_WAVEFORM: "square",
        CONF_TONAL_BASE_FREQUENCY: 1040.0,
        CONF_TONAL_SECONDARY_RATIO: 1.0,
        CONF_TONAL_PULSE_DURATION: 220.0,
        CONF_TONAL_PAUSE_DURATION: 160.0,
        CONF_TONAL_ATTACK: 5.0,
        CONF_TONAL_DECAY: 60.0,
    },
    "mellow_bell": {
        CONF_TONAL_WAVEFORM: "triangle",
        CONF_TONAL_BASE_FREQUENCY: 660.0,
        CONF_TONAL_SECONDARY_RATIO: 2.0,
        CONF_TONAL_PULSE_DURATION: 700.0,
        CONF_TONAL_PAUSE_DURATION: 350.0,
        CONF_TONAL_ATTACK: 5.0,
        CONF_TONAL_DECAY: 650.0,
    },
    "sunrise_chime": {
        CONF_TONAL_WAVEFORM: "sine",
        CONF_TONAL_BASE_FREQUENCY: 520.0,
        CONF_TONAL_SECONDARY_RATIO: 3.0,
        CONF_TONAL_PULSE_DURATION: 900.0,
        CONF_TONAL_PAUSE_DURATION: 400.0,
        CONF_TONAL_ATTACK: 30.0,
        CONF_TONAL_DECAY: 700.0,
    },
    "soft_sweep": {
        CONF_TONAL_WAVEFORM: "saw",
        CONF_TONAL_BASE_FREQUENCY: 450.0,
        CONF_TONAL_SECONDARY_RATIO: 4.0,
        CONF_TONAL_PULSE_DURATION: 1200.0,
        CONF_TONAL_PAUSE_DURATION: 420.0,
        CONF_TONAL_ATTACK: 20.0,
        CONF_TONAL_DECAY: 420.0,
    },
    "retro_buzzer": {
        CONF_TONAL_WAVEFORM: "square",
        CONF_TONAL_BASE_FREQUENCY: 640.0,
        CONF_TONAL_SECONDARY_RATIO: 0.0,
        CONF_TONAL_PULSE_DURATION: 250.0,
        CONF_TONAL_PAUSE_DURATION: 120.0,
        CONF_TONAL_ATTACK: 3.0,
        CONF_TONAL_DECAY: 80.0,
    },
    "duet_beeps": {
        CONF_TONAL_WAVEFORM: "sine",
        CONF_TONAL_BASE_FREQUENCY: 600.0,
        CONF_TONAL_SECONDARY_RATIO: 1.25,
        CONF_TONAL_PULSE_DURATION: 300.0,
        CONF_TONAL_PAUSE_DURATION: 200.0,
        CONF_TONAL_ATTACK: 8.0,
        CONF_TONAL_DECAY: 150.0,
    },
    "warm_drone": {
        CONF_TONAL_WAVEFORM: "triangle",
        CONF_TONAL_BASE_FREQUENCY: 220.0,
        CONF_TONAL_SECONDARY_RATIO: 1.01,
        CONF_TONAL_PULSE_DURATION: 2200.0,
        CONF_TONAL_PAUSE_DURATION: 120.0,
        CONF_TONAL_ATTACK: 320.0,
        CONF_TONAL_DECAY: 900.0,
    },
    "sci_fi_ping": {
        CONF_TONAL_WAVEFORM: "sine",
        CONF_TONAL_BASE_FREQUENCY: 1500.0,
        CONF_TONAL_SECONDARY_RATIO: 0.5,
        CONF_TONAL_PULSE_DURATION: 180.0,
        CONF_TONAL_PAUSE_DURATION: 520.0,
        CONF_TONAL_ATTACK: 5.0,
        CONF_TONAL_DECAY: 260.0,
    },
    "pop_chime": {
        CONF_TONAL_WAVEFORM: "triangle",
        CONF_TONAL_BASE_FREQUENCY: 784.0,
        CONF_TONAL_SECONDARY_RATIO: 1.333,
        CONF_TONAL_PULSE_DURATION: 650.0,
        CONF_TONAL_PAUSE_DURATION: 400.0,
        CONF_TONAL_ATTACK: 12.0,
        CONF_TONAL_DECAY: 520.0,
    },
}

TONAL_PRESET_LABELS = {
    "gentle_beep": "Gentle beep",
    "classic_digital": "Classic digital",
    "mellow_bell": "Mellow bell",
    "sunrise_chime": "Sunrise chime",
    "soft_sweep": "Soft sweep",
    "retro_buzzer": "Retro buzzer",
    "duet_beeps": "Duet beeps",
    "warm_drone": "Warm drone",
    "sci_fi_ping": "Sci-fi ping",
    "pop_chime": "Pop chime",
}

TONAL_SUBTYPES = list(TONAL_PRESET_PARAMETERS.keys()) + [TONAL_CUSTOM]
DEFAULT_TONAL_SUBTYPE = list(TONAL_PRESET_PARAMETERS.keys())[0]

COLOR_DISPLAY_LABELS = {
    "white": "White noise",
    "pink": "Pink noise",
    "brown": "Brown noise",
    "custom": "Custom colored noise",
}

TONAL_DISPLAY_LABELS = {**TONAL_PRESET_LABELS, TONAL_CUSTOM: "Custom tonal sound"}


def normalize_subtype(value: str) -> str:
    """Return canonical subtype from UI label or raw value."""

    if not isinstance(value, str):
        return value
    candidate = value.strip()
    if candidate in COLOR_NOISE_SUBTYPES or candidate in TONAL_SUBTYPES:
        return candidate
    # If label contains category separator, take the part after it
    if "·" in candidate:
        candidate = candidate.split("·", 1)[-1].strip()
    lower = candidate.lower()
    for key, label in {**COLOR_DISPLAY_LABELS, **TONAL_DISPLAY_LABELS}.items():
        if lower == label.lower():
            return key
    return candidate

MEDIA_MIME_TYPE = "audio/wav"
SAMPLE_RATE = 44100
STREAM_CHUNK_DURATION = 0.5
STREAM_URL_PATH = f"/api/{DOMAIN}"
STDOUT_READ_SIZE = 32768
CUSTOM_HIGH_CUTOFF_MAX = SAMPLE_RATE / 2 - 200

ACTION_ADD = "add"
ACTION_EDIT = "edit"
ACTION_REMOVE = "remove"
ACTION_FINISH = "finish"
PROFILE_ROUTE = "profile"
