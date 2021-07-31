import os
from typing import Optional
from random import choice

import discord

from utils import exceptions

from utils.constants import GOOGLE_API_SECRETS, LOADING_MESSAGES, EMBED_COLORS

SCOPES = ["https://www.googleapis.com/auth/drive"]


def get_env_variable(name: str):
    try:
        return os.environ[name]
    except KeyError:
        raise exceptions.MissingEnvironmentVariable(
            f'"{name}" is not set in the environment. Check your .env file or '
            f"create one if you don't have it."
        )


def generate_loading_embed(message: Optional[str] = None):
    return discord.Embed(
        title=message if message else choice(LOADING_MESSAGES),
        color=EMBED_COLORS["loading"],
    )
