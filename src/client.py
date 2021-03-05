import logging
import re
import time
import broadlink
import paho.mqtt.client as mqtt
from typing import Optional, Dict
from src.config import Config
from src.converter import Converter
from src.device import Device

log = logging.getLogger("mqtt_to_broadlink")

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
        self.mqtt.on_disconnect = self.on_disconnect
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
        | `m2b/command/<command-name>/add_pronto` | `<command-code>` | Adds a pronto-hex code to the config |
        | `m2b/command/<command-name>/remove` | - | Removes a command code from the config |
        | `m2b/log/level` | `[DEBUG|INFO|WARN|ERROR]` | Sets the level of messages shown in stdout |
        """
        self.message_map = {
            self.handle_device_send:        f'{self.mqtt_prefix}device/(.*)/send',
            self.handle_device_learn:       f'{self.mqtt_prefix}device/(.*)/learn',
            self.handle_device_add:         f'{self.mqtt_prefix}device/(.*)/add',
            self.handle_device_remove:      f'{self.mqtt_prefix}device/(.*)/remove',
            self.handle_device_discover:    f'{self.mqtt_prefix}device/(.*)/discover',
            self.handle_command_add_pronto: f'{self.mqtt_prefix}command/(.*)/add_pronto',
            self.handle_command_add:        f'{self.mqtt_prefix}command/(.*)/add',
            self.handle_command_remove:     f'{self.mqtt_prefix}command/(.*)/remove',
            self.handle_log_level:          f'{self.mqtt_prefix}log/level',
        }

    def device_get(self, device_name: str) -> Optional[Device]:
        device = self.devices.get(device_name)
        if device is None:
            details = self.config.device_details(device_name)
            if details is None:
                log.warning(f'Request for unknown device \'{device_name}\'')
                return

            (devtype, host, mac) = details
            try:
                device = Device(device_name, devtype, host, mac)
                self.devices[device_name] = device
            except Exception as e:
                log.error(f'Could not open device \'{device_name}\': {e}')
        return device

    def device_add(self, device_name: str, device_details: str) -> Device:
        self.config.device_add(device_name, device_details)
        log.info(f'Added device \'{device_name}\' with details \'{device_details}\'')
        return self.device_get(device_name)

    def device_remove(self, device_name: str) -> None:
        device = self.devices.get(device_name)
        if device is not None:
            self.config.device_remove(device_name)
            del self.devices[device_name]
            log.info(f'Removed device \'{device_name}\'')
        else:
            log.warning(f'Can\'t remove unknown device \'{device_name}\'')

    def connect(self) -> bool:
        """
        Connects to the broker specified in the config.ini file

        Returns True when the connection is successful
        """
        mqtt_details = self.config.mqtt_details()
        if mqtt_details.get('user') is not None and mqtt_details.get('pass') is not None:
            self.mqtt.username_pw_set(mqtt_details['user'], mqtt_details['pass'])

        rc = -1
        try:
            host = mqtt_details['host']
            port = int(mqtt_details.get('port') or "1883")
            rc = self.mqtt.connect(host, port, 15)
        except Exception as ex:
            log.error(f"Failed to connect to {host}:{port}, {ex}")
            time.sleep(3.0)
        return 0 == rc

    def start_processing(self) -> None:
        """
        Connects to the broker and processes messages forever.

        This call never returns.
        """
        while True:
            if self.connect():
                break
            time.sleep(3.0)

        self.mqtt.loop_forever()

    def on_connect(self, client, _, flags, rc):
        """
        The callback for when the client receives a CONNACK response from the server.

        Subscribes to required topics
        """
        log.info(f'Connected to broker {client._host}:{client._port}')
        client.subscribe(f'{self.mqtt_prefix}command/+/+')
        client.subscribe(f'{self.mqtt_prefix}device/+/+')
        client.subscribe(f'{self.mqtt_prefix}log/level')

    def on_disconnect(self, client, userdata, rc):
        """
        Callback when disconnected from the server for any reason, loop_forever
        should handle the reconnect logic
        """
        logging.info("Disconnected from broker, reason: {str(rc)}")

    def on_message(self, client, _, msg):
        """
        The callback for when a message is received from the server.

        Passes the message to a registered handler based on a topic match/lookup
        """
        for key in self.message_map:
            value = self.message_map[key]
            if re.match(value, msg.topic):
                key(msg)
                return
        log.error(f'No handler for message topic \'{msg.topic}\'')

    def handle_device_send(self, msg):
        """
        topic: m2b/device/<device-name>/send
        payload: command-name
        """
        command_name = str(msg.payload, 'UTF-8')
        hex_code = self.config.command_get(command_name)
        if hex_code is None:
            log.warning(f'Received request for unknown command \'{command_name}\'')
            return
        try:
            m = re.search(self.message_map[self.handle_device_send], msg.topic)
            device_name = m.group(1) or ''
            device = self.device_get(device_name)
            if device is not None:
                device.send_code(hex_code)
                log.debug(f'{device_name}: Send command \'{command_name}\'')
            else:
                log.error(f'Could not open/connect to device \'{device_name}\'')
        except Exception as e:
            log.error(f'Error while processing MQTT message, topic=\'{msg.topic}\' payload=\'{command_name}\': {e}')

    def handle_device_learn(self, msg):
        """
        topic: m2b/device/<device-name>/learn
        payload: -
        """
        command_name = str(msg.payload, 'UTF-8')
        try:
            m = re.search(self.message_map[self.handle_device_learn], msg.topic)
            device_name = m.group(1) or ''
            device = self.device_get(device_name)
            if device is not None:
                hex_code = device.learn_code()
                if hex_code is not None:
                    self.config.command_add(command_name, hex_code)
                    log.debug(f'{device_name}: Learned code \'{hex_code}\', saved as command \'{command_name}\'')
                else:
                    log.warning('No code received')
            else:
                log.error(f'Could not open/connect to device \'{device_name}\'')
        except Exception as e:
            log.error(f'Error while processing MQTT message, topic=\'{msg.topic}\' payload=\'{command_name}\': {e}')

    def handle_device_discover(self, msg):
        """
        topic: m2b/device/<device-name>/discover
        payload: device-ip address
        """
        ip_address = "invalid"
        try:
            ip_address = str(msg.payload, 'UTF-8')
            m = re.search(self.message_map[self.handle_device_discover], msg.topic)
            device_name = m.group(1)

            log.info(f'Attempting to discover device \'{device_name}\' at \'{ip_address}\'')
            devices = broadlink.discover(timeout=5, discover_ip_address=ip_address)
            for device in devices:
                if device.auth():
                    device_mac = ''.join(format(x, '02x') for x in device.mac)
                    device_details = f'{hex(device.devtype)} {device.host[0]} {device_mac}'
                    self.device_add(device_name, device_details)
                    log.debug(f'Discovered device \'{device_name}\' with details {device_details}')
                else:
                    log.error(f'Error while authenticating with device at \'{ip_address}\'')
        except Exception as e:
            log.error(f'Error while processing MQTT message, topic=\'{msg.topic}\' payload=\'{ip_address}\': {e}')

    def handle_device_add(self, msg):
        """
        topic: m2b/device/<device-name>/add
        payload: device-type device-ip device-mac
        """
        device_details = "invalid"
        try:
            device_details = str(msg.payload, 'UTF-8')
            m = re.search(self.message_map[self.handle_device_add], msg.topic)
            device_name = m.group(1)
            self.device_add(device_name, device_details)
            log.debug(f'Added device \'{device_name}\' with details {device_details}')
        except Exception as e:
            log.error(f'Error while processing MQTT message, topic=\'{msg.topic}\' payload=\'{device_details}\': {e}')

    def handle_device_remove(self, msg):
        """
        topic: m2b/device/<device-name>/remove
        payload: -
        """
        try:
            m = re.search(self.message_map[self.handle_device_remove], msg.topic)
            device_name = m.group(1)
            self.device_remove(device_name)
            log.debug(f'Removed device \'{device_name}\'')
        except Exception as e:
            log.error(f'Error while processing MQTT message, topic=\'{msg.topic}\': {e}')

    def handle_command_add(self, msg):
        """
        topic: m2b/command/<command-name>/add
        payload: command-code
        """
        broadlink_code = "invalid"
        try:
            broadlink_code = str(msg.payload, 'UTF-8')
            m = re.search(self.message_map[self.handle_command_add], msg.topic)
            command_name = m.group(1)

            if broadlink_code is not None and command_name is not None:
                self.config.command_add(command_name, broadlink_code)
                log.debug(f'Added command \'{command_name}\' with code {broadlink_code}')
        except Exception as e:
            log.error(f'Error while processing MQTT message, topic=\'{msg.topic}\' payload=\'{broadlink_code}\': {e}')

    def handle_command_add_pronto(self, msg):
        """
        topic: m2b/command/<command-name>/add_pronto
        payload: command-code
        """
        pronto_code = "invalid"
        try:
            pronto_code = str(msg.payload, 'UTF-8')
            if pronto_code is not None and len(pronto_code) > 0:
                broadlink_code = Converter.pronto_to_broadlink(pronto_code)
                m = re.search(self.message_map[self.handle_command_add_pronto], msg.topic)
                command_name = m.group(1)
                if command_name is not None:
                    self.config.command_add(command_name, broadlink_code)
                    log.debug(f'Added command \'{command_name}\' with broadlink code \'{broadlink_code}\', converted from pronto code \'{pronto_code}\'')
        except Exception as e:
            log.error(f'Error while processing MQTT message, topic=\'{msg.topic}\' payload=\'{pronto_code}\': {e}')

    def handle_command_remove(self, msg):
        """
        topic: m2b/command/<command-name>/remove
        payload: -
        """
        try:
            m = re.search(self.message_map[self.handle_command_remove], msg.topic)
            command_name = m.group(1)

            if command_name is not None:
                self.config.command_remove(command_name)
                log.debug(f'Removed command \'{command_name}\'')
        except Exception as e:
            log.error(f'Error while processing MQTT message, topic=\'{msg.topic}\': {e}')

    def handle_log_level(self, msg):
        """
        topic: m2b/log/level
        payload: [ DEBUG | INFO | WARNING | ERROR | CRITICAL ]
        """
        try:
            level = str(msg.payload, 'UTF-8')
            log.setLevel(logging.getLevelName(level))
            self.config.log_level_set(level)
            log.info(f'Set log level to {level}')

        except Exception as e:
            log.error(f'Error while processing MQTT message, topic=\'{msg.topic}\': {e}')
