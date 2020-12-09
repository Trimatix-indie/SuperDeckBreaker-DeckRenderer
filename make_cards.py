#!/usr/bin/env python3
import csv
from math import exp
import shutil
from concurrent import futures
from itertools import zip_longest
from urllib import request

import psutil

from lib import BUILD_DIR, CARDS_DIR, COLOURS, card_path, make_card

def render_all(expansions, deck_name="Super Deck Breaker"):
    # Clear results directories
    try:
        shutil.rmtree(CARDS_DIR)
        shutil.rmtree(BUILD_DIR)
    except FileNotFoundError:
        pass
    
    print("EXPANSIONS")
    for expansion_name in expansions:
        # Format and Write the cards
        # print(list(zip(COLOURS, (expansions[expansion_name]["white"], expansions[expansion_name]["black"]))))
        for colour, cards in zip(COLOURS, (expansions[expansion_name]["white"], expansions[expansion_name]["black"])):
            for card in cards:
                make_card(card[1], card_path(colour, card[0], expansion=expansion_name), expansion_name, colour)

    print("BACKS")
    # Create card backs
    for colour in COLOURS:
        make_card(
            deck_name,
            card_path(colour, "Back" + colour, root_dir=True),
            show_small=False,
            card_type=colour,
        )
