"""
config.py
Mapeo de pines del ESP32-S2 (WeMos S2 mini) segun el esquematico.
Pines confirmados por el usuario a partir del archivo fuente real.

IMPORTANTE - pendiente de revisar en hardware:
- El esquematico muestra el segundo y tercer LED RGB ambos como "D5"
  (referencia duplicada). Aqui se asume que son D3, D4, D5 en orden.
  Confirma cual es realmente D4.
- Los LEDs RGB no tienen resistencia limitadora en el esquema: se
  recomienda anadir ~220-330 ohm en serie con cada linea R/G/B.
- CSB y SDO del BMP280 no se ven conectados: CSB debe ir a VCC (modo
  I2C) y SDO define la direccion (GND->0x76, VCC->0x77).
- R1 (pull-up del DHT22) aparece como 1k, se recomienda 4.7k-10k.
"""

# ---------- Bus I2C (OLED SSD1306 + BMP280) ----------
I2C_ID = 0
I2C_SDA_PIN = 8
I2C_SCL_PIN = 9
I2C_FREQ = 100_000

BMP280_ADDR = 0x77   # depende de SDO: GND->0x76, VCC->0x77 (verificar en tu placa)
OLED_ADDR = 0x3C      # direccion tipica SSD1306, ajustar si es distinta
OLED_WIDTH = 128
OLED_HEIGHT = 64

# ---------- LDR (fotorresistencia) ----------
# Divisor R2 (LDR07) - R3 (10k), punto medio a GPIO3 (ADC1_CH2)
LDR_ADC_PIN = 3


# ---------- Red WiFi ----------
#WIFI_SSID = "realme 14 5G g9yb"
#WIFI_PASS = "Jack2019"
WIFI_SSID = "FAMILIA HERNANDEZ"
WIFI_PASS = "A1b0302774"
# ---------- DHT22 ----------
DHT22_PIN = 5   # pull-up R1 (ver nota: valor de 1k es bajo, ideal 4.7k-10k)

# ---------- Boton SW1 ----------
BUTTON_PIN = 14   # a GND, usar pull-up interno (activo en bajo)

# ---------- FN-M16P (reproductor MP3, protocolo tipo DFPlayer) ----------
# RX del modulo -> GPIO11 del ESP32 (por lo tanto GPIO11 = TX del ESP32)
# TX del modulo -> GPIO12 del ESP32 (por lo tanto GPIO12 = RX del ESP32)
MP3_UART_ID = 1
MP3_TX_PIN = 11   # ESP32 TX -> RX del modulo
MP3_RX_PIN = 12   # ESP32 RX <- TX del modulo
MP3_BAUDRATE = 9600

# ---------- LEDs RGB (D3, D4, D5) - anodo comun -> logica activa en BAJO ----------
# ---------- LEDs RGB (D3, D4, D5) ----------
LED1_PINS = dict(r_pin=21, g_pin=34, b_pin=33)   # D3
LED2_PINS = dict(r_pin=35, g_pin=39, b_pin=36)   # D4
LED3_PINS = dict(r_pin=38, g_pin=40, b_pin=39)   # D5