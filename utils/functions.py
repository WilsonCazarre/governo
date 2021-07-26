import os
from typing import Optional
from random import choice

import discord
from discord.ext import commands

from utils import exceptions
from google.oauth2 import service_account
from googleapiclient.discovery import build

from utils.constants import GOOGLE_API_SECRETS, LOADING_MESSAGES, EMBED_COLORS

SCOPES = ["https://www.googleapis.com/auth/drive"]


def get_env_variable(name: str):
    try:
        return os.environ[name]
    except KeyError:
        raise exceptions.MissingEnvironmentVariable(
            f'"{name}" is not set in the environment. Check your .env file or'
            f"create one if you don't have it."
        )


def get_spreadsheet_service():
    if GOOGLE_API_SECRETS.exists():
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_API_SECRETS, scopes=SCOPES
        )
    else:
        raise FileNotFoundError("client_secrets.json not found")

    return build("sheets", "v4", credentials=credentials).spreadsheets()


def generate_loading_embed(message: Optional[str] = None):
    return discord.Embed(
        title=message if message else choice(LOADING_MESSAGES),
        color=EMBED_COLORS["loading"],
    )
