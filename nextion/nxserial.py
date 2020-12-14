__all__ = ("Serial",)

import dataclasses
from datetime import datetime
import logging
import serial
from typing import Optional, Union

_LOGGER = logging.getLogger(__name__)

_EOF = b"\xff\xff\xff"


class _Invalid:
    """Instruction sent by user failed."""


class _Success:
    """Instruction sent by user was successful."""


@dataclasses.dataclass
class _TouchEvent:
    page: int
    component_id: int
    event: int


@dataclasses.dataclass
class _String:
    value: str


@dataclasses.dataclass
class _Number:
    value: int


class _Startup:
    """Nextion has started or reset."""


@dataclasses.dataclass
class _Unknown:
    cmd: bytes


_Message = Union[
    _Invalid, _Success, _TouchEvent, _String, _Number, _Startup, _Unknown
]


class Serial:
    def __init__(self, port: serial.Serial):
        self.port = port

    def send(self, cmd: str):
        in_waiting = self.port.in_waiting
        if in_waiting != 0:
            self.port.reset_input_buffer()
            _LOGGER.info(
                "drained %u bytes from input buffer prior to send", in_waiting
            )

        full_cmd = cmd.encode() + _EOF
        nbytes = self.port.write(full_cmd)
        if nbytes != len(full_cmd):
            _LOGGER.error(
                "command '%s' is %u bytes but %u written",
                cmd,
                len(cmd),
                nbytes - len(_EOF),
            )
        else:
            _LOGGER.info("wrote command '%s': %u bytes", cmd, len(cmd))

        if self.port.out_waiting != 0:
            _LOGGER.debug(
                "%u bytes waiting in output buffer", self.port.out_waiting
            )

    def receive(self) -> Optional[_Message]:
        if self.port.in_waiting != 0:
            _LOGGER.debug(
                "%u bytes waiting in input buffer", self.port.in_waiting
            )

        b = self.port.read_until(_EOF)
        if b == b"":
            return None

        _LOGGER.info("received %u bytes: %s", len(b), b)
        if b[-3:] != _EOF:
            _LOGGER.info("%s does not end %s", b, _EOF)
            return _Unknown(b)

        cmd = b[:-3]
        if cmd[0] == 0x00 and len(cmd) == 1:
            return _Invalid()
        if cmd[0] == 0x01 and len(cmd) == 1:
            return _Success()
        if cmd == [0x00, 0x00, 0x00]:
            return _Startup()
        if cmd[0] == 0x65:
            return _TouchEvent(*cmd[1:])
        if cmd[0] == 0x70:
            return _String(cmd[1:].decode("ascii"))
        if cmd[0] == 0x71:
            value = cmd[4] << 24 | cmd[3] << 16 | cmd[2] << 8 | cmd[1]
            return _Number(value)
        return _Unknown(b)

    def loop(self):
        while True:
            obj = self.receive()
            if obj is None:
                continue

            if isinstance(obj, _TouchEvent):
                _LOGGER.info("touch event %s", obj)
            else:
                _LOGGER.info("received %s", obj)

    def send_check(self, cmd: str) -> _Message:
        self.send(cmd)
        obj = self.receive()
        assert obj == _Success()
        return obj

    def page(self, num: int):
        assert num >= 0
        self.send(f"page {num}")

    def ussp(self, secs: int):
        """No-serial-then-sleep timeout."""
        assert secs == 0 or secs >= 3 and secs <= 65535
        self.send(f"ussp={secs}")

    def dim(self, level: int):
        assert level >= 0 and level <= 100
        self.send(f"dim={level}")

    def sleep(self, s: bool):
        self.send(f"sleep={int(s)}")

    def set_text(self, id: str, value: str):
        self.send(f'{id}.txt="{value}"')

    def set_value(self, id: str, value: int):
        self.send(f'{id}.val="{value}"')

    def get_value(self, id: str) -> Union[int, str]:
        self.send(f"get {id}.val")
        obj = self.receive()
        if isinstance(obj, _Number) or isinstance(obj, _String):
            return obj.value
        assert f"Invalid response {obj}"
        return 0

    def set_color(self, id: str, value: int):
        """
        Set text colour:
        0 = black, 0x00f0 = green, 0x0f00 = blue, 0xf000 = red, 0xffff = white
        """
        assert value >= 0 and value <= 65535
        self.send(f"{id}.pco={value}")

    def set_time(
        self,
    ):
        # date = x.strftime("%a %d %b %Y")  # Wed 31 Nov 2020
        # time = x.strftime("%H:%M:%S")  # 23:59:12
        # x.weekday() gives Monday=0, Sunday=6
        # rtc6 expects Sunday=0, Saturday=6
        # send(f"rtc6={(x.weekday()-1)%7}")
        # set_text(id, f"{date}\n{time}")
        x = datetime.now()
        rtc_vals = {
            "rtc0": x.year,
            "rtc1": x.month,
            "rtc2": x.day,
            "rtc3": x.hour,
            "rtc4": x.minute,
            "rtc5": x.second,
        }
        for k, v in rtc_vals.items():
            self.send(f"{k}={v}")