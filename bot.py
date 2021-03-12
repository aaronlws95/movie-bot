import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix='!')

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

@bot.event
async def on_ready():
    print(f'{bot.user.name} online')

@bot.command(name='start-score')
async def start_score(ctx, *args):
    # Args
    if len(args) == 0:
        await ctx.send("Usage: !start-score <initial/final>")
        return
    elif args[0] not in ['initial', 'final']:
        await ctx.send("Usage: !start-score <initial/final>")
        return    
    mode = args[0].lower()

    # Setup
    guild = get_guild()
    general_channel = get_channel(guild, 'general')
    scores_channel = get_channel(guild, 'scores')
    general_voice_channel = get_channel(guild, 'General', voice=True)

    # Participants
    participants = general_voice_channel.members

    if not participants:
        await general_channel.send("No participants.")
        return

    # Start
    await general_channel.send("{} scoring has started.".format(mode.capitalize()))
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

bot.run(TOKEN)