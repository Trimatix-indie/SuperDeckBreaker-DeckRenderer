#!/usr/bin/env python
import csv
import os
from concurrent import futures
from urllib import request

import psutil

from lib import make_card

CSV_NAME = "values.csv"
GDOC_ID = open("spreadsheet_id.txt", "rt").readline()

# Get our csv and decode into string
csv_raw = request.urlopen(
    f"https://docs.google.com/spreadsheets/d/{GDOC_ID}/export?exportFormat=csv"
).read().decode("unicode-escape")

# Create all the cards, with multithreading
with futures.ThreadPoolExecutor(psutil.cpu_count()) as executor:
    executor.map(
        lambda elem: make_card(
            elem[1],
            os.path.join("cards", f"card{elem[0]}.png"),
        ),
        enumerate(csv.reader(csv_raw.split("\n"))),
    )
