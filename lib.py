import math
import os
import textwrap
from urllib import request

from PIL import Image, ImageDraw, ImageFont

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive, GoogleDriveFileList
from googleapiclient.errors import HttpError
from pydrive.files import ApiRequestError
from oauth2client.client import GoogleCredentials
import time

from os import listdir
from os.path import isfile, join

# Card options
CARD_SCALE = 200
CONTENT_TEXT_SCALE = 100
TITLE_TEXT_SCALE = 40
# Margins (top big text, top small text, sides, bottom)
MARGINS = (150, 50, 50, 50)
# Chars to wrap at
TEXT_WRAP = 16
# otf/ttf file to use for the font
FONT_TTF = "HelveticaNeueLTStd-Bd.otf"
# Folders for the in-progress cards and built templates
CARDS_DIR = "cards"
BUILD_DIR = "build"

# Program constants
# Font
CONTENT_FONT = ImageFont.truetype(FONT_TTF, size=CONTENT_TEXT_SCALE)
CONTENT_TEXT_HEIGHT = math.floor(CONTENT_TEXT_SCALE * 1.2)
TITLE_FONT = ImageFont.truetype(FONT_TTF, size=TITLE_TEXT_SCALE)
TITLE_TEXT_HEIGHT = math.floor(TITLE_TEXT_SCALE * 1.2)
# Other
CARD_SIZE = (CARD_SCALE * 5, CARD_SCALE * 7)
COLOURS = ("white", "black")
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

existing_folders = dict()


def card_path(card_type, num, expansion=None, build=False, root_dir=False):
    "Returns {CARDS_DIR|BUILD_DIR}/[expansion]/card_type/card<num>.png"
    global existing_folders
    folder = BUILD_DIR if build else CARDS_DIR

    if root_dir:
        return os.path.join(folder, f"card{num}.png")
    if expansion is not None:
        folder = os.path.join(folder, expansion.replace(" ", ""))
    folder = os.path.join(folder, card_type)
    if not (existing_folders.get(folder) or os.path.isdir(folder)):
        os.makedirs(folder)
        existing_folders[folder] = True
    return os.path.join(folder, f"card{num}.png")


def uploadFile(f):
    currentSleep = 2
    for i in range(5):
        try:
            f.Upload()
        except (HttpError, ApiRequestError):
            time.sleep(currentSleep)
            currentSleep += 1
        else:
            return
    raise TimeoutError("Unable to upload file within 5 retries")


def make_card(
        card_text,
        file_name,
        expansion="",
        card_type=COLOURS[0],
        show_small=True,
        game_name="",
        progress=None,
        drive=None,
        colourDir=None,
        back=False
):
    if card_type == COLOURS[0]:
        text_col = BLACK
        back_col = WHITE
    else:
        text_col = WHITE
        back_col = BLACK

    # Skip blank lines created by fucked formatting
    if card_text in ([""], "", []):
        print("null card found: " + card_text)
        return

    if isinstance(card_text, list):
        for lineNum in range(len(card_text)):
            card_text[lineNum] = card_text[lineNum].replace("\\n", "\n")
        card_text = "".join(card_text)
    elif isinstance(card_text, str):
        card_text = card_text.replace("\\n", "\n")

    # Wrapping
    card_text = textwrap.wrap(card_text, width=TEXT_WRAP)

    # Initialise image
    current_img = Image.new("RGB", CARD_SIZE, color=back_col)
    drawn = ImageDraw.Draw(current_img)

    # Add the main text
    for num, line in enumerate(card_text):
        pos = (MARGINS[2], MARGINS[0] + (CONTENT_TEXT_HEIGHT * num))
        drawn.text(
            pos,
            line,
            font=CONTENT_FONT,
            fill=text_col,
        )

    if show_small is True:
        # Add the header text
        drawn.text(
            (MARGINS[2], MARGINS[1]),
            game_name,
            font=TITLE_FONT,
            fill=text_col,
        )

        # Add the footer text
        drawn.text(
            (MARGINS[2], CARD_SIZE[1] - MARGINS[3] - TITLE_TEXT_HEIGHT),
            expansion,
            font=TITLE_FONT,
            fill=text_col,
        )

    # Save it
    current_img.save(file_name)

    if progress is not None:
        if back:
            newFile = drive.CreateFile(metadata={'parents' : [{'id' : progress.deckFolder['id']}]})
            newFile.SetContentFile(file_name)
            uploadFile(newFile)
            progress.meta_dict[card_type + "_back"] = request.get('http://drive.google.com/uc?export=view&id=' + newFile['id']).url
        
        else:
            newFile = drive.CreateFile(metadata={'parents' : [{'id' : colourDir['id']}]})
            newFile.SetContentFile(file_name)
            uploadFile(newFile)

            if expansion not in progress.meta_dict:
                progress.meta_dict[expansion] = {colour: [] for colour in COLOURS}
            
            if card_type == COLOURS[0]:
                progress.meta_dict[expansion][card_type].append({"text": card_text,
                                                        'url': request.get('http://drive.google.com/uc?export=view&id=' + newFile['id']).url})
            elif card_type == COLOURS[1]:
                progress.meta_dict[expansion][card_type].append({"text": card_text, "requiredWhiteCards": card_text.count("_"),
                                                        'url': request.get('http://drive.google.com/uc?export=view&id=' + newFile['id']).url})
