import asyncio

from cogs.aternos.api import AternosAPI
from discord import Embed
from discord.ext import commands
from discord_slash import cog_ext

from utils.constants import EMBED_COLORS, TRUSTED_GUILD_IDS
from utils.functions import get_env_variable, generate_loading_embed


class Aternos(commands.Cog):
    group_name = "aternos"

    def __init__(self, bot: commands.bot):
        self.bot = bot
        self.aternos_api = AternosAPI(
            headers=get_env_variable("ATERNOS_HEADER_COOKIE"),
            TOKEN=get_env_variable("ATERNOS_TOKEN"),
        )

    def start_server_with_retries(self, retries):
        try:
            self.aternos_api.start_server()
        except AttributeError as e:
            print("Retrying server")
            if retries > 0:
                self.start_server_with_retries(retries - 1)
            else:
                raise e

    @cog_ext.cog_subcommand(
        base=group_name,
        name="start",
        description="Start the server configured on Aternos",
        guild_ids=TRUSTED_GUILD_IDS,
    )
    async def start(self, ctx: commands.Context):
        message = await ctx.send(embed=generate_loading_embed())
        try:
            self.start_server_with_retries(50)
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
        await message.edit(
            content=ctx.author.mention,
            embed=Embed(
                title="Server is starting",
                description="I'll ping you when its ready",
                color=EMBED_COLORS["ready"],
            ),
        )

        while self.aternos_api.get_status() != "Online":
            await asyncio.sleep(7)

        ip, _port, software = self.aternos_api.get_server_info().split(",")
        embed = Embed(
            title="Server is ready",
            color=EMBED_COLORS["ready"],
        )
        embed.add_field(name="Server Address", value=ip, inline=False)
        embed.add_field(
            name="Software (modpack)", value=software, inline=False
        )
        await ctx.send(content=ctx.author.mention, embed=embed)
