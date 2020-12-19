"""
This file is based off some code originally from https://repl.it/HonoredUnconsciousInformation

"""

import binascii
import struct
from cffi.backend_ctypes import xrange, long

ProntoCodes = [
    # Power On
    "0000 006D 0022 0002 0155 00AA 0015 0015 0015 0040 0015 0040 0015 0040 0015 0040 0015 0040 0015 0040 0015 0015 0015 0040 0015 0015 0015 0015 0015 0015 0015 0015 0015 0015 0015 0015 0015 0040 0015 0040 0015 0040 0015 0040 0015 0040 0015 0040 0015 0040 0015 0040 0015 0015 0015 0015 0015 0015 0015 0015 0015 0015 0015 0015 0015 0015 0015 0015 0015 0040 0015 05ED 0155 0055 0015 0E47",
]


def pronto2lirc(pronto):
    codes = [long(binascii.hexlify(pronto[i:i + 2]), 16) for i in xrange(0, len(pronto), 2)]

    if codes[0]:
        raise ValueError('Pronto code should start with 0000')
    if len(codes) != 4 + 2 * (codes[2] + codes[3]):
        raise ValueError('Number of pulse widths does not match the preamble')

    frequency = 1 / (codes[1] * 0.241246)
    return [int(round(code / frequency)) for code in codes[4:]]


def lirc2broadlink(pulses):
    array = bytearray()

    for pulse in pulses:
        pulse = pulse * 269 / 8192  # 32.84ms units

        if pulse < 256:
            array += bytearray(struct.pack('>B', pulse))  # big endian (1-byte)
        else:
            array += bytearray([0x00])  # indicate next number is 2-bytes
            array += bytearray(struct.pack('>H', pulse))  # big endian (2-bytes)

    packet = bytearray([0x26, 0x00])  # 0x26 = IR, 0x00 = no repeats
    packet += bytearray(struct.pack('<H', len(array)))  # little endian byte count
    packet += array
    packet += bytearray([0x0d, 0x05])  # IR terminator

    # Add 0s to make ultimate packet size a multiple of 16 for 128-bit AES encryption.
    remainder = (len(packet) + 4) % 16  # rm.send_data() adds 4-byte header (02 00 00 00)
    if remainder:
        packet += bytearray(16 - remainder)

    return packet


for ProntoCode in ProntoCodes:
    pcode = ProntoCode.replace(' ', "")
    pronto = bytearray.fromhex(pcode)
    pulses = pronto2lirc(pronto)
    packet = lirc2broadlink(pulses)
    print(binascii.hexlify(packet))

