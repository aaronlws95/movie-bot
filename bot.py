import os
from datetime import datetime

import imdb
import discord
from discord.ext import commands
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.members = True

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix='!', intents=intents)

movies_csv = 'data/movies.csv'
next_movie_csv = 'data/next_movie.csv'

def get_guild():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    if not guild:
        raise ValueError("{} guild does not exist".format(GUILD))
    return guild
    
def get_channel(guild, name, voice=False):
    if voice:
        channel = discord.utils.get(guild.voice_channels, name=name)
    else:
        channel = discord.utils.get(guild.channels, name=name)
    if not channel:
        raise ValueError("{} channel does not exist".format(name))
    return channel 

def update_next_movie(title, year, chooser):
    with open(next_movie_csv, 'w') as f:
        f.write("{}|{}|{}".format(title, year, chooser))

def get_next_movie():
    with open(next_movie_csv, 'r') as f:
        lines = f.read().splitlines()[0]
        # title, year, chooser
        return line[0], line[1], line[2]

def get_movie(idx):
    with open(movies_csv, 'r') as f:
        lines = f.read().splitlines()
        line = lines[idx].split('|')
    title = line[0]
    year = line[1]
    return title, year

@bot.event
async def on_ready():
    print(f'{bot.user.name} online')

@bot.command(name='start-score')
async def start_score(ctx, *args):
    # Args
    if len(args) == 0:
        await ctx.send("Usage: [!start-score <initial/final>]")
        return
    elif args[0] not in ['initial', 'final']:
        await ctx.send("Usage: [!start-score <initial/final>]")
        return    
    mode = args[0].lower()

    # Setup guild and channels
    guild = get_guild()
    general_channel = get_channel(guild, 'general')
    scores_channel = get_channel(guild, 'scores')
    general_voice_channel = get_channel(guild, 'General', voice=True)

    # Participants
    if len(args) > 1:
        participants = []
        for i in range(1, len(args)):
            member = discord.utils.get(guild.members, name=args[i])
            if member:
                participants.append(member)
            else:
                await general_channel.send("I dont recognise {}".format(args[i]))
        
        if not participants:
            await general_channel.send("Cannot find participants.")
            return
    else:
        participants = general_voice_channel.members

        if not participants:
            await general_channel.send(
                "Cannot find participants in voice channel. \
                    Try [!start-score <person1> <person2> ... <personN>]")
            return

    # Start
    await general_channel.send("{} scoring has started.".format(mode.capitalize()))
    if mode == 'initial':
        title, year, _ = get_next_movie()
        date = datetime.today().strftime('%d/%m/%Y')
        await scores_channel.send("**{}: {} ({})**".format(date, title, year))
    await scores_channel.send("**{}**".format(mode.capitalize()))

    # Scoring
    for p in participants:
        channel = await p.create_dm()
        await channel.send("Please DM me your {} score.".format(args[0]))
    await general_channel.send("Waiting for everyone to give a score.")
    
    remaining = [p.name for p in participants]
    scores = {}
    def check(message):
        if isinstance(message.channel, discord.channel.DMChannel):
            try:
                score = float(message.content)    
            except ValueError:
                return False
            if message.author.name in remaining:
                remaining.remove(message.author.name)
                scores[message.author.name] = score
        if not remaining:
            return True
        return False

    await bot.wait_for('message', check=check)

    # Finish
    await general_channel.send("{} scoring has finished.".format(mode.capitalize()))
    for k,v in scores.items():
        await scores_channel.send("**{0}**: {1:3.1f}".format(k, v))

@bot.command(name='choose-next-movie')
async def choose_next_movie(ctx, *args):
    # Setup guild and channels
    guild = get_guild()
    general_channel = get_channel(guild, 'general')

    # Args
    if len(args) < 2:
        await ctx.send("Usage: !choose-next-movie \"<title>\" <chooser>")
        return
    if len(args) == 3:
        update_next_movie(args[0], args[1], args[2])
    name = args[0]
    member = discord.utils.get(guild.members, name=args[1])
    if member:
        chooser = member.name
    else:
        await general_channel.send("Cannot find member {}".format(args[1]))
        return

    ia = imdb.IMDb()
    candidates = ia.search_movie(name)
    await general_channel.send("Searching for next movie")
    await general_channel.send("'Y' to select movie")
    await general_channel.send("'EXIT' to cancel search")
    await general_channel.send("Input anything else to continue search.")
    
    def check(message):
        if message.channel == ctx.channel:
            return True
        return False

    for c in candidates:
        if 'movie' in c['kind']:
            await general_channel.send("Did you mean {}?".format(c['long imdb title']))
            msg = await bot.wait_for('message', check=check)
            if msg.content.upper() == 'Y':
                update_next_movie(c['title'], c['year'], chooser)
                await general_channel.send("Yo we watching {}.".format(c['long imdb title']))
                return
            elif msg.content.upper() == 'EXIT':
                return 
    
    await general_channel.send("No movie found, please manually add: [!choose-next-movie <title> <year> <chooser>].")

bot.run(TOKEN)