#!/usr/bin/env python
import csv
import math
import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

# Card options
CARD_SCALE = 200
BIG_TEXT_SCALE = 120
BIG_TEXT_HEIGHT = math.floor(BIG_TEXT_SCALE * 1.333)
BIG_TEXT_SPACING_VERTICAL = math.floor(BIG_TEXT_HEIGHT / 10)
TOP_TEXT_SCALE = 40
TOP_TEXT = "Cult Against Humanity."
MARGIN_SIDE = 50
MARGIN_TOP = (150, 50)  # big, small
TEXT_WRAP = 14
FONT_TTF = "HelveticaNeueLTStd-Bd.otf"

# Program constants
CARD_SIZE = (CARD_SCALE * 5, CARD_SCALE * 7)
VALUES_FILE = "values.csv"
MAIN_FONT = ImageFont.truetype(FONT_TTF, size=BIG_TEXT_SCALE)
SMALL_FONT = ImageFont.truetype(FONT_TTF, size=TOP_TEXT_SCALE)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Get our CSV vals
with open(VALUES_FILE, "rt") as csv_file:
    csv_reader = list(csv.reader(csv_file.read()))

for card_num, card_text in enumerate(csv_reader):
    # Skip blank lines created by fucked formatting
    if card_text in ([""], []):
        continue
    card_text = card_text[0]

    # Wrapping
    card_text = textwrap.wrap(card_text, width=TEXT_WRAP)

    # Initialise image
    current_img = Image.new("RGB", (1000, 1600), color=WHITE)
    drawn = ImageDraw.Draw(current_img)

    # Add the header text
    drawn.text(
        (MARGIN_SIDE, MARGIN_TOP[1]),
        "Cult Against Humanity",
        font=SMALL_FONT,
        fill=BLACK,
    )

    # Add the main text
    for num, line in enumerate(card_text):
        pos = (MARGIN_SIDE,
               MARGIN_TOP[0] + ((BIG_TEXT_HEIGHT + BIG_TEXT_SPACING_VERTICAL) * num))
        drawn.text(
            pos,
            line,
            font=MAIN_FONT,
            fill=BLACK,
        )

    # Save it
    current_img.save(os.path.join("cards", f"card{card_num}.png"))
