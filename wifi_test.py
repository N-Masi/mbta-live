from os import getenv
import board
import busio
import neopixel
from digitalio import DigitalInOut
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi.adafruit_esp32spi_wifimanager import WiFiManager

ssid = getenv("CIRCUITPY_WIFI_SSID")
password = getenv("CIRCUITPY_WIFI_PASSWORD")

esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp32 = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

status_pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)

wifi = WiFiManager(esp32, ssid, password, status_pixel=status_pixel)

API_ADDR = "https://api-v3.mbta.com/routes/83"

response = None
while not response:
    try:
        print("Fetching json from", API_ADDR)
        response = wifi.get(API_ADDR)
        break
    except OSError as e:
        print("Failed to get data, retrying\n", e)
        continue

json = response.json()
route_name = json['data']['attributes']['long_name']

print(route_name)
