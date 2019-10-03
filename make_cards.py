#!/usr/bin/env python
import csv
from concurrent import futures
from itertools import zip_longest
from urllib import request

import psutil

from lib import COLOURS, TOP_TEXT, card_path, make_card

SPREADSHEET_ID = open("spreadsheet_id.txt", "rt").readline()
CSV_FILE = "raw.csv"

# Get our csv and decode into string
csv_raw = request.urlopen(
    f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?exportFormat=csv"
).read().decode("utf-8")
csv_reader = csv.reader(csv_raw.split("\n"))

# Write the csv data to a file for debugging
with open(CSV_FILE, "wt") as my_file:
    my_file.write(csv_raw)

# Format and Write the cards
expansion = "Base Game"  # Temp var
for colour, cards in zip(COLOURS, zip_longest(*csv_reader)):
    with futures.ThreadPoolExecutor(psutil.cpu_count()) as executor:
        executor.map(
            lambda elem: make_card(*elem),
            [(
                c[1],
                card_path(colour, c[0], expansion=expansion),
                expansion,
                colour,
            ) for c in enumerate(cards)],
        )

# Create card backs
for colour in COLOURS:
    make_card(
        TOP_TEXT + ".",
        card_path(colour, "Back"),
        show_small=False,
        card_type=colour,
    )
