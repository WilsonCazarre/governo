from typing import Optional

import discord
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.bot.remove_command("help")

    @staticmethod
    async def get_help_for_command(
        ctx: commands.Context, command: commands.Command
    ):

        embed = discord.Embed(title=command.name, description=command.help)
        if command.signature:
            embed.add_field(
                name="**How to use (syntax)**",
                value=f"{command.name} {command.signature}",
            )

        await ctx.send(embed=embed)

    async def get_general_help(
        self,
        ctx: commands.Context,
    ):
        embed = discord.Embed(
            title="🤔 Command Help!",
            description=f"Type {ctx.prefix}help [command_name] "
            f"to get help on a specific command.",
        )
        current_cmd: commands.Command
        for current_cmd in self.bot.commands:
            embed.add_field(
                name=f"{current_cmd.name} {current_cmd.signature}",
                value=current_cmd.short_doc
                if current_cmd.short_doc
                else "No description given.",
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command(name="help")
    async def show_help(
        self, ctx: commands.Context, command_name: Optional[str]
    ):
        """
        Help with commands.
        """
        if command_name:
            for command in self.bot.commands:
                if command.name == command_name:
                    await self.get_help_for_command(ctx, command)
                    break
            else:
                await ctx.send(
                    embed=discord.Embed(
                        title="Command not found",
                        description=f'"{command_name}" is not a know command. '
                        f"Try {ctx.prefix}help to see all the "
                        "available commands.",
                    )
                )

        else:
            await self.get_general_help(ctx)
