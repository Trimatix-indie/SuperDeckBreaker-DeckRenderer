#!/usr/bin/env bash

DOC_ID="$(cat spreadsheet_id.txt)"
FILE_NAME="values.csv"

curl -s -d "/dev/null" "https://docs.google.com/spreadsheets/d/$DOC_ID/export?exportFormat=csv" >$FILE_NAME
dos2unix $FILE_NAME
sed $FILE_NAME -i "s/^\\([^\"]\\)/\"\\1/" -i "s/\\([^\"]\\)$/\\1\"/"
