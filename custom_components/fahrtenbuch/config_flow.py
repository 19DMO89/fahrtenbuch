"""Config flow for the Fahrtenbuch integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import CONF_ODOMETER_ENTITY, CONF_PERSON_ENTITY, DOMAIN


class FahrtenbuchConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial setup dialog."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            odometer = user_input[CONF_ODOMETER_ENTITY]
            person = user_input[CONF_PERSON_ENTITY]

            if not self.hass.states.get(odometer):
                errors[CONF_ODOMETER_ENTITY] = "entity_not_found"
            elif not self.hass.states.get(person):
                errors[CONF_PERSON_ENTITY] = "entity_not_found"
            else:
                # Prevent duplicate entries
                await self.async_set_unique_id(
                    f"{odometer}_{person}"
                )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input.get("name", "Fahrtenbuch"),
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Optional("name", default="Fahrtenbuch"): selector.TextSelector(),
                vol.Required(CONF_ODOMETER_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Required(CONF_PERSON_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["person", "device_tracker"]
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
