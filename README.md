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

## Running

The program can be run from the command line or in a Docker container. The
Docker method is the most well tested option.

### Docker image

A [docker image](https://hub.docker.com/r/d6jyahgwk/mqtt_to_broadlink)
is available for amd64 and arm64 systems.

```bash
docker run --rm -it \
  --name "mqtt_to_broadlink" \
  -v "$(pwd)/config.ini:/service/data/config.ini" \
  d6jyahgwk/mqtt_to_broadlink:latest
```

This will use `config.ini` file from the directory where the command is run, to
work fully the `config.ini` file will need to be writable by UID 65534
(user `nobody`, group `nogroup` on many default linux installs) as the docker
image runs as that user.

The image can be built locally from a repo checkout using the
`scripts/docker_build.sh` script.

### Command line

This requires a checkout of the repository and python3, python3-pip and
optionally python3-venv to be installed before running.

```bash
git clone https://github.com/shanemiller60/mqtt_to_broadlink.git
cd mqtt_to_broadlink
python3 -m venv venv        # only if using a virtual-env
source venv/bin/activate    # only if using a virtual-env
python3 -m pip install -r requirements.txt
./scripts/run.sh
```

Commands can be learned or added by hand using IR code converters. The device
details (`<device-type> <device-ip> <device-mac>`) match the output from the
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
| `m2b/command/<command-name>/remove` | - | Removes a command code from the config |
| `m2b/log/level` | `DEBUG, INFO, WARN or ERROR` | Sets the level of messages shown in stdout |

`<command-name>` is the key of a value of an entry in the `[commands]` section of
the `config.ini`. 

`<device-name>` is the key of a value in the `[devices]` section of
`config.ini`.

`<device-ip address>` is the IP address of the RM3/4 device.

`<device-type> <device-ip> <device-mac>` is the device string produced by `broadlink_discover` CLI.

`<command-code>` is an IR code in either broadlink or pronto format as required.

### Discover a device

These examples require the `mosquitto-clients` package to be installed on a
linux system to have access to the `mosquitt_pub` program.

> mosquitto_pub -h 192.168.1.6 -t m2b/device/rm3/discover -m "192.168.1.2"

### Learning commands

> mosquitto_pub -h 192.168.1.6 -t m2b/device/rm3/learn -m command_2

This puts the IR device into learning mode, the light will come on and it
can learn a code from a remote. Learned commands are saved into the
`config.ini` file.

### Sending commands

> mosquitto_pub -h 192.168.1.6 -t m2b/device/rm3/send -m command_2

Device name (`rm3` in the example) and command name (`command_2` in the
example) must be defined in the `config.ini` file.

## `config.ini` and command codes

The config file has 3 sections, `mqtt`, `devices` and `commands`.

The `mqtt` section can have up to 5 values:

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
code databases. 

[irdb](http://irdb.tk/find/) \
[Remote Central](http://www.remotecentral.com/index.html) \
[Tasmota - Codes for IR Remotes](https://tasmota.github.io/docs/Codes-for-IR-Remotes/)

This program only saves and uses broadlink codes, they look like the example
`command_1` value above. Pronto codes can also be added manually, they look
like `0000 006C 0000 0022 00AD 00AD 0016 0041 0016 0041 ...`. NEC codes
look similar to `7F 4A` (can be longer or shorter) and they can be converted
to pronto format using the
[Yamaha IR Hex Converter](https://www.yamaha.com/ypab/irhex_converter.asp)
website.
