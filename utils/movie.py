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