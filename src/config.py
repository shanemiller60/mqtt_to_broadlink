import configparser
from typing import List, Tuple, Optional

MQTT_SECTION = 'mqtt'
DEVICES_SECTION = 'devices'
COMMANDS_SECTION = 'commands'
LOGGING_SECTION = 'logging'


class Config:
    config: configparser.ConfigParser
    config_file: str

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        # Create devices and commands section if they don't exist yet
        if not self.config.has_section(DEVICES_SECTION):
            self.config.add_section(DEVICES_SECTION)
        if not self.config.has_section(COMMANDS_SECTION):
            self.config.add_section(COMMANDS_SECTION)

    def device_names(self) -> List[str]:
        devices_section = self.config[DEVICES_SECTION]
        return list(devices_section.keys())

    def device_add(self, device_name: str, device_details: str) -> None:
        # TODO: Sanity check device_details to see if it's kind of valid
        self.config[DEVICES_SECTION][device_name] = device_details
        self._save_config()

    def device_remove(self, device_name: str) -> None:
        del self.config[DEVICES_SECTION][device_name]
        self._save_config()

    def device_details(self, device_name: str) -> Optional[Tuple[int, str, str]]:
        device_settings = self.config[DEVICES_SECTION].get(device_name)
        if device_settings is not None:
            split = device_settings.split(' ')
            return int(split[0], 16), split[1], split[2]
        return None

    def mqtt_details(self) -> configparser.SectionProxy:
        return self.config[MQTT_SECTION]

    def mqtt_prefix(self) -> str:
        prefix = self.config.get(MQTT_SECTION, 'prefix', fallback="m2b")
        if not prefix.endswith("/"):
            prefix += "/"
        return prefix

    def command_add(self, command_name: str, command_code: str) -> None:
        self.config[COMMANDS_SECTION][command_name] = command_code
        self._save_config()

    def command_remove(self, command_name: str) -> None:
        del self.config[COMMANDS_SECTION][command_name]
        self._save_config()

    def command_get(self, command: str) -> Optional[str]:
        return self.config[COMMANDS_SECTION].get(command)

    def log_level_get(self) -> str:
        return self.config.get(LOGGING_SECTION, 'level', fallback='INFO')

    def log_level_set(self, level: str) -> None:
        if not self.config.has_section(LOGGING_SECTION):
            self.config.add_section(LOGGING_SECTION)
        self.config.set(LOGGING_SECTION, 'level', level)
        self._save_config()

    def _save_config(self) -> None:
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
