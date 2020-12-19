import configparser
from typing import List, Tuple, Optional


class Config:
    config: configparser.ConfigParser
    config_file: str

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def device_names(self) -> List[str]:
        devices_section = self.config['devices']
        return list(devices_section.keys())

    def device_add(self, device_name: str, device_details: str) -> None:
        # TODO: Sanity check device_details to see if it's kind of valid
        self.config['devices'][device_name] = device_details
        self._save_config()

    def device_remove(self, device_name: str) -> None:
        del self.config['devices'][device_name]
        self._save_config()

    def device_details(self, device_name: str) -> Optional[Tuple[int, str, str]]:
        device_settings = self.config['devices'].get(device_name)
        if device_settings is not None:
            split = device_settings.split(' ')
            return int(split[0], 16), split[1], split[2]
        return None

    def mqtt_details(self) -> configparser.SectionProxy:
        return self.config['mqtt']

    def mqtt_prefix(self) -> str:
        prefix = self.config['mqtt'].get('prefix') or "m2b"
        if not prefix.endswith("/"):
            prefix += "/"
        return prefix

    def command_add(self, command_name: str, command_code: str) -> None:
        self.config['commands'][command_name] = command_code
        self._save_config()

    def command_remove(self, command_name: str) -> None:
        del self.config['commands'][command_name]
        self._save_config()

    def command_get(self, command: str) -> Optional[str]:
        return self.config['commands'].get(command)

    def _save_config(self) -> None:
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
