"""
rgb_led.py
Control de LEDs RGB de anodo comun (D3, D4, D5) segun el esquematico.

Como son de anodo comun (pin comun a +3V3), la logica es INVERTIDA:
  - GPIO en 0 (bajo)  -> LED encendido
  - GPIO en 1 (alto)  -> LED apagado

RECORDATORIO: el esquema no muestra resistencias limitadoras en serie
con R/G/B. Anade ~220-330 ohm en cada linea para no danar los LEDs ni
sobrecargar los pines del ESP32-S2.
"""

from machine import Pin, PWM


class RGBLed:
    def __init__(self, r_pin, g_pin, b_pin, use_pwm=True):
        self.use_pwm = use_pwm
        if use_pwm:
            self.r = PWM(Pin(r_pin, Pin.OUT), freq=1000)
            self.g = PWM(Pin(g_pin, Pin.OUT), freq=1000)
            self.b = PWM(Pin(b_pin, Pin.OUT), freq=1000)
            self.off()
        else:
            self.r = Pin(r_pin, Pin.OUT, value=1)
            self.g = Pin(g_pin, Pin.OUT, value=1)
            self.b = Pin(b_pin, Pin.OUT, value=1)

    def set_color(self, r, g, b):
        """r,g,b en rango 0-255. 0 = apagado, 255 = brillo maximo."""
        if self.use_pwm:
            # anodo comun -> invertir duty (255 -> duty 0, 0 -> duty max)
            self.r.duty_u16(int((255 - r) / 255 * 65535))
            self.g.duty_u16(int((255 - g) / 255 * 65535))
            self.b.duty_u16(int((255 - b) / 255 * 65535))
        else:
            self.r.value(0 if r else 1)
            self.g.value(0 if g else 1)
            self.b.value(0 if b else 1)

    def off(self):
        self.set_color(0, 0, 0)

    def red(self):
        self.set_color(255, 0, 0)

    def green(self):
        self.set_color(0, 255, 0)

    def blue(self):
        self.set_color(0, 0, 255)

    def white(self):
        self.set_color(255, 255, 255)

if __name__ == "__main__":
    from time import sleep

    # Cambia los pines si son diferentes
    led1 = RGBLed(r_pin=38, g_pin=40, b_pin=39, use_pwm=True)
    led2 = RGBLed(r_pin=35, g_pin=37, b_pin=36, use_pwm=True)
    led3 = RGBLed(r_pin=21, g_pin=34, b_pin=33, use_pwm=True)

    print("Prueba de LED RGB")

    # Colores básicos
    pruebas = [
        ("Rojo", (255, 0, 0)),
        ("Verde", (0, 255, 0)),
        ("Azul", (0, 0, 255)),
        ("Amarillo", (255, 255, 0)),
        ("Cian", (0, 255, 255)),
        ("Magenta", (255, 0, 255)),
        ("Blanco", (255, 255, 255)),
        ("Apagado", (0, 0, 0)),
    ]

    while True:
        print("Prueba de colores...")
        for nombre, color in pruebas:
            print(nombre)
            led1.set_color(*color)
            led2.set_color(*color)
            led3.set_color(*color)
            sleep(1)

        print("Fundido Rojo")
        for i in range(256):
            led1.set_color(i, 0, 0)
            sleep(0.005)
        for i in range(255, -1, -1):
            led1.set_color(i, 0, 0)
            sleep(0.005)

        print("Fundido Verde")
        for i in range(256):
            led1.set_color(0, i, 0)
            sleep(0.005)
        for i in range(255, -1, -1):
            led1.set_color(0, i, 0)
            sleep(0.005)

        print("Fundido Azul")
        for i in range(256):
            led1.set_color(0, 0, i)
            sleep(0.005)
        for i in range(255, -1, -1):
            led1.set_color(0, 0, i)
            sleep(0.005)