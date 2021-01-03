#!/usr/bin/env python3
import csv
import shutil
from concurrent import futures
from itertools import zip_longest
from urllib import request
import json

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive, GoogleDriveFileList
from googleapiclient.errors import HttpError
from pydrive.files import ApiRequestError
from oauth2client.client import GoogleCredentials
import time

import psutil

from lib import BUILD_DIR, CARDS_DIR, COLOURS, card_path, make_card, uploadFile


class ProgressTracker:
    def __init__(self):
        self.soFar, self.totalCards, self.percent = 0, 0, 0

    def renderCard(self, elem):
        make_card(*elem)
        if self.totalCards > 9:
            self.soFar += 1
            if (self.soFar / self.totalCards) * 100 >= self.percent + 5:
                self.percent += 5
                print(str(self.percent) + "% done")



def render_all(gameData):
    expansions, deck_name = gameData["expansions"], gameData["title"]

    gauth = GoogleAuth()
    gauth.credentials = GoogleCredentials.get_application_default()
    drive = GoogleDrive(gauth)

    sdbFolder = None
    file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    for rootF in file_list:
        if rootF["title"] == "SuperDeckBreaker" and rootF["mimeType"] == 'application/vnd.google-apps.folder':
            sdbFolder = rootF
            break

    if sdbFolder is None:
        sdbFolder = drive.CreateFile({'title' : "SuperDeckBreaker", 'mimeType' : 'application/vnd.google-apps.folder'})
        uploadFile(sdbFolder)

    deckFolder = None
    file_list = drive.ListFile({'q': "'" + sdbFolder['id'] + "' in parents and trashed=false"}).GetList()
    for rootF in file_list:
        if rootF["title"] == deck_name and rootF["mimeType"] == 'application/vnd.google-apps.folder':
            deckFolder = rootF
            break

    if deckFolder is not None:
        deckFolder.Trash()

    deckFolder = drive.CreateFile({'title' : deck_name, 'mimeType' : 'application/vnd.google-apps.folder', 'parents': [{'id' : sdbFolder['id']}]})
    uploadFile(deckFolder)
    permission = deckFolder.InsertPermission({
                            'type': 'anyone',
                            'value': 'anyone',
                            'role': 'reader'})
                            
    # Clear results directories
    try:
        shutil.rmtree(CARDS_DIR)
        shutil.rmtree(BUILD_DIR)
    except FileNotFoundError:
        pass

    meta_dict = {}

    for expansion_name in expansions:
        expansionDir = drive.CreateFile({'title' : expansion_name, 'mimeType' : 'application/vnd.google-apps.folder', 'parents': [{'id' : deckFolder['id']}]})
        uploadFile(expansionDir)
        print("Uploading expansion: " + expansion_name)
        # Format and Write the cards
        currentColour = ""
        totalCards = sum(len(expansions[expansion_name][col]) for col in COLOURS)
        progress = None

        for colour, cards in zip(COLOURS, (expansions[expansion_name]["white"], expansions[expansion_name]["black"])):
            if colour != currentColour:
                colourDir = drive.CreateFile({'title' : colour, 'mimeType' : 'application/vnd.google-apps.folder', 'parents': [{'id' : expansionDir['id']}]})
                uploadFile(colourDir)
                print("Uploading " + colour + " cards")
                progress = ProgressTracker()

            with futures.ThreadPoolExecutor(psutil.cpu_count()) as executor:
                executor.map(
                    lambda elem: progress.renderCard(elem),
                    [(
                        c[1],
                        card_path(colour, c[0], expansion=expansion_name),
                        expansion_name,
                        colour,
                        True,
                        deck_name,
                        meta_dict,
                        drive,
                        colourDir
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


    newFile = drive.CreateFile(metadata={'parents' : [{'id' : sdbFolder['id']}]})
    with open(deck_name + ".json", "w") as f:
        f.write(json.dumps(meta_dict))
    newFile.SetContentFile(deck_name + ".json")
    uploadFile(newFile)
    print('Here\'s your deck url! Give this to the SuperDeckBreaker bot\'s add-deck command: http://drive.google.com/uc?export=view&id=' + newFile['id'])
