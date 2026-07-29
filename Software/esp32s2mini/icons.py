"""
icons.py - Dibujo de iconos climaticos (Sol, Luna, Nube)
para pantalla OLED SSD1306 en MicroPython.
"""
def fill_circle(oled, cx, cy, r):
    r2 = r * r
    for y in range(-r, r + 1):
        for x in range(-r, r + 1):
            if x * x + y * y <= r2:
                oled.pixel(cx + x, cy + y, 1)

def draw_sun(oled, x=94, y=18):
    """Dibuja un sol brillante."""
    # Centro del sol
    oled.fill_rect(x + 10, y + 10, 8, 8, 1)
    
    # Rayos (Arriba, Abajo, Izquierda, Derecha)
    oled.vline(x + 13, y + 3, 5, 1)
    oled.vline(x + 14, y + 3, 5, 1)
    oled.vline(x + 13, y + 20, 5, 1)
    oled.vline(x + 14, y + 20, 5, 1)
    
    oled.hline(x + 3, y + 13, 5, 1)
    oled.hline(x + 3, y + 14, 5, 1)
    oled.hline(x + 20, y + 13, 5, 1)
    oled.hline(x + 20, y + 14, 5, 1)
    
    # Rayos diagonales
    oled.line(x + 5, y + 5, x + 8, y + 8, 1)
    oled.line(x + 22, y + 5, x + 19, y + 8, 1)
    oled.line(x + 5, y + 22, x + 8, y + 19, 1)
    oled.line(x + 22, y + 22, x + 19, y + 19, 1)
    

def draw_moon(oled, x=94, y=18):
    """Dibuja una luna creciente suave usando la intersección de dos círculos."""
    cx_outer, cy_outer, r_outer = x + 13, y + 13, 11  # Círculo principal
    cx_inner, cy_inner, r_inner = x + 17, y + 9, 9    # Círculo de sombra

    r_outer_sq = r_outer * r_outer
    r_inner_sq = r_inner * r_inner

    # Recorremos la cuadrícula del icono (24x24 píxeles)
    for dx in range(-r_outer, r_outer + 1):
        for dy in range(-r_outer, r_outer + 1):
            px = cx_outer + dx
            py = cy_outer + dy

            # Pertenece al cuerpo de la luna si está DENTRO del círculo exterior
            # y FUERA del círculo de sombra
            in_outer = (dx * dx + dy * dy) <= r_outer_sq
            
            idx = px - cx_inner
            idy = py - cy_inner
            out_inner = (idx * idx + idy * idy) > r_inner_sq

            if in_outer and out_inner:
                oled.pixel(px, py, 1)


def draw_cloud(oled, x=94, y=18):
    oled.fill_rect(x + 7, y + 11, 20, 7, 1)

    fill_circle(oled, x + 7,  y + 14, 4)
    fill_circle(oled, x + 13, y + 11, 6)
    fill_circle(oled, x + 20, y + 10, 7)
    fill_circle(oled, x + 26, y + 13, 4)


def draw_weather_icon(oled, icon_type, x=94, y=18):
    """Función principal para seleccionar qué icono dibujar."""
    if icon_type == "sun":
        draw_sun(oled, x, y)
    elif icon_type == "moon":
        draw_moon(oled, x, y)
    elif icon_type == "cloud":
        draw_cloud(oled, x, y)
    
if __name__ == "__main__":
    import config
    from machine import Pin, SoftI2C
    from ssd1306 import SSD1306_I2C
    import time

    # Ajusta estos pines a los tuyos
    i2c = SoftI2C(scl=Pin(config.I2C_SCL_PIN), sda=Pin(config.I2C_SDA_PIN), freq=100000)
    oled = SSD1306_I2C(config.OLED_WIDTH, config.OLED_HEIGHT, i2c, addr=config.OLED_ADDR)

    icons = ["sun", "moon", "cloud"]

    while True:
        for icon in icons:
            oled.fill(0)
            draw_weather_icon(oled, icon, 52, 20)  # Centrado aproximadamente
            oled.show()
            time.sleep(1)