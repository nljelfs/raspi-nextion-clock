#!/usr/bin/python3 -i

import dataclasses
from datetime import datetime
import logging
import serial
from typing import Generator, Union

_LOGGER = logging.getLogger(__name__)

_PORT = serial.Serial(port="/dev/serial0", baudrate=9600, timeout=1.0)

_EOF = b"\xff\xff\xff"


def send(cmd: str):
    in_waiting = _PORT.in_waiting
    if in_waiting != 0:
        _PORT.reset_input_buffer()
        _LOGGER.info(
            "drained %u bytes from input buffer prior to send", in_waiting
        )

    full_cmd = cmd.encode() + _EOF
    nbytes = _PORT.write(full_cmd)
    if nbytes != len(full_cmd):
        _LOGGER.error(
            "cmd '%s' is %u bytes but %u written",
            cmd,
            len(cmd),
            nbytes - len(_EOF),
        )
    else:
        _LOGGER.info("wrote cmd '%s': %u bytes", cmd, len(cmd))
    if _PORT.out_waiting != 0:
        _LOGGER.info("%u bytes waiting in output buffer", _PORT.out_waiting)


@dataclasses.dataclass
class TouchEvent:
    page: int
    component_id: int
    event: int


@dataclasses.dataclass
class ReceivedNumber:
    value: int


@dataclasses.dataclass
class Unknown:
    cmd: bytes


class Nothing:
    pass


def receive() -> Generator[
    Union[TouchEvent, ReceivedNumber, Unknown, Nothing], None, None
]:
    if _PORT.in_waiting != 0:
        _LOGGER.info("%u bytes waiting in input buffer", _PORT.in_waiting)
    b = _PORT.read_until(_EOF)
    if b == b"":
        yield Nothing()
    else:
        _LOGGER.info("received %u bytes: %s", len(b), b)
        if b[-3:] != _EOF:
            _LOGGER.info("%s does not end %s", b, _EOF)
            yield Unknown(b)
        else:
            cmd = b[:-3]
            if cmd[0] == 0x65:
                yield TouchEvent(*cmd[1:])
            elif cmd[0] == 0x71:
                value = (
                    (cmd[4] << 24) | (cmd[3] << 16) | (cmd[2] << 8) | cmd[1]
                )
                yield ReceivedNumber(value)
            else:
                yield Unknown(b)


def dim(lvl: int):
    assert lvl >= 0 and lvl <= 100
    send(f"dim={lvl}")


def sleep(s: bool):
    send(f"sleep={int(s)}")


def set_text(id: str, value: str):
    send(f'{id}.txt="{value}"')


def set_value(id: str, value: int):
    send(f'{id}.val="{value}"')


_LAST_REQ_ID = None


def get_value(id: str):
    global _LAST_REQ_ID
    send(f"get {id}.val")
    _LAST_REQ_ID = id


def set_color(id: str, value: int):
    """
    Set text colour:
      0 = black, 0x00f0 = green, 0x0f00 = blue, 0xf000 = red, 0xffff = white
    """
    assert value >= 0 and value <= 65535
    send(f"{id}.pco={value}")


def show_time(id: str):
    x = datetime.now()
    date = x.strftime("%a %d %b %Y")  # Wed 31 Nov 2020
    time = x.strftime("%H:%M:%S")  # 23:59:12
    set_text(id, f"{date}\n{time}")


def loop():
    while True:
        for obj in receive():
            if isinstance(obj, TouchEvent):
                _LOGGER.info("touch event %s", obj)
                if obj.component_id == 5:  # slider s0
                    # set_text("t0", "slider")
                    get_value("s0")
                elif obj.component_id == 2:  # checkbox c0
                    # set_text("t0", "check")
                    get_value("c0")
            elif isinstance(obj, ReceivedNumber):
                _LOGGER.info("number %s", obj)
                if _LAST_REQ_ID == "s0":
                    set_text("t0", f"slider {obj.value}")
                elif _LAST_REQ_ID == "c0":
                    set_text("t0", f"check {obj.value}")
                else:
                    assert f"Unknown last request ID {_LAST_REQ_ID}"
            elif isinstance(obj, Nothing):
                pass


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    loop()