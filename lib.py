import math
import os
import textwrap
import aiohttp
import shutil
import urllib

from PIL import Image, ImageDraw, ImageFont

import time

from os import listdir, getcwd, sep
from os.path import isfile, join

# Card options
CARD_SCALE = 200
CONTENT_TEXT_SCALE = 100
TITLE_TEXT_SCALE = 40
# Margins (top big text, top small text, sides, bottom)
MARGINS = (150, 50, 50, 50)
# Chars to wrap at
TEXT_WRAP = 16
# Folders for the in-progress cards and built templates
CARDS_DIR = ""
BUILD_DIR = "build"

# Program constants
# Font
CONTENT_TEXT_HEIGHT = math.floor(CONTENT_TEXT_SCALE * 1.2)
TITLE_TEXT_HEIGHT = math.floor(TITLE_TEXT_SCALE * 1.2)

# Other
CARD_SIZE = (CARD_SCALE * 5, CARD_SCALE * 7)
COLOURS = ("white", "black")
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
IMG_FORMAT = "jpg"
BASE_URL = "cahbot.edjoduf.co.uk:8081/"
PROTOCOL = "http"


class CardFontConfig:
    def __init__(self, cardFont, contentFontSize=CONTENT_TEXT_SCALE, titleFontSize=TITLE_TEXT_SCALE):
        self.cardFont = cardFont
        self.contentFont = ImageFont.truetype(cardFont, size=contentFontSize)
        self.titleFont = ImageFont.truetype(cardFont, size=titleFontSize)
        self.contentFontHeight = math.floor(contentFontSize * 1.2)
        self.titleFontHeight = math.floor(titleFontSize * 1.2)


def deck_path(decks_dir, guild_id, deck_name):
    if type(deck_name) == int:
        return decks_dir + os.sep + str(guild_id) + os.sep + str(deck_name)
    return decks_dir + os.sep + str(guild_id) + os.sep + str(hash(deck_name))


def clear_deck_path(decks_dir, guild_id, deck_name):
    try:
        shutil.rmtree(deck_path(decks_dir, guild_id, deck_name))
    except FileNotFoundError:
        pass


def card_path(existing_folders, decks_dir, guild_id, deck_name, card_type, num, expansion=None, build=False, root_dir=False):
    "Returns deck_path/{CARDS_DIR|BUILD_DIR}/[hash(expansion)]/card_type/card<num>." + IMG_FORMAT
    folder = deck_path(decks_dir, guild_id, deck_name) + os.sep + (BUILD_DIR if build else CARDS_DIR)

    if root_dir:
        return os.path.join(folder, f"card{num}." + IMG_FORMAT)
    if expansion is not None:
        folder = os.path.join(folder, str(hash(expansion)))
    folder = os.path.join(folder, card_type)
    if not (existing_folders.get(folder) or os.path.isdir(folder)):
        os.makedirs(folder)
        existing_folders[folder] = True
    return os.path.join(folder, f"card{num}." + IMG_FORMAT)


def local_file_url(card_path):
    return PROTOCOL + "://" + BASE_URL + urllib.parse.quote(card_path.lstrip("/" + os.sep).replace(os.sep, "/"))


def url_to_local_path(url):
    return os.path.normpath(url.split(BASE_URL)[1].lstrip("/"))


def make_card(
        card_text,
        file_name,
        fonts,
        expansion="",
        card_type=COLOURS[0],
        show_small=True,
        game_name="",
):
    if card_type == COLOURS[0]:
        text_col = BLACK
        back_col = WHITE
    else:
        text_col = WHITE
        back_col = BLACK

    # Skip blank lines created by fucked formatting
    if card_text in ([""], "", []):
        return

    if isinstance(card_text, list):
        card_text = "".join(card_text)

    rawText = card_text

    # Wrapping
    splitting_text = card_text.split("\\n")
    card_text = []
    for line in splitting_text:
        for newline in textwrap.wrap(line, width=TEXT_WRAP):
            card_text.append(newline)

    # Initialise image
    current_img = Image.new("RGB", CARD_SIZE, color=back_col)
    drawn = ImageDraw.Draw(current_img)

    # Add the main text
    for num, line in enumerate(card_text):
        pos = (MARGINS[2], MARGINS[0] + (fonts.contentFontHeight * num))
        drawn.text(
            pos,
            line,
            font=fonts.contentFont,
            fill=text_col,
        )

    if show_small is True:
        # Add the header text
        drawn.text(
            (MARGINS[2], MARGINS[1]),
            game_name,
            font=fonts.titleFont,
            fill=text_col,
        )

        # Add the footer text
        drawn.text(
            (MARGINS[2], CARD_SIZE[1] - MARGINS[3] - fonts.titleFontHeight),
            expansion,
            font=fonts.titleFont,
            fill=text_col,
        )

    # Save it
    current_img.save(file_name)
