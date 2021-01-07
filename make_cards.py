#!/usr/bin/env python3
import shutil
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
import json
import time
import psutil
import asyncio
from .lib import BUILD_DIR, CARDS_DIR, COLOURS, card_path, make_card, CardFontConfig
import os
from discord import File


def _render_cards(messageID, gameData, cardFont):
    expansions, deck_name = gameData["expansions"], gameData["title"]
    fonts = CardFontConfig(cardFont)
                            
    # Clear results directories
    try:
        shutil.rmtree(str(messageID) + os.sep + CARDS_DIR)
        shutil.rmtree(str(messageID) + os.sep + BUILD_DIR)
    except FileNotFoundError:
        pass

    cardData = {"expansions": {}, "deck_name": deck_name}

    def saveCard(elem):
        make_card(*elem)
        if elem[2] not in cardData["expansions"]:
            cardData["expansions"][elem[2]] = {col: [] for col in COLOURS}
        cardData["expansions"][elem[2]][elem[3]].append({"text": elem[0], "url":elem[1]})
        if elem[3] == COLOURS[1]:
            cardData["expansions"][elem[2]][elem[3]][-1]["requiredWhiteCards"] = elem[0].count("_")

    for expansion_name in expansions:
        for colour, cards in zip(COLOURS, (expansions[expansion_name]["white"], expansions[expansion_name]["black"])):
            with futures.ThreadPoolExecutor(len(psutil.Process().cpu_affinity())) as executor:
                executor.map(
                    lambda elem: saveCard(elem),
                    [(
                        c[1],
                        card_path(messageID, colour, c[0], expansion=expansion_name),
                        fonts,
                        expansion_name,
                        colour,
                        True,
                        deck_name
                    ) for c in enumerate(cards)],
                )

    # Create card backs
    for colour in COLOURS:
        make_card(
            deck_name,
            card_path(messageID, colour, "Back" + colour, root_dir=True),
            show_small=False,
            card_type=colour,
        )
        cardData[colour + "_back"] = card_path(messageID, colour, "Back" + colour, root_dir=True)
    
    return cardData


async def render_all(storageChannel, callingMsg, gameData, cardFont):
    expansions, deck_name = gameData["expansions"], gameData["title"]

    eventloop = asyncio.get_event_loop()
    cardData = await eventloop.run_in_executor(ThreadPoolExecutor(), _render_cards, callingMsg.id, gameData, cardFont)

    for expansion in cardData["expansions"]:
        for colour in cardData["expansions"][expansion]:
            for card in cardData["expansions"][expansion][colour]:
                cardPath = card["url"]
                with open(cardPath, "rb") as f:
                    cardMsg = await storageChannel.send(str(callingMsg.author.id) + "@" + str(callingMsg.guild.id) + "/" + str(callingMsg.channel.id) + "\n" + gameData["title"] + " -> " + expansion + " -> " + card["text"], file=File(f))
                    card["url"] = cardMsg.attachments[0].url

    for colour in COLOURS:
        cardPath = cardData[colour + "_back"]
        with open(cardPath, "rb") as f:
            cardMsg = await storageChannel.send(str(callingMsg.author.id) + "@" + str(callingMsg.guild.id) + "/" + str(callingMsg.channel.id) + "\n" + gameData["title"] + " -> " + colour + "_back", file=File(f))
            cardData[colour + "_back"] = cardMsg.attachments[0].url

    try:
        shutil.rmtree(str(callingMsg.id))
    except FileNotFoundError:
        pass

    cardData["white_count"] = sum(len(cardData["expansions"][expansion]["white"]) for expansion in cardData["expansions"] if "white" in cardData["expansions"][expansion])
    cardData["black_count"] = sum(len(cardData["expansions"][expansion]["black"]) for expansion in cardData["expansions"] if "black" in cardData["expansions"][expansion])

    return cardData
