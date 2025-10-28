from os import getenv
import adafruit_connection_manager
import adafruit_requests
import board
import busio
import neopixel
from digitalio import DigitalInOut
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi.adafruit_esp32spi_wifimanager import WiFiManager

import displayio
from adafruit_matrixportal.matrixportal import MatrixPortal
import terminalio

ssid = getenv("CIRCUITPY_WIFI_SSID")
password = getenv("CIRCUITPY_WIFI_PASSWORD")
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp32 = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
for ap in esp32.scan_networks():
    print("\t%-23s RSSI: %d" % (ap.ssid, ap.rssi))
while not esp32.is_connected:
    try:
        esp32.connect_AP(ssid, password)
    except OSError as e:
        print("could not connect to AP, retrying: ", e)
        continue
print('successfully connected')

print("Ping google.com: %d ms" % esp32.ping("google.com"))

TEXT_URL = "http://wifitest.adafruit.com/testwifi/index.html"
JSON_URL = "http://wifitest.adafruit.com/testwifi/sample.json"

pool = adafruit_connection_manager.get_radio_socketpool(esp32)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(esp32)
requests = adafruit_requests.Session(pool, ssl_context)

print("Fetching text from", TEXT_URL)
r = requests.get(TEXT_URL)
message = r.text
r.close()
print("-" * 40)
print(message)
print("-" * 40)
r.close()

import rgbmatrix
import framebufferio
import adafruit_display_text.label

displayio.release_displays()
matrix = rgbmatrix.RGBMatrix(
    width=64, height=64, bit_depth=2,
    rgb_pins=[
        board.MTX_R1,
        board.MTX_G1,
        board.MTX_B1,
        board.MTX_R2,
        board.MTX_G2,
        board.MTX_B2
    ],
    addr_pins=[
        board.MTX_ADDRA,
        board.MTX_ADDRB,
        board.MTX_ADDRC,
        board.MTX_ADDRD,
        board.MTX_ADDRE
    ],
    clock_pin=board.MTX_CLK,
    latch_pin=board.MTX_LAT,
    output_enable_pin=board.MTX_OE
)
matrix.brightness = 0.00001
display = framebufferio.FramebufferDisplay(matrix)

print('LED board connected!')

line1 = adafruit_display_text.label.Label(
    terminalio.FONT,
    color=0x777777,
    text=message)
line1.x = display.width
line1.y = 8

line2 = adafruit_display_text.label.Label(
    terminalio.FONT,
    color=0xFFC72C,
    text="Hello to all CircuitPython contributors worldwide <3")
line2.x = display.width
line2.y = 40

# Put each line of text into a Group, then show that group.
g = displayio.Group()
g.append(line1)
g.append(line2)
display.root_group = g

# This function will scoot one label a pixel to the left and send it back to
# the far right if it's gone all the way off screen. This goes in a function
# because we'll do exactly the same thing with line1 and line2 below.
def scroll(line):
    line.x = line.x - 1
    line_width = line.bounding_box[2]
    if line.x < -line_width:
        line.x = display.width

# This function scrolls lines backwards.  Try switching which function is
# called for line2 below!
def reverse_scroll(line):
    line.x = line.x + 1
    line_width = line.bounding_box[2]
    if line.x >= display.width:
        line.x = -line_width

# You can add more effects in this loop. For instance, maybe you want to set the
# color of each label to a different value.
while True:
    scroll(line1)
    scroll(line2)
    #reverse_scroll(line2)
    display.refresh(minimum_frames_per_second=0)

# matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=True)
# matrixportal.set_text("Connecting", 1)
