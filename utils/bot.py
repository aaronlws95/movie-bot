import discord

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