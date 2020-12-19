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

| Topic | Payload | Description |
| --- | --- | --- |
| `m2b/device/<device-name>/send` | `<command-name>` | Sends a command through the device |
| `m2b/device/<device-name>/learn` | `<command-name>` | Learns a command through the device and saves the code to the config |
| `m2b/device/<device-name>/discover` | `<device-ip address>` | Attempts to discover a device and save its details to the config |
| `m2b/device/<device-name>/add` | `<device-type> <device-ip> <device-mac>` | Adds a device to the config from a known device string |
| `m2b/device/<device-name>/remove` | - | Removes the device from the config |
| `m2b/command/<command-name>/add` | `<command-code>` | Adds a broadlink code to the config |
| `m2b/command/<command-name>/add_pronto` | `<command-code>` | Adds a pronto-hex code to the config |
| `m2b/command/<command-name>/add_nec` | `<command-code>` | Adds a pronto-hex code to the config |
| `m2b/command/<command-name>/remove` | - | Removes a command code from the config |

`<command-name>` is the key of a value of an entry in the `[commands]` section of
the `config.ini`. 

`<device-name>` is the key of a value in the `[devices]` section of
`config.ini`.

`<device-ip address>` is the IP address of the RM3/4 device.

`<device-type> <device-ip> <device-mac>` is the device string produced by `broadlink_discover` CLI.

### Learning commands

> mosquitto_pub -h 192.168.1.6 -t m2b/device/rm3/learn -m command_2

Learned commands are saved into the `config.ini` file.

### Sending commands

> mosquitto_pub -h 192.168.1.6 -t m2b/device/rm3/send -m command_1

Device name (`rm3` in the example) and command name (`command_1` in the
example) must be defined in the `config.ini` file.

## `config.ini`

The config file has 3 sections, `mqtt`, `devices` and `commands`.

The `mqtt` section can have upto 5 values:

| Name | Default | Notes |
| --- | --- | --- |
| host | - | Required |
| port | 1883 | Optional |
| user | '' | Optional |
| pass | '' | Optional |
| prefix | `m2b` | Optional, this is added to the start of all topics used by this program |

The `devices` section has 1 value for each device under control, the name of
the device is the key and the `broadlink_discovery` output is the value.

```ini
[devices]
rm3_1 = 0x5f36 192.168.1.11 aaaaaaaaaaaa
rm3_2 = 0x5f36 192.168.1.12 aaaaaaaaaaab
...
rm3_n = 0x5f36 192.168.1.19 aaaaaaaaaaaf

# General format is:
<device-name> = <device-type> <device-ip> <device-mac>
```

The `commands` section lists each command that can be sent to any of the
devices.

```ini
[commands]
command_1 = 2600660072380e0e0e2a0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e2a0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e2a0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e2a0e2a0e2a0e2a0e2a0e2a0e0e0e0e0e2a0e2a0e2a0e2a0e2a0e2a0e0e0e2a0e00097b0d05

# General format is:
<command-name> = <command-code>
```

Command codes can be learned by the device, or built manually from available
code libraries. 

[Tasmota - Codes for IR Remotes](https://tasmota.github.io/docs/Codes-for-IR-Remotes/) \
[Remote Central](http://www.remotecentral.com/index.html)

[Yamaha IR Hex Converter](https://www.yamaha.com/ypab/irhex_converter.asp)

This project may include some tools to do code conversions in the future.

## Docker image

A [docker image](https://hub.docker.com/repository/docker/d6jyahgwk/mqtt_to_broadlink)
is available for amd64 and arm64 systems.

```bash
docker run --rm -d \
  -v "$(pwd)/config.ini:/service/data/config.ini" \
  d6jyahgwk/mqtt_to_broadlink:latest
```

This will use `config.ini` file from the directory where the command is run, to
work fully the `config.ini` file will need to be writable by UID 65534
(user `nobody` on many default linux installs) as the docker image runs as that
user.
