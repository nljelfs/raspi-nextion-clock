#!/bin/bash

if ! [ -d nextion ]; then
    echo "ERROR: directory 'nextion' not found" >&2
    exit 1
fi

env PYTHONPATH=nextion python3 -m clock "$@"