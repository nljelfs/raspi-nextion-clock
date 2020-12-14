#!/bin/bash

# Get weather icons
# https://openweathermap.org/weather-conditions
# e.g. http://openweathermap.org/img/wn/10d@2x.png

cd icons || exit $?
for i in 1 2 3 4 9 10 11 13 50; do
    num=$(printf "%02d" $i)
    for j in n d; do
        wget -O "${num}${j}.png" "http://openweathermap.org/img/wn/${num}${j}@2x.png"
    done
done