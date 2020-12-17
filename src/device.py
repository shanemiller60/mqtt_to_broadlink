"""
Device is used to interact with the broadlink device

"""
import broadlink


class Device:
    name: str

    def __init__(self, device_name: str, devtype: int, host: str, mac: str):
        self.name = device_name
        self.device = broadlink.gendevice(devtype, (host, 80), mac)
        self.device.auth()

    def send_code(self, hex_code: str):
        self.device.send_data(bytearray.fromhex(hex_code))
