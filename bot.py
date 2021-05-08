import atexit

import discord
from discord.ext import commands
from discord.ext.commands import errors
from dotenv import load_dotenv

from cogs.help import Help
from server import Server
from utils import get_env_variable
from constants import DISCORD_MAX_BODY_LENGTH, SERVER_HOST_NAME

load_dotenv()

memory = "4096M"

server: Server = Server(memory)
bot = commands.Bot(command_prefix="$")


@bot.command(name="list")
async def list_servers(ctx: commands.Context):
    """
    Lists all the available servers.
    """
    embed = discord.Embed(
        title="Minecraft versions",
        description="This are the available servers to run",
    )
    servers = server.discover_paths()
    for s in range(len(servers)):
        embed.add_field(name=servers[s], value=f"ID: {s + 1}", inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def stop_server(ctx: commands.Context):
    """
    Stops the current running server.
    """
    if server.process.poll() is None:
        await ctx.send("Shutting down internal server...")
        server.stop()
        await bot.change_presence(status=discord.Status.idle)
        await ctx.send("Server was stopped")
    else:
        await ctx.send("There's no server running...")


@bot.command()
async def run_server(ctx: commands.Context, server_id: int):
    """
    Runs the server with the specified ID.
    A list of the available server can be retrieved with the "list" command.
    This command will always try to stop a running server before starting a new
    one.
    """
    server.stop()
    server.run(server_id - 1)
    server_name = server.paths[server_id - 1].name
    await bot.change_presence(
        activity=discord.Game(name=f"Hosting {server_name}")
    )
    await ctx.send(
        embed=discord.Embed(
            title=f"{server_name} is yours",
            description=f"Your server is currently running and can be accessed "
            f"**{SERVER_HOST_NAME}**",
        )
    )


@run_server.error
async def on_run_server_error(
    ctx: commands.Context, error: errors.CommandError
):
    if isinstance(error, errors.MissingRequiredArgument):
        await ctx.send("Você precisa especificar um ID para o servidor.")
    else:
        raise error


@bot.command()
async def log_server(ctx: commands.Context):
    """
    Returns the java process log of the running server.
    """
    if server.process.poll() is None:
        with open("server_log.txt", "r") as log_file:
            message = ""
            for line in log_file.readlines():
                if len(message) + len(line) >= DISCORD_MAX_BODY_LENGTH:
                    await ctx.send(f"```{message}```")
                    message = ""
                message += line

            if len(message) == 0:
                await ctx.send("Nothing to log yet")
            else:
                await ctx.send(f"```{message}```")
    else:
        await ctx.send(
            embed=discord.Embed(
                title="No server running",
                description=f"You can start one by running {ctx.prefix}run_server <server_id>",
            )
        )


@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.idle)
    print(f"Cheers love, the {bot.user} is here!")


@bot.event
async def on_command_error(ctx: commands.Context, error: errors.CommandError):
    if isinstance(error, errors.CommandNotFound):
        await ctx.send(
            "Looks like you're a little lost. "
            "Try $help to see all the available commands."
        )
    else:
        raise error


@atexit.register
def goodbye():
    print("Trying to stop servers...")
    if server.process.poll() is None:
        server.stop()


bot.add_cog(Help(bot))

bot.run(get_env_variable("TOKEN"))
