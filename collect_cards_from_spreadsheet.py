from google.colab import auth
import gspread
from oauth2client.client import GoogleCredentials

import make_cards

def collect_cards():
    auth.authenticate_user()
    gc = gspread.authorize(GoogleCredentials.get_application_default())
    sheetLink = input("Spreadsheet url: ")
    sheetFound = False

    while not sheetFound:
        try:
            worksheet = gc.open_by_url(sheetLink)
        except gspread.SpreadsheetNotFound:
            print("Unrecognised spreadsheet! Please make sure the file exists and is accessable by your account.")
        else:
            sheetFound = True
    
    expansions = {}

    for expansion in worksheet.worksheets():
        expansions[expansion.title] = {"white": [card for card in expansion.col_values(1) if card],
                                        "black": [card for card in expansion.col_values(2) if card]}

    return expansions


