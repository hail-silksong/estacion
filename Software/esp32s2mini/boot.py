"""
boot.py
Se ejecuta al arrancar el ESP32-S2, antes de main.py.
"""

import gc
import machine

gc.collect()
# Descomenta si quieres desactivar el modo REPL por webrepl, etc.
# import webrepl
# webrepl.start()

print("Arranque OK - ESP32-S2 listo, entrando a main.py")
