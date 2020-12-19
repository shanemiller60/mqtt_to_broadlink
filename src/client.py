from typing import Optional, Dict
import re

import broadlink
import paho.mqtt.client as mqtt
from src.config import Config
from src.device import Device


class Client:
    mqtt: mqtt.Client
    mqtt_prefix: str
    config: Config
    devices: Dict[str, Device]

    def __init__(self, config: Config):
        self.mqtt = mqtt.Client()
        self.config = config
        self.mqtt_prefix = self.config.mqtt_prefix()
        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_message = self.on_message
        self.devices = {}

        for device_name in self.config.device_names():
            self.device_get(device_name)

        """
        | Topic | Payload | Description |
        | --- | --- | --- |
        | `m2b/device/<device-name>/send` | `<command-name>` | Sends a command through the device |
        | `m2b/device/<device-name>/learn` | `<command-name>` | Learns a command through the device and saves the code to the config |
        | `m2b/device/<device-name>/discover` | `<device-ip address>` | Attempts to discover a device and save its details to the config |
        | `m2b/device/<device-name>/add` | `<device-type> <device-ip> <device-mac>` | Adds a device to the config from a known device string |
        | `m2b/device/<device-name>/remove` | - | Removes the device from the config |
        | `m2b/command/<command-name>/add` | `<command-code>` | Adds a command code to the config |
        | `m2b/command/<command-name>/remove` | - | Removes a command code from the config |
        """
        self.message_map = {
            self.handle_command_send:    f'{self.mqtt_prefix}device/(.*)/send',
            self.handle_command_learn:   f'{self.mqtt_prefix}device/(.*)/learn',
            self.handle_device_add:      f'{self.mqtt_prefix}device/(.*)/add',
            self.handle_device_remove:   f'{self.mqtt_prefix}device/(.*)/remove',
            self.handle_command_add:     f'{self.mqtt_prefix}command/(.*)/add',
            self.handle_command_remove:  f'{self.mqtt_prefix}command/(.*)/remove',
            self.handle_device_discover: f'{self.mqtt_prefix}device/(.*)/discover',
        }

    def device_get(self, device_name: str) -> Optional[Device]:
        device = self.devices.get(device_name)
        if device is None:
            details = self.config.device_details(device_name)
            if details is None:
                print(f'Request for unknown device \'{device_name}\'')
                return

            (devtype, host, mac) = details
            try:
                device = Device(device_name, devtype, host, mac)
                self.devices[device_name] = device
            except:
                print(f'Could not open device \'{device_name}\'')
        return device

    def device_add(self, device_name: str, device_details: str) -> Device:
        self.config.device_add(device_name, device_details)
        print(f'Added device \'{device_name}\' with details \'{device_details}\'')
        return self.device_get(device_name)

    def device_remove(self, device_name: str) -> None:
        device = self.devices.get(device_name)
        if device is not None:
            self.config.device_remove(device_name)
            del self.devices[device_name]
            print(f'Removed device \'{device_name}\'')
        else:
            print(f'Can\'t remove unknown device \'{device_name}\'')

    def connect(self) -> None:
        mqtt_details = self.config.mqtt_details()
        if mqtt_details.get('user') is not None and mqtt_details.get('pass') is not None:
            self.mqtt.username_pw_set(mqtt_details['user'], mqtt_details['pass'])
        self.mqtt.connect(mqtt_details['host'], int(mqtt_details.get('port') or "1883"), 60)

    def loop_forever(self) -> None:
        """

        Blocking call that processes network traffic, dispatches callbacks and
        handles reconnecting.
        Other loop*() functions are available that give a threaded interface and a
        manual interface.

        """
        self.mqtt.loop_forever()

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, _, flags, rc):
        client.subscribe(f'{self.mqtt_prefix}command/+/+')
        client.subscribe(f'{self.mqtt_prefix}device/+/+')

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, _, msg):
        for key in self.message_map:
            value = self.message_map[key]
            if re.match(value, msg.topic):
                key(msg)
                return
        print(f'No handler for message topic \'{msg.topic}\'')

    def handle_command_send(self, msg):
        command_name = str(msg.payload, 'UTF-8')
        hex_code = self.config.command_get(command_name)
        if hex_code is None:
            print(f'Received request for unknown command \'{command_name}\'')
            return
        try:
            m = re.search(self.message_map[self.handle_command_send], msg.topic)
            device_name = m.group(1) or ''
            device = self.device_get(device_name)
            if device is not None:
                device.send_code(hex_code)
            else:
                print(f'Could not open/connect to device \'{device_name}\'')
        except:
            print(f'Error while processing MQTT message, topic=\'{msg.topic}\' payload=\'{command_name}\'')

    def handle_command_learn(self, msg):
        command_name = str(msg.payload, 'UTF-8')
        try:
            m = re.search(self.message_map[self.handle_command_learn], msg.topic)
            device_name = m.group(1) or ''
            device = self.device_get(device_name)
            if device is not None:
                hex_code = device.learn_code()
                if hex_code is not None:
                    print(f'{device_name}: Learned code \'{hex_code}\', saved as command \'{command_name}\'')
                    self.config.command_add(command_name, hex_code)
                else:
                    print('No code received')
            else:
                print(f'Could not open/connect to device \'{device_name}\'')
        except:
            print(f'Error while processing MQTT message, topic=\'{msg.topic}\' payload=\'{command_name}\'')

    """
    topic: m2b/command/<command-name>/add
    payload: command-code 
    """
    def handle_command_add(self, msg):
        payload = "invalid"
        try:
            payload = str(msg.payload, 'UTF-8')
            m = re.search(self.message_map[self.handle_command_add], msg.topic)
            command_name = m.group(1)

            if payload is not None and command_name is not None:
                self.config.command_add(command_name, payload)
        except:
            print(f'Error while processing MQTT message, topic=\'{msg.topic}\' payload=\'{payload}\'')

    """
    topic: m2b/command/<command-name>/remove
    payload: -
    """
    def handle_command_remove(self, msg):
        try:
            m = re.search(self.message_map[self.handle_command_remove], msg.topic)
            command_name = m.group(1)

            if command_name is not None:
                self.config.command_remove(command_name)
        except:
            print(f'Error while processing MQTT message, topic=\'{msg.topic}\'')

    """
    topic: m2b/device/<device-name>/discover
    payload: device-ip address
    """
    def handle_device_discover(self, msg):
        ip_address = "invalid"
        try:
            ip_address = str(msg.payload, 'UTF-8')
            m = re.search(self.message_map[self.handle_device_discover], msg.topic)
            device_name = m.group(1)

            print(f'Attempting to discover device \'{device_name}\' at \'{ip_address}\'')
            devices = broadlink.discover(timeout=5, discover_ip_address=ip_address)
            for device in devices:
                if device.auth():
                    device_mac = ''.join(format(x, '02x') for x in device.mac)
                    device_details = f'{hex(device.devtype)} {device.host[0]} {device_mac}'
                    self.device_add(device_name, device_details)
                else:
                    print(f'Error while authenticating with device at \'{ip_address}\'')
        except:
            print(f'Error while processing MQTT message, topic=\'{msg.topic}\' payload=\'{ip_address}\'')

    """
    topic: m2b/device/<device-name>/add
    payload: device-type device-ip device-mac
    """
    def handle_device_add(self, msg):
        device_details = "invalid"
        try:
            device_details = str(msg.payload, 'UTF-8')
            m = re.search(self.message_map[self.handle_device_add], msg.topic)
            device_name = m.group(1)
            self.device_add(device_name, device_details)
        except:
            print(f'Error while processing MQTT message, topic=\'{msg.topic}\' payload=\'{device_details}\'')

    """
    topic: m2b/device/<device-name>/remove
    payload: -
    """
    def handle_device_remove(self, msg):
        try:
            m = re.search(self.message_map[self.handle_device_remove], msg.topic)
            device_name = m.group(1)
            self.device_remove(device_name)
        except:
            print(f'Error while processing MQTT message, topic=\'{msg.topic}\'')
