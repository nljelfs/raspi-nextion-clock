import argparse
import logging
import serial
import serial.tools.list_ports

import nextion

_LOGGER = logging.getLogger(__name__)


def _get_weather():
    # Wheathampstead as JSON
    url = "http://api.openweathermap.org/data/2.5/weather?id=2634172&appid=c2a506286299a3de585b1b0d4daed7ac"
    return url


def _connect(port: str) -> nextion.Serial:
    port = serial.Serial(port=port, baudrate=9600, timeout=1.0)
    nx = nextion.Serial(port)
    return nx


def _parse_args() -> argparse.Namespace:
    comports = serial.tools.list_ports.comports()

    p = argparse.ArgumentParser()
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
    return p.parse_args()


def _main():
    args = _parse_args()

    logging.basicConfig(level="DEBUG" if args.verbose else "INFO")

    nx = _connect(args.port)
    nx.page(0)


if __name__ == "__main__":
    _main()
