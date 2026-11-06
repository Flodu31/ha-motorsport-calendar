"""Config flow: one click, with an optional language choice."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback

from .const import CONF_LANGUAGE, DOMAIN, LANGUAGES


def _default_language(hass) -> str:
    lang = (hass.config.language or "en").split("-")[0].lower()
    return lang if lang in LANGUAGES else "en"


class MotorsportConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title="Motorsport Calendar", data={}, options=user_input)
        schema = vol.Schema({vol.Required(CONF_LANGUAGE, default=_default_language(self.hass)): vol.In(LANGUAGES)})
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return MotorsportOptionsFlow()


class MotorsportOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(CONF_LANGUAGE, _default_language(self.hass))
        schema = vol.Schema({vol.Required(CONF_LANGUAGE, default=current): vol.In(LANGUAGES)})
        return self.async_show_form(step_id="init", data_schema=schema)
