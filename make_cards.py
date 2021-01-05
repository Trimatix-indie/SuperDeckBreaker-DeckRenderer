#!/usr/bin/env python3
import shutil
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
import json
import time
import psutil
import asyncio
from lib import BUILD_DIR, CARDS_DIR, COLOURS, card_path, make_card
import os
from discord import File


def _render_cards(messageID, gameData):
    expansions, deck_name = gameData["expansions"], gameData["title"]
                            
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
            cardData["expansions"][elem[2]] = []
        cardData["expansions"][elem[2]].append({"text": elem[0], "url":elem[1]})
        if elem[3] == COLOURS[1]:
            cardData["expansions"][elem[2]][-1]["requiredWhiteCards"] = elem[0].count("_")

    for expansion_name in expansions:
        for colour, cards in zip(COLOURS, (expansions[expansion_name]["white"], expansions[expansion_name]["black"])):
            with futures.ThreadPoolExecutor(psutil.cpu_count()) as executor:
                executor.map(
                    lambda elem: saveCard(elem),
                    [(
                        c[1],
                        card_path(messageID, colour, c[0], expansion=expansion_name),
                        expansion_name,
                        colour,
                        True,
                        deck_name,
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


async def render_all(storageChannel, callingMsg, gameData):
    expansions, deck_name = gameData["expansions"], gameData["title"]

    eventloop = asyncio.get_event_loop()
    cardData = await eventloop.run_in_executor(ThreadPoolExecutor(), _render_cards, callingMsg.id, gameData)

    for expansion in cardData["expansions"]:
        for card in cardData["expansions"][expansion]:
            cardPath = card["url"]
            with open(cardPath, "rb") as f:
                cardMsg = await storageChannel.send(callingMsg.author.id + "@" + callingMsg.guild.id + "/" + callingMsg.channel.id + "\n" + gameData["title"] + " -> " + expansion + " -> " + card["text"], file=File(f))
                card["url"] = cardMsg.attachments[0].url

    for colour in COLOURS:
        cardPath = cardData[colour + "_back"]
        with open(cardPath, "rb") as f:
            cardMsg = await storageChannel.send(callingMsg.author.id + "@" + callingMsg.guild.id + "/" + callingMsg.channel.id + "\n" + gameData["title"] + " -> " + colour + "_back", file=File(f))
            cardData[colour + "_back"] = cardMsg.attachments[0].url

    try:
        shutil.rmtree(str(callingMsg.id))
    except FileNotFoundError:
        pass

    return cardData
