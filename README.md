# todo list buddy

## Description

A CircuitPython app that lets you view and check off tasks from your todoist todo list using buttons and a small OLED display.

## Hardware

Any CircuitPython capable board with an ESP32 chip should be able to run this project, I used an [Adafruit Feather ESP32-S2](https://www.adafruit.com/product/5000) board. You'll also need an OLED display and 3 buttons, I used an [Adafruit Featherwing OLED 128x64](https://www.adafruit.com/product/4650) since it comes with both. It you want it to be wire free, you'll also need a lipo battery. I use [these](https://www.amazon.co.uk/EEMB-1100mAh-Battery-Rechargeable-Connector/dp/B08FD39Y5R), although annoyingly they have the positive and negative connected the opposite way round to the JST SH connector on the Feather so I just crimp a new connector on that matches the wiring on the Feather.

## Setup

There is a little bit of config/secrets setup required to connect to wifi and interact with the Todoist API. You're going to need to create a file called `secrets.py` that contains a dict, secrets, that holds your wifi credentials and api key. For example:

```python
secrets = {
  "ssid": "WideFi",
  "password": "super-secret-password",
  "todoist_api_key": "1C976062-B9FC-40D3-86C4-4DD02BAEC996"
}
```

To get your API key for todoist, just log into your account in the browser and head to [your integration settings](https://todoist.com/app/settings/integrations). Scroll to the bottom and you'll find your API key.

The other config values are set in [config.py](config.py):

```python
config = {
    "project_name": "To Do", # the name of the todoist project to work with
    "poll_interval": 60, # how often to update the task list from the todoist api
    "rotate_interval": 10, # how long to pause on displaying each task in the list
    "auto_sleep": 900, # how long, in seconds, of inactivity to allow before sending the device to sleep. Set to zero to disable auto sleep.
}
```

## Usage
![todo-buddy](https://user-images.githubusercontent.com/1926537/147387648-4a6937ef-ab33-4489-84de-0a84caf9a862.jpg)

Copy `code.py` and `secrets.py` onto your microcontroller, create a `lib` directory on the microcontroller and copy over the dependencies:
* adafruit_requests
* adafruit_displayio_sh1107
* adafruit_display_text
* adafruit_datetime
* adafruit_debouncer
You can get them all in the [Adafruit CircuitPython Bundle](https://circuitpython.org/libraries).

When the microcontroller starts up, you should see the checkmark screen splash, then your tasks should load up. Once task is displayed at a time, along with when it was added to the list. Every 10 seconds the display is cycled to show the next task. Every 60 seconds the task list is updated to fetch any newly added tasks.

You can use button A and button C to navigate through the task list, pressing button B will mark the current task as complete and refresh the list.

When the device has been idle for the number of seconds defined in the `auto_sleep` config value it will go into deep sleep mode. Press button A to wake the device back up.
