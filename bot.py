import os
import atexit

from discord import Embed
from discord.ext import commands
from dotenv import load_dotenv

from server import Server

load_dotenv()

memory = "4096M"

server: Server = Server(memory)
bot = commands.Bot(command_prefix='$')


@bot.command(name='list')
async def list_servers(ctx: commands.Context):
    embed = Embed(title="Servidores",
                  description="Essa é a lista de servidores disponíveis para uso")
    servers = server.discover_paths()
    for s in range(len(servers)):
        embed.add_field(name=servers[s], value=f'ID: {s + 1}', inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def stop_server(ctx: commands.Context):
    server.stop()
    await ctx.send('Server was stopped')


@bot.command()
async def run_server(ctx: commands.Context, server_id: int):
    await stop_server(ctx)
    server.run(server_id - 1)
    await ctx.send('Server is running')


@bot.command()
async def log_server(ctx: commands.Context):
    await ctx.send('logging...')
    with open('server_log.txt', 'r') as log_file:
        message = ''
        for line in log_file.readlines():
            message += line
        await ctx.send(f"```{message}```")


@bot.event
async def on_ready():
    print(f'Cheers love, the {bot.user} is here!')


@atexit.register
def goodbye():
    print("Stopping servers...")
    if server.process:
        server.process.kill()


bot.run(os.getenv('TOKEN'))
