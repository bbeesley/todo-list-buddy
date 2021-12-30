from math import floor
import terminalio
from adafruit_datetime import datetime
from displayio import Group
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect

MONTHNAMES = (
    None,
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)
DAYNAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
FONTBOUNDINGBOX = (6, 12, 0, -2)


class TaskView:
    def __init__(self, width, height, rotation):
        self.TEXT_COLOUR = 0xFFFFFF
        self.WIDTH = width
        self.HEIGHT = height
        self.ROTATION = rotation

        self.BORDER_SIZE = 6
        self.MAX_CHARS = floor((self.WIDTH - 2 * self.BORDER_SIZE) / FONTBOUNDINGBOX[0])

        self.group = Group()

        # create a border around the display
        self.border = Rect(0, 0, self.WIDTH, self.HEIGHT, outline=self.TEXT_COLOUR)
        self.group.append(self.border)

        # create a border around the "created at" timestamp
        self.timestamp_border = Rect(
            0,
            self.HEIGHT - FONTBOUNDINGBOX[1] + FONTBOUNDINGBOX[3] - self.BORDER_SIZE,
            self.WIDTH,
            FONTBOUNDINGBOX[1] - FONTBOUNDINGBOX[3] + self.BORDER_SIZE,
            outline=self.TEXT_COLOUR,
        )
        self.group.append(self.timestamp_border)

        # create the task text object
        self.task_name = label.Label(
            terminalio.FONT,
            text="---",
            color=self.TEXT_COLOUR,
            x=self.BORDER_SIZE,
            y=self.BORDER_SIZE - FONTBOUNDINGBOX[3],
            scale=1,
        )
        self.group.append(self.task_name)

        # create the "created at" text object
        self.task_added = label.Label(
            terminalio.FONT,
            text="---",
            color=self.TEXT_COLOUR,
            x=self.BORDER_SIZE,
            y=self.HEIGHT - FONTBOUNDINGBOX[1] - FONTBOUNDINGBOX[3],
            scale=1,
        )
        self.group.append(self.task_added)

    def update(self):
        # wrap the text onto multiple lines if needed
        self.task_name.text = self._wrap_text()
        # get the created at time
        created = datetime.fromisoformat(self.task["created"].replace("Z", ""))
        # format the time and add it to the "created at" object
        self.task_added.text = "%s %s %2d %04d" % (
            DAYNAMES[created.weekday()],
            MONTHNAMES[created.month],
            created.day,
            created.year,
        )

    def _wrap_text(self):
        # remove any existing newlines and break the string down to an array of words
        string = self.task["content"].replace("\n", "").replace("\r", "")
        words = string.split(" ")

        # create and populate an array using the words, when a line is longer than
        # max chars then we move to the next element in the lines array
        lines = []
        line = ""
        for w in words:
            if len(line + " " + w) <= self.MAX_CHARS:
                line += " " + w
            else:
                lines.append(line)
                line = w
        if line:
            lines.append(line)

        # get rid of the leading " " character on line 1
        lines[0] = lines[0][1:]

        # join the lines array element using newlines, omit the trailing newline from
        # the final line of text
        wrapped_text = ""
        for ix, w in enumerate(lines):
            if 1 + ix == len(lines):
                wrapped_text += w
            else:
                wrapped_text += w + "\n"
        return wrapped_text
