"""
Device is used to interact with the broadlink device
"""
from typing import Optional

import broadlink
import time
from broadlink.exceptions import ReadError, StorageError

TICK = 32.84
TIMEOUT = 10


class Device:
    name: str

    def __init__(self, device_name: str, devtype: int, host: str, mac: str):
        self.name = device_name
        self.device = broadlink.gendevice(devtype, (host, 80), mac)
        self.device.auth()

    def send_code(self, hex_code: str) -> None:
        self.device.send_data(bytearray.fromhex(hex_code))

    def learn_code(self) -> Optional[str]:
        self.device.enter_learning()

        print(f'{self.name}: Learning...')
        start = time.time()
        while time.time() - start < TIMEOUT:
            time.sleep(1)
            try:
                data = self.device.check_data()
                return ''.join(format(x, '02x') for x in bytearray(data))
            except (ReadError, StorageError):
                continue

        print(f'{self.name}: No data received...')
        return None
