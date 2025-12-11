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
HARVARD_109_URL = f"http://api-v3.mbta.com/predictions?api_key={getenv("MBTA_API_KEY")}&page[limit]=1&filter[route]=109&filter[stop]=2546"
HARVARD_69_URL = f"http://api-v3.mbta.com/predictions?api_key={getenv("MBTA_API_KEY")}&page[limit]=1&filter[route]=69&filter[stop]=1427"
LECHMERE_69_URL = f"http://api-v3.mbta.com/predictions?api_key={getenv("MBTA_API_KEY")}&page[limit]=1&filter[route]=69&filter[stop]=1403"
HEADERS = {"user-agent": "mbta-tracker"}
WIFI_DEBUG = False
COLOR_DARK_WHITE = 0x777777
COLOR_BUS_83 = 0x7a5800
COLOR_BUS_109 = 0x7a0022
COLOR_BUS_69 = 0x144700
COLOR_TIME = 0x1111a0
LOGGING = True

# helper functions
def calibrate_realtime_clock() -> bool:
    the_rtc = rtc.RTC()
    response = requests.get(TIME_URL, headers=HEADERS)
    log(response.headers)
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
    return True

def get_time_msg_text(now: datetime) -> str:
    hour = now.hour // 12
    if hour == 0:
        hour = 12
    hour = str(hour)
    if len(hour) == 1:
        hour = "0"+hour
    minute = str(now.minute)
    if len(minute) == 1:
        minute = "0"+minute
    return f'{hour}:{minute}'

def log(*args):
    if LOGGING:
        print(*args)

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
    color=COLOR_DARK_WHITE,
    text='LED: on',
    x=1,
    y=8)
G.append(led_msg)
display.refresh()
log(led_msg.text)

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
        log("could not connect to AP, retrying: ", e)
        continue
wifi_msg = adafruit_display_text.label.Label(
    FONT,
    color=COLOR_DARK_WHITE,
    text='Lighthouse: on',
    x=1,
    y=16)
G.append(wifi_msg)
display.refresh()
log(wifi_msg.text)

if esp32.status == adafruit_esp32spi.WL_IDLE_STATUS:
    log("ESP32 found and in idle mode")
log("Firmware vers.", esp32.firmware_version)
log("MAC addr:", ":".join("%02X" % byte for byte in esp32.MAC_address))

# establish http connection
pool = adafruit_connection_manager.get_radio_socketpool(esp32)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(esp32)
requests = adafruit_requests.Session(pool, ssl_context)
http_msg = adafruit_display_text.label.Label(
    FONT,
    color=COLOR_DARK_WHITE,
    text='HTTP: on',
    x=1,
    y=24)
G.append(http_msg)
display.refresh()
log(http_msg.text)

# calibrate onboard clock
clock_calibrated = calibrate_realtime_clock()
if clock_calibrated:
    clock_msg = adafruit_display_text.label.Label(
        FONT,
        color=COLOR_DARK_WHITE,
        text='Realtime: on',
        x=1,
        y=32)
    G.append(clock_msg)
    display.refresh()
    log(clock_msg.text)
else:
    log('failed to calibrate clock')

time.sleep(5)
G.remove(led_msg)
G.remove(wifi_msg)
G.remove(http_msg)
G.remove(clock_msg)

# reset screen
central_83_msg = adafruit_display_text.label.Label(
    FONT,
    color=COLOR_BUS_83,
    text=f'83 Central: ---',
    x=1,
    y=27)
porter_83_msg = adafruit_display_text.label.Label(
    FONT,
    color=COLOR_BUS_83,
    text=f'83 Porter: ---',
    x=1,
    y=35)
harvard_109_msg = adafruit_display_text.label.Label(
    FONT,
    color=COLOR_BUS_109,
    text=f'109 Harvard: ---',
    x=1,
    y=43)
harvard_69_msg = adafruit_display_text.label.Label(
    FONT,
    color=COLOR_BUS_69,
    text=f'69 Harvard: ---',
    x=1,
    y=51)
lechmere_69_msg = adafruit_display_text.label.Label(
    FONT,
    color=COLOR_BUS_69,
    text=f'69 Lechmere: ---',
    x=1,
    y=59)
G.append(central_83_msg)
G.append(porter_83_msg)
G.append(harvard_109_msg)
G.append(harvard_69_msg)
G.append(lechmere_69_msg)

# time message
time_msg = adafruit_display_text.label.Label(
    FONT,
    color=COLOR_DARK_WHITE,
    text=f'--:--',
    x=22,
    y=17
    )
G.append(time_msg)

# other messages
happy_msg = adafruit_display_text.label.Label(
    FONT,
    color=COLOR_BUS_69,
    text='HAPPY',
    x=3,
    y=6)
holidays_msg = adafruit_display_text.label.Label(
    FONT,
    color=COLOR_BUS_109,
    text='HOLIDAYS!',
    x=27,
    y=6)
G.append(happy_msg)
G.append(holidays_msg)

display.refresh()

cycles_since_calibration = 0
while True:
    cycles_since_calibration += 1
    now = datetime.now()
    time_msg.text = get_time_msg_text(now)

    response = requests.get(CENTRAL_83_URL)
    central_83 = response.json()
    response.close()

    response = requests.get(PORTER_83_URL)
    porter_83 = response.json()
    response.close()

    response = requests.get(HARVARD_109_URL)
    harvard_109 = response.json()
    response.close()

    response = requests.get(HARVARD_69_URL)
    harvard_69 = response.json()
    response.close()

    response = requests.get(LECHMERE_69_URL)
    lechmere_69 = response.json()
    response.close()

    if len(central_83['data']) > 0:
        next_central_timestamp = central_83['data'][0]['attributes']['arrival_time']
        next_central_time = datetime.fromisoformat(next_central_timestamp).replace(tzinfo = None) # this hack only works because the local time is in the same timezone as the train stations
        central_wait = (next_central_time - now).seconds // 60
        central_83_msg.text = f'83 Central: {central_wait}m'
        log(f'central wait {central_wait}')
    else:
        central_83_msg.text = f'83 Central: tmrw'

    if len(porter_83['data']) > 0:
        next_porter_timestamp = porter_83['data'][0]['attributes']['arrival_time']
        next_porter_time = datetime.fromisoformat(next_porter_timestamp).replace(tzinfo = None)
        porter_wait = (next_porter_time - now).seconds // 60
        log(f'porter_wait {porter_wait}')
        porter_83_msg.text = f'83 Porter: {porter_wait}m'
    else:
        porter_83_msg.text = f'83 Porter: tmrw'

    if len(harvard_109['data']) > 0:
        next_harvard_timestamp = harvard_109['data'][0]['attributes']['arrival_time']
        next_harvard_time = datetime.fromisoformat(next_harvard_timestamp).replace(tzinfo = None)
        harvard_wait = (next_harvard_time - now).seconds // 60
        log(f'harvard_wait {harvard_wait}')
        harvard_109_msg.text = f'109 Harvard: {harvard_wait}m'
    else:
        harvard_109_msg.text = f'109 Harvard: tmrw'

    if len(harvard_69['data']) > 0:
        next_harvard_timestamp = harvard_69['data'][0]['attributes']['arrival_time']
        next_harvard_time = datetime.fromisoformat(next_harvard_timestamp).replace(tzinfo = None)
        harvard_wait = (next_harvard_time - now).seconds // 60
        log(f'harvard_wait_69 {harvard_wait}')
        harvard_69_msg.text = f'69 Harvard: {harvard_wait}m'
    else:
        harvard_69_msg.text = f'69 Harvard: tmrw'

    if len(lechmere_69['data']) > 0:
        next_lechmere_timestamp = lechmere_69['data'][0]['attributes']['arrival_time']
        next_lechmere_time = datetime.fromisoformat(next_lechmere_timestamp).replace(tzinfo = None)
        lechmere_wait = (next_lechmere_time - now).seconds // 60
        # log(f'lechmere_wait_69 {lechmere_wait}')
        lechmere_69_msg.text = f'69 Lechmere: {lechmere_wait}m'
    else:
        lechmere_69_msg.text = f'69 Lechmere: tmrw'

    if cycles_since_calibration >= 180: # every 30 mins
        clock_calibrated = calibrate_realtime_clock()
        if clock_calibrated:
            log('clock calibrated !')
            cycles_since_calibration = 0
        else:
            log('clock failed to calibrate :(')

    display.refresh()
    time.sleep(10)



