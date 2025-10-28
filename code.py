from os import getenv
import rtc
import time
from adafruit_datetime import datetime
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
TIME_URL = "http://worldtimeapi.org/api/ip"
FONT = bitmap_font.load_font("fonts/4x6_kujala.pcf")
CENTRAL_83_URL = f"http://api-v3.mbta.com/predictions?api_key={getenv("MBTA_API_KEY")}&page[limit]=1&filter[route]=83&filter[stop]=2437"
PORTER_83_URL = f"http://api-v3.mbta.com/predictions?api_key={getenv("MBTA_API_KEY")}&page[limit]=1&filter[route]=83&filter[stop]=2453"
print(CENTRAL_83_URL)

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
esp32 = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset, debug=True)
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
response = requests.get(TIME_URL)
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

# reset screen
G = displayio.Group()
central_83_msg = adafruit_display_text.label.Label(
    FONT,
    color=0xFFC72C,
    text=f'83 Central: {0}m',
    x=1,
    y=8)
porter_83_msg = adafruit_display_text.label.Label(
    FONT,
    color=0xFFC72C,
    text=f'83 Porter: {0}m',
    x=1,
    y=16)
G.append(central_83_msg)
G.append(porter_83_msg)

JSON_URL = "http://wifitest.adafruit.com/testwifi/sample.json"
r = requests.get(JSON_URL)
print(r.json())
r.close()

time.sleep(5)

r = requests.get(CENTRAL_83_URL)
central_83 = response.json()
print(central_83)
r.close()

# while True:
#     now = datetime.fromtimestamp(time.time())
#     r = requests.get(CENTRAL_83_URL)
#     central_83 = response.json()
#     r.close()
#     r = requests.get(PORTER_83_URL)
#     porter_83 = response.json()
#     r.close()

#     next_central_timestamp = central_83['data'][0]['attributes']['arrival_time']
#     next_central_time = datetime.fromisoformat(next_central_timestamp)
#     central_wait = (next_central_time - now).seconds // 60
#     central_83_msg.text = f'83 Central: {central_wait}m'

#     next_porter_timestamp = porter_83['data'][0]['attributes']['arrival_time']
#     next_porter_time = datetime.fromisoformat(next_porter_timestamp)
#     porter_wait = (next_porter_time - now).seconds // 60
#     porter_83_msg.text = f'83 Porter: {porter_wait}m'

#     display.refresh()
#     time.sleep(1)






