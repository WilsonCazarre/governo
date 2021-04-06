import os
import subprocess

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

memory = "4096M"
minecraft_executable = os.getenv("MINECRAFT_EXECUTABLE")
minecraft_command = f'java -Xmx{memory} -Xms{memory} -jar {minecraft_executable} nogui'
process: subprocess.Popen = None

bot = commands.Bot(command_prefix='$')


@bot.command()
async def start(ctx):
    process = subprocess.Popen(minecraft_command)
    ctx.send('Server started')


@bot.command()
async def stop(ctx):
    if process:
        ctx.send('Server stopped')


@bot.command()
async def log(ctx):
    if process:
        ctx.send(process.stdout)

bot.run(os.getenv('TOKEN'))
