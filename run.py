import csv
import os
import random
from pathlib import Path
from datetime import datetime

import imdb
import discord
from discord.ext import commands
from dotenv import load_dotenv

import utils


# Environment
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

# Bot
help_command = commands.DefaultHelpCommand(no_category = 'Commands')
intents = discord.Intents.default()
intents.members = True
intents.messages = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=help_command)


@bot.event
async def on_ready():
    print(f'{bot.user.name} online')


@bot.event
async def on_message(message):
    if isinstance(message.channel, discord.channel.TextChannel):
        if message.channel.name == 'screenshots':
            await utils.discord.download_attachments(message.attachments)
    await bot.process_commands(message)


@bot.command(name='start-score',
             brief="Handle the scoring process",
             description="Run the command to start scoring. The bot will DM you for a response. Unless explicitly given, participants will be taken from whoever is in the General voice channel.",
             usage="<initial/final> [person1] [person2] ... [personN]")
async def start_score(ctx, *args):
    # Args
    if len(args) == 0:
        await ctx.send("Usage: !start-score <initial/final>")
        return
    elif args[0] not in ['initial', 'final']:
        await ctx.send("Usage: !start-score <initial/final>")
        return
    mode = args[0].lower()

    # Setup guild and channels
    guild = utils.discord.get_guild(bot, GUILD)
    bot_info_channel = utils.discord.get_channel(guild, 'bot-info')
    scores_channel = utils.discord.get_channel(guild, 'scores')
    general_voice_channel = utils.discord.get_channel(guild, 'General', voice=True)

    # Participants
    if len(args) > 1:
        participants = []
        for i in range(1, len(args)):
            # Validate member
            member = await utils.discord.get_member(bot_info_channel, args[i])
            if member:
                participants.append(member)

        if not participants:
            await bot_info_channel.send("Cannot find participants")
            return
    else:
        participants = general_voice_channel.members

        if not participants:
            await bot_info_channel.send(
                "Cannot find participants in voice channel. Try !start-score <person1> <person2> ... <personN>")
            return

    # Start
    await bot_info_channel.send("{} scoring has started".format(mode.capitalize()))
    title, year, chooser = utils.csv.get_next_movie()
    if mode == 'initial':
        date = datetime.today().strftime('%d/%m/%Y')
        await scores_channel.send("**{}: {} ({})**".format(date, title, year))
        sh = utils.sheets.get_sheet(utils.sheets.SHEET)
        utils.csv.append_movie(title, year, date, chooser)
        utils.sheets.append_csv_to_sheets(sh, "{}|{}|{}|{}".format(title, year, date, chooser), "Movies")
    await scores_channel.send("**{}**".format(mode.capitalize()))

    # Scoring
    for p in participants:
        channel = await p.create_dm()
        await channel.send("Please DM me your {} score".format(args[0]))
    await bot_info_channel.send("Waiting for everyone to give a score")

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
    await bot_info_channel.send("{} scoring has finished".format(mode.capitalize()))
    for k,v in scores.items():
        await scores_channel.send("**{}**: {:.2f}".format(k, v))

    # Add data
    if mode == 'final':
        sh = utils.sheets.get_sheet(utils.sheets.SHEET)
        for p in participants:
            row_value = "{}|{:.2f}".format(title, scores[p.name])
            utils.sheets.append_csv_to_sheets(sh, row_value, p.name)
            with open(utils.csv.CSV_PATH + "/{}.csv".format(p.name.lower()), 'a') as f:
                f.write(row_value + "\n")


@bot.command(name='choose-next-movie',
             brief="Register the next movie",
             description="Adds the next movie to the database. The bot will help you find the movie unless you add the year to the command.",
             usage="\"<title>\" [year] <chooser>")
async def choose_next_movie(ctx, *args):
    # Setup guild and channels
    guild = utils.discord.get_guild(bot, GUILD)
    bot_info_channel = utils.discord.get_channel(guild, 'bot-info')

    # Args
    if len(args) < 2:
        await ctx.send("Usage: !choose-next-movie \"<title>\" <chooser>")
        return
    if len(args) == 3:
        member = await utils.discord.get_member(bot_info_channel, args[1])
        if member:
            chooser = member.name
        else:
            return
        utils.csv.update_next_movie(args[0], args[1], chooser)
        return

    # Validate member
    member = await utils.discord.get_member(bot_info_channel, args[1])
    if member:
        chooser = member.name
    else:
        return

    # Search movie
    ia = imdb.IMDb()
    candidates = ia.search_movie(args[0])
    await bot_info_channel.send("Searching for next movie")
    await bot_info_channel.send("'Y' to select movie")
    await bot_info_channel.send("'EXIT' to cancel search")
    await bot_info_channel.send("Input anything else to continue search")

    def check(message):
        if message.channel == ctx.channel:
            return True
        return False

    for c in candidates:
        if 'movie' in c['kind']:
            await bot_info_channel.send("Did you mean {}?".format(c['long imdb title']))
            msg = await bot.wait_for('message', check=check)
            if msg.content.upper() == 'Y':
                utils.csv.update_next_movie(c['title'], c['year'], chooser)
                await bot_info_channel.send("Yo we watching {}".format(c['long imdb title']))
                return
            elif msg.content.upper() == 'EXIT':
                await bot_info_channel.send("Exiting search")
                return

    await bot_info_channel.send("No movie found, please manually add: !choose-next-movie \"<title>\" <year> <chooser>")


@bot.command(name='next-movie',
             brief="Display the next movie",
             description="Displays the currently registered next movie.")
async def next_movie(ctx):
    guild = utils.discord.get_guild(bot, GUILD)
    bot_info_channel = utils.discord.get_channel(guild, 'bot-info')
    title, year, _ = utils.csv.get_next_movie()
    await bot_info_channel.send("We are watching {} ({})".format(title, year))


@bot.command(name='fuck',
             brief="Display information regarding the next movie",
             description="lol")
async def random_next_movie_info(ctx):
    guild = utils.discord.get_guild(bot, GUILD)
    bot_info_channel = utils.discord.get_channel(guild, 'bot-info')
    title, year, _ = utils.csv.get_next_movie()
    ia = imdb.IMDb()
    movie = ia.search_movie(title)[0]
    ia.update(movie)
    message = [
        "{} is a {} {} movie".format(movie['title'], movie['year'], random.choice(movie['genres'])),
        "{} directed {}".format(random.choice(movie['directors']), movie['title']),
        "{} acted in {}".format(random.choice(movie['cast']), movie['title']),
        "{} is spoken in {}".format(random.choice(movie['languages']), movie['title'])
    ]
    await bot_info_channel.send(random.choice(message))


@bot.command(name='score',
             brief="Display a user's score for a given movie",
             description="Displays a user's score for a given movie provided the user has already watched the movie.",
             usage="\"<title>\" <username>")
async def score(ctx, *args):
    guild = utils.discord.get_guild(bot, GUILD)
    bot_info_channel = utils.discord.get_channel(guild, 'bot-info')

    if len(args) != 2:
        await bot_info_channel.send("Usage: !score \"<title>\" <username>")

    title = args[0]
    name = args[1]

    member = await utils.discord.get_member(bot_info_channel, name)
    if not member:
        return
    member_name = member.name

    ia = imdb.IMDb()
    movie = ia.search_movie(title)
    if not movie:
        await bot_info_channel.send("Could not find {}".format(title))
        return

    imdb_title = movie[0]['title']

    entry = utils.csv.get_entry(imdb_title, member_name)
    if not entry:
        await bot_info_channel.send("{} did not watch {}".format(member_name, imdb_title))
        return

    await bot_info_channel.send("{} rated {} {:.2f}/10.00".format(member_name, imdb_title, float(entry.split('|')[1])))


@bot.command(name='scrape-images',
             brief="Download images",
             description="Downloads images from the screenshots channel.")
@commands.is_owner()
async def scrape_images(ctx):
    guild = utils.discord.get_guild(bot, GUILD)
    bot_info_channel = utils.discord.get_channel(guild, 'bot-info')
    ss_channel = utils.discord.get_channel(guild, 'screenshots')
    await bot_info_channel.send("Downloading screenshots")
    async for message in ss_channel.history(limit=None):
        await utils.discord.download_attachments(message.attachments)


@bot.command(name='backup',
             brief="Export data to backup",
             description="Exports movie record and scores to Google Sheets")
@commands.is_owner()
async def backup(ctx):
    guild = utils.discord.get_guild(bot, GUILD)
    bot_info_channel = utils.discord.get_channel(guild, 'bot-info')
    await bot_info_channel.send("Backing up data")

    sh = utils.sheets.get_sheet(utils.sheets.SHEET_BACKUP)
    csv_files = [str(p) for p in Path(utils.csv.CSV_PATH).glob('*.csv')]
    for csv_path in csv_files:
        worksheet_name = csv_path.split('.')[-2].split('/')[-1].split('\\')[-1]
        utils.sheets.export_csv_to_sheets(sh, csv_path, worksheet_name)


@bot.command(name='shutdown',
             brief="Shut the bot down",
             description="Shuts the bot down.")
@commands.is_owner()
async def shutdown(ctx):
    await bot.logout()

bot.run(TOKEN)