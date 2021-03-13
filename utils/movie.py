import csv
import os

import gspread
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

# Environment
load_dotenv()
SHEET = os.getenv('GOOGLESHEET_ID')
CREDENTIALS = os.getenv('GOOGLE_CREDENTIALS')

# Paths
ROOT = "data"
MOVIES_CSV = ROOT + '/movies.csv'
NEXT_MOVIE_CSV = ROOT + '/next_movie.csv'

def update_next_movie(title, year, chooser):
    with open(NEXT_MOVIE_CSV, 'w') as f:
        f.write("{}|{}|{}\n".format(title, year, chooser))

def get_next_movie():
    with open(NEXT_MOVIE_CSV, 'r') as f:
        line = f.read().splitlines()[0].split('|')
        # title, year, chooser
        return line[0], line[1], line[2]

def get_movie(idx):
    with open(MOVIES_CSV, 'r') as f:
        lines = f.read().splitlines()
        line = lines[idx].split('|')
    title = line[0]
    year = line[1]
    return title, year

def append_movie(title, year, date, chooser):
    with open(MOVIES_CSV, 'a') as f:
        f.write("{}|{}|{}|{}\n".format(title, year, date, chooser))

def get_entry(title, member):
    with open(ROOT + "/{}.csv".format(member.lower()), 'r') as f:
        lines = f.read().splitlines()
        for l in lines:
            if l.split('|')[0] == title:
                return l

    return None

def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive.file",
             "https://www.googleapis.com/auth/drive"]

    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS + '.json', scope)
    client = gspread.authorize(credentials)
    return client.open_by_key(SHEET)

def export_csv_to_sheets(csv_path, worksheet_name, delimiter='|'):
    sh = get_sheet()

    with open(csv_path, 'r') as f:
        csv_file = list(csv.reader(f, delimiter=delimiter))

    sh.values_update(
        worksheet_name,
        params={'valueInputOption': 'USER_ENTERED'},
        body={'values': csv_file}
    )

def append_csv_to_sheets(values, worksheet_name, delimiter="|"):
    sh = get_sheet()

    values = [values.split(delimiter)]

    try:
        sh.values_append(
            worksheet_name,
            params={'valueInputOption': 'USER_ENTERED'},
            body={'values': values}
        )
    except:
        print("Error: Check your inputs")