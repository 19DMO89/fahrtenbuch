"""Sensor platform for the Fahrtenbuch integration."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import FahrtenbuchCoordinator


@dataclass(frozen=True, kw_only=True)
class FahrtenbuchSensorDescription(SensorEntityDescription):
    value_fn: Callable[[FahrtenbuchCoordinator], Any] = field(default=None)
    extra_fn: Callable[[FahrtenbuchCoordinator], dict | None] = field(default=None)


SENSORS: tuple[FahrtenbuchSensorDescription, ...] = (
    FahrtenbuchSensorDescription(
        key="status",
        name="Status",
        icon="mdi:car",
        value_fn=lambda c: "Fahrt aktiv" if c.is_trip_active else "Bereit",
        extra_fn=lambda c: (
            {
                "start_time": c.active_trip.get("start_time"),
                "start_km": c.active_trip.get("start_km"),
                "start_location": c.active_trip.get("start_location"),
            }
            if c.active_trip
            else None
        ),
    ),
    FahrtenbuchSensorDescription(
        key="trips_count",
        name="Fahrten gesamt",
        icon="mdi:counter",
        native_unit_of_measurement="Fahrten",
        value_fn=lambda c: len(c.trips),
        extra_fn=lambda c: {"letzte_fahrten": c.trips[-5:][::-1]} if c.trips else None,
    ),
    FahrtenbuchSensorDescription(
        key="km_business",
        name="Dienstliche KM",
        icon="mdi:briefcase",
        native_unit_of_measurement="km",
        value_fn=lambda c: c.total_km_business,
    ),
    FahrtenbuchSensorDescription(
        key="km_private",
        name="Private KM",
        icon="mdi:home",
        native_unit_of_measurement="km",
        value_fn=lambda c: c.total_km_private,
    ),
    FahrtenbuchSensorDescription(
        key="active_start_km",
        name="Aktuelle Fahrt Start-KM",
        icon="mdi:map-marker-right",
        native_unit_of_measurement="km",
        value_fn=lambda c: (
            c.active_trip.get("start_km") if c.active_trip else None
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FahrtenbuchCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        FahrtenbuchSensor(coordinator, description) for description in SENSORS
    )


class FahrtenbuchSensor(SensorEntity):
    """A sensor that reads from the FahrtenbuchCoordinator."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FahrtenbuchCoordinator,
        description: FahrtenbuchSensorDescription,
    ) -> None:
        self.entity_description = description
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.entry.title,
            manufacturer="Fahrtenbuch",
            model="Digitales Fahrtenbuch",
            entry_type="service",
        )

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self._coordinator)

    @property
    def extra_state_attributes(self) -> dict | None:
        if self.entity_description.extra_fn:
            return self.entity_description.extra_fn(self._coordinator)
        return None

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self._coordinator.async_add_listener(self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
