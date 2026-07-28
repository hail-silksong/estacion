"""
bmp280.py
Driver minimo para el sensor BMP280 (presion / temperatura) por I2C,
MicroPython.

NOTA IMPORTANTE (ver esquematico): el pin CSB debe estar a VCC para
que el sensor trabaje en modo I2C (en el esquema aparece flotante,
revisalo). El pin SDO define la direccion I2C:
    SDO -> GND : 0x76
    SDO -> VCC : 0x77
En el esquema SDO tampoco aparece conectado; confirma la direccion
real probando 0x76 y 0x77 si falla la comunicacion.
"""

from micropython import const
import time

_REG_ID = const(0xD0)
_REG_RESET = const(0xE0)
_REG_CTRL_MEAS = const(0xF4)
_REG_CONFIG = const(0xF5)
_REG_PRESS = const(0xF7)
_REG_TEMP = const(0xFA)
_REG_CALIB = const(0x88)


class BMP280:
    def __init__(self, i2c, addr=0x77):
        self.i2c = i2c
        self.addr = addr
        chip_id = self.i2c.readfrom_mem(self.addr, _REG_ID, 1)[0]
        if chip_id != 0x58:
            raise RuntimeError(
                "BMP280 no encontrado en 0x%02X (chip id=0x%02X)" % (addr, chip_id)
            )
        self._read_calibration()
        # modo normal, oversampling x1 en temp y presion
        self.i2c.writeto_mem(self.addr, _REG_CTRL_MEAS, bytes([0x27]))
        self.i2c.writeto_mem(self.addr, _REG_CONFIG, bytes([0xA0]))
        self.t_fine = 0

    def _read_calibration(self):
        data = self.i2c.readfrom_mem(self.addr, _REG_CALIB, 24)

        def u16(o):
            return data[o] | (data[o + 1] << 8)

        def s16(o):
            v = u16(o)
            return v - 65536 if v > 32767 else v

        self.dig_T1 = u16(0)
        self.dig_T2 = s16(2)
        self.dig_T3 = s16(4)
        self.dig_P1 = u16(6)
        self.dig_P2 = s16(8)
        self.dig_P3 = s16(10)
        self.dig_P4 = s16(12)
        self.dig_P5 = s16(14)
        self.dig_P6 = s16(16)
        self.dig_P7 = s16(18)
        self.dig_P8 = s16(20)
        self.dig_P9 = s16(22)

    def _raw(self):
        data = self.i2c.readfrom_mem(self.addr, _REG_PRESS, 6)
        raw_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        raw_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        return raw_t, raw_p

    def read(self):
        """Devuelve (temperatura_C, presion_hPa)."""
        raw_t, raw_p = self._raw()

        # compensacion temperatura
        var1 = (raw_t / 16384.0 - self.dig_T1 / 1024.0) * self.dig_T2
        var2 = ((raw_t / 131072.0 - self.dig_T1 / 8192.0) ** 2) * self.dig_T3
        self.t_fine = var1 + var2
        temperature = self.t_fine / 5120.0

        # compensacion presion
        var1 = self.t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * self.dig_P6 / 32768.0
        var2 = var2 + var1 * self.dig_P5 * 2.0
        var2 = var2 / 4.0 + self.dig_P4 * 65536.0
        var1 = (self.dig_P3 * var1 * var1 / 524288.0 + self.dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.dig_P1
        if var1 == 0:
            pressure = 0
        else:
            p = 1048576.0 - raw_p
            p = (p - var2 / 4096.0) * 6250.0 / var1
            var1 = self.dig_P9 * p * p / 2147483648.0
            var2 = p * self.dig_P8 / 32768.0
            pressure = (p + (var1 + var2 + self.dig_P7) / 16.0) / 100.0  # hPa

        return temperature, pressure


# ==============================================================================
# PRUEBA STANDALONE / EJECUCIÓN DIRECTA
# ==============================================================================
if __name__ == "__main__":
    from machine import Pin, SoftI2C
    import config  # Intenta importar pines de config si existe

    print("--- Modo de prueba individual: BMP280 ---")

    # Obtención de pines del archivo config o asignación por defecto para ESP32-S2
    try:
        scl_pin = config.I2C_SCL_PIN
        sda_pin = config.I2C_SDA_PIN
    except (ImportError, AttributeError):
        scl_pin = 9
        sda_pin = 8

    # Inicialización del bus I2C por software a 50 kHz para evitar errores de ruido
    i2c = SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin), freq=50000)

    devices = i2c.scan()
    print("Dispositivos detectados en bus I2C:", [hex(d) for d in devices])

    # Detección automática de la dirección (0x77 o 0x76)
    sensor = None
    for addr in [0x77, 0x76]:
        if addr in devices:
            try:
                sensor = BMP280(i2c, addr=addr)
                print("¡BMP280 inicializado con éxito en la dirección 0x%02X!" % addr)
                break
            except Exception as e:
                print("Error al conectar en 0x%02X: %s" % (addr, e))

    if not sensor:
        print("ERROR: No se encontró ningún sensor BMP280 funcional en el bus I2C.")
    else:
        print("\nIniciando lecturas continuas (Presiona Ctrl+C para detener):")
        try:
            while True:
                temp, pres = sensor.read()
                print("Temperatura: {:.2f} °C | Presión: {:.2f} hPa".format(temp, pres))
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nPrueba finalizada por el usuario.")
            