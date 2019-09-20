from discord import Server, Member
from typing import List
from ..commands import unsafe_always_command, command, command_help
from ..util import output, getrole
from ..config import get_config
from ..client import client
from ..permissions import isbanned, bantypes
import logging
import asyncio
import bottom
import re


# List of messages relayed to IRC. Prevent getting kicked for repeated messages.
last_messages = [None] * 3  # type: List[str]

# Functions that do message modification before sending to IRC
# Take message, author, discord server, irc client
irc_transforms = []


def irc_transform(func):
    irc_transforms.append(func)
    logger.debug(func.__name__)
    return func

# Functions that do message modification before sending to Discord
# Take message, author, irc client, discord server
discord_transforms = []


def discord_transform(func):
    discord_transforms.append(func)
    return func

#irc_client = irc_client = bottom.Client(
#    host=get_config("mainserver.irc.irc.address"),
#    port=get_config("mainserver.irc.irc.port"),
#    loop=asyncio.get_event_loop(),
#    ssl=True
#)
irc_client = None
logger = logging.getLogger(__name__)
messagelogger = logging.getLogger("IRC")
MENTION_RE = re.compile(r"<@!?(\d+)>")
ROLE_RE = re.compile(r"<@&(\d+)>")
CHANNEL_RE = re.compile(r"<#(\d+)>")
EMOJI_RE = re.compile(r"<:(.+):(\d+)>")
IRC_MENTION_RE = re.compile(r"@([^@]+?)@")
IGNORED_NAMES = {"travis-ci", "vg-bot", "py-ctcp", "MrStonedOne"}


async def unload(loop=None):
    logger.info("Dropping IRC connection.")
    await irc_client.disconnect()


#@irc_client.on("client_connect")
async def connect(**kwargs):
    logger.info("Connected")
    irc_client.send("NICK", nick=get_config("mainserver.irc.irc.user.nick"))
    irc_client.send("USER", user=get_config("mainserver.irc.irc.user.name"), realname=get_config("mainserver.irc.irc.user.realname"))

    done, pending = await asyncio.wait(
        [irc_client.wait("RPL_ENDOFMOTD"),
         irc_client.wait("ERR_NOMOTD")],
        loop=irc_client.loop,
        return_when=asyncio.FIRST_COMPLETED
    )

    for future in pending:
        future.cancel()

    irc_client.send('JOIN', channel=get_config("mainserver.irc.irc.channel"))

#asyncio.ensure_future(irc_client.connect(), loop=irc_client.loop)


#@irc_client.on("PRIVMSG")
async def message(nick, target, message, **kvargs):
    if nick in IGNORED_NAMES:
        return

    messagelogger.info(message)
    channel = client.get_channel(str(get_config("mainserver.irc.discord.channel")))

    content = message

    for func in discord_transforms:
        content = func(content, nick, channel.server, irc_client)

    await output(channel, "\u200B**IRC:** `<{}>` {}".format(nick, content))


#@irc_client.on('PING')
def keepalive(message, **kwargs):
    irc_client.send('PONG', message=message)


#@unsafe_always_command()
async def ircrelay(message):
    if isbanned(message.author, bantypes.irc):
        return

    if len(message.content) == 0 or message.content[0] == "\u200B" or message.channel.id != str(get_config("mainserver.irc.discord.channel")):
        return

    content = message.content

    # Yes, I could use a loop.
    # Know what a loop would do? Bloat this line count way too bloody much.
    if content == last_messages[0] == last_messages[1] == last_messages[2]:
        return

    if len(last_messages) == 3:
        last_messages.pop(0)

    last_messages.append(content)

    for func in irc_transforms:
        content = func(content, message.author, irc_client, message.server)

    # Insert a zero-width space so people with the same name on IRC don't get pinged.
    author = prevent_ping(message.author.name)

    try:
        irc_client.send("PRIVMSG", target=get_config("mainserver.irc.irc.channel"), message="<{}> {}".format(author, content))
    except RuntimeError:
        pass

"""
@command_help("irc", "Commands for interacting with IRC.", "irc who")
@command("irc who")
async def irc_command(content, match, message):
    """


def prevent_ping(name: str):
    return name[:1] + "\u200B" + name[1:]


#@irc_transform
def convert_disc_mention(message, author, irc_client, discord_server):
    try:
        return MENTION_RE.sub(lambda match: "@{}".format(prevent_ping(discord_server.get_member(match.group(1)).name)), message)
    except:
        return message


#@irc_transform
def convert_disc_channel(message, author, irc_client, discord_server: Server):
    try:
        return CHANNEL_RE.sub(lambda match: "#{}".format(discord_server.get_channel(match.group(1)).name), message)

    except:
        return message


#@irc_transform
def convert_role_mention(message, author, irc_client, discord_server: Server):
    try:
        return ROLE_RE.sub(lambda match: "@{}".format(getrole(discord_server, match.group(1)).name), message)

    except:
        return message


#@irc_transform
def convert_custom_emoji(message, author, irc_client, discord_server: Server):
    try:
        return EMOJI_RE.sub(lambda match: ":{}:".format(match.group(1)), message)

    except:
        return message


#@discord_transform
def convert_irc_mention(message, author, discord_server, irc_client):
    try:
        return IRC_MENTION_RE.sub(lambda match: "<@{}>".format(discord_server.get_member_named(match.group(1)).id), message)
    except:
        return message
