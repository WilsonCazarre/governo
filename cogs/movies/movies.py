import datetime
from random import choice
from typing import Dict

import discord
import sqlalchemy
from discord import Embed
from discord.ext import commands
from discord_slash import cog_ext
from imdb import IMDb, IMDbError
from sqlalchemy import select, update
from sqlalchemy.future import Engine
from sqlalchemy.orm import Session

from cogs.movies.models import Movie, ConfigVariable
from utils.constants import EMBED_COLORS, GUILD_IDS
from utils.functions import generate_loading_embed


class Movies(commands.Cog):
    group_name = "movie"

    def __init__(self, bot: commands.Bot, db_engine: Engine):
        self.bot = bot
        self.db = db_engine
        self.imdb = IMDb()
        self.currently_watching: Dict[str, Movie] = dict()
        self.default_idle_message = "Assistindo nada 😴"

    def get_config_variable(self, guild_id: int, var_name: str):
        with Session(self.db) as session:
            config_var = session.execute(
                select(ConfigVariable).where(
                    ConfigVariable.guild_id == str(guild_id),
                    ConfigVariable.key == var_name,
                )
            ).one()

        return config_var[0].value

    @cog_ext.cog_subcommand(
        base=group_name,
        name="list",
        description="Returns the list of movies",
    )
    async def list_movies(self, ctx: commands.Context):
        message = await ctx.send(embed=generate_loading_embed())
        embed = discord.Embed(
            title="Homies watchlist",
            description=":white_check_mark:=Watched    :x:=Not Watched",
            color=EMBED_COLORS["ready"],
        )
        with Session(self.db) as session:
            for movie in session.execute(select(Movie)).all():
                movie = movie[0]
                emote = ":white_check_mark:" if movie.watched_date else ":x:"
                embed.add_field(
                    name=f"{emote} {movie.title} ({movie.year})",
                    value=f"IMDb rating: {movie.rating}",
                    inline=False,
                )
        await message.edit(embed=embed)

    @cog_ext.cog_subcommand(
        base=group_name,
        name="add",
        description="Adds a new movie to the list, based on its IMDb ID. ",
    )
    async def add_movie(self, ctx: commands.Context, imdb_id: int):
        message = await ctx.send(
            embed=generate_loading_embed("Searching for your movie...")
        )
        with Session(self.db) as session:
            try:
                session.execute(
                    select(Movie).filter_by(imdb_id=imdb_id)
                ).scalar_one()
                await message.edit(
                    embed=Embed(
                        title="This movie is already in the list!",
                        color=EMBED_COLORS["error"],
                    )
                )
            except sqlalchemy.orm.exc.NoResultFound:
                try:
                    data = self.imdb.get_movie(imdb_id).data
                    new_movie = Movie(
                        imdb_id=imdb_id,
                        title=data["original title"],
                        year=data["year"],
                        rating=data["rating"],
                        guild_id=ctx.guild.id,
                    )
                except (IMDbError, KeyError) as e:
                    if e.args[0] == "original title":
                        new_movie = Movie(
                            imdb_id=imdb_id,
                            title=data["localized title"],
                            year=data["year"],
                            rating=data["rating"],
                            guild_id=ctx.guild.id,
                        )
                    else:
                        await message.edit(
                            embed=Embed(
                                title="Invalid movie ID",
                                color=EMBED_COLORS["error"],
                            )
                        )
                        return

                session.add(new_movie)
                session.flush()
                session.commit()
                await message.edit(
                    content="New Movie added",
                    embed=Embed(
                        title=f"{imdb_id} - {new_movie.title}",
                        description=f"IMDb rating: {new_movie.rating}",
                        color=EMBED_COLORS["ready"],
                    ),
                )

    @cog_ext.cog_subcommand(
        base=group_name,
        name="watch",
        description="Select a random movie from the list"
        "You can also specify a movie ID that is already in the list",
    )
    async def watch_movie(self, ctx: commands.Context, imdb_id: int = None):
        message = await ctx.send(embed=generate_loading_embed("beep boop"))
        if self.currently_watching.get(ctx.guild.id):
            await message.edit(
                embed=Embed(
                    title="A movie is already being watched!",
                    color=EMBED_COLORS["error"],
                )
            )
            return

        with Session(self.db) as session:
            if imdb_id:
                try:
                    chosen: Movie = session.execute(
                        select(Movie).filter_by(imdb_id=imdb_id)
                    ).scalar_one()
                    if chosen.watched_date:
                        await message.edit(
                            embed=Embed(
                                title="This movie was already watched!",
                                color=EMBED_COLORS["error"],
                            )
                        )
                        return
                except sqlalchemy.orm.exc.NoResultFound:
                    await message.edit(
                        embed=Embed(
                            title="Movie is not on the list.",
                            color=EMBED_COLORS["error"],
                        )
                    )
                    return

            else:
                movies = session.execute(
                    select(Movie).filter_by(watched_date=None)
                ).all()
                if not movies:
                    await message.edit(
                        embed=Embed(
                            title="All movies were watched!",
                            color=EMBED_COLORS["error"],
                        )
                    )
                    return

                chosen: Movie = choice(movies)[0]

            self.currently_watching[ctx.guild.id] = chosen
            channel = discord.utils.get(
                ctx.guild.channels,
                id=int(
                    self.get_config_variable(ctx.guild.id, "cinema_channel_id")
                ),
            )
            role = discord.utils.get(
                ctx.guild.roles,
                id=int(
                    self.get_config_variable(ctx.guild.id, "cinema_role_id")
                ),
            )

            embed = Embed(
                title="The movie will begin right now!",
                color=EMBED_COLORS["ready"],
            )
            embed.add_field(
                name=f"{chosen.title} ({chosen.year})",
                value=f"IMDb rating: {chosen.rating}",
            )

            await message.edit(content=role.mention, embed=embed)

            await channel.edit(name=f"🎬🔴 {chosen.title}")

    @cog_ext.cog_subcommand(
        base=group_name,
        name="stop",
        description="Resets channel name and set the current movie as watched",
    )
    async def stop_watching(self, ctx: commands.Context):
        message = await ctx.send(embed=generate_loading_embed())

        if not self.currently_watching.get(ctx.guild.id):
            await message.edit(
                embed=Embed(
                    title="No movie being watched", color=EMBED_COLORS["error"]
                )
            )
            return

        with Session(self.db) as session:
            session.execute(
                update(Movie)
                .where(
                    Movie.imdb_id
                    == self.currently_watching[ctx.guild.id].imdb_id
                )
                .values(watched_date=datetime.datetime.now())
            )
            session.flush()
            session.commit()

        channel = discord.utils.get(
            ctx.guild.channels,
            id=int(
                self.get_config_variable(ctx.guild.id, "cinema_channel_id")
            ),
        )
        await message.edit(
            embed=Embed(
                title="Movie tagged as watched :)",
                description=f"{self.currently_watching[ctx.guild.id].title} "
                f"({self.currently_watching[ctx.guild.id].year})",
                color=EMBED_COLORS["ready"],
            )
        )
        del self.currently_watching[ctx.guild.id]
        await channel.edit(name=self.default_idle_message)

    @cog_ext.cog_subcommand(
        base=group_name,
        name="set_channel",
        description="Set the channel that will be used to watch movies",
    )
    async def set_cinema_channel(self, ctx: commands.Context, channel_id: str):
        message = await ctx.send(embed=generate_loading_embed())
        channel = discord.utils.get(ctx.guild.channels, id=int(channel_id))
        if not channel:
            await message.edit(
                embed=Embed(
                    title="Channel not found", color=EMBED_COLORS["error"]
                )
            )
            return

        with Session(self.db) as session:
            session.execute(
                update(ConfigVariable)
                .where(
                    ConfigVariable.guild_id == str(GUILD_IDS[0]),
                    ConfigVariable.key == "cinema_channel_id",
                )
                .values(value=channel_id)
            )
            session.flush()
            session.commit()

        await channel.edit(name=self.default_idle_message, bitrate=96000)
        await message.edit(
            embed=Embed(
                title="Channel updated",
                description=f"{channel.mention} "
                f"will now be used to watch movies :)",
                color=EMBED_COLORS["ready"],
            )
        )

    @cog_ext.cog_subcommand(
        base=group_name,
        name="set_mention",
        description="Set the role that will be mentioned "
        "when a new movie is choose",
    )
    async def set_mention(self, ctx: commands.Context, mention_id: str):
        message = await ctx.send(embed=generate_loading_embed())
        role = discord.utils.get(ctx.guild.roles, id=int(mention_id))
        if not role:
            await message.edit(
                embed=Embed(
                    title="Channel not found", color=EMBED_COLORS["error"]
                )
            )
            return

        with Session(self.db) as session:
            session.execute(
                update(ConfigVariable)
                .where(
                    ConfigVariable.key == "cinema_role_id",
                    ConfigVariable.guild_id == str(GUILD_IDS[0]),
                )
                .values(value=mention_id)
            )
            session.flush()
            session.commit()

        await message.edit(
            embed=Embed(
                title="Role Updated",
                description=f"Ok, I'll mention {role.mention} "
                f"when a new movie is choose",
                color=EMBED_COLORS["ready"],
            )
        )
