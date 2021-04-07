import atexit

import discord
from discord.ext import commands
from discord.ext.commands import errors
from dotenv import load_dotenv

from server import Server
from utils import get_env_variable
from constants import DISCORD_MAX_BODY_LENGTH

load_dotenv()

memory = "4096M"

server: Server = Server(memory)
bot = commands.Bot(command_prefix='$')


@bot.command(name='list')
async def list_servers(ctx: commands.Context):
    embed = discord.Embed(
        title="Servidores",
        description="Essa é a lista de servidores disponíveis para uso"
    )
    servers = server.discover_paths()
    for s in range(len(servers)):
        embed.add_field(name=servers[s], value=f'ID: {s + 1}', inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def stop_server(ctx: commands.Context):
    server.stop()
    await bot.change_presence(status=discord.Status.idle)
    await ctx.send('Server was stopped')


@bot.command()
async def run_server(ctx: commands.Context, server_id: int):
    await stop_server(ctx)
    server.run(server_id - 1)
    await bot.change_presence(activity=discord.Game(
        name=f"Hosting {server.paths[server_id - 1].name}")
    )
    await ctx.send('Server is running')


@run_server.error
async def on_run_server_error(ctx: commands.Context, error: errors.CommandError):
    if isinstance(error, errors.MissingRequiredArgument):
        await ctx.send('Você precisa especificar um ID para o servidor.')
    else:
        raise error


@bot.command()
async def log_server(ctx: commands.Context):
    await ctx.send('logging...')
    with open('server_log.txt', 'r') as log_file:
        message = ''
        for line in log_file.readlines():
            if len(message) + len(line) >= DISCORD_MAX_BODY_LENGTH:
                await ctx.send(f"```{message}```")
                message = ''
            message += line

        if len(message) == 0:
            await ctx.send('Nothing to log yet')
        else:
            await ctx.send(f"```{message}```")


@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.idle
    )
    print(f'Cheers love, the {bot.user} is here!')


@bot.event
async def on_command_error(ctx: commands.Context, error: errors.CommandError):
    if isinstance(error, errors.CommandNotFound):
        await ctx.send("Looks like you're a little lost. "
                       "Try $help to see all the available commands.")
    else:
        raise error


@atexit.register
def goodbye():
    print("Stopping servers...")
    if server.process:
        server.process.kill()


bot.run(get_env_variable('TOKEN'))
