import json
import alarm


def save(task):
    filler = " " * len(alarm.sleep_memory)
    memory_bytes = bytearray(filler.encode("utf-8"))
    task_bytes = bytearray(json.dumps(task).encode("utf-8"))
    memory_bytes[0 : len(task_bytes)] = task_bytes
    for ix, value in enumerate(memory_bytes):
        alarm.sleep_memory[ix] = value


def load():
    memory_bytes = alarm.sleep_memory[0 : len(alarm.sleep_memory)]
    return json.loads(memory_bytes.decode("utf-8"))
