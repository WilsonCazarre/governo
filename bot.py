import discord
from discord.ext import commands
from discord.ext.commands import errors
from dotenv import load_dotenv

from cogs.help import Help
from cogs.movies import Movies
from utils import get_env_variable

load_dotenv()

memory = "4096M"

bot = commands.Bot(command_prefix="$")


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


# @atexit.register
# def goodbye():
#     print("Trying to stop servers...")
#     if server.process.poll() is None:
#         server.stop()


# Not loading those cogs, cuz server is down
# bot.add_cog(Backups(bot, server))
# bot.add_cog(MinecraftCog(bot))
bot.add_cog(Movies(bot))
bot.add_cog(Help(bot))

bot.run(get_env_variable("TOKEN"))
