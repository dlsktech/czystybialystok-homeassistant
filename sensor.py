import requests
import json
import logging
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)

API_URL = "https://dev.omnihub.pl/api/infotechwidget/?format=json"

async def async_setup_entry(hass, config_entry, async_add_entities):
    update_interval = timedelta(minutes=5)
    coordinator = OmnihubDataUpdateCoordinator(hass, update_interval)

    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        raise UpdateFailed("Failed to update data from Omnihub API.")

    entities = []
    for device in coordinator.data:
        for variable in device['vars']:
            entities.append(OmnihubSensor(coordinator, device['device'], variable))

    async_add_entities(entities, update_before_add=True)

class OmnihubDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, update_interval):
        super().__init__(hass, _LOGGER, name="Omnihub API", update_interval=update_interval)

    async def _async_update_data(self):
        try:
            response = requests.get(API_URL)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.RequestException as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

class OmnihubSensor(Entity):
    def __init__(self, coordinator, device_name, variable):
        self.coordinator = coordinator
        self.device_name = device_name
        self.variable = variable
        self._attr_name = f"{device_name} {variable['var_name']}"

    @property
    def state(self):
        return self.variable['var_value']

    @property
    def unit_of_measurement(self):
        return self.variable['var_label']

    async def async_update(self):
        await self.coordinator.async_request_refresh()
        for device in self.coordinator.data:
            if device['device'] == self.device_name:
                for var in device['vars']:
                    if var['var_name'] == self.variable['var_name']:
                        self.variable = var
                        break

    async def async_added_to_hass(self):
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))