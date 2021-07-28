from cogs.aternos.api import AternosAPI
from discord import Embed
from discord.ext import commands
from discord_slash import cog_ext

from utils.constants import EMBED_COLORS
from utils.functions import generate_loading_embed


class Aternos(commands.Cog):
    group_name = "aternos"

    def __init__(self, bot: commands.Bot, aternos_api: AternosAPI):
        self.bot = bot
        self.aternos_api = aternos_api

    @cog_ext.cog_subcommand(
        base=group_name,
        name="start",
        description="Start the server configured on Aternos",
        guild_ids=[691057767024295997],
    )
    async def start(self, ctx: commands.Context):
        message = await ctx.send(embed=generate_loading_embed())
        try:
            self.aternos_api.start_server()
        except AttributeError:
            await message.edit(
                content=ctx.author.mention,
                embed=Embed(
                    title=":(",
                    description="Error while starting the server, you can "
                    "wait and try to run the command again",
                    color=EMBED_COLORS["error"],
                ),
            )
            return
        embed = Embed(
            title="Server is starting",
            description="You can check the server status inside Minecraft",
            color=EMBED_COLORS["ready"],
        )
        embed.add_field(
            name="Server address", value=self.aternos_api.server_address
        )
        await message.edit(content=ctx.author.mention, embed=embed)
