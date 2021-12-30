import ssl
import time
import alarm
import adafruit_requests
import board
import digitalio
import displayio
import socketpool
import terminalio
import wifi
import adafruit_displayio_sh1107
from adafruit_display_text import label
from adafruit_debouncer import Debouncer
from config import config
from task_view import TaskView

import sleep_dictionary

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
saved_task = None

# set up display
displayio.release_displays()
i2c = board.I2C()
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)

WIDTH = 128
HEIGHT = 64

display = adafruit_displayio_sh1107.SH1107(
    display_bus, width=WIDTH, height=HEIGHT, rotation=0
)

# fast wake if possible
task_view = TaskView(width=WIDTH, height=HEIGHT, rotation=0)

if alarm.wake_alarm:
    try:
        saved_task = sleep_dictionary.load()
        task_view.task = saved_task
        task_view.update()
        display.show(task_view.group)
    # pylint: disable=broad-except
    except Exception as e:
        print(e)

# set up wifi
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise
wifi.radio.connect(secrets["ssid"], secrets["password"])

# set up checkmark image
bitmap = displayio.OnDiskBitmap("/checkmark.bmp")
tile_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
checkmark_group = displayio.Group()
checkmark_group.append(tile_grid)
if saved_task is None:
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
    if query is not None:
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
    if project["name"] == config["project_name"]:
        project_id = project["id"]
        break
if project_id is None:
    print(projects)
    raise RuntimeError("missing project")

# set up task carousel
page_turned = 0
task_index = 0
tasks_refreshed = 0
idle_since = time.time()
tasks_response = None
tasks = None


def refresh_tasks():
    global tasks
    global tasks_refreshed
    overdue_tasks_response = requests.get(
        get_endpoint(
            "tasks",
            {
                "project_id": project_id,
                "filter": "overdue",
            },
        ),
        headers=headers,
    )
    overdue_tasks = overdue_tasks_response.json()
    today_tasks_response = requests.get(
        get_endpoint(
            "tasks",
            {
                "project_id": project_id,
                "filter": "today",
            },
        ),
        headers=headers,
    )
    today_tasks = today_tasks_response.json()
    undated_tasks_response = requests.get(
        get_endpoint(
            "tasks",
            {
                "project_id": project_id,
                "filter": "no date",
            },
        ),
        headers=headers,
    )
    undated_tasks = undated_tasks_response.json()
    tasks = overdue_tasks + undated_tasks + today_tasks
    tasks_refreshed = time.time()


def update_display_task(ix: int):
    global page_turned
    global task_index
    page_turned = time.time()
    task_index = ix
    task_view.task = tasks[task_index]
    task_view.update()
    display.show(task_view.group)


def complete_task():
    requests.post(
        get_endpoint("tasks/{}/close".format(tasks[task_index]["id"])),
        headers=headers,
    )
    display.show(checkmark_group)
    time.sleep(2)
    display.show(task_view.group)
    update_display_task((task_index + 1) % len(tasks))
    refresh_tasks()


def deep_sleep():
    sleep_dictionary.save(tasks[task_index])
    pin_a.deinit()
    goodbye = displayio.Group()
    idle_label = label.Label(
        terminalio.FONT,
        text="idle for {} seconds".format(config["auto_sleep"]),
        color=0xFFFFFF,
        x=8,
        y=16,
        scale=1,
    )
    goodbye_label = label.Label(
        terminalio.FONT, text="going to sleep", color=0xFFFFFF, x=8, y=32, scale=1
    )
    goodbye.append(idle_label)
    goodbye.append(goodbye_label)
    display.show(goodbye)
    time.sleep(3)
    display.sleep()
    wake_on_pin = alarm.pin.PinAlarm(pin=board.D9, value=False, pull=True)
    alarm.exit_and_deep_sleep_until_alarms(wake_on_pin)


while True:
    t = time.time()
    # handler button presses
    switch_a.update()
    switch_b.update()
    switch_c.update()
    if switch_a.fell:
        idle_since = t
        update_display_task((task_index - 1) % len(tasks))
    if switch_b.fell:
        idle_since = t
        complete_task()
    if switch_c.fell:
        idle_since = t
        update_display_task((task_index + 1) % len(tasks))

    # handler data and display updates
    if tasks_refreshed + config["poll_interval"] < t:
        refresh_tasks()
    if page_turned + config["rotate_interval"] < t:
        update_display_task((task_index + 1) % len(tasks))
    if config["auto_sleep"] > 0 and idle_since + config["auto_sleep"] < t:
        deep_sleep()
