import ssl
import time
import adafruit_requests
import board
import digitalio
import displayio
import rtc
import socketpool
import terminalio
import wifi
import adafruit_displayio_sh1107
from adafruit_display_text import label
from adafruit_datetime import datetime
from adafruit_debouncer import Debouncer

PROJECT_NAME = "To Do"

# set up buttons
pin_a = digitalio.DigitalInOut(board.D9)
pin_a.direction = digitalio.Direction.INPUT
pin_a.pull = digitalio.Pull.UP
switch_a = Debouncer(pin_a)
pin_b = digitalio.DigitalInOut(board.D6)
pin_b.direction = digitalio.Direction.INPUT
pin_b.pull = digitalio.Pull.UP
switch_b = Debouncer(pin_b)
pin_c = digitalio.DigitalInOut(board.D5)
pin_c.direction = digitalio.Direction.INPUT
pin_c.pull = digitalio.Pull.UP
switch_c = Debouncer(pin_c)

requests = None
pool = None

# set up wifi
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!" % secrets["ssid"])

# set up display
displayio.release_displays()
i2c = board.I2C()
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)

WIDTH = 128
HEIGHT = 64
BORDER = 2

display = adafruit_displayio_sh1107.SH1107(
    display_bus, width=WIDTH, height=HEIGHT, rotation=0
)

# set up checkmark image
bitmap = displayio.OnDiskBitmap("/checkmark.bmp")
tile_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
checkmark_group = displayio.Group()
checkmark_group.append(tile_grid)
display.show(checkmark_group)

# set up request lib
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer {}".format(secrets["todoist_api_key"]),
}

BASE_URL = "https://api.todoist.com/rest/v1"


def get_endpoint(path: str, query: dict = None):
    querystring = ""
    if query is None:
        querystring += "?"
        for key in query.keys():
            querystring += str(key) + "=" + str(query[key]) + "&"
        querystring = querystring[:-1]
    return "{0}/{1}{2}".format(BASE_URL, path, querystring)


# get projects list
projects_response = requests.get(get_endpoint("projects"), headers=headers)
projects = projects_response.json()
project_id = None
for project in projects:
    if project["name"] == PROJECT_NAME:
        project_id = project["id"]
        break
if project_id is None:
    print(projects)
    raise RuntimeError("missing project")

# set up time
TIME_ENDPOINT = "http://worldclockapi.com/api/json/utc/now"
time_response = requests.get(TIME_ENDPOINT)
time_data = time_response.json()
now = datetime.fromisoformat(time_data["currentDateTime"].replace("Z", ""))
rtc.RTC().datetime = now.timetuple()

# set up task carousel
page_turned = 0
tasks_refreshed = 0
task_index = 0
tasks_response = None
tasks = None
splash = displayio.Group()
display.show(splash)
task_label = label.Label(
    terminalio.FONT, text="task:", color=0xFFFFFF, x=0, y=8, scale=1
)
splash.append(task_label)
task_name = label.Label(terminalio.FONT, text="---", color=0xFFFFFF, x=8, y=24, scale=1)
splash.append(task_name)
task_added_label = label.Label(
    terminalio.FONT, text="added:", color=0xFFFFFF, x=0, y=40, scale=1
)
splash.append(task_added_label)
task_added = label.Label(
    terminalio.FONT, text="---", color=0xFFFFFF, x=8, y=54, scale=1
)
splash.append(task_added)

# block out start or task label
block_bitmap = displayio.Bitmap(8, 16, 1)
block_palette = displayio.Palette(1)
block_palette[0] = 0x000000  # Black
inner_sprite = displayio.TileGrid(block_bitmap, pixel_shader=block_palette, x=0, y=16)
splash.append(inner_sprite)


def refresh_tasks():
    global tasks
    global tasks_refreshed
    new_tasks_response = requests.get(
        get_endpoint(
            "tasks",
            {
                "project_id": project_id,
            },
        ),
        headers=headers,
    )
    tasks = new_tasks_response.json()
    tasks_refreshed = time.time()


def update_display_task(ix: int):
    global page_turned
    global task_index
    page_turned = time.time()
    task_index = ix
    fix()
    task_name.text = tasks[task_index]["content"]
    created = datetime.fromisoformat(tasks[task_index]["created"].replace("Z", ""))
    task_added.text = created.ctime()


def complete_task():
    requests.post(
        get_endpoint("tasks/{}/close".format(tasks[task_index]["id"])),
        headers=headers,
    )
    display.show(checkmark_group)
    time.sleep(2)
    display.show(splash)
    refresh_tasks()
    update_display_task((task_index + 1) % len(tasks))


def scroll():
    task_name.x = task_name.x - 1
    line_width = task_name.bounding_box[2]
    if task_name.x < -line_width:
        task_name.x = display.width


def fix():
    if task_name.x != 8:
        task_name.x = 8


while True:
    # handler button presses
    switch_a.update()
    switch_b.update()
    switch_c.update()
    if switch_a.fell:
        update_display_task((task_index - 1) % len(tasks))
    if switch_b.fell:
        complete_task()
    if switch_c.fell:
        update_display_task((task_index + 1) % len(tasks))

    # handler data and display updates
    if tasks_refreshed + 60 < time.time():
        refresh_tasks()
    if page_turned + 10 < time.time():
        update_display_task((task_index + 1) % len(tasks))
    if (len(task_name.text) * 6) > (WIDTH - 8):
        scroll()
    else:
        fix()
