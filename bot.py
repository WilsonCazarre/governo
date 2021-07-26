import discord
from discord_slash import SlashCommand
from discord.ext import commands
from discord.ext.commands import errors
from dotenv import load_dotenv
from sqlalchemy import create_engine

from cogs.help import Help
from cogs.movies.models import Base
from cogs.movies.movies import Movies
from utils.functions import get_env_variable

load_dotenv()

memory = "4096M"

bot = commands.Bot(command_prefix="$")
slash = SlashCommand(bot, sync_commands=True, sync_on_cog_reload=True)


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


DATABASE_URL: str = get_env_variable("DATABASE_URL")
engine = create_engine(
    DATABASE_URL.replace("postgres", "postgresql"), echo=False, future=True
)
Base.metadata.create_all(engine)

bot.add_cog(Movies(bot, engine))
bot.add_cog(Help(bot))

bot.run(get_env_variable("TOKEN"))
