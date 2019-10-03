#!/usr/bin/env python
import csv
import itertools
import os
from concurrent import futures
from urllib import request

import psutil

from lib import CARD_TYPE, make_card

SPREADSHEET_ID = open("spreadsheet_id.txt", "rt").readline()
CARDS_DIR = "cards"
CSV_FILE = "raw.csv"

# Get our csv and decode into string
csv_raw = request.urlopen(
    f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?exportFormat=csv"
).read().decode("utf-8")
csv_reader = csv.reader(csv_raw.split("\n"))

# Write the csv data to a file for debugging
with open(CSV_FILE, "wt") as my_file:
    my_file.write(csv_raw)

# Change from mixed pairs to pure lists
white_cards, black_cards = list(itertools.zip_longest(*csv_reader))

# Filter and prepare args for make_card
white_cards = [(c[1], os.path.join("cards", f"white{c[0]}.png"), "Base Game",
                CARD_TYPE.WHITE) for c in enumerate(white_cards)]
black_cards = [(c[1], os.path.join("cards", f"black{c[0]}.png"), "Base Game",
                CARD_TYPE.BLACK) for c in enumerate(black_cards)]

# Write the cards
with futures.ThreadPoolExecutor(psutil.cpu_count()) as executor:
    executor.map(lambda elem: make_card(*elem), white_cards + black_cards)

# Create card backs
make_card("Cult Against Humanity.",
          os.path.join(CARDS_DIR, "backBlack.png"),
          show_small=False,
          card_type=CARD_TYPE.BLACK)
make_card("Cult Against Humanity.",
          os.path.join(CARDS_DIR, "backWhite.png"),
          show_small=False,
          card_type=CARD_TYPE.WHITE)
