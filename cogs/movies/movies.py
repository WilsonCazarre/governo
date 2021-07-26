import datetime
from random import choice
from typing import Dict

import discord
from discord import Embed
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option
from imdb import IMDb, IMDbError
from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.future import Engine
from sqlalchemy.orm import Session

from cogs.movies.models import Movie, ConfigVariable
from utils.constants import EMBED_COLORS, GUILD_CONFIG_VARIABLES
from utils.functions import generate_loading_embed


class MovieCogNotConfigured(Exception):
    pass


class Movies(commands.Cog):
    group_name = "movie"

    def __init__(self, bot: commands.Bot, db_engine: Engine):
        self.bot = bot
        self.db = db_engine
        self.imdb = IMDb()
        self.currently_watching: Dict[int, Movie] = dict()
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

    def get_config_variables(self, guild_id: int):
        configs = dict()
        with Session(self.db) as session:
            for var_name in GUILD_CONFIG_VARIABLES:
                var_model = session.execute(
                    select(ConfigVariable).where(
                        ConfigVariable.guild_id == str(guild_id),
                        ConfigVariable.key == var_name,
                    )
                ).scalar_one()
                if var_model.value is None:
                    raise MovieCogNotConfigured
                configs[var_name] = var_model.value
        return configs

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
            for movie in session.execute(
                select(Movie).filter_by(guild_id=ctx.guild.id)
            ).all():
                movie = movie[0]
                emote = ":white_check_mark:" if movie.watched_date else ":x:"
                embed.add_field(
                    name=f"{emote} {movie.imdb_id} - {movie.title}",
                    value=f"IMDb rating: {movie.rating}"
                    f"{f' - Watched on: {movie.watched_date}' if movie.watched_date else ''}",
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
                    select(Movie).filter_by(
                        imdb_id=imdb_id, guild_id=ctx.guild.id
                    )
                ).scalar_one()
                await message.edit(
                    embed=Embed(
                        title="This movie is already in the list!",
                        color=EMBED_COLORS["error"],
                    )
                )
            except NoResultFound:
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
        description="Select a random movie from the list. "
        "You can also specify a movie ID that is already in the list",
    )
    async def watch_movie(self, ctx: commands.Context, imdb_id: int = None):
        message = await ctx.send(embed=generate_loading_embed("beep boop"))
        try:
            configs = self.get_config_variables(ctx.guild.id)
        except MovieCogNotConfigured:
            await message.edit(
                embed=Embed(
                    title="I am not ready :(",
                    description="Try to use `/movie set_mention` "
                    "and `/movie set_channel` to get me ready.",
                    color=EMBED_COLORS["error"],
                )
            )
            return
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
                        select(Movie).filter(
                            imdb_id=imdb_id,
                            guild_id=ctx.guild.id,
                        )
                    ).scalar_one()
                    if chosen.watched_date:
                        await message.edit(
                            embed=Embed(
                                title="This movie was already watched!",
                                color=EMBED_COLORS["error"],
                            )
                        )
                        return
                except NoResultFound:
                    await message.edit(
                        embed=Embed(
                            title="Movie is not on the list.",
                            color=EMBED_COLORS["error"],
                        )
                    )
                    return

            else:
                movies = session.execute(
                    select(Movie).filter_by(
                        watched_date=None, guild_id=ctx.guild.id
                    )
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
                id=int(configs["cinema_channel_id"]),
            )
            role = discord.utils.get(
                ctx.guild.roles,
                id=int(configs["cinema_role_id"]),
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
        try:
            configs = self.get_config_variables(ctx.guild.id)
        except MovieCogNotConfigured:
            await message.edit(
                embed=Embed(
                    title="I am not ready :(",
                    description="Try to use `/movie set_mention` "
                    "and `/movie set_channel` to get me ready.",
                    color=EMBED_COLORS["error"],
                )
            )
            return

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
                    == self.currently_watching[ctx.guild.id].imdb_id,
                    Movie.guild_id == ctx.guild.id,
                )
                .values(watched_date=datetime.datetime.now())
            )
            session.flush()
            session.commit()

        channel = discord.utils.get(
            ctx.guild.channels,
            id=int(configs["cinema_channel_id"]),
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
        options=[
            create_option(
                name="voice_channel",
                description="The voice channel to watch movies on",
                option_type=7,
                required=True,
            )
        ],
    )
    async def set_cinema_channel(self, ctx: commands.Context, voice_channel):
        message = await ctx.send(embed=generate_loading_embed())

        with Session(self.db) as session:
            session.execute(
                update(ConfigVariable)
                .where(
                    ConfigVariable.guild_id == str(ctx.guild.id),
                    ConfigVariable.key == "cinema_channel_id",
                )
                .values(value=voice_channel.id)
            )
            session.flush()
            session.commit()

        await voice_channel.edit(name=self.default_idle_message, bitrate=96000)
        await message.edit(
            embed=Embed(
                title="Channel updated",
                description=f"{voice_channel.mention} "
                f"will now be used to watch movies :)",
                color=EMBED_COLORS["ready"],
            )
        )

    @cog_ext.cog_subcommand(
        base=group_name,
        name="set_mention",
        description="Set the role that will be mentioned "
        "when a new movie is choose",
        options=[
            create_option(
                name="role",
                description="The role to be mentioned",
                option_type=8,
                required=True,
            )
        ],
    )
    async def set_mention(self, ctx: commands.Context, role):
        message = await ctx.send(embed=generate_loading_embed())

        with Session(self.db) as session:
            session.execute(
                update(ConfigVariable)
                .where(
                    ConfigVariable.key == "cinema_role_id",
                    ConfigVariable.guild_id == str(ctx.guild.id),
                )
                .values(value=role.id)
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

    @cog_ext.cog_subcommand(
        base=group_name,
        name="remove",
        description="Removes a movie from the list",
    )
    async def remove_movie(self, ctx: commands.Context, imdb_id: int):
        message = await ctx.send(embed=generate_loading_embed())
        with Session(self.db) as session:
            try:
                movie = session.execute(
                    select(Movie).filter_by(
                        imdb_id=imdb_id, guild_id=ctx.guild.id
                    )
                ).scalar_one()
            except NoResultFound:
                await message.edit(
                    embed=Embed(
                        title="This movie is not on the list",
                        color=EMBED_COLORS["error"],
                    )
                )
                return
            session.delete(movie)
            session.flush()
            session.commit()
            await message.edit(
                embed=Embed(
                    title="Movie removed :)", color=EMBED_COLORS["ready"]
                )
            )
