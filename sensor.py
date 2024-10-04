import logging
import requests
import json
from datetime import timedelta
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import TEMP_CELSIUS, PERCENTAGE, PRESSURE_HPA
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

# Limitujemy odświeżanie danych do co 5 minut
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)

# URL API
API_URL = "https://dev.omnihub.pl/api/infotechwidget/?format=json"

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Ustawienie platformy czujników."""
    sensors = []
    
    # Pobranie danych z API
    data = InfotechSensorData()
    data.update()

    # Przypisanie czujników dla każdego urządzenia
    for device in data.devices:
        for var in device['vars']:
            sensors.append(InfotechSensor(device['device'], var['var_name'], var['var_value'], var['var_label']))

    add_entities(sensors, True)

class InfotechSensor(Entity):
    """Reprezentacja pojedynczego sensora."""

    def __init__(self, device_name, var_name, var_value, var_label):
        """Inicjalizacja czujnika."""
        self._device_name = device_name
        self._var_name = var_name
        self._state = var_value
        self._unit = var_label
        self._name = f"{device_name} {var_name}"

    @property
    def name(self):
        """Zwraca nazwę sensora."""
        return self._name

    @property
    def state(self):
        """Zwraca aktualny stan sensora."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Zwraca jednostkę miary."""
        return self._unit

    def update(self):
        """Aktualizuje stan sensora."""
        data = InfotechSensorData()
        data.update()

        for device in data.devices:
            if device['device'] == self._device_name:
                for var in device['vars']:
                    if var['var_name'] == self._var_name:
                        self._state = var['var_value']


class InfotechSensorData:
    """Pobieranie danych z API."""

    def __init__(self):
        self.devices = []

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Aktualizacja danych z API."""
        try:
            response = requests.get(API_URL)
            if response.status_code == 200:
                self.devices = response.json()
            else:
                _LOGGER.error("Błąd podczas pobierania danych z API: %s", response.status_code)
        except requests.exceptions.RequestException as error:
            _LOGGER.error("Błąd połączenia z API: %s", error)
