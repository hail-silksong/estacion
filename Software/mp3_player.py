"""
mp3_player.py
Control del modulo FN-M16P (compatible con el protocolo tipo DFPlayer
Mini / YX5xxx) via UART.

Trama: 7E FF 06 CMD FB PARAM1 PARAM2 CHECKSUM(2 bytes) EF
"""

from machine import UART, Pin
import time

_START = 0x7E
_VERSION = 0xFF
_LEN = 0x06
_FEEDBACK = 0x00  # 0x00 = sin feedback, 0x01 = con feedback
_END = 0xEF

CMD_NEXT = 0x01
CMD_PREV = 0x02
CMD_PLAY_TRACK = 0x03
CMD_VOLUME_UP = 0x04
CMD_VOLUME_DOWN = 0x05
CMD_SET_VOLUME = 0x06
CMD_PLAY = 0x0D
CMD_PAUSE = 0x0E
CMD_STOP = 0x16
CMD_SET_LOOP = 0x19
CMD_SELECT_SOURCE = 0x09


class MP3Player:
    def __init__(self, uart_id, tx_pin, rx_pin, baudrate=9600):
        self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        self.uart.init(baudrate, bits=8, parity=None, stop=1)
        time.sleep_ms(500)
        self.select_sd_source()

    def _checksum(self, cmd, param1, param2):
        total = _VERSION + _LEN + cmd + _FEEDBACK + param1 + param2
        return -total

    def _send(self, cmd, param1=0, param2=0):
        chk = self._checksum(cmd, param1, param2)
        frame = bytearray(
            [
                _START,
                _VERSION,
                _LEN,
                cmd,
                _FEEDBACK,
                param1,
                param2,
                (chk >> 8) & 0xFF,
                chk & 0xFF,
                _END,
            ]
        )
        self.uart.write(frame)
        time.sleep_ms(50)

    def select_sd_source(self):
        self._send(CMD_SELECT_SOURCE, 0, 2)   # 2 = tarjeta SD/TF

    def play_track(self, track_num):
        self._send(CMD_PLAY_TRACK, (track_num >> 8) & 0xFF, track_num & 0xFF)

    def play(self):
        self._send(CMD_PLAY)

    def pause(self):
        self._send(CMD_PAUSE)

    def stop(self):
        self._send(CMD_STOP)

    def next(self):
        self._send(CMD_NEXT)

    def prev(self):
        self._send(CMD_PREV)

    def set_volume(self, volume):
        """volume: 0-30"""
        volume = max(0, min(30, volume))
        self._send(CMD_SET_VOLUME, 0, volume)
    def mute(self):
        self.set_volume(0)

    def unmute(self, volume=20):
        self.set_volume(volume)