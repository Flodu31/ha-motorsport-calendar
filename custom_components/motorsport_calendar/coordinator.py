"""Periodic fetch of the MotoGP and F1 schedules."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_LANGUAGE,
    DOMAIN,
    F1_MEETINGS_URL,
    F1_SESSIONS_URL,
    MOTOGP_EVENTS_URL,
    SERIES_F1,
    SERIES_MOTOGP,
    STORAGE_KEY,
    STORAGE_VERSION,
    UPDATE_INTERVAL,
)
from .parse import parse_f1, parse_motogp

_LOGGER = logging.getLogger(__name__)
_HEADERS = {"User-Agent": "HomeAssistant-motorsport_calendar/1.1 (+https://github.com/Flodu31/ha-motorsport-calendar)", "Accept": "application/json"}
_TIMEOUT = aiohttp.ClientTimeout(total=60)


class MotorsportCoordinator(DataUpdateCoordinator[dict[str, list[dict[str, Any]]]]):
    """Keeps the last good schedule of each series (also on disk)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)
        self._entry = entry
        self._session = async_get_clientsession(hass)
        self._store: Store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._cache: dict[str, list[dict[str, Any]]] = {SERIES_MOTOGP: [], SERIES_F1: []}

    async def async_load_cache(self) -> None:
        data = await self._store.async_load()
        if isinstance(data, dict):
            for k in (SERIES_MOTOGP, SERIES_F1):
                if isinstance(data.get(k), list):
                    self._cache[k] = data[k]

    async def _get(self, url: str) -> Any:
        async with self._session.get(url, headers=_HEADERS, timeout=_TIMEOUT) as resp:
            resp.raise_for_status()
            return await resp.json(content_type=None)

    @property
    def _lang(self) -> str:
        lang = self._entry.options.get(CONF_LANGUAGE) or (self.hass.config.language or "en")
        return lang.split("-")[0].lower()

    def _years(self) -> list[int]:
        y = dt_util.now().year
        return [y, y + 1]

    async def _fetch_motogp(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        ok = False
        for year in self._years():
            try:
                events = await self._get(MOTOGP_EVENTS_URL.format(year=year))
                out += parse_motogp(events if isinstance(events, list) else [], self._lang)
                ok = True
            except Exception as err:  # noqa: BLE001
                if year == self._years()[0]:
                    raise
                _LOGGER.debug("MotoGP %s not available: %s", year, err)
        if not ok or not out:
            raise UpdateFailed("No MotoGP session received")
        return out

    async def _fetch_f1(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for year in self._years():
            try:
                sessions = await self._get(F1_SESSIONS_URL.format(year=year))
                await asyncio.sleep(0.5)
                meetings = await self._get(F1_MEETINGS_URL.format(year=year))
                await asyncio.sleep(0.5)
            except Exception as err:  # noqa: BLE001
                if year == self._years()[0]:
                    raise
                _LOGGER.debug("F1 %s not available: %s", year, err)
                continue
            if isinstance(sessions, list):
                out += parse_f1(sessions, meetings if isinstance(meetings, list) else [], self._lang)
        if not out:
            raise UpdateFailed("No F1 session received")
        return out

    async def _async_update_data(self) -> dict[str, list[dict[str, Any]]]:
        errors = []
        for series, fetch in ((SERIES_MOTOGP, self._fetch_motogp), (SERIES_F1, self._fetch_f1)):
            try:
                items = await fetch()
                items.sort(key=lambda x: x["start"])
                self._cache[series] = items
            except Exception as err:  # noqa: BLE001
                errors.append(f"{series}: {err}")
                _LOGGER.warning("Could not update %s, keeping previous data: %s", series, err)
        if errors and not any(self._cache.values()):
            raise UpdateFailed("; ".join(errors))
        await self._store.async_save(self._cache)
        return dict(self._cache)
