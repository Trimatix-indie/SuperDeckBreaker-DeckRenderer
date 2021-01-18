#!/usr/bin/env python3
import shutil
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
import json
import time
import psutil
import asyncio
from .lib import BUILD_DIR, CARDS_DIR, COLOURS, card_path, make_card, CardFontConfig, deck_path, local_file_url, clear_deck_path, CONTENT_TEXT_SCALE, TITLE_TEXT_SCALE
import os
from discord import File
import traceback


def _render_cards(existingFolders, decksFolder, guildID, gameData, cardFont, fontSizes):
    expansions, deck_name = gameData["expansions"], gameData["title"]
    fonts = CardFontConfig(cardFont, contentFontSize=fontSizes["content"], titleFontSize=fontSizes["title"])
    
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
                        "file_name": card_path(existingFolders, decksFolder, guildID, deck_name, colour, c[0], expansion=expansion_name),
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
            card_path(existingFolders, decksFolder, guildID, deck_name, colour, "Back" + colour, root_dir=True),
            fonts,
            show_small=False,
            card_type=colour,
        )
        cardData[colour + "_back"] = card_path(existingFolders, "", guildID, deck_name, colour, "Back" + colour, root_dir=True)
    
    return cardData


async def render_all(decksFolder, gameData, cardFont, guildID, contentFontSize=CONTENT_TEXT_SCALE, titleFontSize=TITLE_TEXT_SCALE):
    deck_name = gameData["title"]
    deckDir = deck_path(decksFolder, guildID, deck_name)
    if os.path.isdir(deckDir) and os.listdir(deckDir):
        raise RuntimeError("deck directory already exists and is not empty: " + deckDir)

    eventloop = asyncio.get_event_loop()
    existingFolders = dict()
    cardData = await eventloop.run_in_executor(ThreadPoolExecutor(), _render_cards, existingFolders, decksFolder, guildID, gameData, cardFont, {"content": contentFontSize, "title": titleFontSize})

    return cardData


async def store_cards_discord(decksFolder, cardData, storageChannel, callingMsg):
    cardUploaders = set()

    async def uploadCard(card, cardPath, msgText):
        with open(cardPath, "rb") as f:
            cardMsg = await storageChannel.send(msgText, file=File(f))
            card["url"] = cardMsg.attachments[0].url

    def scheduleCardUpload(card, cardPath, msgText):
        task = asyncio.ensure_future(uploadCard(card, cardPath, msgText))
        cardUploaders.add(task)
        task.add_done_callback(cardUploaders.remove)

    for expansion in cardData["expansions"]:
        for colour in cardData["expansions"][expansion]:
            for card in cardData["expansions"][expansion][colour]:
                cardPath = decksFolder + os.sep + card["url"]
                scheduleCardUpload(card, cardPath, str(callingMsg.author.id) + "@" + str(callingMsg.guild.id) + "/" + str(callingMsg.channel.id) + "\n" + cardData["deck_name"] + " -> " + expansion + " -> " + card["text"])

    for colour in COLOURS:
        cardPath = decksFolder + os.sep + cardData[colour + "_back"]
        with open(cardPath, "rb") as f:
            cardMsg = await storageChannel.send(str(callingMsg.author.id) + "@" + str(callingMsg.guild.id) + "/" + str(callingMsg.channel.id) + "\n" + cardData["deck_name"] + " -> " + colour + "_back", file=File(f))
            cardData[colour + "_back"] = cardMsg.attachments[0].url

    if cardUploaders:
        await asyncio.wait(cardUploaders)

    try:
        clear_deck_path(decksFolder, callingMsg.guild.id, cardData["deck_name"])
    except FileNotFoundError:
        pass

    return cardData


def store_cards_local(cardData):
    for expansion in cardData["expansions"]:
        for colour in cardData["expansions"][expansion]:
            for card in cardData["expansions"][expansion][colour]:
                card["url"] = local_file_url(card["url"])

    for colour in COLOURS:
        cardData[colour + "_back"] = local_file_url(cardData[colour + "_back"])

    return cardData