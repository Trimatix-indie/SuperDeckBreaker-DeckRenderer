#!/usr/bin/env python3
import csv
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

    for expansion_name in expansions:
        # Format and Write the cards
        for colour, cards in zip(COLOURS, (expansions[expansion_name]["white"], expansions[expansion_name]["black"])):
            with futures.ThreadPoolExecutor(psutil.cpu_count()) as executor:
                executor.map(
                    lambda elem: make_card(*elem),
                    [(
                        c[1],
                        card_path(colour, c[0], expansion=expansion_name),
                        expansion_name,
                        colour,
                        deck_name
                    ) for c in enumerate(cards)],
                )

    # Create card backs
    for colour in COLOURS:
        make_card(
            deck_name,
            card_path(colour, "Back" + colour, root_dir=True),
            show_small=False,
            card_type=colour,
        )
