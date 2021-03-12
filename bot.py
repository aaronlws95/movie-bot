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

@bot.command(name='start-vote')
async def start_scoring(ctx, *args):
    if len(args) == 0:
        await ctx.send("Usage: !start-vote <initial/final>")
        return
    elif args[0] not in ['initial', 'final']:
        await ctx.send("Usage: !start-vote <initial/final>")
        return    

    args[0] = args[0].lower()

    guild = get_guild()

    general_channel = get_channel(guild, 'general')
    await general_channel.send("{} scoring has begun.".format(args[0].capitalize()))

    scores_channel = get_channel(guild, 'scores')
    await scores_channel.send("**{}**".format(args[0].capitalize()))

    general_voice_channel = get_channel(guild, 'General', voice=True)
    participants = general_voice_channel.members

    for p in participants:
        channel = await p.create_dm()
        await channel.send("Please DM me your {} score.".format(args[0]))

    await general_channel.send("Waiting for everyone to give a score.")


bot.run(TOKEN)