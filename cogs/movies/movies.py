from random import choice
from typing import Optional

import discord
import sqlalchemy
from discord import Embed
from discord.ext import commands
from discord_slash import cog_ext
from imdb import IMDb, IMDbError
from sqlalchemy import select, update
from sqlalchemy.future import Engine
from sqlalchemy.orm import Session

from cogs.movies.models import Movie
from utils.constants import EMBED_COLORS, GUILD_IDS
from utils.functions import generate_loading_embed


class Movies(commands.Cog):
    group_name = "movie"

    def __init__(self, bot: commands.Bot, db_engine: Engine):
        self.bot = bot
        self.db = db_engine
        self.imdb = IMDb()
        self.currently_watching: Optional[Movie] = None
        self.cinema_channel_id = 842199075960782878

    @cog_ext.cog_subcommand(
        base=group_name,
        name="list",
        guild_ids=GUILD_IDS,
        description="Returns the list of movies",
    )
    async def list_movies(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            message = await ctx.send(embed=generate_loading_embed())
            # List movies
            await message.edit(
                embed=Embed(title="ready :)", color=EMBED_COLORS["ready"])
            )

    @cog_ext.cog_subcommand(
        base=group_name,
        name="add",
        guild_ids=GUILD_IDS,
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
                        watched=False,
                    )
                except (IMDbError, KeyError):
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
                        title=f'{imdb_id} - {data["original title"]}',
                        description=f"IMDb rating: {data['rating']}",
                        color=EMBED_COLORS["ready"],
                    ),
                )

    @cog_ext.cog_subcommand(
        base=group_name,
        name="watch",
        guild_ids=GUILD_IDS,
        description="Select a random movie from the list"
        "You can also specify a movie ID that is already in the list",
    )
    async def watch_movie(self, ctx: commands.Context, imdb_id: int = None):
        message = await ctx.send(embed=generate_loading_embed())
        if self.currently_watching:
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
                    if chosen.watched:
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
                    select(Movie).filter_by(watched=False)
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

            self.currently_watching = chosen
            channel = discord.utils.get(
                ctx.guild.channels, id=self.cinema_channel_id
            )

            embed = Embed(
                title="The movie will begin right now!",
                color=EMBED_COLORS["ready"],
            )
            embed.add_field(
                name=f"{chosen.title} ({chosen.year})",
                value=f"IMDb rating: {chosen.rating}",
            )

            await message.edit(embed=embed)

            await channel.edit(name=f"🎬🔴 {chosen.title}")

    @cog_ext.cog_subcommand(
        base=group_name,
        name="stop",
        guild_ids=GUILD_IDS,
        description="Resets channel name and set the current movie as watched",
    )
    async def stop_watching(self, ctx: commands.Context):
        message = await ctx.send(embed=generate_loading_embed())

        if not self.currently_watching:
            await message.edit(
                embed=Embed(
                    title="No movie being watched", color=EMBED_COLORS["error"]
                )
            )
            return

        with Session(self.db) as session:
            session.execute(
                update(Movie)
                .where(Movie.imdb_id == self.currently_watching.imdb_id)
                .values(watched=True)
            )
            session.flush()
            session.commit()

        channel = discord.utils.get(
            ctx.guild.channels, id=self.cinema_channel_id
        )
        await channel.edit(name=f"Assistindo nada 😴")

        await message.edit(
            embed=Embed(title="Done :)", color=EMBED_COLORS["ready"])
        )
