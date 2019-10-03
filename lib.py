import enum
import math
import textwrap

from PIL import Image, ImageDraw, ImageFont

# Card options
CARD_SCALE = 200
BIG_TEXT_SCALE = 100
TOP_TEXT_SCALE = 40
TOP_TEXT = "Cult Against Humanity."
# Margins (top big text, top small text, sides, bottom)
MARGINS = (150, 50, 50, 50)
# Chars to wrap at
TEXT_WRAP = 17
FONT_TTF = "HelveticaNeueLTStd-Bd.otf"

# Program constants
CARD_SIZE = (CARD_SCALE * 5, CARD_SCALE * 7)
MAIN_FONT = ImageFont.truetype(FONT_TTF, size=BIG_TEXT_SCALE)
SMALL_FONT = ImageFont.truetype(FONT_TTF, size=TOP_TEXT_SCALE)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BIG_TEXT_HEIGHT = math.floor(BIG_TEXT_SCALE * 1.2)
TOP_TEXT_HEIGHT = math.floor(TOP_TEXT_SCALE * 1.333)


class CARD_TYPE(enum.Enum):
    WHITE = 0
    BLACK = 1


def make_card(card_text,
              file_name,
              expansion="",
              card_type=CARD_TYPE.WHITE,
              show_small=True):
    if card_type == CARD_TYPE.WHITE:
        text_col = BLACK
        back_col = WHITE
    else:
        text_col = WHITE
        back_col = BLACK

    # Skip blank lines created by fucked formatting
    if card_text in ([""], "", []):
        return
    card_text = "".join(card_text)

    # Wrapping
    card_text = textwrap.wrap(card_text, width=TEXT_WRAP)

    # Initialise image
    current_img = Image.new("RGB", CARD_SIZE, color=back_col)
    drawn = ImageDraw.Draw(current_img)

    # Add the main text
    for num, line in enumerate(card_text):
        pos = (MARGINS[2], MARGINS[0] + (BIG_TEXT_HEIGHT * num))
        drawn.text(
            pos,
            line,
            font=MAIN_FONT,
            fill=text_col,
        )

    if show_small is True:
        # Add the header text
        drawn.text(
            (MARGINS[2], MARGINS[1]),
            "Cult Against Humanity",
            font=SMALL_FONT,
            fill=text_col,
        )

        # Add the footer text
        drawn.text(
            (MARGINS[2], CARD_SIZE[1] - MARGINS[3] - TOP_TEXT_HEIGHT),
            expansion,
            font=SMALL_FONT,
            fill=text_col,
        )

    # Save it
    current_img.save(file_name)
