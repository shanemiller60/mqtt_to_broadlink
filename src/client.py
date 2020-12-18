from typing import Optional, Dict
import re
import paho.mqtt.client as mqtt
from src.config import Config
from src.device import Device


class Client:
    mqtt: mqtt.Client
    config: Config
    devices: Dict[str, Device]

    def __init__(self, config: Config):
        self.mqtt = mqtt.Client()
        self.config = config
        self.mqtt.on_connect = self.on_connect
        self.mqtt.on_message = self.on_message
        self.devices = {}

        for device_name in self.config.get_device_names():
            self.get_device(device_name)

    def get_device(self, device_name: str) -> Optional[Device]:
        device = self.devices.get(device_name)
        if device is None:
            (devtype, host, mac) = self.config.get_device_details(device_name)
            try:
                device = Device(device_name, devtype, host, mac)
                self.devices[device_name] = device
            except:
                print(f'Could not open device \'{device_name}\'')
        return device

    def connect(self) -> None:
        mqtt_details = self.config.get_mqtt_details()
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
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        for device in self.config.get_device_names():
            client.subscribe(device + "/command/send")
            client.subscribe(device + "/command/run")
            client.subscribe(device + "/command/learn")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, _, msg):
        if msg.topic.endswith("/command/run") or msg.topic.endswith("/command/send"):
            self.handle_send_command(msg)
        elif msg.topic.endswith("/command/learn"):
            self.handle_learn(msg)

    def handle_send_command(self, msg):
        command_name = str(msg.payload, 'UTF-8')
        hex_code = self.config.get_command(command_name)
        if hex_code is None:
            print(f'Received request for unknown command \'{command_name}\'')
            return
        try:
            m = re.search('(.*)/command/[run|send]', msg.topic)
            device_name = m.group(1) or ''
            device = self.get_device(device_name)
            if device is not None:
                device.send_code(hex_code)
            else:
                print(f'Could not open/connect to device \'{device_name}\'')
        except:
            print(f'Error while processing MQTT message, topic=\'{msg.topic}\' payload=\'{command_name}\'')

    def handle_learn(self, msg):
        command_name = str(msg.payload, 'UTF-8')
        try:
            m = re.search('(.*)/command/learn', msg.topic)
            device_name = m.group(1) or ''
            device = self.get_device(device_name)
            if device is not None:
                hex_code = device.learn_code()
                if hex_code is not None:
                    print(f'{device_name}: Learned code \'{hex_code}\', saved as command \'{command_name}\'')
                    self.config.save_command(command_name, hex_code)
                else:
                    print('No code received')
            else:
                print(f'Could not open/connect to device \'{device_name}\'')
        except:
            print(f'Error while processing MQTT message, topic=\'{msg.topic}\' payload=\'{command_name}\'')
