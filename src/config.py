import configparser
from typing import List, Tuple, Optional


class Config:
    config: configparser.ConfigParser

    def __init__(self, config_file: str):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def get_device_names(self) -> List[str]:
        devices_section = self.config['devices']
        return list(devices_section.keys())

    def get_device_details(self, device_name: str) -> Tuple[int, str, str]:
        """
        device_name **must** exist in the [devices] section

        :param device_name:
        :return:
        """
        device_settings = self.config['devices'].get(device_name)
        split = device_settings.split(' ')
        return int(split[0], 16), split[1], split[2]

    def get_mqtt_details(self) -> configparser.SectionProxy:
        return self.config['mqtt']

    def get_command(self, command: str) -> Optional[str]:
        return self.config['commands'].get(command)
