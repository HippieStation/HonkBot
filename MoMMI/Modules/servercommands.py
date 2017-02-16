import logging
import struct
import asyncio
import subprocess
from urllib.parse import parse_qs
from ..client import client
from ..commands import command, command_help
from ..config import get_config
from .serverstatus import server_topic
from ..commloop import comm_event

logger = logging.getLogger(__name__)

@comm_event
async def updatenudge(msg):
    if msg["type"] != "update":
        return

    logger.info("Receiving am update message!")
    msg = msg["cont"]

    channel = client.get_channel("276456582500319244")
    if not channel:
        logger.error("Unable to get a reference to the channel! Is the ID incorrect?")
        return

    output = msg["content"].replace("@", "@ ^ ^ ")

    logger.info(output)
    await client.send_message(channel, output)


async def command_server(action, channel):
    p = subprocess.Popen('sudo systemctl {} byond.service'.format(action), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = ""
    for line in p.stdout.readlines():
        logger.info(line)
        output = output + str(line, 'utf-8')
    retval = p.wait()
    await client.send_message(channel, "```{}```\nreturned exit code: {}".format(output, retval))

async def update_server(channel):
    await client.send_message(channel, "Updating server")
    subprocess.Popen('/home/byond/updater.py', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

@command_help("server", "Controls the server", "server {action}", "The actions are 'status', 'stop', 'start', 'restart', 'update'")
@command("serv(?:er)\s*(\S*)", role=get_config("mainserver.roles.admin"))
async def stop_server_command(content, match, message):
    actions = ['status', 'stop', 'start', 'restart', 'update']
    action = match.group(1)

    if action == "":
        await client.send_message(message.channel, "Please refer to the instructions you can get by running the help command")
        return

    if action not in actions:
        await client.send_message(message.channel, "Invalid command, please refer to the instructions you can get by running the help command")
        return

    if action == "stop":
        await client.send_message(message.channel, "Stopping server")
        await command_server("stop", message.channel)
        return

    if action == "start":
        await client.send_message(message.channel, "Starting server")
        await command_server("start", message.channel)
        return

    if action == "status":
        await command_server("status", message.channel)
        return

    if action == "restart":
        await client.send_message(message.channel, "Restarting server")
        await command_server("stop", message.channel)
        await command_server("start", message.channel)
        return

    if action == "update":
        await update_server(message.channel)
        return

    await client.send_message(message.channel, action)
