#!/usr/bin/env python
import csv
import shutil
from concurrent import futures
from itertools import zip_longest
from urllib import request

import psutil

from lib import BUILD_DIR, CARDS_DIR, COLOURS, TITLE_TEXT, card_path, make_card

SPREADSHEET_ID = open("spreadsheet_id.txt", "rt").readline()
CSV_FILE = "raw.csv"
EXPANSIONS = (
    "Base_Game",
    "Apex_Expansion",
    "Danganronpa_Expansion",
    "FragSoc_Expansion",
    "Misc_Games_Expansion",
    "Overwatch_Expansion",
    "TF2_Expansion",
    "Titanfall_Expansion",
)

# Clear results directories
shutil.rmtree(BUILD_DIR)
shutil.rmtree(CARDS_DIR)

for expansion in EXPANSIONS:
    # Get our csv, decode into string and make a reader
    csv_raw = request.urlopen(
        f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={expansion}"
    ).read().decode("utf-8")
    csv_reader = csv.reader(csv_raw.split("\n"))

    # Write the csv data to a file for debugging
    with open(CSV_FILE, "wt") as my_file:
        my_file.write(csv_raw)

    # Format and Write the cards
    for colour, cards in zip(COLOURS, zip_longest(*csv_reader)):
        with futures.ThreadPoolExecutor(psutil.cpu_count()) as executor:
            executor.map(
                lambda elem: make_card(*elem),
                [(
                    c[1],
                    card_path(colour, c[0], expansion=expansion),
                    expansion.replace("_", " "),
                    colour,
                ) for c in enumerate(cards)],
            )

# Create card backs
for colour in COLOURS:
    make_card(
        TITLE_TEXT + ".",
        card_path(colour, "Back"),
        show_small=False,
        card_type=colour,
    )
