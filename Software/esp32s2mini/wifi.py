"""
wifi.py - Conexión robusta compatible con despertares de Deep Sleep
"""

import network
import time

def connect(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if wlan.isconnected():
        return wlan.ifconfig()[0]

    print("Conectando a WiFi:", ssid)
    
    # Forzar desconexión previa para limpiar estados colgados post-deepsleep
    try:
        wlan.disconnect()
        time.sleep_ms(200)
    except Exception:
        pass

    wlan.connect(ssid, password)
    
    # Dar hasta 15 intentos (15 segundos)
    for _ in range(15):
        if wlan.isconnected():
            ip = wlan.ifconfig()[0]
            print("¡Conectado a WiFi! IP asignada:", ip)
            return ip
        time.sleep(1)

    print("Error: No se pudo conectar a la red WiFi")
    return None