from homeassistant.const import (
    CONF_DEVICES,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
)
from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerState,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.storage import STORAGE_DIR

import voluptuous as vol
from googletv import AdbKey, GoogleTv


DOMAIN = 'googletv'


CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_DEVICES): [
            vol.Schema({
                vol.Required(CONF_NAME): cv.string,
                vol.Required(CONF_HOST): cv.string,
                vol.Optional(CONF_PORT): cv.port,
            }),
        ],
    }),
})


STATES = {
    "off": MediaPlayerState.OFF,
    "idle": MediaPlayerState.IDLE,
    "playing": MediaPlayerState.PLAYING,
    "paused": MediaPlayerState.PAUSED,
}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up platform."""
    devices = []
    for device_config in config[CONF_DEVICES]:
        name = device_config[CONF_NAME]
        host = device_config[CONF_HOST]
        port = device_config.get(CONF_PORT, 5555)

        key_path = hass.config.path(STORAGE_DIR, f'{DOMAIN}_{name}_adb_key')
        key = AdbKey(key_path)
        if not key.exists:
            key = key.generate(key_path)

        device = GoogleTv(key, host, port)
        try:
            await device.connect()
        except:
            continue

        devices.append(GoogleTvDevice(name, device))

    if devices:
        async_add_entities(devices)


class GoogleTvDevice(MediaPlayerEntity):
    _attr_device_class = MediaPlayerDeviceClass.TV

    def __init__(self, name: str, device: GoogleTv) -> None:
        self._attr_name = name
        self._attr_unique_id = name

        self._device = device

    async def async_update(self) -> None:
        if not self._device.available and not await self._connect():
            return

        await self._device.update()

        self._attr_app_id = self._device.state.app
        if self._device.state.playback_state:
            self._attr_state = STATES[self._device.state.playback_state]
        elif self._device.state.awake:
            self._attr_state = MediaPlayerState.IDLE
        else:
            self._attr_state = MediaPlayerState.OFF

    async def _connect(self):
        if not self._device.available:
            try:
                await self._device.connect()
            except:
                self._attr_available = False
                return False

        self._attr_available = True
        return True
