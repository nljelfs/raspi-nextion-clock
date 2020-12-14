import argparse
import logging
import serial
import serial.tools.list_ports
import sys

import nextion

_LOGGER = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    comports = serial.tools.list_ports.comports()

    p = argparse.ArgumentParser()
    p.add_argument(
        "-l",
        "--list-ports",
        action="store_true",
        help="list serial ports",
    )
    p.add_argument(
        "-p",
        "--port",
        metavar="PORT",
        choices=[port.device for port in comports],
        help="serial port for Nextion (default %(default)s)",
        default="/dev/ttyUSB0",
    )
    p.add_argument(
        "-v", "--verbose", action="store_true", help="enable DEBUG logging"
    )
    parsed = p.parse_args()

    if parsed.list_ports:
        for port in comports:
            print(port.device)
            print(f"\t{port.description}")
        sys.exit(0)

    return parsed


def _connect(port: str) -> nextion.Serial:
    serport = serial.Serial(port=port, baudrate=9600, timeout=1.0)
    nx = nextion.Serial(serport)
    _LOGGER.info("Connected to Nextion on %s", port)
    return nx


args = _parse_args()

logging.basicConfig(level="DEBUG" if args.verbose else "INFO")

nx = _connect(args.port)
