"""
main.py - Estación Ambiental con ESP32-S2
Novedades integradas:
  - Debouncing por software optimizado mediante temporizadores ticks_ms.
  - Salta la pantalla de bienvenida automáticamente si App Inventor se conecta
    o si presionas el botón SW1 manualmente.
  - Reproduce Pista 1 (Saludo) al arrancar.
  - Alertas de audio en carpeta 'mp3' usando play_mp3_folder(pista).
  - Servidor HTTP con soporte para comandos /mute, /unmute, /toggle_mute y /reset.
  - Control de LEDs RGB atenuados por PWM con semántica: Rojo (Crítico), Amarillo (Normal), Verde (Bajo/Noche).
"""

import time
import machine
import esp32
import json
import socket
from machine import Pin, SoftI2C

import config
import wifi
import icons
from ssd1306 import SSD1306_I2C
from bmp280 import BMP280
from sensors import DHT22Sensor, LDRSensor
from rgb_led import RGBLed
from mp3_player import MP3Player

# ---------- Bus I2C por Software ----------
i2c = SoftI2C(scl=Pin(config.I2C_SCL_PIN), sda=Pin(config.I2C_SDA_PIN), freq=100000)
print("Dispositivos I2C encontrados:", [hex(a) for a in i2c.scan()])

bmp = BMP280(i2c, addr=config.BMP280_ADDR)
oled = SSD1306_I2C(config.OLED_WIDTH, config.OLED_HEIGHT, i2c, addr=config.OLED_ADDR)

# ---------- Conectar a WiFi ----------
ip_local = wifi.connect(config.WIFI_SSID, config.WIFI_PASS)

# ---------- Servidor Web HTTP ----------
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('', 80))
server_socket.listen(2)
server_socket.settimeout(0.02)  # Timeout de 20ms

# ---------- Sensores y Actuadores ----------
dht22 = DHT22Sensor(config.DHT22_PIN)
ldr = LDRSensor(config.LDR_ADC_PIN)

# LEDs RGB con PWM suave (max_brightness=35 para regular el brillo)
led1 = RGBLed(**config.LED1_PINS, use_pwm=True, max_brightness=8)
led2 = RGBLed(**config.LED2_PINS, use_pwm=True, max_brightness=8)
led3 = RGBLed(**config.LED3_PINS, use_pwm=True, max_brightness=8)

button = Pin(config.BUTTON_PIN, Pin.IN, Pin.PULL_UP)

mp3 = MP3Player(config.MP3_UART_ID, config.MP3_TX_PIN, config.MP3_RX_PIN, config.MP3_BAUDRATE)
VOLUMEN_DEFECTO = 20
mp3.set_volume(VOLUMEN_DEFECTO)

is_muted = False
ultima_pista = None


def show_ip_screen(ip):
    oled.fill(0)
    oled.text("Estacion Lista!", 0, 0)
    oled.text("IP WiFi:", 0, 16)
    oled.text(ip if ip else "Sin Conexion", 0, 30)
    oled.text("Esperando App...", 0, 52)
    oled.show()


def show_data(temp_dht, hum, temp_bmp, pres, luz):
    oled.fill(0)
    oled.text("T:{:.1f}C".format(temp_dht or 0), 0, 0)
    oled.text("H:{:.0f}%".format(hum or 0), 0, 16)
    oled.text("P:{:.0f}hP".format(pres or 0), 0, 32)
    oled.text("Luz:{:.0f}%".format(luz or 0), 0, 48)

    if luz < 25:
        icono = "moon"
    elif (hum or 0) > 70:
        icono = "cloud"
    else:
        icono = "sun"

    icons.draw_weather_icon(oled, icono, x=94, y=18)
    oled.show()


def update_leds(luz, hum, temp_dht):
    # LED HUMEDAD (led3)
    hum = hum or 0
    if hum > 70:
        led1.red()        # Crítico (Humedad muy alta)
    elif hum >= 30:
        led1.yellow()     # Normal (30% - 70%)
    else:
        led1.green()      # Extremo bajo (< 30%)

    # LED TEMPERATURA (led2)
    temp_dht = temp_dht or 0
    if temp_dht > 30:
        led2.red()        # Crítico (Calor > 30°C)
    elif temp_dht >= 20:
        led2.yellow()     # Normal (20°C - 30°C)
    else:
        led2.green()      # Extremo bajo (Frío < 20°C)

    # LED LUZ (led1)
    luz = luz or 0
    if luz > 70:
        led3.red()        # Crítico (Luz muy alta > 70%)
    elif luz >= 30:
        led3.yellow()     # Normal (30% - 70%)
    else:
        led3.green()      # Extremo bajo (Noche / Oscuridad < 30%)


def update_track(luz, temp_dht, hum, pres, variacion_presion):
    global ultima_pista

    pista = None
    t_val = temp_dht or 0
    h_val = hum or 0
    l_val = luz or 0

    if t_val > 39:
        pista = 3
    elif t_val < 11:
        pista = 4
    elif h_val > 70:
        pista = 6
    elif h_val < 30:
        pista = 5
    elif l_val < 30:
        pista = 2
    elif variacion_presion <= -2:
        pista = 7

    if pista is not None and pista != ultima_pista:
        print("Nueva alerta de audio en carpeta 'mp3' -> {:04d}.mp3".format(pista))
        mp3.play_mp3_folder(pista)
        ultima_pista = pista


def enter_sleep():
    print("Entrando en sleep...")

    oled.poweroff()
    led1.off()
    led2.off()
    led3.off()
    mp3.pause()

    machine.lightsleep()


def handle_http_request():
    """Atiende peticiones HTTP. Devuelve True si se procesó una petición."""
    global is_muted
    try:
        conn, addr = server_socket.accept()
        raw_req = conn.recv(1024)
        if not raw_req:
            conn.close()
            return False

        req_str = raw_req.decode('utf-8')
        first_line = req_str.split('\r\n')[0]
        parts = first_line.split(' ')

        path = parts[1] if len(parts) > 1 else "/"
        action_msg = "OK"
        should_reset = False

        # --- Rutas de Control ---
        if path == "/mute":
            mp3.set_volume(0)
            is_muted = True
            action_msg = "Muted"
            print("HTTP: Mute")

        elif path == "/unmute":
            mp3.set_volume(VOLUMEN_DEFECTO)
            is_muted = False
            action_msg = "Unmuted"
            print("HTTP: Unmute")

        elif path == "/toggle_mute":
            if is_muted:
                mp3.set_volume(VOLUMEN_DEFECTO)
                is_muted = False
                action_msg = "Unmuted"
            else:
                mp3.set_volume(0)
                is_muted = True
                action_msg = "Muted"
            print("HTTP: Toggle Mute")

        elif path == "/reset":
            action_msg = "Resetting..."
            should_reset = True
            print("HTTP: Reiniciando sistema...")

        # --- Respuesta JSON ---
        payload = {
            "temp": temp_dht or 0,
            "hum": hum or 0,
            "pres": pres or 0,
            "luz": luz or 0,
            "muted": is_muted,
            "msg": action_msg
        }

        response_body = json.dumps(payload)
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "Connection: close\r\n\r\n" + response_body
        )

        conn.sendall(response.encode('utf-8'))
        conn.close()

        if should_reset:
            time.sleep_ms(500)
            machine.reset()

        return True  # Petición atendida con éxito

    except OSError:
        return False  # Sin peticiones entrantes


# ==============================================================================
#  PASO INICIAL: Mostrar IP y esperar pulsación de SW1 O conexión de la App
# ==============================================================================
show_ip_screen(ip_local)
print("Esperando conexión de App Inventor o pulsación de SW1...")

temp_dht, hum, temp_bmp, pres, luz = 0, 0, 0, 0, 0

pres_anterior = None
variacion_presion = 0

time.sleep_ms(300)
while button.value() == 1:
    if handle_http_request():
        print("¡Petición de App Inventor detectada! Omitiendo botón SW1...")
        break
    time.sleep_ms(30)

if button.value() == 0:
    while button.value() == 0:
        time.sleep_ms(30)
    time.sleep_ms(200)

print("Cargando interfaz principal...")

# --- Reproducir Pista de Saludo / Bienvenida (0001.mp3 en carpeta 'mp3') ---

print("Reproduciendo Saludo Inicial (0001.mp3)...")
mp3.play_mp3_folder(1)
ultima_pista = 1
time.sleep_ms(300)


# ==============================================================================
#  BUCLE PRINCIPAL (Monitoreo)
# ==============================================================================
# Variables para Debouncing
LONG_PRESS_MS = 1500
DEBOUNCE_MS = 30

debounced_state = 1
last_raw_state = 1
last_debounce_time = 0

press_start_time = 0
is_pressing = False
long_press_handled = False

last_read = 0

sleeping = False
SLEEP_FREQ = 80_000_000
NORMAL_FREQ = 240_000_000

while True:
    now = time.ticks_ms()
    raw_state = button.value()

    # --- 1. DEBOUNCING DEL BOTÓN ---
    if raw_state != last_raw_state:
        last_debounce_time = now
        last_raw_state = raw_state

    if time.ticks_diff(now, last_debounce_time) > DEBOUNCE_MS:
        if raw_state != debounced_state:
            debounced_state = raw_state

            # Flanco de bajada (Presionado)
            if debounced_state == 0:
                is_pressing = True
                press_start_time = now
                long_press_handled = False

            # Flanco de subida (Soltado)
            elif debounced_state == 1:
                if is_pressing and not long_press_handled:
                    # Pulsación corta: Mute / Unmute
                    if is_muted:
                        mp3.set_volume(VOLUMEN_DEFECTO)
                        is_muted = False
                        print("Audio: Unmute")
                    else:
                        mp3.set_volume(0)
                        is_muted = True
                        print("Audio: Mute")

                is_pressing = False

    # --- 2. DETECCIÓN DE PULSACIÓN LARGA ---
    if is_pressing and not long_press_handled and debounced_state == 0:
        if time.ticks_diff(now, press_start_time) >= LONG_PRESS_MS:
            long_press_handled = True
            is_pressing = False

            if not sleeping:
                print("Entrando en modo ahorro...")
                oled.poweroff()
                led1.off()
                led2.off()
                led3.off()
                mp3.pause()

                machine.freq(SLEEP_FREQ)
                sleeping = True

    # ==========================================================
    # MODO AHORRO
    # ==========================================================
    if sleeping:
        # Si se presiona el botón para despertar
        if debounced_state == 0 and is_pressing and not long_press_handled:
            long_press_handled = True
            is_pressing = False

            print("Saliendo del modo ahorro...")
            machine.freq(NORMAL_FREQ)

            oled.poweron()
            oled.fill(0)
            oled.show()

            sleeping = False

            # Esperar debouncing para evitar lecturas fantasmas al salir
            time.sleep_ms(200)

        handle_http_request()
        time.sleep_ms(20)
        continue

    # ==========================================================
    # LECTURA DE SENSORES Y PANTALLA
    # ==========================================================
    if time.ticks_diff(now, last_read) > 2000 or last_read == 0:

        temp_dht, hum = dht22.read()
        temp_bmp, pres = bmp.read()
        luz = ldr.read_percent()
0
        if pres_anterior is not None and pres is not None:
            variacion_presion = pres - pres_anterior

        pres_anterior = pres

        show_data(temp_dht, hum, temp_bmp, pres, luz)
        update_track(luz, temp_dht, hum, pres, variacion_presion)
        update_leds(luz, hum, temp_dht)

        print(
            "DHT22: {}C {}% | BMP280: {:.1f}C {:.1f}hPa (Var: {:.1f}) | Luz: {}% | Pista: {}".format(
                temp_dht,
                hum,
                temp_bmp,
                pres,
                variacion_presion,
                luz,
                ultima_pista,
            )
        )

        last_read = now

    handle_http_request()
    time.sleep_ms(20) 
