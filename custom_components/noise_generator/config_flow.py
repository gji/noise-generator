"""Config flow for the Noise Generator integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import (
    ACTION_ADD,
    ACTION_EDIT,
    ACTION_FINISH,
    ACTION_REMOVE,
    CONF_ACTION,
    CONF_CUSTOM_HIGH_CUTOFF,
    CONF_CUSTOM_LOW_CUTOFF,
    CONF_CUSTOM_SLOPE,
    CONF_PROFILE_SUBTYPE,
    CONF_PROFILE_NAME,
    CONF_PROFILE_PARAMETERS,
    CONF_PROFILE_TYPE,
    CONF_PROFILES,
    CONF_SEED,
    CONF_TONAL_ATTACK,
    CONF_TONAL_BASE_FREQUENCY,
    CONF_TONAL_DECAY,
    CONF_TONAL_PAUSE_DURATION,
    CONF_TONAL_PULSE_DURATION,
    CONF_TONAL_SECONDARY_RATIO,
    CONF_TONAL_WAVEFORM,
    CONF_VOLUME,
    COLOR_DISPLAY_LABELS,
    COLOR_NOISE_SUBTYPES,
    CUSTOM_HIGH_CUTOFF_MAX,
    CUSTOM_LOW_CUTOFF_MIN,
    CUSTOM_SLOPE_MAX,
    CUSTOM_SLOPE_MIN,
    DEFAULT_CUSTOM_HIGH_CUTOFF,
    DEFAULT_CUSTOM_LOW_CUTOFF,
    DEFAULT_CUSTOM_SLOPE,
    DEFAULT_PROFILE_NAME,
    DEFAULT_PROFILE_SUBTYPE,
    DEFAULT_PROFILE_TYPE,
    DEFAULT_VOLUME,
    DOMAIN,
    DEFAULT_TONAL_SUBTYPE,
    TONAL_CUSTOM,
    TONAL_DISPLAY_LABELS,
    TONAL_PRESET_PARAMETERS,
    TONAL_SUBTYPES,
    TONAL_WAVEFORMS,
    normalize_subtype,
    PROFILE_TYPES,
)
from .noise import coerce_profile

def _subtype_label(subtype: str) -> str:
    if subtype in COLOR_DISPLAY_LABELS:
        return f"Colored noises · {COLOR_DISPLAY_LABELS[subtype]}"
    if subtype in TONAL_DISPLAY_LABELS:
        return f"Tonal noises · {TONAL_DISPLAY_LABELS[subtype]}"
    return subtype


def _resolve_profile_type(subtype: str) -> str:
    if subtype in COLOR_NOISE_SUBTYPES:
        return "color_noise"
    return "tonal_noise"




def _color_custom_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_CUSTOM_SLOPE,
                default=defaults.get(CONF_CUSTOM_SLOPE, DEFAULT_CUSTOM_SLOPE),
            ): vol.All(vol.Coerce(float), vol.Range(min=CUSTOM_SLOPE_MIN, max=CUSTOM_SLOPE_MAX)),
            vol.Required(
                CONF_CUSTOM_LOW_CUTOFF,
                default=defaults.get(CONF_CUSTOM_LOW_CUTOFF, DEFAULT_CUSTOM_LOW_CUTOFF),
            ): vol.All(vol.Coerce(float), vol.Range(min=CUSTOM_LOW_CUTOFF_MIN, max=CUSTOM_HIGH_CUTOFF_MAX)),
            vol.Required(
                CONF_CUSTOM_HIGH_CUTOFF,
                default=defaults.get(CONF_CUSTOM_HIGH_CUTOFF, DEFAULT_CUSTOM_HIGH_CUTOFF),
            ): vol.All(vol.Coerce(float), vol.Range(min=CUSTOM_LOW_CUTOFF_MIN, max=CUSTOM_HIGH_CUTOFF_MAX)),
        }
    )


def _color_custom_defaults(params: Mapping[str, Any] | None = None) -> dict[str, float]:
    params = params or {}
    return {
        CONF_CUSTOM_SLOPE: float(params.get(CONF_CUSTOM_SLOPE, DEFAULT_CUSTOM_SLOPE)),
        CONF_CUSTOM_LOW_CUTOFF: float(params.get(CONF_CUSTOM_LOW_CUTOFF, DEFAULT_CUSTOM_LOW_CUTOFF)),
        CONF_CUSTOM_HIGH_CUTOFF: float(params.get(CONF_CUSTOM_HIGH_CUTOFF, DEFAULT_CUSTOM_HIGH_CUTOFF)),
    }


def _tonal_defaults(params: Mapping[str, Any] | None = None) -> dict[str, Any]:
    merged = dict(TONAL_PRESET_PARAMETERS.get(DEFAULT_TONAL_SUBTYPE, {}))
    if params:
        merged.update(params)
    return merged


def _tonal_params_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    defaults = _tonal_defaults(defaults)
    waveform_selector = selector.selector(
        {
            "select": {
                "options": [
                    {"label": name.capitalize(), "value": name}
                    for name in TONAL_WAVEFORMS
                ]
            }
        }
    )
    return vol.Schema(
        {
            vol.Required(
                CONF_TONAL_WAVEFORM,
                default=defaults.get(CONF_TONAL_WAVEFORM, TONAL_WAVEFORMS[0]),
            ): waveform_selector,
            vol.Required(
                CONF_TONAL_BASE_FREQUENCY,
                default=float(defaults.get(CONF_TONAL_BASE_FREQUENCY, 880.0)),
            ): vol.All(vol.Coerce(float), vol.Range(min=100.0, max=4000.0)),
            vol.Required(
                CONF_TONAL_SECONDARY_RATIO,
                default=float(defaults.get(CONF_TONAL_SECONDARY_RATIO, 0.0)),
            ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=5.0)),
            vol.Required(
                CONF_TONAL_PULSE_DURATION,
                default=float(defaults.get(CONF_TONAL_PULSE_DURATION, 400.0)),
            ): vol.All(vol.Coerce(float), vol.Range(min=50.0, max=4000.0)),
            vol.Required(
                CONF_TONAL_PAUSE_DURATION,
                default=float(defaults.get(CONF_TONAL_PAUSE_DURATION, 300.0)),
            ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=3000.0)),
            vol.Required(
                CONF_TONAL_ATTACK,
                default=float(defaults.get(CONF_TONAL_ATTACK, 10.0)),
            ): vol.All(vol.Coerce(float), vol.Range(min=1.0, max=1000.0)),
            vol.Required(
                CONF_TONAL_DECAY,
                default=float(defaults.get(CONF_TONAL_DECAY, 200.0)),
            ): vol.All(vol.Coerce(float), vol.Range(min=10.0, max=4000.0)),
        }
    )


def _profile_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    seed_default = ""
    raw_seed = defaults.get(CONF_SEED)
    if isinstance(raw_seed, (str, int)):
        seed_default = raw_seed

    subtype_default = defaults.get(CONF_PROFILE_SUBTYPE, DEFAULT_PROFILE_SUBTYPE)
    subtype_default = normalize_subtype(subtype_default)
    if subtype_default not in (*COLOR_NOISE_SUBTYPES, *TONAL_SUBTYPES):
        subtype_default = DEFAULT_PROFILE_SUBTYPE

    options = [
        {"label": _subtype_label(subtype), "value": subtype}
        for subtype in COLOR_NOISE_SUBTYPES + TONAL_SUBTYPES
    ]

    return vol.Schema(
        {
            vol.Required(
                CONF_PROFILE_NAME,
                default=defaults.get(CONF_PROFILE_NAME, DEFAULT_PROFILE_NAME),
            ): str,
            vol.Required(
                CONF_PROFILE_SUBTYPE,
                default=subtype_default,
            ): selector.selector({"select": {"options": options}}),
            vol.Required(
                CONF_VOLUME,
                default=defaults.get(CONF_VOLUME, DEFAULT_VOLUME),
            ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
            vol.Optional(CONF_SEED, default=seed_default): str,
        }
    )


def _profile_from_user_input(user_input: Mapping[str, Any]) -> dict[str, Any]:
    subtype = normalize_subtype(user_input[CONF_PROFILE_SUBTYPE])
    profile_type = _resolve_profile_type(subtype)

    profile = {
        CONF_PROFILE_NAME: user_input[CONF_PROFILE_NAME],
        CONF_PROFILE_TYPE: profile_type,
        CONF_PROFILE_SUBTYPE: subtype,
        CONF_PROFILE_PARAMETERS: {
            CONF_VOLUME: user_input[CONF_VOLUME],
        },
    }
    seed = user_input.get(CONF_SEED)
    if seed not in (None, ""):
        profile[CONF_PROFILE_PARAMETERS][CONF_SEED] = seed

    if profile_type == "color_noise":
        if subtype == "custom":
            profile[CONF_PROFILE_PARAMETERS][CONF_CUSTOM_SLOPE] = float(
                user_input.get(CONF_CUSTOM_SLOPE, DEFAULT_CUSTOM_SLOPE)
            )
            profile[CONF_PROFILE_PARAMETERS][CONF_CUSTOM_LOW_CUTOFF] = float(
                user_input.get(CONF_CUSTOM_LOW_CUTOFF, DEFAULT_CUSTOM_LOW_CUTOFF)
            )
            profile[CONF_PROFILE_PARAMETERS][CONF_CUSTOM_HIGH_CUTOFF] = float(
                user_input.get(CONF_CUSTOM_HIGH_CUTOFF, DEFAULT_CUSTOM_HIGH_CUTOFF)
            )
    else:
        if subtype != TONAL_CUSTOM:
            profile[CONF_PROFILE_PARAMETERS].update(
                TONAL_PRESET_PARAMETERS.get(subtype, {})
            )
        else:
            profile[CONF_PROFILE_PARAMETERS][CONF_TONAL_WAVEFORM] = user_input[
                CONF_TONAL_WAVEFORM
            ]
            profile[CONF_PROFILE_PARAMETERS][CONF_TONAL_BASE_FREQUENCY] = float(
                user_input[CONF_TONAL_BASE_FREQUENCY]
            )
            profile[CONF_PROFILE_PARAMETERS][CONF_TONAL_SECONDARY_RATIO] = float(
                user_input[CONF_TONAL_SECONDARY_RATIO]
            )
            profile[CONF_PROFILE_PARAMETERS][CONF_TONAL_PULSE_DURATION] = float(
                user_input[CONF_TONAL_PULSE_DURATION]
            )
            profile[CONF_PROFILE_PARAMETERS][CONF_TONAL_PAUSE_DURATION] = float(
                user_input[CONF_TONAL_PAUSE_DURATION]
            )
            profile[CONF_PROFILE_PARAMETERS][CONF_TONAL_ATTACK] = float(
                user_input[CONF_TONAL_ATTACK]
            )
            profile[CONF_PROFILE_PARAMETERS][CONF_TONAL_DECAY] = float(
                user_input[CONF_TONAL_DECAY]
            )

    cleaned = coerce_profile(profile)
    cleaned[CONF_PROFILE_NAME] = profile[CONF_PROFILE_NAME]
    return cleaned


class NoiseGeneratorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the Noise Generator config flow."""

    VERSION = 1

    def __init__(self) -> None:
        super().__init__()
        self._pending_profile_base: dict[str, Any] | None = None
        self._pending_color_defaults: dict[str, float] | None = None
        self._pending_tonal_defaults: dict[str, Any] | None = None

    async def async_step_user(self, user_input: Mapping[str, Any] | None = None):
        """Configure the integration via the UI."""

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: dict[str, str] = {}

        if user_input is not None:
            user_input = dict(user_input)
            subtype = normalize_subtype(user_input[CONF_PROFILE_SUBTYPE])
            profile_type = _resolve_profile_type(subtype)
            if profile_type == "color_noise" and subtype == "custom":
                self._pending_profile_base = user_input
                self._pending_color_defaults = _color_custom_defaults()
                return await self.async_step_user_custom()
            if profile_type == "tonal_noise" and subtype == TONAL_CUSTOM:
                self._pending_profile_base = user_input
                self._pending_tonal_defaults = _tonal_defaults()
                return await self.async_step_user_tonal()

            profile = _profile_from_user_input(user_input)
            return self.async_create_entry(title="Noise Generator", data={CONF_PROFILES: [profile]})

        return self.async_show_form(
            step_id="user",
            data_schema=_profile_schema(),
            errors=errors,
        )

    async def async_step_user_custom(self, user_input: Mapping[str, Any] | None = None):
        """Collect custom noise parameters for the first profile."""

        if not self._pending_profile_base:
            return await self.async_step_user()

        errors: dict[str, str] = {}

        if user_input is not None:
            merged = {**self._pending_profile_base, **user_input}
            profile = _profile_from_user_input(merged)
            self._pending_profile_base = None
            self._pending_color_defaults = None
            return self.async_create_entry(
                title="Noise Generator",
                data={CONF_PROFILES: [profile]},
            )

        return self.async_show_form(
            step_id="user_custom",
            data_schema=_color_custom_schema(self._pending_color_defaults),
            errors=errors,
        )

    async def async_step_user_tonal(self, user_input: Mapping[str, Any] | None = None):
        """Collect custom tonal parameters for the first profile."""

        if not self._pending_profile_base:
            return await self.async_step_user()

        errors: dict[str, str] = {}

        if user_input is not None:
            merged = {**self._pending_profile_base, **user_input}
            profile = _profile_from_user_input(merged)
            self._pending_profile_base = None
            self._pending_tonal_defaults = None
            return self.async_create_entry(
                title="Noise Generator",
                data={CONF_PROFILES: [profile]},
            )

        return self.async_show_form(
            step_id="user_tonal",
            data_schema=_tonal_params_schema(self._pending_tonal_defaults),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return NoiseGeneratorOptionsFlowHandler(config_entry)


class NoiseGeneratorOptionsFlowHandler(config_entries.OptionsFlow):
    """Manage options for the Noise Generator integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry
        self._profiles: list[dict[str, Any]] = []
        self._selected_index: int | None = None
        self._action: str | None = None
        self._pending_profile_base: dict[str, Any] | None = None
        self._pending_color_defaults: dict[str, float] | None = None
        self._pending_tonal_defaults: dict[str, Any] | None = None

    async def async_step_init(self, user_input: Mapping[str, Any] | None = None):
        self._profiles = [
            {
                CONF_PROFILE_NAME: profile.get(CONF_PROFILE_NAME),
                **coerce_profile(profile),
            }
            for profile in self._config_entry.options.get(
                CONF_PROFILES,
                self._config_entry.data.get(CONF_PROFILES, []),
            )
        ]
        self._selected_index = None
        self._action = None
        self._pending_profile_base = None
        self._pending_color_defaults = None
        self._pending_tonal_defaults = None
        return await self.async_step_action()

    async def async_step_action(self, user_input: Mapping[str, Any] | None = None):
        errors: dict[str, str] = {}

        actions: dict[str, str] = {
            ACTION_ADD: "Add profile",
            ACTION_EDIT: "Edit profile",
            ACTION_REMOVE: "Remove profile",
            ACTION_FINISH: "Save changes",
        }
        if not self._profiles:
            actions.pop(ACTION_EDIT)
            actions.pop(ACTION_REMOVE)

        if user_input is not None:
            action = user_input[CONF_ACTION]
            if action == ACTION_ADD:
                self._action = ACTION_ADD
                self._selected_index = None
                return await self.async_step_profile()
            if action == ACTION_EDIT:
                self._action = ACTION_EDIT
                return await self.async_step_select_profile()
            if action == ACTION_REMOVE:
                self._action = ACTION_REMOVE
                return await self.async_step_select_profile()
            if action == ACTION_FINISH:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_PROFILES: self._profiles,
                    },
                )

        return self.async_show_form(
            step_id="action",
            data_schema=vol.Schema({vol.Required(CONF_ACTION): vol.In(actions)}),
            errors=errors,
        )

    async def async_step_profile(self, user_input: Mapping[str, Any] | None = None):
        errors: dict[str, str] = {}
        defaults: dict[str, Any] = {}
        color_defaults = _color_custom_defaults()
        tonal_defaults = _tonal_defaults()

        if self._action == ACTION_EDIT and self._selected_index is not None:
            profile = self._profiles[self._selected_index]
            params = profile[CONF_PROFILE_PARAMETERS]
            seed_default = params.get(CONF_SEED) or ""
            defaults = {
                CONF_PROFILE_NAME: profile[CONF_PROFILE_NAME],
                CONF_PROFILE_SUBTYPE: profile.get(CONF_PROFILE_SUBTYPE, DEFAULT_PROFILE_SUBTYPE),
                CONF_VOLUME: params[CONF_VOLUME],
                CONF_SEED: seed_default,
            }
            if profile.get(CONF_PROFILE_TYPE) == "color_noise" and profile.get(CONF_PROFILE_SUBTYPE) == "custom":
                color_defaults = _color_custom_defaults(params)
            if profile.get(CONF_PROFILE_TYPE) == "tonal_noise" and profile.get(CONF_PROFILE_SUBTYPE) == TONAL_CUSTOM:
                tonal_defaults = _tonal_defaults(params)

        self._pending_profile_base = None
        self._pending_color_defaults = color_defaults
        self._pending_tonal_defaults = tonal_defaults

        if user_input is not None:
            name = user_input[CONF_PROFILE_NAME]
            lower_name = name.casefold()
            for idx, profile in enumerate(self._profiles):
                if idx == self._selected_index:
                    continue
                if profile[CONF_PROFILE_NAME].casefold() == lower_name:
                    errors[CONF_PROFILE_NAME] = "duplicate"
                    break

            if not errors:
                subtype = normalize_subtype(user_input[CONF_PROFILE_SUBTYPE])
                profile_type = _resolve_profile_type(subtype)
                if profile_type == "color_noise" and subtype == "custom":
                    self._pending_profile_base = dict(user_input)
                    if self._action == ACTION_EDIT and self._selected_index is not None:
                        params = self._profiles[self._selected_index][CONF_PROFILE_PARAMETERS]
                        self._pending_color_defaults = _color_custom_defaults(params)
                    else:
                        self._pending_color_defaults = _color_custom_defaults()
                    return await self.async_step_profile_custom()
                if profile_type == "tonal_noise" and subtype == TONAL_CUSTOM:
                    self._pending_profile_base = dict(user_input)
                    if self._action == ACTION_EDIT and self._selected_index is not None:
                        params = self._profiles[self._selected_index][CONF_PROFILE_PARAMETERS]
                        self._pending_tonal_defaults = _tonal_defaults(params)
                    else:
                        self._pending_tonal_defaults = _tonal_defaults()
                    return await self.async_step_profile_tonal()
                profile = _profile_from_user_input(user_input)
                if self._action == ACTION_EDIT and self._selected_index is not None:
                    self._profiles[self._selected_index] = profile
                else:
                    self._profiles.append(profile)
                return await self.async_step_action()

        return self.async_show_form(
            step_id="profile",
            data_schema=_profile_schema(defaults),
            errors=errors,
        )

    async def async_step_profile_custom(self, user_input: Mapping[str, Any] | None = None):
        errors: dict[str, str] = {}

        if not self._pending_profile_base:
            return await self.async_step_profile()

        if user_input is not None:
            merged = {**self._pending_profile_base, **user_input}
            profile = _profile_from_user_input(merged)
            if self._action == ACTION_EDIT and self._selected_index is not None:
                self._profiles[self._selected_index] = profile
            else:
                self._profiles.append(profile)
            self._pending_profile_base = None
            self._pending_color_defaults = None
            return await self.async_step_action()

        return self.async_show_form(
            step_id="profile_custom",
            data_schema=_color_custom_schema(self._pending_color_defaults),
            errors=errors,
        )

    async def async_step_profile_tonal(self, user_input: Mapping[str, Any] | None = None):
        errors: dict[str, str] = {}

        if not self._pending_profile_base:
            return await self.async_step_profile()

        if user_input is not None:
            merged = {**self._pending_profile_base, **user_input}
            profile = _profile_from_user_input(merged)
            if self._action == ACTION_EDIT and self._selected_index is not None:
                self._profiles[self._selected_index] = profile
            else:
                self._profiles.append(profile)
            self._pending_profile_base = None
            self._pending_tonal_defaults = None
            return await self.async_step_action()

        return self.async_show_form(
            step_id="profile_tonal",
            data_schema=_tonal_params_schema(self._pending_tonal_defaults),
            errors=errors,
        )

    async def async_step_select_profile(self, user_input: Mapping[str, Any] | None = None):
        errors: dict[str, str] = {}
        options: list[dict[str, str]] = []
        for idx, profile in enumerate(self._profiles):
            name = profile.get(CONF_PROFILE_NAME) or f"Profile {idx + 1}"
            display = name.strip() or f"Profile {idx + 1}"
            options.append({"label": display, "value": str(idx)})

        if not options:
            return await self.async_step_action()

        if user_input is not None:
            try:
                self._selected_index = int(user_input[CONF_PROFILE_NAME])
            except (TypeError, ValueError):
                errors["base"] = "unknown"
            else:
                if self._action == ACTION_REMOVE:
                    self._profiles.pop(self._selected_index)
                    self._selected_index = None
                    return await self.async_step_action()
                return await self.async_step_profile()

        return self.async_show_form(
            step_id="select_profile",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PROFILE_NAME): selector.selector(
                        {"select": {"options": options}}
                    )
                }
            ),
            errors=errors,
        )
