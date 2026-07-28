"""
sensors.py
Manejo del DHT22 (temperatura/humedad) y del LDR (luz ambiente).
"""

import dht
from machine import Pin, ADC


class DHT22Sensor:
    def __init__(self, pin_num):
        self.sensor = dht.DHT22(Pin(pin_num))

    def read(self):
        """Devuelve (temperatura_C, humedad_%) o (None, None) si falla."""
        try:
            self.sensor.measure()
            return self.sensor.temperature(), self.sensor.humidity()
        except OSError as e:
            print("Error leyendo DHT22:", e)
            return None, None


class LDRSensor:
    def __init__(self, pin_num):
        self.adc = ADC(Pin(pin_num))
        self.adc.atten(ADC.ATTN_11DB)  

    def read_raw(self):
        return self.adc.read()

    def read_percent(self):
        """0 = oscuridad total, 100 = luz maxima (aprox, calibrar segun LDR)."""
        raw = self.read_raw()
        return round(raw / 8050 * 100, 1)
