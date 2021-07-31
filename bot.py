import os

import discord
from discord import Guild
from discord_slash import SlashCommand
from discord.ext import commands
from discord.ext.commands import errors
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from cogs.help import Help
from cogs.movies.models import Base, ConfigVariable
from cogs.movies import Movies
from utils.constants import GUILD_CONFIG_VARIABLES
from utils.functions import get_env_variable

load_dotenv()

memory = "4096M"

bot = commands.Bot(command_prefix="$")
slash = SlashCommand(bot, sync_commands=True, sync_on_cog_reload=True)

I_AM_HEROKU = os.getenv("I_AM_HEROKU") == "true"
if I_AM_HEROKU:
    DATABASE_URL: str = get_env_variable("DATABASE_URL").replace(
        "postgres", "postgresql"
    )
else:
    DATABASE_URL: str = "sqlite:///db.sqlite3"
engine = create_engine(DATABASE_URL, echo=True, future=True)
Base.metadata.create_all(engine)

bot.add_cog(Movies(bot, engine))
bot.add_cog(Help(bot))


@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    print(f"Cheers love, the {bot.user} is here!")


@bot.event
async def on_guild_join(guild: Guild):
    print(f"New Guild joined: {guild.name} - Creating config vars")
    with Session(engine) as session:
        for var in GUILD_CONFIG_VARIABLES:
            session.add(ConfigVariable(guild_id=guild.id, key=var, value=None))
        session.flush()
        session.commit()


@bot.event
async def on_command_error(ctx: commands.Context, error: errors.CommandError):
    if isinstance(error, errors.CommandNotFound):
        await ctx.send(
            "Looks like you're a little lost. "
            "Try $help to see all the available commands."
        )
    else:
        raise error


bot.run(get_env_variable("TOKEN"))
