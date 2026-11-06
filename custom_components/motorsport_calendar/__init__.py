"""Motorsport Calendar: MotoGP (official motogp.com data) and F1 (OpenF1) calendars."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import MotorsportCoordinator

PLATFORMS = [Platform.CALENDAR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = MotorsportCoordinator(hass, entry)
    await coordinator.async_load_cache()
    if any(coordinator._cache.values()):  # noqa: SLF001
        # Start right away from cache, refresh from the network in the background
        coordinator.async_set_updated_data(dict(coordinator._cache))  # noqa: SLF001
        entry.async_create_background_task(hass, coordinator.async_refresh(), f"{DOMAIN}_refresh")
    else:
        await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Language changed: rebuild the session names."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok
