import json
import alarm


def save(task):
    # parsing json with trailing "space" chars is fine, parsing json with whatever
    # guff you get by converting the default sleep memory content is not fine, so
    # we're going to pad out the json with space chars so that we can just json load
    # the whole lot later

    # create a string of space chars with the length being that of the available sleep memory
    filler = " " * len(alarm.sleep_memory)
    # convert to bytearray
    memory_bytes = bytearray(filler.encode("utf-8"))
    # convert task dict to json to bytearray
    task_bytes = bytearray(json.dumps(task).encode("utf-8"))
    # write the json bytes over the filler
    memory_bytes[0 : len(task_bytes)] = task_bytes
    # write out the bytearray, one byte at a time, to the sleep memory
    # using alarm.sleep_memory[[0 : len(memory_bytes)]] = memory_bytes
    # doesn't seem to store the bytes correctly, writing one at a time does work though
    for ix, value in enumerate(memory_bytes):
        alarm.sleep_memory[ix] = value


def load():
    # grab the bytearray from sleep memory
    memory_bytes = alarm.sleep_memory[0 : len(alarm.sleep_memory)]
    # convert to json then return dict
    return json.loads(memory_bytes.decode("utf-8"))
