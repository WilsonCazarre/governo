import os
import random

import discord
import json
from imdb import IMDb, IMDbError
from discord.ext import commands

from constants import BASE_DIR


class Movies(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.movies_list = []
        self.current_watching = None
        self.cinema_channel_id = None
        self.load_movies_file()
        self.imdb = IMDb()

    def load_movies_file(self):
        file_path = os.getenv("MOVIES_COG_FILE")
        with open(BASE_DIR / file_path, "r") as infile:
            file_content = json.load(infile)
            self.movies_list = file_content["movies_list"]
            self.cinema_channel_id = file_content["cinema_channel_id"]

    def save_movies_file(self):
        file_path = os.getenv("MOVIES_COG_FILE")
        with open(BASE_DIR / file_path, "w") as outfile:
            json.dump(
                {
                    "cinema_channel_id": self.cinema_channel_id,
                    "movies_list": self.movies_list,
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
            await ctx.send("🎬 The movie will begin right now!", embed=embed)
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

    @movie_group.command(pass_context=True, name="change_channel")
    async def change_channel(self, ctx: commands.Context, new_id):
        """
        Changes the channel that is used for the Cinema.
        """
        self.cinema_channel_id = new_id
        self.save_movies_file()
        await ctx.send("New ID saved.")
