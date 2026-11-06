"""calendar.motogp and calendar.f1 entities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SERIES_F1, SERIES_MOTOGP
from .coordinator import MotorsportCoordinator

SERIES = {
    SERIES_MOTOGP: ("MotoGP", "mdi:motorbike", "motogp.com"),
    SERIES_F1: ("F1", "mdi:racing-helmet", "OpenF1"),
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: MotorsportCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(MotorsportCalendar(coordinator, entry, s) for s in SERIES)


def _to_event(item: dict[str, Any]) -> CalendarEvent:
    return CalendarEvent(
        start=dt_util.as_local(dt_util.parse_datetime(item["start"])),
        end=dt_util.as_local(dt_util.parse_datetime(item["end"])),
        summary=item["summary"],
        description=item.get("description"),
        location=item.get("location") or None,
        uid=item.get("uid"),
    )


class MotorsportCalendar(CoordinatorEntity[MotorsportCoordinator], CalendarEntity):
    _attr_has_entity_name = False

    def __init__(self, coordinator: MotorsportCoordinator, entry: ConfigEntry, series: str) -> None:
        super().__init__(coordinator)
        name, icon, source = SERIES[series]
        self._series = series
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{DOMAIN}_{series}"
        self._attr_attribution = f"Data: {source}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Motorsport Calendar",
            manufacturer="Flodu31",
            model="MotoGP + F1",
            entry_type=DeviceEntryType.SERVICE,
        )

    def _items(self) -> list[dict[str, Any]]:
        return (self.coordinator.data or {}).get(self._series, [])

    @property
    def event(self) -> CalendarEvent | None:
        now = dt_util.utcnow()
        for item in self._items():
            end = dt_util.parse_datetime(item["end"])
            if end and end > now:
                return _to_event(item)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        nxt = self.event
        return {"sessions": len(self._items()), "next": nxt.summary if nxt else None}

    async def async_get_events(self, hass: HomeAssistant, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
        s, e = dt_util.as_utc(start_date), dt_util.as_utc(end_date)
        out = []
        for item in self._items():
            st, en = dt_util.parse_datetime(item["start"]), dt_util.parse_datetime(item["end"])
            if st and en and en > s and st < e:
                out.append(_to_event(item))
        return out
