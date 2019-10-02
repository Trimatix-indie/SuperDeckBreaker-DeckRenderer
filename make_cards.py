#!/usr/bin/env python
import csv
import textwrap

from PIL import Image, ImageDraw, ImageFont

# Card options
CARD_SCALE = 200
BIG_TEXT_SCALE = 150
SMALL_TEXT_SCALE = 40
FONT_TTF = "./HelveticaNeueLTStd-Bd.otf"

# Program constants
CARD_SIZE = (CARD_SCALE * 5, CARD_SCALE * 7)
TEXT_WIDTH = CARD_SCALE // BIG_TEXT_SCALE
print(TEXT_WIDTH)
VALUES_FILE = "values.csv"
MAIN_FONT = ImageFont.truetype(FONT_TTF, size=BIG_TEXT_SCALE)
SMALL_FONT = ImageFont.truetype(FONT_TTF, size=SMALL_TEXT_SCALE)
WHITE = (0, 0, 0)
BLACK = (255, 255, 255)

# Get our CSV vals
with open(VALUES_FILE, "rt") as csv_file:
    csv_reader = list(csv.reader(csv_file.read()))

for card_num, card_text in enumerate(csv_reader):
    # Skip blank lines created by fucked formatting
    if card_text in ([""], []):
        continue
    card_text = card_text[0]

    # Wrapping
    card_text = textwrap.fill(card_text, width=9)

    # Initialise image
    current_img = Image.new("RGB", (1000, 1600), color=BLACK)
    drawn = ImageDraw.Draw(current_img)

    # Add the main text
    drawn.text(
        [x / 20 for x in CARD_SIZE],
        card_text,
        font=MAIN_FONT,
        fill=WHITE,
    )

    # Add the smol text
    drawn.text(
        [x / 50 for x in CARD_SIZE],
        "Cult Against Humanity",
        font=SMALL_FONT,
        fill=WHITE,
    )

    # Save it
    current_img.save(f"cards/card{card_num}.png")
