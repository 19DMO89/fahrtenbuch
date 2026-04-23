"""Fahrtenbuch – Digitales Fahrtenbuch für Home Assistant."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    SERVICE_DELETE_TRIP,
    SERVICE_EXPORT_CSV,
    SERVICE_START_TRIP,
    SERVICE_STOP_TRIP,
    SERVICE_UPDATE_TRIP,
    TRIP_TYPE_BUSINESS,
    TRIP_TYPE_PRIVATE,
)
from .coordinator import FahrtenbuchCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fahrtenbuch from a config entry."""
    coordinator = FahrtenbuchCoordinator(hass, entry)
    await coordinator.async_load()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # ------------------------------------------------------------------ #
    # Services                                                             #
    # ------------------------------------------------------------------ #

    async def handle_start_trip(call: ServiceCall) -> None:
        start_km = call.data.get("start_km")
        await coordinator.async_start_trip(start_km_override=start_km)

    async def handle_stop_trip(call: ServiceCall) -> None:
        trip_type = call.data["trip_type"]
        purpose = call.data.get("purpose", "")
        end_km = call.data.get("end_km")
        await coordinator.async_stop_trip(trip_type, purpose, end_km_override=end_km)

    async def handle_export_csv(call: ServiceCall) -> None:
        path = await coordinator.async_export_csv()
        _LOGGER.info("CSV gespeichert: %s", path)

    async def handle_delete_trip(call: ServiceCall) -> None:
        await coordinator.async_delete_trip(call.data["trip_id"])

    async def handle_update_trip(call: ServiceCall) -> None:
        await coordinator.async_update_trip(
            trip_id=call.data["trip_id"],
            start_km=call.data.get("start_km"),
            end_km=call.data.get("end_km"),
            trip_type=call.data.get("trip_type"),
            purpose=call.data.get("purpose"),
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_START_TRIP,
        handle_start_trip,
        schema=vol.Schema(
            {
                vol.Optional("start_km"): vol.Coerce(float),
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_TRIP,
        handle_stop_trip,
        schema=vol.Schema(
            {
                vol.Required("trip_type"): vol.In(
                    [TRIP_TYPE_BUSINESS, TRIP_TYPE_PRIVATE]
                ),
                vol.Optional("purpose", default=""): cv.string,
                vol.Optional("end_km"): vol.Coerce(float),
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_CSV,
        handle_export_csv,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_TRIP,
        handle_delete_trip,
        schema=vol.Schema(
            {
                vol.Required("trip_id"): cv.string,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_TRIP,
        handle_update_trip,
        schema=vol.Schema(
            {
                vol.Required("trip_id"): cv.string,
                vol.Optional("start_km"): vol.Coerce(float),
                vol.Optional("end_km"): vol.Coerce(float),
                vol.Optional("trip_type"): vol.In(
                    [TRIP_TYPE_BUSINESS, TRIP_TYPE_PRIVATE]
                ),
                vol.Optional("purpose"): cv.string,
            }
        ),
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and remove services."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    ):
        hass.data[DOMAIN].pop(entry.entry_id)

        # Only remove services when the last instance is unloaded
        if not hass.data[DOMAIN]:
            for service in (
                SERVICE_START_TRIP,
                SERVICE_STOP_TRIP,
                SERVICE_EXPORT_CSV,
                SERVICE_DELETE_TRIP,
            ):
                hass.services.async_remove(DOMAIN, service)

    return unload_ok
