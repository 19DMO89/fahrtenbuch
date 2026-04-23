"""Fahrtenbuch data coordinator."""
from __future__ import annotations

import csv
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

from .const import (
    CONF_ODOMETER_ENTITY,
    CONF_PERSON_ENTITY,
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
    TRIP_TYPE_BUSINESS,
)

_LOGGER = logging.getLogger(__name__)


class FahrtenbuchCoordinator:
    """Manages trip data persistence and business logic."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._store: Store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict[str, Any] = {"trips": [], "active_trip": None}
        self._listeners: list[Any] = []

    async def async_load(self) -> None:
        """Load persisted data from storage."""
        data = await self._store.async_load()
        if data:
            self._data = data

    async def async_save(self) -> None:
        """Persist data to storage."""
        await self._store.async_save(self._data)

    @callback
    def async_add_listener(self, listener: Any) -> Any:
        """Register a listener that is called on data changes."""
        self._listeners.append(listener)

        @callback
        def remove_listener() -> None:
            self._listeners.remove(listener)

        return remove_listener

    @callback
    def _notify_listeners(self) -> None:
        for listener in self._listeners:
            listener()

    # ------------------------------------------------------------------ #
    # Properties                                                           #
    # ------------------------------------------------------------------ #

    @property
    def trips(self) -> list[dict]:
        return self._data.get("trips", [])

    @property
    def active_trip(self) -> dict | None:
        return self._data.get("active_trip")

    @property
    def is_trip_active(self) -> bool:
        return self._data.get("active_trip") is not None

    @property
    def total_km_business(self) -> float:
        return round(
            sum(
                t.get("km_driven", 0) or 0
                for t in self.trips
                if t.get("trip_type") == TRIP_TYPE_BUSINESS
            ),
            1,
        )

    @property
    def total_km_private(self) -> float:
        return round(
            sum(
                t.get("km_driven", 0) or 0
                for t in self.trips
                if t.get("trip_type") != TRIP_TYPE_BUSINESS
            ),
            1,
        )

    # ------------------------------------------------------------------ #
    # Entity state helpers                                                 #
    # ------------------------------------------------------------------ #

    def _get_odometer(self) -> float | None:
        entity_id = self.entry.data[CONF_ODOMETER_ENTITY]
        state = self.hass.states.get(entity_id)
        if state is None:
            _LOGGER.warning("Odometer entity '%s' not found", entity_id)
            return None
        try:
            return float(state.state)
        except (ValueError, TypeError):
            _LOGGER.warning("Cannot parse odometer state '%s'", state.state)
            return None

    def _get_location(self) -> str | None:
        entity_id = self.entry.data[CONF_PERSON_ENTITY]
        state = self.hass.states.get(entity_id)
        if state is None:
            return None
        lat = state.attributes.get("latitude")
        lon = state.attributes.get("longitude")
        if lat is not None and lon is not None:
            return f"{round(float(lat), 6)},{round(float(lon), 6)}"
        # fall back to zone name (e.g. "home", "work")
        return state.state

    # ------------------------------------------------------------------ #
    # Service handlers                                                     #
    # ------------------------------------------------------------------ #

    async def async_start_trip(self) -> None:
        """Record trip start with current odometer reading and location."""
        if self.is_trip_active:
            _LOGGER.warning("A trip is already active – ignoring start_trip")
            return

        start_km = self._get_odometer()
        start_location = self._get_location()

        self._data["active_trip"] = {
            "id": str(uuid4()),
            "start_time": datetime.now().isoformat(),
            "start_km": start_km,
            "start_location": start_location,
        }
        await self.async_save()
        self._notify_listeners()
        _LOGGER.info(
            "Trip started – odometer: %s km, location: %s", start_km, start_location
        )

    async def async_stop_trip(self, trip_type: str, purpose: str = "") -> None:
        """Finalise the active trip and append it to the log."""
        if not self.is_trip_active:
            _LOGGER.warning("No active trip to stop")
            return

        end_km = self._get_odometer()
        end_location = self._get_location()
        active = self._data["active_trip"]
        start_km = active.get("start_km")

        km_driven: float | None = None
        if end_km is not None and start_km is not None:
            km_driven = round(end_km - start_km, 1)

        completed = {
            **active,
            "end_time": datetime.now().isoformat(),
            "end_km": end_km,
            "km_driven": km_driven,
            "end_location": end_location,
            "trip_type": trip_type,
            "purpose": purpose,
        }

        self._data["trips"].append(completed)
        self._data["active_trip"] = None
        await self.async_save()
        self._notify_listeners()
        _LOGGER.info(
            "Trip ended – %.1f km, type: %s", km_driven or 0.0, trip_type
        )

    async def async_delete_trip(self, trip_id: str) -> None:
        """Remove a trip entry by ID."""
        before = len(self._data["trips"])
        self._data["trips"] = [
            t for t in self._data["trips"] if t.get("id") != trip_id
        ]
        if len(self._data["trips"]) < before:
            await self.async_save()
            self._notify_listeners()
            _LOGGER.info("Deleted trip %s", trip_id)
        else:
            _LOGGER.warning("Trip ID '%s' not found", trip_id)

    async def async_export_csv(self) -> str:
        """Write all trips to a CSV file in the HA config directory."""
        filename = f"fahrtenbuch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path = self.hass.config.path(filename)

        fieldnames = [
            "Datum",
            "Startzeit",
            "Endzeit",
            "Start-KM",
            "End-KM",
            "Gefahrene KM",
            "Startort",
            "Endort",
            "Typ",
            "Zweck",
        ]

        with open(path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for trip in sorted(
                self.trips, key=lambda t: t.get("start_time", "")
            ):
                start_dt = datetime.fromisoformat(trip["start_time"])
                end_dt = (
                    datetime.fromisoformat(trip["end_time"])
                    if trip.get("end_time")
                    else None
                )
                writer.writerow(
                    {
                        "Datum": start_dt.strftime("%d.%m.%Y"),
                        "Startzeit": start_dt.strftime("%H:%M"),
                        "Endzeit": end_dt.strftime("%H:%M") if end_dt else "",
                        "Start-KM": trip.get("start_km", ""),
                        "End-KM": trip.get("end_km", ""),
                        "Gefahrene KM": trip.get("km_driven", ""),
                        "Startort": trip.get("start_location", ""),
                        "Endort": trip.get("end_location", ""),
                        "Typ": trip.get("trip_type", ""),
                        "Zweck": trip.get("purpose", ""),
                    }
                )

        _LOGGER.info("Fahrtenbuch exported to %s", path)
        return path
