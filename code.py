from os import getenv
import rtc
import time
from adafruit_datetime import datetime, timezone, timedelta
import board
import busio
from digitalio import DigitalInOut
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_connection_manager
import adafruit_requests
import displayio
from adafruit_bitmap_font import bitmap_font
import rgbmatrix
import framebufferio
import adafruit_display_text.label

# constants
G = displayio.Group() # TODO: a global, not a constant
TIME_URL = "https://worldtimeapi.org/api/ip"
FONT = bitmap_font.load_font("fonts/4x6_kujala.pcf")
CENTRAL_83_URL = f"http://api-v3.mbta.com/predictions?api_key={getenv("MBTA_API_KEY")}&page[limit]=1&filter[route]=83&filter[stop]=2437"
PORTER_83_URL = f"http://api-v3.mbta.com/predictions?api_key={getenv("MBTA_API_KEY")}&page[limit]=1&filter[route]=83&filter[stop]=2453"
print(CENTRAL_83_URL)
HEADERS = {"user-agent": "mbta-tracker"}
WIFI_DEBUG = True

# setup LED board
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
display = framebufferio.FramebufferDisplay(matrix)
display.root_group = G
led_msg = adafruit_display_text.label.Label(
    FONT,
    color=0x777777,
    text='LED: on',
    x=1,
    y=8)
G.append(led_msg)
display.refresh()
print(led_msg.text)

# connect to wifi
ssid = getenv("CIRCUITPY_WIFI_SSID")
password = getenv("CIRCUITPY_WIFI_PASSWORD")
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp32 = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset, debug=WIFI_DEBUG)
while not esp32.is_connected:
    try:
        esp32.connect_AP(ssid, password)
    except OSError as e:
        print("could not connect to AP, retrying: ", e)
        continue
wifi_msg = adafruit_display_text.label.Label(
    FONT,
    color=0x777777,
    text='Lighthouse: on',
    x=1,
    y=16)
G.append(wifi_msg)
display.refresh()
print(wifi_msg.text)

if esp32.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("ESP32 found and in idle mode")
print("Firmware vers.", esp32.firmware_version)
print("MAC addr:", ":".join("%02X" % byte for byte in esp32.MAC_address))

# establish http connection
pool = adafruit_connection_manager.get_radio_socketpool(esp32)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(esp32)
requests = adafruit_requests.Session(pool, ssl_context)
http_msg = adafruit_display_text.label.Label(
    FONT,
    color=0x777777,
    text='HTTP: on',
    x=1,
    y=24)
G.append(http_msg)
display.refresh()
print(http_msg.text)

# calibrate onboard clock
the_rtc = rtc.RTC()

# get realtime
response = requests.get(TIME_URL, headers=HEADERS)
print(response.headers)
json = response.json()
response.close()
current_time = json["datetime"]
the_date, the_time = current_time.split("T")
year, month, mday = (int(x) for x in the_date.split("-"))
the_time = the_time.split(".")[0]
hours, minutes, seconds = (int(x) for x in the_time.split(":"))
year_day = json["day_of_year"]
week_day = json["day_of_week"]
is_dst = json["dst"]
now = time.struct_time((year, month, mday, hours, minutes, seconds, week_day, year_day, is_dst))
the_rtc.datetime = now
time_msg = adafruit_display_text.label.Label(
    FONT,
    color=0x777777,
    text='Realtime: on',
    x=1,
    y=32)
G.append(time_msg)
display.refresh()
print(time_msg.text)

time.sleep(5)
G.remove(led_msg)
G.remove(wifi_msg)
G.remove(http_msg)
G.remove(time_msg)

# reset screen
central_83_msg = adafruit_display_text.label.Label(
    FONT,
    color=0xFFC72C,
    text=f'83 Central: ---',
    x=1,
    y=8)
porter_83_msg = adafruit_display_text.label.Label(
    FONT,
    color=0xFFC72C,
    text=f'83 Porter: ---',
    x=1,
    y=16)
G.append(central_83_msg)
G.append(porter_83_msg)
display.refresh()

while True:
    now = datetime.now()
    response = requests.get(CENTRAL_83_URL)
    central_83 = response.json()
    response.close()
    response = requests.get(PORTER_83_URL)
    porter_83 = response.json()
    response.close()

    if len(central_83['data']) > 0:
        next_central_timestamp = central_83['data'][0]['attributes']['arrival_time']
        next_central_time = datetime.fromisoformat(next_central_timestamp).replace(tzinfo = None) # this hack only works because the local time is in the same timezone as the train stations
        central_wait = (next_central_time - now).seconds // 60
        central_83_msg.text = f'83 Central: {central_wait}m'
    else:
        central_83_msg.text = f'83 Central: tmrw'

    if len(porter_83['data']) > 0:
        next_porter_timestamp = porter_83['data'][0]['attributes']['arrival_time']
        next_porter_time = datetime.fromisoformat(next_porter_timestamp).replace(tzinfo = None)
        porter_wait = (next_porter_time - now).seconds // 60
        porter_83_msg.text = f'83 Porter: {porter_wait}m'
    else:
        porter_83_msg.text = f'83 Porter: tmrw'

    display.refresh()
    time.sleep(10)
