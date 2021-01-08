#!/usr/bin/env python3
import shutil
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
import json
import time
import psutil
import asyncio
from .lib import BUILD_DIR, CARDS_DIR, COLOURS, card_path, make_card, CardFontConfig, deck_path, local_file_url, clear_deck_path
import os
from discord import File
import traceback


def _render_cards(decksFolder, guildID, gameData, cardFont):
    expansions, deck_name = gameData["expansions"], gameData["title"]
    fonts = CardFontConfig(cardFont)
    
    # Clear results directories
    try:
        shutil.rmtree(deck_path(decksFolder, guildID, deck_name) + os.sep + CARDS_DIR)
        shutil.rmtree(deck_path(decksFolder, guildID, deck_name) + os.sep + BUILD_DIR)
    except FileNotFoundError:
        pass

    cardData = {"expansions": {}, "deck_name": deck_name}

    def saveCard(args):
        try:
            if args["expansion"] not in cardData["expansions"]:
                cardData["expansions"][args["expansion"]] = {col: [] for col in COLOURS}

            cardData["expansions"][args["expansion"]][args["card_type"]].append({"text": args["card_text"], "url":args["file_name"].split(decksFolder)[1]})

            if args["card_type"] == COLOURS[1]:
                cardData["expansions"][args["expansion"]][args["card_type"]][-1]["requiredWhiteCards"] = args["card_text"].count("_")
                
            make_card(*args.values())
        except Exception as e:
            print(traceback.format_exc())
            raise e

    for expansion_name in expansions:
        for colour, cards in zip(COLOURS, (expansions[expansion_name]["white"], expansions[expansion_name]["black"])):
            with futures.ThreadPoolExecutor(len(psutil.Process().cpu_affinity())) as executor:
                executor.map(
                    lambda elem: saveCard(elem),
                    [{
                        "card_text": c[1],
                        "file_name": card_path(decksFolder, guildID, deck_name, colour, c[0], expansion=expansion_name),
                        "fonts": fonts,
                        "expansion": expansion_name,
                        "card_type": colour,
                        "show_small": True,
                        "game_name": deck_name
                    } for c in enumerate(cards)],
                )

    # Create card backs
    for colour in COLOURS:
        make_card(
            deck_name,
            card_path(decksFolder, guildID, deck_name, colour, "Back" + colour, root_dir=True),
            fonts,
            show_small=False,
            card_type=colour,
        )
        cardData[colour + "_back"] = card_path("", guildID, deck_name, colour, "Back" + colour, root_dir=True)
    
    return cardData


async def render_all(decksFolder, gameData, cardFont, guildID):
    deck_name = gameData["title"]
    deckDir = deck_path(decksFolder, guildID, deck_name)
    if os.path.isdir(deckDir) and os.listdir(deckDir):
        raise RuntimeError("deck directory already exists and is not empty: " + deckDir)

    eventloop = asyncio.get_event_loop()
    cardData = await eventloop.run_in_executor(ThreadPoolExecutor(), _render_cards, decksFolder, guildID, gameData, cardFont)

    cardData["white_count"] = sum(len(cardData["expansions"][expansion]["white"]) for expansion in cardData["expansions"] if "white" in cardData["expansions"][expansion])
    cardData["black_count"] = sum(len(cardData["expansions"][expansion]["black"]) for expansion in cardData["expansions"] if "black" in cardData["expansions"][expansion])

    return cardData


async def store_cards_discord(decksFolder, cardData, storageChannel, callingMsg):
    for expansion in cardData["expansions"]:
        for colour in cardData["expansions"][expansion]:
            for card in cardData["expansions"][expansion][colour]:
                cardPath = card["url"]
                with open(cardPath, "rb") as f:
                    cardMsg = await storageChannel.send(str(callingMsg.author.id) + "@" + str(callingMsg.guild.id) + "/" + str(callingMsg.channel.id) + "\n" + cardData["deck_name"] + " -> " + expansion + " -> " + card["text"], file=File(f))
                    card["url"] = cardMsg.attachments[0].url

    for colour in COLOURS:
        cardPath = cardData[colour + "_back"]
        with open(cardPath, "rb") as f:
            cardMsg = await storageChannel.send(str(callingMsg.author.id) + "@" + str(callingMsg.guild.id) + "/" + str(callingMsg.channel.id) + "\n" + cardData["deck_name"] + " -> " + colour + "_back", file=File(f))
            cardData[colour + "_back"] = cardMsg.attachments[0].url

    try:
        clear_deck_path(decksFolder, callingMsg.guild.id, cardData["deck_name"])
    except FileNotFoundError:
        pass


def store_cards_local(cardData):
    for expansion in cardData["expansions"]:
        for colour in cardData["expansions"][expansion]:
            for card in cardData["expansions"][expansion][colour]:
                card["url"] = local_file_url(card["url"])

    for colour in COLOURS:
        cardData[colour + "_back"] = local_file_url(cardData[colour + "_back"])

    return cardData