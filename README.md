# MQTT to Broadlink

This project links MQTT messages to commands on Broadlink RM3/4 remote IR
devices. It relies on the [python-broadlink](https://github.com/mjg59/python-broadlink)
project to communicate with the broadlink devices and uses
[paho-mqtt](https://pypi.org/project/paho-mqtt/) to process MQTT messages.

## Setup

All configuration is stored in the `data/config.ini` file, it has details for
connecting to a MQTT broker, details for connecting to the broadlink devices
and details of known command codes.

A minimal config could look like this:

```ini
[mqtt]
host = 192.168.1.6

[devices]
rm3 = 0x5f36 192.168.1.2 aaaaaaaaaaaa

[commands]
command_1 = 2600660072380e0e0e2a0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e2a0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e2a0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e2a0e2a0e2a0e2a0e2a0e2a0e0e0e0e0e2a0e2a0e2a0e2a0e2a0e2a0e0e0e2a0e00097b0d05
```

Commands can be learned or added by hand using IR code converters. The device
details (\<device-type\> \<device-ip\> \<device-mac\>) match the output from the
`broadlink_discovery` tool.

## MQTT interface / topics

The program listens on the following topics:

* <device_name>/command/send
* <device_name>/command/learn

and expects the payload to be a command name, when sending the command name
must be the key of a value in the `[commands]` section of the `config.ini`.
When learning the command name will be used to save the code as a command in
`config.ini`.

`<device_name>` is the key of a value in the `[devices]` section of
`config.ini`.

### Learning commands

> mosquitto_pub -h 192.168.1.6 -t rm3/command/learn -m command_2

Learned commands are saved into the `config.ini` file.

### Sending commands

> mosquitto_pub -h 192.168.1.6 -t rm3/command/send -m command_1


## `config.ini`

## Docker image

A docker image is available for amd64 and arm64 systems.

```bash
docker run --rm -d \
  -v "$(pwd)/config.ini:/service/data/config.ini" \
  d6jyahgwk/mqtt_to_broadlink:latest
```

This will use `config.ini` file from the directory where the command is run.
