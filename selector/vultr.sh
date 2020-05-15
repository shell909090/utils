#!/bin/bash

curl -k -s 'https://www.vultr.com/features/datacenter-locations/' | python3 cssselector.py -c 'a.content-slider__item' -a href
