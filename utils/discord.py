import discord
from pathlib import Path

# Path
SS_PATH = "data/screenshots"


def get_guild(bot, name):
    guild = discord.utils.get(bot.guilds, name=name)
    if not guild:
        raise ValueError("{} guild does not exist".format(name))
    return guild


def get_channel(guild, name, voice=False):
    if voice:
        channel = discord.utils.get(guild.voice_channels, name=name)
    else:
        channel = discord.utils.get(guild.channels, name=name)
    if not channel:
        raise ValueError("{} channel does not exist".format(name))
    return channel


async def get_member(channel, name):
    member = discord.utils.get(channel.guild.members, name=name)
    if not member:
        await channel.send("I dont recognise {}".format(name))
    return member


async def download_attachments(attachments):
    Path(SS_PATH).mkdir(parents=True, exist_ok=True)
    for a in attachments:
        file_format = a.filename.split('.')[-1]
        filename = str(a.id) + '.' + file_format
        print("Downloaded {}".format(filename))
        await a.save(SS_PATH + "/" + filename)