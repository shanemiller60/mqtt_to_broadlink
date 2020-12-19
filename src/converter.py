"""
This file is based off some code originally from https://repl.it/HonoredUnconsciousInformation
"""

import binascii
import struct
from typing import List


class Converter:

    @staticmethod
    def pronto_to_broadlink(pronto_hex: str) -> str:
        pcode = pronto_hex.replace(' ', "")
        pronto = bytearray.fromhex(pcode)
        pulses = Converter.pronto_to_lirc(pronto)
        packet = Converter.lirc_to_broadlink(pulses)
        return str(binascii.hexlify(packet), 'UTF-8')

    @staticmethod
    def pronto_to_lirc(pronto: bytes) -> List[int]:
        codes = [int(binascii.hexlify(pronto[i:i + 2]), 16) for i in range(0, len(pronto), 2)]

        if codes[0]:
            raise ValueError('Pronto code should start with 0000')
        if len(codes) != 4 + 2 * (codes[2] + codes[3]):
            raise ValueError('Number of pulse widths does not match the preamble')

        frequency = 1 / (codes[1] * 0.241246)
        return [int(round(code / frequency)) for code in codes[4:]]

    @staticmethod
    def lirc_to_broadlink(pulses: List[int]) -> bytearray:
        array = bytearray()

        for pulse in pulses:
            pulse = pulse * 269 / 8192  # 32.84ms units

            if pulse < 256:
                array += bytearray(struct.pack('>B', int(pulse)))  # big endian (1-byte)
            else:
                array += bytearray([0x00])  # indicate next number is 2-bytes
                array += bytearray(struct.pack('>H', int(pulse)))  # big endian (2-bytes)

        packet = bytearray([0x26, 0x00])  # 0x26 = IR, 0x00 = no repeats
        packet += bytearray(struct.pack(b'<H', len(array)))  # little endian byte count
        packet += array
        packet += bytearray([0x0d, 0x05])  # IR terminator

        # Add 0s to make ultimate packet size a multiple of 16 for 128-bit AES encryption.
        remainder = (len(packet) + 4) % 16  # rm.send_data() adds 4-byte header (02 00 00 00)
        if remainder:
            packet += bytearray(16 - remainder)

        return packet
