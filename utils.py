import os

import discord
from discord.ext import commands
from mcstatus import MinecraftServer
from mcstatus.pinger import PingResponse

import exceptions
from constants import SERVER_HOST_NAME


def get_env_variable(name: str):
    try:
        return os.environ[name]
    except KeyError:
        raise exceptions.MissingEnvironmentVariable(
            f'"{name}" is not set in the environment. Check your .env file or'
            f"create one if you don't have it."
        )


async def update_status(bot: commands.Bot):
    try:
        status: PingResponse = await MinecraftServer(
            host=SERVER_HOST_NAME
        ).async_status()
    except Exception as e:
        await bot.change_presence(status=discord.Status.idle)
        raise e

    await bot.change_presence(activity=discord.Activity(
        name=f"Hosting {status.description['text']}",
        type=discord.ActivityType.playing, details=status.version.name,
        state="Playing solo",
        assets={'large_image': 'mc_logo', 'small_image': 'mc_logo', })
    )
    return status
