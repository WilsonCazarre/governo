import os
import random

import discord
import json

from discord import VoiceChannel
from discord.ext.commands import errors
from imdb import IMDb, IMDbError
from discord.ext import commands

from constants import BASE_DIR


class Movies(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.movies_list = []
        self.current_watching = None
        self.cinema_channel_id = None
        self.mention_id = None
        self.load_movies_file()
        self.imdb = IMDb()

    def load_movies_file(self):
        file_path = os.getenv("MOVIES_COG_FILE")
        with open(BASE_DIR / file_path, "r") as infile:
            file_content = json.load(infile)
            try:

                self.movies_list = file_content["movies_list"]
                self.cinema_channel_id = file_content["cinema_channel_id"]
                self.mention_id = file_content["mention_id"]
            except KeyError as e:
                print(f"{e.args} is not set in movies config file")

    def save_movies_file(self):
        file_path = os.getenv("MOVIES_COG_FILE")
        with open(BASE_DIR / file_path, "w") as outfile:
            json.dump(
                {
                    "cinema_channel_id": int(self.cinema_channel_id),
                    "movies_list": self.movies_list,
                    "mention_id": self.mention_id,
                },
                outfile,
            )

    @commands.group(pass_context=True, name="movie")
    async def movie_group(self, ctx: commands.Context):
        """
        Movie list related commands. Type $help movie for more info.
        """
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Movies list",
                description=":white_check_mark:=Watched    :x:=Not Watched",
            )
            movie_list = sorted(self.movies_list, key=lambda m: m["watched"])
            for movie in movie_list:
                emote = ":white_check_mark:" if movie["watched"] else ":x:"
                embed.add_field(
                    name=f'{emote} {movie["title"]} ({movie["year"]})',
                    value=f"IMDb rating: {movie['rating']}",
                    inline=False,
                )
            await ctx.send(embed=embed)

    @movie_group.command(pass_context=True, name="add")
    async def add_movie(self, ctx: commands.Context, imdb_id):
        """
        Adds a movie to the list. You must specify the IMDb id of the movie.
        """
        if imdb_id in map(lambda x: x["id"], self.movies_list):
            await ctx.send("The movie is already on the list!")
        else:
            message = await ctx.send("Searching for your movie...")
            try:
                movie = self.imdb.get_movie(imdb_id)
                self.movies_list.append(
                    {
                        "id": imdb_id,
                        "title": movie.data["original title"],
                        "year": movie.data["year"],
                        "rating": movie.data["rating"],
                        "watched": False,
                    }
                )
                self.save_movies_file()
                embed = discord.Embed(
                    title=f'{imdb_id} - {movie.data["original title"]}',
                    description=f"IMDb rating: {movie.data['rating']}",
                )
                await message.edit(content=f"New movie added", embed=embed)
            except IMDbError or KeyError:
                await message.edit(content="Invalid movie ID")

    @movie_group.command(pass_context=True, name="watch")
    async def start_watching(self, ctx: commands.Context):
        """
        Selects a random movie from the list and changes the voice channel name
        """
        if self.current_watching:
            await ctx.send("A movie is already being watched")
        else:
            channel = discord.utils.get(
                ctx.guild.channels, id=self.cinema_channel_id
            )
            # getting all the non-watched movies in the list
            movie = random.choice(
                [m for m in self.movies_list if not m["watched"]]
            )
            self.current_watching = movie
            embed = discord.Embed(
                title=movie["title"],
                description=f'IMDb rating: {movie["rating"]}',
            )
            await ctx.send(
                f"🎬 The movie will begin soon! {self.mention_id}", embed=embed
            )
            await channel.edit(name=f"🎬🔴 {movie['title']}")

    @movie_group.command(pass_context=True, name="stop")
    async def stop_watching(self, ctx: commands.Context):
        """
        Resets the channel name and mark the current movie as watched
        """

        if self.current_watching:
            channel = discord.utils.get(
                ctx.guild.channels, id=self.cinema_channel_id
            )
            movie_index = self.movies_list.index(self.current_watching)
            self.movies_list[movie_index]["watched"] = True
            self.current_watching = None
            self.save_movies_file()
            await channel.edit(name=f"Assistindo nada 😴")
        else:
            await ctx.send("There's no movie being watched 😴")

    @movie_group.command(pass_context=True, name="set_channel")
    async def set_channel(self, ctx: commands.Context, new_id):
        """
        Changes the channel that is used for the Cinema.
        """
        try:
            new_id = int(new_id)
        except ValueError:
            await ctx.send("Channel ID should be an integer")
            return
        try:
            new_channel = next(
                filter(
                    lambda ch: ch.id == new_id
                    and isinstance(ch, VoiceChannel),
                    ctx.guild.channels,
                )
            )
        except StopIteration:
            await ctx.send("There's no voice channel with this id")
            return

        self.cinema_channel_id = new_id
        self.save_movies_file()

        await ctx.send(f"Cinema channel is now set to {new_channel.mention}")

    @set_channel.error
    async def on_run_server_error(
        self, ctx: commands.Context, error: errors.CommandError
    ):
        if isinstance(error, errors.MissingRequiredArgument):
            await ctx.send("You need to specify a channel ID")
        else:
            raise error

    @movie_group.command(pass_context=True, name="set_mention")
    async def set_mention(self, ctx: commands.Context, new_role):
        """
        Changes the mention role that is used for the Cinema.
        """
        try:
            next(
                filter(
                    lambda role: role.mention == new_role,
                    ctx.guild.roles,
                )
            )
        except StopIteration:
            await ctx.send("The specified mention does not exist")
            return

        self.mention_id = new_role
        self.save_movies_file()

        await ctx.send(
            f"Ok, I'll mention {new_role} every time we chose a movie!"
        )
